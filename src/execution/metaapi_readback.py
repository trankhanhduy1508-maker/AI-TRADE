"""Read-only normalized MT5 DEMO broker snapshot from a synchronized MetaApi state.

This module needs an already-authorized client/account from the caller. It
never connects, decrypts credentials, sends orders, or confuses a DEMO-looking
server name with the account's actual broker trade mode.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.execution.demo_readback import (
    DemoAccountSnapshot,
    DemoPositionSnapshot,
    _finite,
    _protective_price,
)
from src.execution.metaapi_demo_guard import (
    MetaApiDemoBlocked,
    _value,
    assert_metaapi_demo_context,
)


def read_metaapi_demo_snapshot(account: Any, terminal: Any) -> DemoAccountSnapshot:
    """Reject missing/ambiguous broker data rather than guessing P&L or equity.

    Call only after connection.wait_synchronized() and an owner-bound session.
    ``as_of`` is the local read time, not an assertion about quote freshness.
    """
    assert_metaapi_demo_context(account, terminal)
    info = _value(terminal, "account_information")
    balance = _finite(_value(info, "balance"), "BALANCE")
    equity = _finite(_value(info, "equity"), "EQUITY")
    currency = _value(info, "currency")
    if not isinstance(currency, str) or not currency.isalpha() or not 3 <= len(currency) <= 8:
        raise MetaApiDemoBlocked("BROKER_CURRENCY_MISSING")
    raw_positions = _value(terminal, "positions")
    if raw_positions is None or not isinstance(raw_positions, (list, tuple)):
        raise MetaApiDemoBlocked("BROKER_POSITIONS_INCOMPLETE")

    result: list[DemoPositionSnapshot] = []
    tickets: set[str] = set()
    for row in raw_positions:
        ticket = str(_value(row, "id", ""))
        symbol = _value(row, "symbol")
        kind = _value(row, "type")
        if not ticket or ticket == "None" or ticket == "0" or ticket in tickets:
            raise MetaApiDemoBlocked("BROKER_POSITION_ID_INVALID")
        tickets.add(ticket)
        if not isinstance(symbol, str) or not symbol.strip():
            raise MetaApiDemoBlocked("BROKER_POSITION_SYMBOL_INVALID")
        if kind not in ("POSITION_TYPE_BUY", "POSITION_TYPE_SELL"):
            raise MetaApiDemoBlocked("BROKER_POSITION_SIDE_INVALID")
        lot = _finite(_value(row, "volume"), "POSITION_LOT")
        if lot <= 0:
            raise MetaApiDemoBlocked("BROKER_POSITION_LOT_INVALID")
        result.append(DemoPositionSnapshot(
            ticket=ticket,
            symbol=symbol,
            side="BUY" if kind == "POSITION_TYPE_BUY" else "SELL",
            lot=lot,
            floating_pnl=_finite(_value(row, "profit"), "POSITION_PNL"),
            stop_loss=_protective_price(_value(row, "stopLoss", 0.0), "STOP_LOSS"),
            take_profit=_protective_price(_value(row, "takeProfit", 0.0), "TAKE_PROFIT"),
        ))

    # A concurrent broker/account switch during position traversal voids this
    # read even when the old account's balances appeared valid initially.
    assert_metaapi_demo_context(account, terminal)
    info_after = _value(terminal, "account_information")
    if info_after is not info:
        raise MetaApiDemoBlocked("BROKER_ACCOUNT_CHANGED_DURING_READ")
    if (_finite(_value(info_after, "balance"), "BALANCE") != balance
            or _finite(_value(info_after, "equity"), "EQUITY") != equity):
        raise MetaApiDemoBlocked("BROKER_BALANCE_CHANGED_DURING_READ")
    return DemoAccountSnapshot(
        login=str(_value(account, "login")),
        server=str(_value(account, "server")),
        currency=currency.upper(),
        balance=balance,
        equity=equity,
        positions=tuple(result),
        trade_allowed=True,
        as_of=datetime.now(timezone.utc),
        source="METAAPI_CLOUD",
    )
