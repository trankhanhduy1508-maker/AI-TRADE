"""Async MetaApi cloud adapter for MT5 DEMO execution.

This path removes the Windows/desktop MetaTrader dependency. The account is
hosted by MetaApi and accessed through its official Python SDK/WebSocket API.
LIVE is deliberately not implemented here.
"""

from __future__ import annotations

import hashlib
import math
from pathlib import Path
from typing import Any

from src.execution.demo_readback import DemoAccountSnapshot
from src.execution.metaapi_demo_guard import MetaApiDemoBlocked, assert_metaapi_demo_context
from src.execution.metaapi_readback import read_metaapi_demo_snapshot
from src.execution.mt5_adapter import (
    MT5OrderRequest,
    MT5OrderResult,
    MT5Position,
    MT5SymbolContract,
    OrderIntentLedger,
    TradingDisabledError,
)


def _get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(key, default)
    return getattr(value, key, default)


class MetaApiCloudAdapter:
    """Fail-closed async broker adapter for a MetaApi-hosted MT5 DEMO account."""

    def __init__(
        self,
        account: Any,
        connection: Any,
        *,
        allow_order_send: bool = False,
        ledger_path: str | Path = ":memory:",
    ):
        self.account = account
        self.connection = connection
        self.allow_order_send = allow_order_send
        self._ledger = OrderIntentLedger(ledger_path)
        self._connected = False

    async def connect(self) -> bool:
        platform = str(_get(self.account, "platform", "")).lower()
        server = str(_get(self.account, "server", ""))
        if platform != "mt5":
            raise TradingDisabledError("MetaApi cloud path requires MT5")
        # MetaApi account objects do not expose a universal real/demo flag.
        # Fail closed unless the broker server itself is explicitly a DEMO server.
        if "demo" not in server.lower():
            raise TradingDisabledError(
                "DEMO server marker required; live-money cloud execution is locked"
            )

        if str(_get(self.account, "state", "")).upper() != "DEPLOYED":
            await self.account.deploy()
        if str(_get(self.account, "connection_status", "")).upper() != "CONNECTED":
            await self.account.wait_connected()

        await self.connection.connect()
        await self.connection.wait_synchronized()

        terminal = self.connection.terminal_state
        if not bool(_get(terminal, "connected", False)):
            raise ConnectionError("MetaApi terminal state is disconnected")
        if not bool(_get(terminal, "connected_to_broker", False)):
            raise ConnectionError("MetaApi is not connected to broker")

        info = _get(terminal, "account_information")
        if info is None:
            raise ConnectionError("MetaApi account information unavailable")
        if _get(info, "tradeAllowed", _get(info, "trade_allowed", True)) is False:
            raise TradingDisabledError("account trading is disabled")
        if _get(info, "investorMode", _get(info, "investor_mode", False)) is True:
            raise TradingDisabledError("investor/read-only account cannot trade")
        # DEMO-looking broker names are not evidence: confirm the actual mode,
        # login and server from the synchronized MT5 broker account.
        assert_metaapi_demo_context(self.account, terminal)

        self._connected = True
        return True

    async def close(self) -> None:
        close_method = getattr(self.connection, "close", None)
        if callable(close_method):
            result = close_method()
            if hasattr(result, "__await__"):
                await result
        self._connected = False
        self._ledger.close()

    async def account_snapshot(self) -> DemoAccountSnapshot:
        """Read broker DEMO balance/equity/positions, with no order submission.

        Owner authorization is required at the caller. Broker synchronization
        and identity must be confirmed before this read on every request.
        """
        await self._ensure_connected()
        await self.connection.wait_synchronized()
        await self._ensure_connected()
        return read_metaapi_demo_snapshot(self.account, self.connection.terminal_state)

    async def positions(self, symbol: str | None = None) -> tuple[MT5Position, ...]:
        await self._ensure_connected()
        records = _get(self.connection.terminal_state, "positions", None)
        if records is None or not isinstance(records, (tuple, list)):
            raise MetaApiDemoBlocked("BROKER_POSITIONS_INCOMPLETE")
        positions = tuple(self._position_from_record(record) for record in records)
        await self._ensure_connected()
        if symbol is not None:
            positions = tuple(p for p in positions if p.symbol == symbol)
        return positions

    async def broker_position_ids(self, *, magic: int | None = None) -> set[str]:
        positions = await self.positions()
        if magic is not None:
            positions = tuple(position for position in positions if position.magic == magic)
        return {position.position_id for position in positions}

    async def quote(self, symbol: str) -> tuple[float, float, Any]:
        await self._ensure_connected()
        terminal = self.connection.terminal_state
        price = terminal.price(symbol)
        if price is None:
            await self.connection.subscribe_to_market_data(symbol)
            price = terminal.price(symbol)
        if price is None:
            raise RuntimeError(f"MetaApi price unavailable for {symbol}")
        bid = float(_get(price, "bid", 0.0) or 0.0)
        ask = float(_get(price, "ask", 0.0) or 0.0)
        if not math.isfinite(bid) or not math.isfinite(ask) or bid <= 0 or ask <= 0 or bid > ask:
            raise RuntimeError("invalid MetaApi quote")
        return bid, ask, _get(price, "time")

    async def symbol_contract(self, symbol: str) -> MT5SymbolContract:
        await self._ensure_connected()
        spec = self.connection.terminal_state.specification(symbol)
        if spec is None:
            await self.connection.subscribe_to_market_data(symbol)
            spec = self.connection.terminal_state.specification(symbol)
        if spec is None:
            raise ValueError("SYMBOL_INFO_MISSING")
        trade_mode = str(_get(spec, "tradeMode", "")).upper()
        disabled = "DISABLED" in trade_mode if trade_mode else False
        return MT5SymbolContract(
            point=float(_get(spec, "point")),
            digits=int(_get(spec, "digits")),
            volume_min=float(_get(spec, "minVolume")),
            volume_max=float(_get(spec, "maxVolume")),
            volume_step=float(_get(spec, "volumeStep")),
            trade_stops_level=int(_get(spec, "stopsLevel", 0) or 0),
            trade_mode=0 if disabled else 1,
        )

    async def submit(self, order: MT5OrderRequest) -> MT5OrderResult:
        duplicate = self._duplicate_result(order.client_order_id)
        if duplicate is not None:
            return duplicate
        self._ensure_mutation_allowed()
        await self._ensure_connected()

        contract = await self.symbol_contract(order.symbol)
        rejection = contract.rejection_reason(order)
        if rejection is not None:
            return MT5OrderResult(order.client_order_id, "CONTRACT_REJECTED", message=rejection)

        await self._ensure_connected()
        self._ledger.record(order.client_order_id, "SUBMITTING")
        client_id = self._broker_client_id(order.client_order_id)
        options = {"clientId": client_id, "magic": order.magic}
        try:
            if order.direction.upper() == "UP":
                response = await self.connection.create_market_buy_order(
                    order.symbol,
                    order.volume,
                    order.stop_loss,
                    order.take_profit,
                    options,
                )
            else:
                response = await self.connection.create_market_sell_order(
                    order.symbol,
                    order.volume,
                    order.stop_loss,
                    order.take_profit,
                    options,
                )
        except Exception as exc:
            # Keep SUBMITTING in the ledger. A retry with the same intent is
            # suppressed until broker reconciliation resolves the ambiguity.
            return MT5OrderResult(
                order.client_order_id,
                "AMBIGUOUS",
                message=type(exc).__name__,
            )
        return self._record_response(order.client_order_id, response)

    async def modify_position(
        self,
        position_id: str,
        *,
        client_order_id: str,
        stop_loss: float,
        take_profit: float | None = None,
    ) -> MT5OrderResult:
        duplicate = self._duplicate_result(client_order_id)
        if duplicate is not None:
            return duplicate
        self._ensure_mutation_allowed()
        position = await self._require_position(position_id)
        bid, ask, _ = await self.quote(position.symbol)
        contract = await self.symbol_contract(position.symbol)
        market_price = bid if position.direction == "UP" else ask
        validation = MT5OrderRequest(
            client_order_id,
            position.symbol,
            position.direction,
            position.volume,
            market_price,
            stop_loss,
            take_profit,
            position.magic,
        )
        rejection = contract.rejection_reason(validation)
        if rejection is not None:
            return MT5OrderResult(client_order_id, "CONTRACT_REJECTED", message=rejection)
        if position.stop_loss is not None:
            if position.direction == "UP" and stop_loss < position.stop_loss:
                return MT5OrderResult(client_order_id, "RISK_REJECTED", message="STOP_WOULD_INCREASE_RISK")
            if position.direction == "DOWN" and stop_loss > position.stop_loss:
                return MT5OrderResult(client_order_id, "RISK_REJECTED", message="STOP_WOULD_INCREASE_RISK")

        await self._ensure_connected()
        self._ledger.record(client_order_id, "SUBMITTING", position.position_id)
        try:
            response = await self.connection.modify_position(
                position_id,
                stop_loss,
                0.0 if take_profit is None else take_profit,
            )
        except Exception as exc:
            return MT5OrderResult(
                client_order_id,
                "AMBIGUOUS",
                position.position_id,
                message=type(exc).__name__,
            )
        return self._record_response(client_order_id, response, position.position_id)

    async def normalize_partial_volume(self, position: MT5Position, fraction: float) -> float:
        if not math.isfinite(fraction) or not 0 < fraction < 1:
            raise ValueError("fraction must be between 0 and 1")
        contract = await self.symbol_contract(position.symbol)
        raw = position.volume * fraction
        steps = math.floor((raw + 1e-12) / contract.volume_step)
        volume = steps * contract.volume_step
        decimals = max(0, len(f"{contract.volume_step:.10f}".rstrip("0").split(".")[-1]))
        volume = round(volume, decimals)
        if volume < contract.volume_min:
            volume = contract.volume_min
        remaining = position.volume - volume
        if remaining > 1e-12 and remaining < contract.volume_min:
            volume = round(position.volume - contract.volume_min, decimals)
        if volume <= 0 or volume >= position.volume or not contract.valid_volume(volume):
            raise ValueError("PARTIAL_VOLUME_NOT_REPRESENTABLE")
        return volume

    async def close_position(
        self,
        position_id: str,
        *,
        client_order_id: str,
        volume: float | None = None,
    ) -> MT5OrderResult:
        duplicate = self._duplicate_result(client_order_id)
        if duplicate is not None:
            return duplicate
        self._ensure_mutation_allowed()
        position = await self._require_position(position_id)
        close_volume = position.volume if volume is None else float(volume)
        if close_volume <= 0 or close_volume > position.volume:
            return MT5OrderResult(client_order_id, "CONTRACT_REJECTED", message="CLOSE_VOLUME_INVALID")

        contract = await self.symbol_contract(position.symbol)
        partial = not math.isclose(close_volume, position.volume, rel_tol=0.0, abs_tol=1e-12)
        if partial and not contract.valid_volume(close_volume):
            return MT5OrderResult(client_order_id, "CONTRACT_REJECTED", message="CLOSE_VOLUME_STEP_INVALID")

        await self._ensure_connected()
        self._ledger.record(client_order_id, "SUBMITTING", position.position_id)
        try:
            if partial:
                response = await self.connection.close_position_partially(position_id, close_volume)
            else:
                response = await self.connection.close_position(position_id)
        except Exception as exc:
            return MT5OrderResult(
                client_order_id,
                "AMBIGUOUS",
                position.position_id,
                message=type(exc).__name__,
            )
        return self._record_response(client_order_id, response, position.position_id)

    async def _ensure_connected(self) -> None:
        if not self._connected:
            await self.connect()
        else:
            # A stale/changed broker identity invalidates this session until a
            # complete re-synchronization, even if the old account returns.
            try:
                assert_metaapi_demo_context(self.account, self.connection.terminal_state)
            except MetaApiDemoBlocked:
                self._connected = False
                raise

    def _ensure_mutation_allowed(self) -> None:
        if not self.allow_order_send:
            raise TradingDisabledError("MetaApi cloud order submission is disabled")

    async def _require_position(self, position_id: str) -> MT5Position:
        for position in await self.positions():
            if position.position_id == str(position_id):
                return position
        raise LookupError(f"position {position_id} not found")

    def _position_from_record(self, record: Any) -> MT5Position:
        position_type = str(_get(record, "type", "")).upper()
        if position_type == "POSITION_TYPE_BUY":
            direction = "UP"
        elif position_type == "POSITION_TYPE_SELL":
            direction = "DOWN"
        else:
            raise RuntimeError(f"unknown MetaApi position type: {position_type}")
        stop = float(_get(record, "stopLoss", 0.0) or 0.0)
        target = float(_get(record, "takeProfit", 0.0) or 0.0)
        return MT5Position(
            position_id=str(_get(record, "id")),
            symbol=str(_get(record, "symbol")),
            direction=direction,
            volume=float(_get(record, "volume")),
            entry_price=float(_get(record, "openPrice")),
            stop_loss=stop if stop > 0 else None,
            take_profit=target if target > 0 else None,
            magic=int(_get(record, "magic", 0) or 0),
            comment=str(_get(record, "comment", _get(record, "clientId", "")) or ""),
        )

    def _duplicate_result(self, client_order_id: str) -> MT5OrderResult | None:
        existing = self._ledger.get(client_order_id)
        if existing is None:
            return None
        status, broker_order_id, retcode = existing
        return MT5OrderResult(
            client_order_id,
            "DUPLICATE_SUPPRESSED",
            broker_order_id,
            retcode,
            f"existing cloud intent status={status}; reconcile before retry",
        )

    def _record_response(
        self,
        client_order_id: str,
        response: Any,
        fallback_position_id: str | None = None,
    ) -> MT5OrderResult:
        numeric = _get(response, "numericCode")
        retcode = int(numeric) if numeric is not None else None
        string_code = str(_get(response, "stringCode", ""))
        if retcode == 10009 or string_code == "TRADE_RETCODE_DONE":
            status = "FILLED"
        elif retcode == 10010 or string_code == "TRADE_RETCODE_DONE_PARTIAL":
            status = "PARTIAL"
        else:
            status = "REJECTED"
        broker_id = _get(response, "positionId", _get(response, "orderId", fallback_position_id))
        broker_id = str(broker_id) if broker_id not in (None, "") else fallback_position_id
        message = str(_get(response, "message", string_code))
        self._ledger.record(client_order_id, status, broker_id, retcode)
        return MT5OrderResult(client_order_id, status, broker_id, retcode, message)

    @staticmethod
    def _broker_client_id(client_order_id: str) -> str:
        # MetaApi documents comment + clientId <= 26 chars for MT positions.
        if len(client_order_id) <= 26:
            return client_order_id
        return "AI" + hashlib.sha256(client_order_id.encode()).hexdigest()[:20]
