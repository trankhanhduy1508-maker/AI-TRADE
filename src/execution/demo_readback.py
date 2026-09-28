"""Verified, read-only MT5 DEMO account and position snapshot.

Supply an already-initialized MT5-compatible terminal. This module never logs
in, reads credentials, executes orders, or treats historical DB state as live.
The caller must authorize the owner and reject stale snapshots separately.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import math
from typing import Any


@dataclass(frozen=True)
class DemoPositionSnapshot:
    ticket: str
    symbol: str
    side: str
    lot: float
    floating_pnl: float
    stop_loss: float | None
    take_profit: float | None


@dataclass(frozen=True)
class DemoAccountSnapshot:
    login: str
    server: str
    currency: str
    balance: float
    equity: float
    positions: tuple[DemoPositionSnapshot, ...]
    trade_allowed: bool
    as_of: datetime
    source: str = "MT5_TERMINAL"

    @property
    def gross_profit(self) -> float:
        return sum(max(0.0, p.floating_pnl) for p in self.positions)

    @property
    def gross_loss(self) -> float:
        return sum(min(0.0, p.floating_pnl) for p in self.positions)

    @property
    def net_pnl(self) -> float:
        return sum(p.floating_pnl for p in self.positions)

    @property
    def symbols_with_positions(self) -> int:
        return len({p.symbol for p in self.positions})


def _finite(value: Any, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise RuntimeError(f"INVALID_{field}") from exc
    if not math.isfinite(number):
        raise RuntimeError(f"INVALID_{field}")
    return number


def _protective_price(value: Any, field: str) -> float | None:
    number = _finite(value, field)
    if number == 0:
        return None
    if number < 0:
        raise RuntimeError(f"INVALID_{field}")
    return number


def read_demo_snapshot(
    terminal: Any, *, expected_login: str, expected_server: str
) -> DemoAccountSnapshot:
    """Read fresh broker data only for the exactly bound DEMO identity.

    Investor/read-only credentials may read snapshots, but `trade_allowed` is
    false and must never be interpreted as authorization to place an order.
    """
    if not expected_login or not expected_server:
        raise ValueError("EXPECTED_DEMO_IDENTITY_REQUIRED")
    terminal_info = getattr(terminal, "terminal_info", None)
    if not callable(terminal_info):
        raise RuntimeError("TERMINAL_INFO_UNAVAILABLE")
    connection = terminal_info()
    if connection is None or getattr(connection, "connected", None) is not True:
        raise RuntimeError("BROKER_DISCONNECTED")
    account_info = getattr(terminal, "account_info", None)
    if not callable(account_info):
        raise RuntimeError("ACCOUNT_INFO_UNAVAILABLE")
    account = account_info()
    if account is None:
        raise RuntimeError("ACCOUNT_READ_FAILED")
    if getattr(account, "trade_mode", None) != 0:
        raise RuntimeError("LIVE_OR_NON_DEMO_ACCOUNT_BLOCKED")
    login = str(getattr(account, "login", ""))
    server = str(getattr(account, "server", ""))
    if login != str(expected_login) or server != expected_server:
        raise RuntimeError("ACCOUNT_IDENTITY_MISMATCH")
    currency = getattr(account, "currency", None)
    if not isinstance(currency, str) or not currency.strip():
        raise RuntimeError("INVALID_CURRENCY")
    balance = _finite(getattr(account, "balance", None), "BALANCE")
    equity = _finite(getattr(account, "equity", None), "EQUITY")
    position_getter = getattr(terminal, "positions_get", None)
    if not callable(position_getter):
        raise RuntimeError("POSITIONS_UNAVAILABLE")
    rows = position_getter()
    if rows is None:
        raise RuntimeError("POSITIONS_READ_FAILED")
    result: list[DemoPositionSnapshot] = []
    buy = getattr(terminal, "POSITION_TYPE_BUY", 0)
    sell = getattr(terminal, "POSITION_TYPE_SELL", 1)
    for position in rows:
        ticket = getattr(position, "ticket", None)
        symbol = getattr(position, "symbol", None)
        pos_type = getattr(position, "type", None)
        if ticket is None or str(ticket) in {"", "0"}:
            raise RuntimeError("INVALID_POSITION_TICKET")
        if not isinstance(symbol, str) or not symbol.strip():
            raise RuntimeError("INVALID_POSITION_SYMBOL")
        if pos_type != buy and pos_type != sell:
            raise RuntimeError("INVALID_POSITION_SIDE")
        lot = _finite(getattr(position, "volume", None), "POSITION_LOT")
        if lot <= 0:
            raise RuntimeError("INVALID_POSITION_LOT")
        result.append(DemoPositionSnapshot(
            ticket=str(ticket), symbol=symbol,
            side="BUY" if pos_type == buy else "SELL", lot=lot,
            floating_pnl=_finite(getattr(position, "profit", None), "POSITION_PNL"),
            stop_loss=_protective_price(getattr(position, "sl", None), "STOP_LOSS"),
            take_profit=_protective_price(getattr(position, "tp", None), "TAKE_PROFIT"),
        ))
    # This timestamp identifies the fresh terminal read, not a guaranteed
    # broker heartbeat or proof that the Android client remains connected.
    return DemoAccountSnapshot(
        login=login, server=server, currency=currency,
        balance=balance, equity=equity, positions=tuple(result),
        trade_allowed=(getattr(account, "trade_allowed", None) is True
                       and getattr(account, "trade_expert", None) is True),
        as_of=datetime.now(timezone.utc),
    )
