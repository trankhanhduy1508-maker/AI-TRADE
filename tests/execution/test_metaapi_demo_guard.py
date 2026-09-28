"""Isolated fake-account checks, NOT MetaApi broker execution evidence."""
from types import SimpleNamespace
import pytest
from src.execution.metaapi_demo_guard import MetaApiDemoBlocked, assert_metaapi_demo_context


def context():
    account = SimpleNamespace(platform="mt5", server="Broker-Demo", login="123456")
    terminal = SimpleNamespace(
        connected=True, connected_to_broker=True,
        account_information={
            "type": "ACCOUNT_TRADE_MODE_DEMO", "server": "Broker-Demo",
            "login": 123456, "tradeAllowed": True, "investorMode": False,
        },
    )
    return account, terminal


def test_exact_runtime_demo_identity_is_accepted():
    assert assert_metaapi_demo_context(*context()) is None


@pytest.mark.parametrize("field,value,error", [
    ("platform", "mt4", "MT5_PLATFORM_REQUIRED"),
    ("server", "Broker-Live", "PROVISIONED_DEMO_IDENTITY_REQUIRED"),
    ("server", "Fake-Demo", "BROKER_ACCOUNT_IDENTITY_MISMATCH"),
    ("login", "654321", "BROKER_ACCOUNT_IDENTITY_MISMATCH"),
])
def test_provisioned_account_mismatch_is_blocked(field, value, error):
    account, terminal = context()
    setattr(account, field, value)
    with pytest.raises(MetaApiDemoBlocked, match=error):
        assert_metaapi_demo_context(account, terminal)


@pytest.mark.parametrize("field,value,error", [
    ("connected", False, "BROKER_DISCONNECTED"),
    ("connected_to_broker", False, "BROKER_DISCONNECTED"),
    ("account_information", None, "BROKER_ACCOUNT_INFORMATION_MISSING"),
])
def test_missing_broker_connection_is_blocked(field, value, error):
    account, terminal = context()
    setattr(terminal, field, value)
    with pytest.raises(MetaApiDemoBlocked, match=error):
        assert_metaapi_demo_context(account, terminal)


@pytest.mark.parametrize("field,value,error", [
    ("type", "ACCOUNT_TRADE_MODE_REAL", "BROKER_DEMO_MODE_NOT_VERIFIED"),
    ("type", "ACCOUNT_TRADE_MODE_CONTEST", "BROKER_DEMO_MODE_NOT_VERIFIED"),
    ("type", None, "BROKER_DEMO_MODE_NOT_VERIFIED"),
    ("server", "Broker-Other-Demo", "BROKER_ACCOUNT_IDENTITY_MISMATCH"),
    ("login", 654321, "BROKER_ACCOUNT_IDENTITY_MISMATCH"),
    ("tradeAllowed", False, "BROKER_TRADING_NOT_ALLOWED"),
    ("tradeAllowed", None, "BROKER_TRADING_NOT_ALLOWED"),
    ("investorMode", True, "BROKER_INVESTOR_MODE"),
])
def test_actual_broker_account_mode_and_rights_gate(field, value, error):
    account, terminal = context()
    terminal.account_information[field] = value
    with pytest.raises(MetaApiDemoBlocked, match=error):
        assert_metaapi_demo_context(account, terminal)
