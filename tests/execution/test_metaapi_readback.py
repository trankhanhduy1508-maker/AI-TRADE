from types import SimpleNamespace
import pytest

from src.execution.metaapi_demo_guard import MetaApiDemoBlocked
from src.execution.metaapi_readback import read_metaapi_demo_snapshot


def context():
    account = SimpleNamespace(platform="mt5", login="43210", server="Unit-Demo")
    terminal = SimpleNamespace(
        connected=True,
        connected_to_broker=True,
        account_information={
            "type": "ACCOUNT_TRADE_MODE_DEMO", "login": 43210,
            "server": "Unit-Demo", "tradeAllowed": True, "investorMode": False,
            "balance": 1012.5, "equity": 1021.75, "currency": "USD",
        },
        positions=[
            {"id": "400", "symbol": "EURUSD", "type": "POSITION_TYPE_BUY",
             "volume": 0.02, "profit": 11.25, "stopLoss": 1.01, "takeProfit": 1.15},
            {"id": "401", "symbol": "GBPUSD", "type": "POSITION_TYPE_SELL",
             "volume": 0.01, "profit": -2.0, "stopLoss": 0, "takeProfit": 0},
        ],
    )
    return account, terminal


def test_two_positions_equity_and_profit_without_total_lot_kpi():
    a, t = context()
    x = read_metaapi_demo_snapshot(a, t)
    assert (x.login, x.server, x.currency) == ("43210", "Unit-Demo", "USD")
    assert (x.balance, x.equity) == (1012.5, 1021.75)
    assert x.gross_profit == 11.25
    assert x.gross_loss == -2.0
    assert x.net_pnl == 9.25
    assert x.symbols_with_positions == 2
    assert [(p.ticket, p.side, p.lot) for p in x.positions] == [
        ("400", "BUY", 0.02), ("401", "SELL", 0.01)
    ]
    assert x.positions[1].stop_loss is None
    assert x.source == "METAAPI_CLOUD"
    assert not hasattr(x, "total_lot")


def test_empty_positions_is_distinct_from_failed_positions():
    a, t = context()
    t.positions = []
    x = read_metaapi_demo_snapshot(a, t)
    assert x.positions == ()
    assert x.net_pnl == 0


@pytest.mark.parametrize("field,value,error", [
    ("connected", False, "BROKER_DISCONNECTED"),
    ("connected_to_broker", False, "BROKER_DISCONNECTED"),
    ("positions", None, "BROKER_POSITIONS_INCOMPLETE"),
    ("positions", {}, "BROKER_POSITIONS_INCOMPLETE"),
])
def test_connection_and_positions_must_be_complete(field, value, error):
    a, t = context()
    setattr(t, field, value)
    with pytest.raises(MetaApiDemoBlocked, match=error):
        read_metaapi_demo_snapshot(a, t)


@pytest.mark.parametrize("key,value,error", [
    ("type", "ACCOUNT_TRADE_MODE_REAL", "BROKER_DEMO_MODE_NOT_VERIFIED"),
    ("type", None, "BROKER_DEMO_MODE_NOT_VERIFIED"),
    ("login", 12345, "BROKER_ACCOUNT_IDENTITY_MISMATCH"),
    ("server", "Other-Demo", "BROKER_ACCOUNT_IDENTITY_MISMATCH"),
    ("balance", None, "INVALID_BALANCE"),
    ("equity", None, "INVALID_EQUITY"),
    ("currency", "", "BROKER_CURRENCY_MISSING"),
    ("tradeAllowed", False, "BROKER_TRADING_NOT_ALLOWED"),
])
def test_unverified_account_and_incomplete_balance_rejected(key, value, error):
    a, t = context()
    t.account_information[key] = value
    with pytest.raises((MetaApiDemoBlocked, RuntimeError), match=error):
        read_metaapi_demo_snapshot(a, t)


@pytest.mark.parametrize("key,value,error", [
    ("id", "", "BROKER_POSITION_ID_INVALID"),
    ("symbol", "", "BROKER_POSITION_SYMBOL_INVALID"),
    ("type", "BUY", "BROKER_POSITION_SIDE_INVALID"),
    ("volume", 0, "BROKER_POSITION_LOT_INVALID"),
    ("volume", -1, "BROKER_POSITION_LOT_INVALID"),
    ("profit", None, "INVALID_POSITION_PNL"),
    ("stopLoss", -1, "INVALID_STOP_LOSS"),
    ("takeProfit", float("inf"), "INVALID_TAKE_PROFIT"),
])
def test_incomplete_position_is_not_silently_dropped(key, value, error):
    a, t = context()
    t.positions[0][key] = value
    with pytest.raises((MetaApiDemoBlocked, RuntimeError), match=error):
        read_metaapi_demo_snapshot(a, t)


def test_duplicate_position_identifier_rejected():
    a, t = context()
    t.positions[1]["id"] = t.positions[0]["id"]
    with pytest.raises(MetaApiDemoBlocked, match="BROKER_POSITION_ID_INVALID"):
        read_metaapi_demo_snapshot(a, t)


def test_broker_account_switch_during_position_iteration_is_blocked():
    a, t = context()

    class SwitchingList(list):
        def __iter__(self):
            for item in super().__iter__():
                yield item
                t.account_information = {**t.account_information, "login": 55555}

    t.positions = SwitchingList(t.positions)
    with pytest.raises(MetaApiDemoBlocked, match="BROKER_ACCOUNT_IDENTITY_MISMATCH"):
        read_metaapi_demo_snapshot(a, t)
