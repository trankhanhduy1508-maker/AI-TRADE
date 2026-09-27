"""MetaApi cloud MT5 adapter.

This is the cloud-only execution path. It talks to a MetaTrader account through
MetaApi REST instead of requiring a local Windows MetaTrader terminal.

Secrets are injected at runtime and never persisted by this module.
LIVE accounts are rejected. The adapter is intentionally DEMO-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from src.execution.mt5_adapter import (
    MT5OrderRequest,
    MT5OrderResult,
    MT5Position,
    OrderIntentLedger,
    TradingDisabledError,
)


class MetaApiTransport(Protocol):
    def request(
        self,
        method: str,
        url: str,
        *,
        token: str,
        body: dict[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> Any: ...


class UrllibMetaApiTransport:
    """Small stdlib HTTP transport to avoid coupling the core to one SDK."""

    def request(
        self,
        method: str,
        url: str,
        *,
        token: str,
        body: dict[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> Any:
        headers = {
            "Accept": "application/json",
            "auth-token": token,
        }
        data = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body, separators=(",", ":")).encode("utf-8")
        request = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=timeout) as response:
                payload = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"MetaApi HTTP {exc.code}: {detail[:500]}") from exc
        except URLError as exc:
            raise ConnectionError(f"MetaApi network error: {exc.reason}") from exc
        return json.loads(payload) if payload else None


@dataclass(frozen=True)
class MetaApiCloudConfig:
    account_id: str
    token: str
    region: str = "new-york"
    client_base_url: str | None = None
    market_base_url: str | None = None
    request_timeout: float = 30.0

    def __post_init__(self) -> None:
        if not self.account_id.strip():
            raise ValueError("MetaApi account_id is required")
        if not self.token.strip():
            raise ValueError("MetaApi token is required")
        if not self.region.strip():
            raise ValueError("MetaApi region is required")
        if not math.isfinite(self.request_timeout) or self.request_timeout <= 0:
            raise ValueError("request_timeout must be finite and positive")

    @property
    def client_base(self) -> str:
        return (
            self.client_base_url.rstrip("/")
            if self.client_base_url
            else f"https://mt-client-api-v1.{self.region}.agiliumtrade.ai"
        )

    @property
    def market_base(self) -> str:
        return (
            self.market_base_url.rstrip("/")
            if self.market_base_url
            else f"https://mt-market-data-client-api-v1.{self.region}.agiliumtrade.ai"
        )


@dataclass(frozen=True)
class MetaApiSymbolContract:
    tick_size: float
    digits: int
    min_volume: float
    max_volume: float
    volume_step: float

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "MetaApiSymbolContract":
        contract = cls(
            tick_size=float(payload["tickSize"]),
            digits=int(payload["digits"]),
            min_volume=float(payload["minVolume"]),
            max_volume=float(payload["maxVolume"]),
            volume_step=float(payload["volumeStep"]),
        )
        if (
            contract.tick_size <= 0
            or contract.digits < 0
            or contract.min_volume <= 0
            or contract.max_volume < contract.min_volume
            or contract.volume_step <= 0
        ):
            raise ValueError("invalid MetaApi symbol specification")
        return contract

    def valid_volume(self, volume: float) -> bool:
        if not math.isfinite(volume) or volume < self.min_volume or volume > self.max_volume:
            return False
        steps = (volume - self.min_volume) / self.volume_step
        return math.isclose(steps, round(steps), rel_tol=0.0, abs_tol=1e-9)


class MetaApiCloudAdapter:
    """Duck-compatible broker adapter for the existing AI-TRADE coordinators."""

    SUCCESS_CODES = {10009: "FILLED", 10010: "PARTIAL"}

    def __init__(
        self,
        config: MetaApiCloudConfig,
        *,
        ledger_path: str | Path = ":memory:",
        allow_order_send: bool = False,
        transport: MetaApiTransport | None = None,
    ):
        self.config = config
        self._allow_order_send = allow_order_send
        self._transport = transport or UrllibMetaApiTransport()
        self._ledger = OrderIntentLedger(ledger_path)
        self._connected = False

    def connect(self) -> bool:
        info = self.account_information(refresh=True)
        account_type = str(info.get("type", ""))
        if account_type != "ACCOUNT_TRADE_MODE_DEMO":
            raise TradingDisabledError("MetaApi DEMO account required; LIVE is locked")
        if info.get("tradeAllowed") is not True:
            raise TradingDisabledError("MetaApi DEMO account trading is disabled")
        self._connected = True
        return True

    def close(self) -> None:
        self._ledger.close()
        self._connected = False

    def account_information(self, *, refresh: bool = False) -> dict[str, Any]:
        path = "/account-information"
        if refresh:
            path += "?refreshTerminalState=true"
        result = self._client_get(path)
        if not isinstance(result, dict):
            raise RuntimeError("invalid MetaApi account-information response")
        return result

    def positions(self, symbol: str | None = None) -> tuple[MT5Position, ...]:
        rows = self._client_get("/positions?refreshTerminalState=true")
        if not isinstance(rows, list):
            raise RuntimeError("invalid MetaApi positions response")
        positions = tuple(self._position_from_payload(row) for row in rows)
        if symbol is not None:
            positions = tuple(position for position in positions if position.symbol == symbol)
        return positions

    def broker_position_ids(self, *, magic: int | None = None) -> set[str]:
        positions = self.positions()
        if magic is not None:
            positions = tuple(position for position in positions if position.magic == magic)
        return {position.position_id for position in positions}

    def current_price(self, symbol: str) -> dict[str, Any]:
        result = self._client_get(
            f"/symbols/{quote(symbol, safe='')}/current-price?keepSubscription=true"
        )
        if not isinstance(result, dict):
            raise RuntimeError("invalid MetaApi current-price response")
        bid = float(result.get("bid", 0.0))
        ask = float(result.get("ask", 0.0))
        if not math.isfinite(bid) or not math.isfinite(ask) or bid <= 0 or ask <= 0 or bid > ask:
            raise RuntimeError("invalid MetaApi price")
        return result

    def symbol_contract(self, symbol: str) -> MetaApiSymbolContract:
        result = self._client_get(f"/symbols/{quote(symbol, safe='')}/specification")
        if not isinstance(result, dict):
            raise RuntimeError("invalid MetaApi specification response")
        return MetaApiSymbolContract.from_payload(result)

    def historical_candles(
        self,
        symbol: str,
        timeframe: str,
        *,
        limit: int,
    ) -> tuple[dict[str, Any], ...]:
        if not 1 <= limit <= 1000:
            raise ValueError("MetaApi candle limit must be between 1 and 1000")
        query = urlencode({"limit": limit})
        path = (
            f"/historical-market-data/symbols/{quote(symbol, safe='')}"
            f"/timeframes/{quote(timeframe, safe='')}/candles?{query}"
        )
        rows = self._market_get(path)
        if not isinstance(rows, list):
            raise RuntimeError("invalid MetaApi candles response")
        return tuple(rows)

    def daily_pnl(self, *, magic: int, now: datetime | None = None) -> float:
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        current = current.astimezone(timezone.utc)
        start = current.replace(hour=0, minute=0, second=0, microsecond=0)
        start_iso = start.isoformat(timespec="milliseconds").replace("+00:00", "Z")
        end_iso = current.isoformat(timespec="milliseconds").replace("+00:00", "Z")
        path = (
            "/history-deals/time/"
            f"{quote(start_iso, safe=':.-TZ')}/{quote(end_iso, safe=':.-TZ')}"
            "?limit=1000"
        )
        rows = self._client_get(path)
        if not isinstance(rows, list):
            raise RuntimeError("invalid MetaApi history-deals response")
        total = 0.0
        for deal in rows:
            if int(deal.get("magic", 0) or 0) != magic:
                continue
            total += float(deal.get("profit", 0.0) or 0.0)
            total += float(deal.get("commission", 0.0) or 0.0)
            total += float(deal.get("swap", 0.0) or 0.0)
            total += float(deal.get("fee", 0.0) or 0.0)
        return total

    def submit(self, order: MT5OrderRequest) -> MT5OrderResult:
        duplicate = self._duplicate_result(order.client_order_id)
        if duplicate is not None:
            return duplicate
        self._ensure_send_allowed()
        if not self._connected:
            self.connect()
        contract = self.symbol_contract(order.symbol)
        rejection = self._entry_rejection(order, contract)
        if rejection is not None:
            return MT5OrderResult(order.client_order_id, "CONTRACT_REJECTED", message=rejection)

        client_id = self._cloud_client_id(order.client_order_id)
        body: dict[str, Any] = {
            "actionType": "ORDER_TYPE_BUY" if order.direction.upper() == "UP" else "ORDER_TYPE_SELL",
            "symbol": order.symbol,
            "volume": order.volume,
            "clientId": client_id,
            "magic": order.magic,
        }
        if order.stop_loss is not None:
            body["stopLoss"] = order.stop_loss
        if order.take_profit is not None:
            body["takeProfit"] = order.take_profit

        self._ledger.record(order.client_order_id, "SUBMITTING")
        return self._trade(order.client_order_id, body)

    def modify_position(
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
        self._ensure_send_allowed()
        position = self._require_position(position_id)
        price = self.current_price(position.symbol)
        market_price = float(price["bid"] if position.direction == "UP" else price["ask"])
        if position.direction == "UP":
            if stop_loss >= market_price:
                return MT5OrderResult(client_order_id, "CONTRACT_REJECTED", message="STOP_DISTANCE_INVALID")
            if position.stop_loss is not None and stop_loss < position.stop_loss:
                return MT5OrderResult(client_order_id, "RISK_REJECTED", message="STOP_WOULD_INCREASE_RISK")
        else:
            if stop_loss <= market_price:
                return MT5OrderResult(client_order_id, "CONTRACT_REJECTED", message="STOP_DISTANCE_INVALID")
            if position.stop_loss is not None and stop_loss > position.stop_loss:
                return MT5OrderResult(client_order_id, "RISK_REJECTED", message="STOP_WOULD_INCREASE_RISK")

        body: dict[str, Any] = {
            "actionType": "POSITION_MODIFY",
            "positionId": str(position_id),
            "stopLoss": stop_loss,
        }
        body["takeProfit"] = take_profit if take_profit is not None else 0.0
        self._ledger.record(client_order_id, "SUBMITTING", str(position_id))
        return self._trade(client_order_id, body, broker_order_id=str(position_id))

    def normalize_partial_volume(self, position: MT5Position, fraction: float) -> float:
        if not math.isfinite(fraction) or not 0 < fraction < 1:
            raise ValueError("fraction must be between 0 and 1")
        contract = self.symbol_contract(position.symbol)
        raw = position.volume * fraction
        steps = math.floor((raw + 1e-12) / contract.volume_step)
        volume = round(steps * contract.volume_step, contract.digits)
        if volume < contract.min_volume:
            volume = contract.min_volume
        remaining = position.volume - volume
        if remaining > 1e-12 and remaining < contract.min_volume:
            volume = position.volume - contract.min_volume
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
        duplicate = self._duplicate_result(client_order_id)
        if duplicate is not None:
            return duplicate
        self._ensure_send_allowed()
        position = self._require_position(position_id)
        body: dict[str, Any] = {
            "actionType": "POSITION_CLOSE_ID" if volume is None else "POSITION_PARTIAL",
            "positionId": str(position_id),
            "clientId": self._cloud_client_id(client_order_id),
            "magic": position.magic,
        }
        if volume is not None:
            contract = self.symbol_contract(position.symbol)
            if volume <= 0 or volume >= position.volume or not contract.valid_volume(volume):
                return MT5OrderResult(client_order_id, "CONTRACT_REJECTED", message="CLOSE_VOLUME_INVALID")
            body["volume"] = volume
        self._ledger.record(client_order_id, "SUBMITTING", str(position_id))
        return self._trade(client_order_id, body, broker_order_id=str(position_id))

    def _ensure_send_allowed(self) -> None:
        if not self._allow_order_send:
            raise TradingDisabledError("MetaApi order submission is disabled")

    def _entry_rejection(
        self,
        order: MT5OrderRequest,
        contract: MetaApiSymbolContract,
    ) -> str | None:
        if not contract.valid_volume(order.volume):
            return "VOLUME_INVALID"
        direction = order.direction.upper()
        if order.stop_loss is None:
            return "STOP_REQUIRED"
        if direction == "UP":
            if order.stop_loss >= order.price:
                return "STOP_DISTANCE_INVALID"
            if order.take_profit is not None and order.take_profit <= order.price:
                return "TARGET_DISTANCE_INVALID"
        else:
            if order.stop_loss <= order.price:
                return "STOP_DISTANCE_INVALID"
            if order.take_profit is not None and order.take_profit >= order.price:
                return "TARGET_DISTANCE_INVALID"
        return None

    def _require_position(self, position_id: str) -> MT5Position:
        for position in self.positions():
            if position.position_id == str(position_id):
                return position
        raise LookupError(f"MetaApi position {position_id} not found")

    def _position_from_payload(self, row: dict[str, Any]) -> MT5Position:
        kind = str(row.get("type", ""))
        if kind == "POSITION_TYPE_BUY":
            direction = "UP"
        elif kind == "POSITION_TYPE_SELL":
            direction = "DOWN"
        else:
            raise RuntimeError(f"unknown MetaApi position type: {kind}")
        stop = float(row.get("stopLoss", 0.0) or 0.0)
        target = float(row.get("takeProfit", 0.0) or 0.0)
        return MT5Position(
            position_id=str(row["id"]),
            symbol=str(row["symbol"]),
            direction=direction,
            volume=float(row["volume"]),
            entry_price=float(row["openPrice"]),
            stop_loss=stop if stop > 0 else None,
            take_profit=target if target > 0 else None,
            magic=int(row.get("magic", 0) or 0),
            comment=str(row.get("clientId", "") or row.get("comment", "") or ""),
        )

    def _trade(
        self,
        client_order_id: str,
        body: dict[str, Any],
        *,
        broker_order_id: str | None = None,
    ) -> MT5OrderResult:
        response = self._client_post("/trade", body)
        if not isinstance(response, dict):
            self._ledger.record(client_order_id, "REJECTED", broker_order_id)
            return MT5OrderResult(client_order_id, "REJECTED", broker_order_id, message="invalid MetaApi trade response")
        code_raw = response.get("numericCode")
        code = int(code_raw) if isinstance(code_raw, (int, float)) else None
        status = self.SUCCESS_CODES.get(code, "REJECTED")
        remote_id = (
            str(response.get("positionId") or response.get("orderId") or broker_order_id or "")
            or None
        )
        message = str(response.get("message", "") or response.get("stringCode", ""))
        self._ledger.record(client_order_id, status, remote_id, code)
        return MT5OrderResult(client_order_id, status, remote_id, code, message)

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

    @staticmethod
    def _cloud_client_id(client_order_id: str) -> str:
        digest = hashlib.sha256(client_order_id.encode("utf-8")).hexdigest()
        return f"AI_{digest[:8]}_{digest[8:16]}"

    def _client_get(self, path: str) -> Any:
        return self._request("GET", self.config.client_base + self._account_path(path))

    def _client_post(self, path: str, body: dict[str, Any]) -> Any:
        return self._request("POST", self.config.client_base + self._account_path(path), body)

    def _market_get(self, path: str) -> Any:
        return self._request("GET", self.config.market_base + self._account_path(path))

    def _account_path(self, path: str) -> str:
        return f"/users/current/accounts/{quote(self.config.account_id, safe='')}{path}"

    def _request(
        self,
        method: str,
        url: str,
        body: dict[str, Any] | None = None,
    ) -> Any:
        return self._transport.request(
            method,
            url,
            token=self.config.token,
            body=body,
            timeout=self.config.request_timeout,
        )
