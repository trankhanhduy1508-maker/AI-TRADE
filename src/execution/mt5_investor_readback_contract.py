"""MT5 DEMO investor-only readback contract for a short-lived cloud preflight.

No broker SDK dependency, no credential persistence and no order interface.
Caller must obtain the INVESTOR credential through the scoped GitHub OIDC
lease and must never log returned account or positions data.
"""
from __future__ import annotations

import math
import re
from typing import Any


class InvestorReadbackBlocked(RuntimeError):
    """Fail closed instead of falling back to stale broker information."""


def investor_lease(value: Any) -> tuple[int, str, str]:
    if not isinstance(value, dict):
        raise InvestorReadbackBlocked("INVALID_LEASE")
    login = value.get("login")
    server = value.get("server")
    credential = value.get("password")
    if (value.get("ok") is not True
            or value.get("status") != "MT5_DEMO_LEASE"
            or value.get("purpose") != "preflight"
            or value.get("credentialScope") != "INVESTOR_READ_ONLY"
            or value.get("brokerOrdersAllowed") is not False
            or value.get("liveMoneyLocked") is not True
            or value.get("accountType") != "DEMO"
            or not isinstance(login, int) or isinstance(login, bool)
            or login < 10000 or login > 9_007_199_254_740_991
            or server != "MetaQuotes-Demo"
            or not isinstance(credential, str)
            or not 4 <= len(credential) <= 128):
        raise InvestorReadbackBlocked("INVALID_INVESTOR_ONLY_LEASE")
    return login, server, credential


def number(value: Any, field: str) -> float:
    if isinstance(value, bool):
        raise InvestorReadbackBlocked("INVALID_" + field)
    try:
        parsed = float(value)
    except (ValueError, TypeError, OverflowError) as error:
        raise InvestorReadbackBlocked("INVALID_" + field) from error
    if not math.isfinite(parsed):
        raise InvestorReadbackBlocked("INVALID_" + field)
    return parsed


def check_broker_readback(
    account: Any, positions: Any, *, login: int, server: str
) -> dict[str, bool]:
    if (server != "MetaQuotes-Demo" or isinstance(login, bool)
            or not isinstance(login, int) or login < 10000):
        raise InvestorReadbackBlocked("EXPECTED_DEMO_IDENTITY_REQUIRED")
    if not isinstance(account, dict):
        raise InvestorReadbackBlocked("BROKER_ACCOUNT_MISSING")
    if (account.get("account_type") != 1
            or account.get("is_demo") is not True
            or account.get("server") != server):
        raise InvestorReadbackBlocked("BROKER_NOT_EXACT_DEMO")
    # A Vault investor credential must remain investor/read-only at the broker.
    # Treat absent or unrecognized rights as unavailable, never master trading.
    if account.get("is_investor") is not True and account.get("is_read_only") is not True:
        raise InvestorReadbackBlocked("BROKER_INVESTOR_RIGHTS_MISSING")
    if account.get("login") is not None and str(account["login"]) != str(login):
        raise InvestorReadbackBlocked("BROKER_LOGIN_MISMATCH")
    number(account.get("balance"), "BALANCE")
    number(account.get("equity"), "EQUITY")
    currency = account.get("currency")
    if not isinstance(currency, str) or not re.fullmatch(r"[A-Z]{3,8}", currency):
        raise InvestorReadbackBlocked("BROKER_CURRENCY_INVALID")
    if not isinstance(positions, (list, tuple)) or len(positions) > 1000:
        raise InvestorReadbackBlocked("BROKER_POSITIONS_UNAVAILABLE")
    ticket_ids: set[int] = set()
    for position in positions:
        if not isinstance(position, dict):
            raise InvestorReadbackBlocked("BROKER_POSITION_INCOMPLETE")
        ticket = position.get("position_id")
        if (isinstance(ticket, bool) or not isinstance(ticket, int)
                or ticket <= 0 or ticket in ticket_ids):
            raise InvestorReadbackBlocked("BROKER_POSITION_TICKET_INVALID")
        ticket_ids.add(ticket)
        symbol = position.get("trade_symbol")
        if not isinstance(symbol, str) or not re.fullmatch(r"[A-Za-z0-9._-]{2,32}", symbol):
            raise InvestorReadbackBlocked("BROKER_POSITION_SYMBOL_INVALID")
        if position.get("trade_action") not in (0, 1):
            raise InvestorReadbackBlocked("BROKER_POSITION_SIDE_INVALID")
        if number(position.get("trade_volume"), "POSITION_VOLUME") <= 0:
            raise InvestorReadbackBlocked("BROKER_POSITION_VOLUME_INVALID")
        number(position.get("profit"), "POSITION_PNL")
        for optional in ("sl", "tp"):
            if optional in position and number(position[optional], optional.upper()) < 0:
                raise InvestorReadbackBlocked("BROKER_PROTECTIVE_PRICE_INVALID")
    # Public CI output deliberately contains no account ID, balance, equity,
    # positions count, total Lot, account password, token or raw exception.
    return {"balanceRead": True, "equityRead": True, "positionsRead": True,
            "brokerOrders": False, "liveMoneyLocked": True}
