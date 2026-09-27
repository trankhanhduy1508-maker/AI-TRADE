"""Fail-closed MetaTrader 5 adapter for DEMO execution and position lifecycle.

The adapter deliberately uses dependency injection instead of importing the
optional MetaTrader5 package. LIVE mode is hard locked. Every mutating action
uses a persistent client intent id so restart/retry cannot silently duplicate
broker risk.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
import math
from pathlib import Path
import sqlite3
from typing import Any


class ExecutionMode(StrEnum):
    DISABLED = "DISABLED"
    DEMO = "DEMO"
    LIVE = "LIVE"


class TradingDisabledError(RuntimeError):
    """Raised when an execution path is not explicitly enabled and safe."""


DEMO_ACCOUNT_TRADE_MODE = 0


@dataclass(frozen=True)
class MT5OrderRequest:
    client_order_id: str
    symbol: str
    direction: str
    volume: float
    price: float
    stop_loss: float | None = None
    take_profit: float | None = None
    magic: int = 260926

    def __post_init__(self) -> None:
        if not self.client_order_id.strip():
            raise ValueError("client_order_id is required")
        if not self.symbol.strip():
            raise ValueError("symbol is required")
        if self.direction.upper() not in {"UP", "DOWN"}:
            raise ValueError("direction must be UP or DOWN")
        if not math.isfinite(self.volume) or self.volume <= 0:
            raise ValueError("volume must be finite and positive")
        if not math.isfinite(self.price) or self.price <= 0:
            raise ValueError("price must be finite and positive")
        if self.magic < 0:
            raise ValueError("magic must be non-negative")


@dataclass(frozen=True)
class MT5OrderResult:
    client_order_id: str
    status: str
    broker_order_id: str | None = None
    retcode: int | None = None
    message: str = ""


@dataclass(frozen=True)
class MT5Position:
    position_id: str
    symbol: str
    direction: str
    volume: float
    entry_price: float
    stop_loss: float | None
    take_profit: float | None
    magic: int = 0
    comment: str = ""


@dataclass(frozen=True)
class MT5SymbolContract:
    """Broker symbol constraints needed before an order-check call."""

    point: float
    digits: int
    volume_min: float
    volume_max: float
    volume_step: float
    trade_stops_level: int = 0
    trade_mode: int | None = None

    @classmethod
    def from_info(cls, info: Any) -> "MT5SymbolContract":
        if info is None:
            raise ValueError("SYMBOL_INFO_MISSING")
        required = (
            "point",
            "digits",
            "volume_min",
            "volume_max",
            "volume_step",
            "trade_stops_level",
        )
        if any(not hasattr(info, name) for name in required):
            raise ValueError("SYMBOL_INFO_INCOMPLETE")
        point = float(info.point)
        volume_min = float(info.volume_min)
        volume_max = float(info.volume_max)
        volume_step = float(info.volume_step)
        stops_level = int(info.trade_stops_level)
        digits = int(info.digits)
        if (
            not math.isfinite(point)
            or point <= 0
            or not math.isfinite(volume_min)
            or not math.isfinite(volume_max)
            or not math.isfinite(volume_step)
            or volume_min <= 0
            or volume_max < volume_min
            or volume_step <= 0
            or digits < 0
            or stops_level < 0
        ):
            raise ValueError("SYMBOL_INFO_INVALID")
        return cls(
            point=point,
            digits=digits,
            volume_min=volume_min,
            volume_max=volume_max,
            volume_step=volume_step,
            trade_stops_level=stops_level,
            trade_mode=getattr(info, "trade_mode", None),
        )

    def rejection_reason(self, order: MT5OrderRequest) -> str | None:
        if self.trade_mode == 0:
            return "TRADE_MODE_DISABLED"
        if order.volume < self.volume_min or order.volume > self.volume_max:
            return "VOLUME_OUT_OF_RANGE"
        steps = (order.volume - self.volume_min) / self.volume_step
        if not math.isclose(steps, round(steps), rel_tol=0.0, abs_tol=1e-9):
            return "VOLUME_STEP_INVALID"
        minimum_distance = self.trade_stops_level * self.point
        direction = order.direction.upper()
        if direction == "UP":
            if order.stop_loss is not None and (
                order.stop_loss >= order.price
                or order.stop_loss > order.price - minimum_distance
            ):
                return "STOP_DISTANCE_INVALID"
            if order.take_profit is not None and (
                order.take_profit <= order.price
                or order.take_profit < order.price + minimum_distance
            ):
                return "TARGET_DISTANCE_INVALID"
        else:
            if order.stop_loss is not None and (
                order.stop_loss <= order.price
                or order.stop_loss < order.price + minimum_distance
            ):
                return "STOP_DISTANCE_INVALID"
            if order.take_profit is not None and (
                order.take_profit >= order.price
                or order.take_profit > order.price - minimum_distance
            ):
                return "TARGET_DISTANCE_INVALID"
        return None

    def valid_volume(self, volume: float) -> bool:
        if not math.isfinite(volume) or volume < self.volume_min or volume > self.volume_max:
            return False
        steps = (volume - self.volume_min) / self.volume_step
        return math.isclose(steps, round(steps), rel_tol=0.0, abs_tol=1e-9)


class OrderIntentLedger:
    """Persistent ledger used to fail closed on ambiguous retries."""

    def __init__(self, path: str | Path):
        self._connection = sqlite3.connect(str(path))
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS order_intents (
                client_order_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                broker_order_id TEXT,
                retcode INTEGER,
                updated_at TEXT NOT NULL
            )
            """
        )
        self._connection.commit()

    def get(self, client_order_id: str) -> tuple[str, str | None, int | None] | None:
        row = self._connection.execute(
            "SELECT status, broker_order_id, retcode FROM order_intents "
            "WHERE client_order_id = ?",
            (client_order_id,),
        ).fetchone()
        return row if row is not None else None

    def record(
        self,
        client_order_id: str,
        status: str,
        broker_order_id: str | None = None,
        retcode: int | None = None,
    ) -> None:
        self._connection.execute(
            """
            INSERT INTO order_intents
              (client_order_id, status, broker_order_id, retcode, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(client_order_id) DO UPDATE SET
              status=excluded.status,
              broker_order_id=excluded.broker_order_id,
              retcode=excluded.retcode,
              updated_at=excluded.updated_at
            """,
            (
                client_order_id,
                status,
                broker_order_id,
                retcode,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self._connection.commit()

    def close(self) -> None:
        self._connection.close()


class MT5BrokerAdapter:
    """Fail-closed MT5 Python integration boundary, DEMO only."""

    def __init__(
        self,
        terminal: Any,
        *,
        mode: ExecutionMode = ExecutionMode.DISABLED,
        allow_order_send: bool = False,
        ledger_path: str | Path = ":memory:",
    ):
        self._terminal = terminal
        self._mode = ExecutionMode(mode)
        self._allow_order_send = allow_order_send
        self._ledger = OrderIntentLedger(ledger_path)
        self._connected = False

    def connect(self) -> bool:
        if self._mode == ExecutionMode.DISABLED:
            return False
        if self._mode == ExecutionMode.LIVE:
            raise TradingDisabledError("LIVE execution is locked")
        initialized = bool(self._terminal.initialize())
        if not initialized:
            return False
        account_info = getattr(self._terminal, "account_info", None)
        if not callable(account_info):
            self._terminal.shutdown()
            return False
        info = account_info()
        if info is None:
            self._terminal.shutdown()
            return False
        trade_mode = getattr(info, "trade_mode", None)
        if trade_mode != DEMO_ACCOUNT_TRADE_MODE:
            self._terminal.shutdown()
            raise TradingDisabledError("DEMO account is required")
        if getattr(info, "trade_allowed", None) is not True or getattr(
            info, "trade_expert", None
        ) is not True:
            self._terminal.shutdown()
            raise TradingDisabledError("account trading disabled")
        self._connected = True
        return True

    def close(self) -> None:
        if self._connected:
            self._terminal.shutdown()
            self._connected = False
        self._ledger.close()

    def submit(self, order: MT5OrderRequest) -> MT5OrderResult:
        duplicate = self._duplicate_result(order.client_order_id)
        if duplicate is not None:
            return duplicate
        self._ensure_mutation_allowed()
        if not self._connected and not self.connect():
            raise ConnectionError("MT5 terminal initialization failed")

        contract_result = self._validate_contract(order)
        if contract_result is not None:
            return contract_result

        self._ledger.record(order.client_order_id, "SUBMITTING")
        return self._checked_send(order.client_order_id, self._request_dict(order))

    def positions(self, symbol: str | None = None) -> tuple[MT5Position, ...]:
        self._ensure_read_allowed()
        if not self._connected and not self.connect():
            raise ConnectionError("MT5 terminal initialization failed")
        getter = getattr(self._terminal, "positions_get", None)
        if not callable(getter):
            raise RuntimeError("positions_get is unavailable")
        records = getter(symbol=symbol) if symbol is not None else getter()
        if records is None:
            raise RuntimeError("positions_get failed")
        return tuple(self._position_from_record(record) for record in records)

    def broker_position_ids(self, *, magic: int | None = None) -> set[str]:
        positions = self.positions()
        if magic is not None:
            positions = tuple(position for position in positions if position.magic == magic)
        return {position.position_id for position in positions}

    def modify_position(
        self,
        position_id: str,
        *,
        client_order_id: str,
        stop_loss: float,
        take_profit: float | None = None,
    ) -> MT5OrderResult:
        """Ratchet protective levels without ever increasing risk."""
        if not client_order_id.strip():
            raise ValueError("client_order_id is required")
        self._ensure_mutation_allowed()
        duplicate = self._duplicate_result(client_order_id)
        if duplicate is not None:
            return duplicate
        position = self._require_position(position_id)
        tick = self._require_tick(position.symbol)
        contract = self._require_contract(position.symbol)
        market_price = float(tick.bid if position.direction == "UP" else tick.ask)
        validation = MT5OrderRequest(
            client_order_id=client_order_id,
            symbol=position.symbol,
            direction=position.direction,
            volume=position.volume,
            price=market_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )
        rejection = contract.rejection_reason(validation)
        if rejection is not None:
            return MT5OrderResult(client_order_id, "CONTRACT_REJECTED", message=rejection)

        if position.stop_loss is not None:
            if position.direction == "UP" and stop_loss < position.stop_loss:
                return MT5OrderResult(client_order_id, "RISK_REJECTED", message="STOP_WOULD_INCREASE_RISK")
            if position.direction == "DOWN" and stop_loss > position.stop_loss:
                return MT5OrderResult(client_order_id, "RISK_REJECTED", message="STOP_WOULD_INCREASE_RISK")

        self._ledger.record(client_order_id, "SUBMITTING")
        request: dict[str, object] = {
            "action": getattr(self._terminal, "TRADE_ACTION_SLTP"),
            "position": int(position.position_id),
            "symbol": position.symbol,
            "sl": stop_loss,
            "tp": take_profit or 0.0,
            "comment": client_order_id,
        }
        return self._checked_send(client_order_id, request, broker_order_id=position.position_id)

    def normalize_partial_volume(self, position: MT5Position, fraction: float) -> float:
        if not math.isfinite(fraction) or not 0 < fraction < 1:
            raise ValueError("fraction must be between 0 and 1")
        contract = self._require_contract(position.symbol)
        raw = position.volume * fraction
        steps = math.floor((raw + 1e-12) / contract.volume_step)
        volume = round(steps * contract.volume_step, contract.digits)
        if volume < contract.volume_min:
            volume = contract.volume_min
        remaining = position.volume - volume
        if remaining > 1e-12 and remaining < contract.volume_min:
            volume = position.volume - contract.volume_min
        if volume <= 0 or volume >= position.volume or not contract.valid_volume(volume):
            raise ValueError("PARTIAL_VOLUME_NOT_REPRESENTABLE")
        return volume

    def close_position(
        self,
        position_id: str,
        *,
        client_order_id: str,
        volume: float | None = None,
    ) -> MT5OrderResult:
        """Close all or part of a DEMO position with duplicate suppression."""
        if not client_order_id.strip():
            raise ValueError("client_order_id is required")
        self._ensure_mutation_allowed()
        duplicate = self._duplicate_result(client_order_id)
        if duplicate is not None:
            return duplicate
        position = self._require_position(position_id)
        close_volume = position.volume if volume is None else float(volume)
        if close_volume <= 0 or close_volume > position.volume:
            return MT5OrderResult(client_order_id, "CONTRACT_REJECTED", message="CLOSE_VOLUME_INVALID")
        contract = self._require_contract(position.symbol)
        if not math.isclose(close_volume, position.volume, rel_tol=0.0, abs_tol=1e-12) and not contract.valid_volume(close_volume):
            return MT5OrderResult(client_order_id, "CONTRACT_REJECTED", message="CLOSE_VOLUME_STEP_INVALID")
        tick = self._require_tick(position.symbol)
        if position.direction == "UP":
            order_type = getattr(self._terminal, "ORDER_TYPE_SELL")
            price = float(tick.bid)
        else:
            order_type = getattr(self._terminal, "ORDER_TYPE_BUY")
            price = float(tick.ask)

        self._ledger.record(client_order_id, "SUBMITTING")
        request = {
            "action": getattr(self._terminal, "TRADE_ACTION_DEAL"),
            "position": int(position.position_id),
            "symbol": position.symbol,
            "volume": close_volume,
            "type": order_type,
            "price": price,
            "deviation": 0,
            "comment": client_order_id,
        }
        return self._checked_send(client_order_id, request, broker_order_id=position.position_id)

    def _ensure_read_allowed(self) -> None:
        if self._mode == ExecutionMode.DISABLED:
            raise TradingDisabledError("MT5 access is disabled")
        if self._mode == ExecutionMode.LIVE:
            raise TradingDisabledError("LIVE execution is locked")

    def _ensure_mutation_allowed(self) -> None:
        if self._mode == ExecutionMode.DISABLED or not self._allow_order_send:
            raise TradingDisabledError("order submission is disabled")
        if self._mode == ExecutionMode.LIVE:
            raise TradingDisabledError("LIVE execution is locked")

    def _duplicate_result(self, client_order_id: str) -> MT5OrderResult | None:
        existing = self._ledger.get(client_order_id)
        if existing is None:
            return None
        status, broker_order_id, retcode = existing
        return MT5OrderResult(
            client_order_id=client_order_id,
            status="DUPLICATE_SUPPRESSED",
            broker_order_id=broker_order_id,
            retcode=retcode,
            message=f"existing intent status={status}; reconcile before retry",
        )

    def _validate_contract(self, order: MT5OrderRequest) -> MT5OrderResult | None:
        try:
            contract = self._require_contract(order.symbol)
        except (AttributeError, TypeError, ValueError, OverflowError) as exc:
            return MT5OrderResult(order.client_order_id, "CONTRACT_REJECTED", message=str(exc))
        rejection = contract.rejection_reason(order)
        if rejection is None:
            return None
        return MT5OrderResult(order.client_order_id, "CONTRACT_REJECTED", message=rejection)

    def _require_contract(self, symbol: str) -> MT5SymbolContract:
        getter = getattr(self._terminal, "symbol_info", None)
        if not callable(getter):
            raise ValueError("SYMBOL_INFO_MISSING")
        return MT5SymbolContract.from_info(getter(symbol))

    def _require_tick(self, symbol: str) -> Any:
        getter = getattr(self._terminal, "symbol_info_tick", None)
        if not callable(getter):
            raise RuntimeError("symbol_info_tick is unavailable")
        tick = getter(symbol)
        if tick is None:
            raise RuntimeError("symbol_info_tick failed")
        bid = float(getattr(tick, "bid", 0.0))
        ask = float(getattr(tick, "ask", 0.0))
        if not math.isfinite(bid) or not math.isfinite(ask) or bid <= 0 or ask <= 0 or bid > ask:
            raise RuntimeError("invalid tick")
        return tick

    def _require_position(self, position_id: str) -> MT5Position:
        for position in self.positions():
            if position.position_id == str(position_id):
                return position
        raise LookupError(f"position {position_id} not found")

    def _position_from_record(self, record: Any) -> MT5Position:
        ticket = self._optional_id(getattr(record, "ticket", None))
        if ticket is None:
            raise RuntimeError("position has no ticket")
        position_type = getattr(record, "type", None)
        buy_type = getattr(self._terminal, "POSITION_TYPE_BUY", 0)
        sell_type = getattr(self._terminal, "POSITION_TYPE_SELL", 1)
        if position_type == buy_type:
            direction = "UP"
        elif position_type == sell_type:
            direction = "DOWN"
        else:
            raise RuntimeError("unknown position type")
        stop = float(getattr(record, "sl", 0.0) or 0.0)
        target = float(getattr(record, "tp", 0.0) or 0.0)
        return MT5Position(
            position_id=ticket,
            symbol=str(record.symbol),
            direction=direction,
            volume=float(record.volume),
            entry_price=float(record.price_open),
            stop_loss=stop if stop > 0 else None,
            take_profit=target if target > 0 else None,
            magic=int(getattr(record, "magic", 0) or 0),
            comment=str(getattr(record, "comment", "") or ""),
        )

    def _checked_send(
        self,
        client_order_id: str,
        request: dict[str, object],
        *,
        broker_order_id: str | None = None,
    ) -> MT5OrderResult:
        check = self._terminal.order_check(request)
        check_retcode = self._retcode(check)
        if check_retcode != 0:
            message = str(getattr(check, "comment", "order_check rejected"))
            self._ledger.record(client_order_id, "CHECK_REJECTED", broker_order_id, check_retcode)
            return MT5OrderResult(client_order_id, "CHECK_REJECTED", broker_order_id, check_retcode, message)

        response = self._terminal.order_send(request)
        retcode = self._retcode(response)
        returned_order_id = self._optional_id(getattr(response, "order", None)) or broker_order_id
        status = "FILLED" if retcode == 10009 else "PARTIAL" if retcode == 10010 else "REJECTED"
        message = str(getattr(response, "comment", ""))
        self._ledger.record(client_order_id, status, returned_order_id, retcode)
        return MT5OrderResult(client_order_id, status, returned_order_id, retcode, message)

    def _request_dict(self, order: MT5OrderRequest) -> dict[str, object]:
        direction = order.direction.upper()
        request: dict[str, object] = {
            "action": getattr(self._terminal, "TRADE_ACTION_DEAL"),
            "symbol": order.symbol,
            "volume": order.volume,
            "type": getattr(self._terminal, "ORDER_TYPE_BUY" if direction == "UP" else "ORDER_TYPE_SELL"),
            "price": order.price,
            "deviation": 0,
            "comment": order.client_order_id,
            "magic": order.magic,
        }
        if order.stop_loss is not None:
            request["sl"] = order.stop_loss
        if order.take_profit is not None:
            request["tp"] = order.take_profit
        return request

    @staticmethod
    def _retcode(result: Any) -> int:
        value = getattr(result, "retcode", None)
        if not isinstance(value, int):
            raise RuntimeError("MT5 response has no integer retcode")
        return value

    @staticmethod
    def _optional_id(value: Any) -> str | None:
        return str(value) if value not in (None, 0, "") else None
