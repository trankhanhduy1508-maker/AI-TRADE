"""Fail-closed MetaApi MT5 DEMO identity check, independent of broker SDK.

A DEMO substring in the server name is never proof of account trade mode.
The account information `type` is required from the synchronized broker state.
"""
from typing import Any


class MetaApiDemoBlocked(RuntimeError):
    """Never issue a broker mutation while identity/mode is unverified."""


def _value(record: Any, key: str, default: Any = None) -> Any:
    if isinstance(record, dict):
        return record.get(key, default)
    return getattr(record, key, default)


def assert_metaapi_demo_context(account: Any, terminal: Any) -> None:
    if str(_value(account, "platform", "")).lower() != "mt5":
        raise MetaApiDemoBlocked("MT5_PLATFORM_REQUIRED")
    server = _value(account, "server", None)
    login = _value(account, "login", None)
    if (not isinstance(server, str) or not server
            or "demo" not in server.lower() or login in (None, "")):
        raise MetaApiDemoBlocked("PROVISIONED_DEMO_IDENTITY_REQUIRED")
    if (_value(terminal, "connected", None) is not True
            or _value(terminal, "connected_to_broker", None) is not True):
        raise MetaApiDemoBlocked("BROKER_DISCONNECTED")
    info = _value(terminal, "account_information", None)
    if info is None:
        raise MetaApiDemoBlocked("BROKER_ACCOUNT_INFORMATION_MISSING")
    if _value(info, "type", None) != "ACCOUNT_TRADE_MODE_DEMO":
        raise MetaApiDemoBlocked("BROKER_DEMO_MODE_NOT_VERIFIED")
    if (str(_value(info, "login", "")) != str(login)
            or _value(info, "server", None) != server):
        raise MetaApiDemoBlocked("BROKER_ACCOUNT_IDENTITY_MISMATCH")
    if _value(info, "tradeAllowed", _value(info, "trade_allowed", None)) is not True:
        raise MetaApiDemoBlocked("BROKER_TRADING_NOT_ALLOWED")
    if _value(info, "investorMode", _value(info, "investor_mode", False)) is True:
        raise MetaApiDemoBlocked("BROKER_INVESTOR_MODE")
