"""Safety boundary for optional MetaTrader 5 order submission.

The adapter deliberately uses dependency injection instead of importing the
optional MetaTrader5 package. This keeps research/test environments offline and
allows the terminal API to be verified with a fake. It is disabled by default,
locks LIVE mode, checks every request before sending, and persists client order
intent IDs so a restart cannot silently resend an ambiguous request.
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
    """Raised when an order path is not explicitly enabled and safe."""


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

    def __post_init__(self) -> None:
        if not self.client_order_id.strip():
            raise ValueError("client_order_id is required")
        if not self.symbol.strip():
            raise ValueError("symbol is required")
        if self.direction.upper() not in {"UP", "DOWN"}:
            raise ValueError("direction must be UP or DOWN")
        if self.volume <= 0:
            raise ValueError("volume must be positive")
        if self.price <= 0:
            raise ValueError("price must be positive")


@dataclass(frozen=True)
class MT5OrderResult:
    client_order_id: str
    status: str
    broker_order_id: str | None = None
    retcode: int | None = None
    message: str = ""


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
            if order.stop_loss is not None and order.stop_loss > order.price - minimum_distance:
                return "STOP_DISTANCE_INVALID"
            if order.take_profit is not None and order.take_profit < order.price + minimum_distance:
                return "TARGET_DISTANCE_INVALID"
        else:
            if order.stop_loss is not None and order.stop_loss < order.price + minimum_distance:
                return "STOP_DISTANCE_INVALID"
            if order.take_profit is not None and order.take_profit > order.price - minimum_distance:
                return "TARGET_DISTANCE_INVALID"
        return None


class OrderIntentLedger:
    """Small persistent ledger used to fail closed on ambiguous retries."""

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
    """Minimal, fail-closed MT5 Python integration boundary."""

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
        existing = self._ledger.get(order.client_order_id)
        if existing is not None:
            status, broker_order_id, retcode = existing
            return MT5OrderResult(
                client_order_id=order.client_order_id,
                status="DUPLICATE_SUPPRESSED",
                broker_order_id=broker_order_id,
                retcode=retcode,
                message=f"existing intent status={status}; reconcile before retry",
            )

        if self._mode == ExecutionMode.DISABLED or not self._allow_order_send:
            raise TradingDisabledError("order submission is disabled")
        if self._mode == ExecutionMode.LIVE:
            raise TradingDisabledError("LIVE execution is locked")
        if not self._connected and not self.connect():
            raise ConnectionError("MT5 terminal initialization failed")

        symbol_info = getattr(self._terminal, "symbol_info", None)
        if not callable(symbol_info):
            return MT5OrderResult(
                client_order_id=order.client_order_id,
                status="CONTRACT_REJECTED",
                message="SYMBOL_INFO_MISSING",
            )
        try:
            contract = MT5SymbolContract.from_info(symbol_info(order.symbol))
        except (AttributeError, TypeError, ValueError, OverflowError) as exc:
            return MT5OrderResult(
                client_order_id=order.client_order_id,
                status="CONTRACT_REJECTED",
                message=str(exc),
            )
        rejection_reason = contract.rejection_reason(order)
        if rejection_reason is not None:
            return MT5OrderResult(
                client_order_id=order.client_order_id,
                status="CONTRACT_REJECTED",
                message=rejection_reason,
            )

        # Record before any terminal call. If the process dies after this point,
        # a restart suppresses the same client ID until reconciliation occurs.
        self._ledger.record(order.client_order_id, "SUBMITTING")
        request = self._request_dict(order)
        check = self._terminal.order_check(request)
        check_retcode = self._retcode(check)
        if check_retcode != 0:
            message = str(getattr(check, "comment", "order_check rejected"))
            self._ledger.record(order.client_order_id, "CHECK_REJECTED", retcode=check_retcode)
            return MT5OrderResult(
                client_order_id=order.client_order_id,
                status="CHECK_REJECTED",
                retcode=check_retcode,
                message=message,
            )

        response = self._terminal.order_send(request)
        retcode = self._retcode(response)
        broker_order_id = self._optional_id(getattr(response, "order", None))
        status = "FILLED" if retcode == 10009 else "PARTIAL" if retcode == 10010 else "REJECTED"
        message = str(getattr(response, "comment", ""))
        self._ledger.record(order.client_order_id, status, broker_order_id, retcode)
        return MT5OrderResult(
            client_order_id=order.client_order_id,
            status=status,
            broker_order_id=broker_order_id,
            retcode=retcode,
            message=message,
        )

    def _request_dict(self, order: MT5OrderRequest) -> dict[str, object]:
        direction = order.direction.upper()
        request: dict[str, object] = {
            "action": getattr(self._terminal, "TRADE_ACTION_DEAL"),
            "symbol": order.symbol,
            "volume": order.volume,
            "type": getattr(
                self._terminal,
                "ORDER_TYPE_BUY" if direction == "UP" else "ORDER_TYPE_SELL",
            ),
            "price": order.price,
            "deviation": 0,
            "comment": order.client_order_id,
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
