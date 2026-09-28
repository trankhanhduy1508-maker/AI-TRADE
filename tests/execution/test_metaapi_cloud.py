import asyncio
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
import tempfile

import pytest
from src.execution.metaapi_cloud import MetaApiCloudAdapter
from src.execution.metaapi_demo_guard import MetaApiDemoBlocked
from src.execution.mt5_adapter import MT5OrderRequest, TradingDisabledError


class TerminalState:
    def __init__(self):
        self.connected = True
        self.connected_to_broker = True
        self.account_information = {"tradeAllowed": True, "investorMode": False,
            "type": "ACCOUNT_TRADE_MODE_DEMO", "server": "Broker-Demo", "login": 123456}
        self.positions = []
        self._price = {"bid": 1.1050, "ask": 1.1052, "time": "2026-09-27T01:00:00+00:00"}
        self._spec = {
            "point": .00001, "digits": 5, "minVolume": .01,
            "maxVolume": 1.0, "volumeStep": .01, "stopsLevel": 10
        }
    def price(self, symbol): return self._price
    def specification(self, symbol): return self._spec


class Connection:
    def __init__(self):
        self.terminal_state = TerminalState()
        self.calls = []
    async def connect(self): self.calls.append(("connect",))
    async def wait_synchronized(self): self.calls.append(("sync",))
    async def close(self): self.calls.append(("close",))
    async def subscribe_to_market_data(self, symbol): self.calls.append(("subscribe", symbol))
    async def create_market_buy_order(self, symbol, volume, sl, tp, options):
        self.calls.append(("buy", symbol, volume, sl, tp, options))
        return {"numericCode": 10009, "stringCode": "TRADE_RETCODE_DONE", "positionId": "42"}
    async def create_market_sell_order(self, symbol, volume, sl, tp, options):
        return {"numericCode": 10009, "positionId": "43"}
    async def modify_position(self, position_id, sl, tp):
        self.calls.append(("modify", position_id, sl, tp))
        return {"numericCode": 10009, "positionId": position_id}
    async def close_position_partially(self, position_id, volume):
        self.calls.append(("partial", position_id, volume))
        return {"numericCode": 10009, "positionId": position_id}
    async def close_position(self, position_id):
        self.calls.append(("close_position", position_id))
        return {"numericCode": 10009, "positionId": position_id}


class Account:
    platform = "mt5"
    login = "123456"
    server = "Broker-Demo"
    state = "DEPLOYED"
    connection_status = "CONNECTED"
    async def deploy(self): pass
    async def wait_connected(self): pass


@contextmanager
def ledger():
    handle = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
    path = Path(handle.name)
    handle.close()
    path.unlink(missing_ok=True)
    try:
        yield path
    finally:
        path.unlink(missing_ok=True)


def run(coro): return asyncio.run(coro)


def test_cloud_adapter_is_demo_only():
    account = Account()
    account.server = "Broker-Live"
    with ledger() as path:
        adapter = MetaApiCloudAdapter(account, Connection(), ledger_path=path)
        try:
            run(adapter.connect())
            assert False, "expected live lock"
        except TradingDisabledError:
            pass


def test_cloud_entry_sets_magic_client_id_and_server_side_stop():
    conn = Connection()
    with ledger() as path:
        adapter = MetaApiCloudAdapter(Account(), conn, allow_order_send=True, ledger_path=path)
        result = run(adapter.submit(MT5OrderRequest(
            "a-very-long-deterministic-client-order-id",
            "EURUSD", "UP", .01, 1.1052, 1.10, None, 260927
        )))
        assert result.status == "FILLED"
        buy = [call for call in conn.calls if call[0] == "buy"][0]
        assert buy[3] == 1.10
        assert buy[4] is None
        assert buy[5]["magic"] == 260927
        assert len(buy[5]["clientId"]) <= 26


def test_cloud_modify_never_widens_stop_and_partial_close_is_supported():
    conn = Connection()
    conn.terminal_state.positions = [{
        "id": "42", "type": "POSITION_TYPE_BUY", "symbol": "EURUSD",
        "magic": 260927, "openPrice": 1.10, "volume": .02,
        "stopLoss": 1.09, "takeProfit": 1.12
    }]
    with ledger() as path:
        adapter = MetaApiCloudAdapter(Account(), conn, allow_order_send=True, ledger_path=path)
        good = run(adapter.modify_position(
            "42", client_order_id="trail-good", stop_loss=1.101, take_profit=1.12
        ))
        bad = run(adapter.modify_position(
            "42", client_order_id="trail-bad", stop_loss=1.08, take_profit=1.12
        ))
        volume = run(adapter.normalize_partial_volume(run(adapter.positions())[0], .5))
        partial = run(adapter.close_position("42", client_order_id="partial", volume=volume))
        assert good.status == "FILLED"
        assert bad.status == "RISK_REJECTED"
        assert partial.status == "FILLED"
        assert ("partial", "42", .01) in conn.calls


def test_cloud_intents_are_duplicate_safe_after_restart():
    with ledger() as path:
        first_conn = Connection()
        first = MetaApiCloudAdapter(Account(), first_conn, allow_order_send=True, ledger_path=path)
        request = MT5OrderRequest("same-intent", "EURUSD", "UP", .01, 1.1052, 1.10)
        assert run(first.submit(request)).status == "FILLED"
        run(first.close())

        second_conn = Connection()
        second = MetaApiCloudAdapter(Account(), second_conn, allow_order_send=True, ledger_path=path)
        result = run(second.submit(request))
        assert result.status == "DUPLICATE_SUPPRESSED"
        assert not [call for call in second_conn.calls if call[0] == "buy"]

@pytest.mark.parametrize("field,value", [
    ("type", "ACCOUNT_TRADE_MODE_REAL"),
    ("type", None),
    ("server", "Other-Demo"),
    ("login", 654321),
])
def test_cloud_rechecks_broker_identity_before_any_demo_order(field, value):
    connection = Connection()
    with ledger() as path:
        adapter = MetaApiCloudAdapter(
            Account(), connection, allow_order_send=True, ledger_path=path
        )
        assert run(adapter.connect())
        connection.terminal_state.account_information[field] = value
        with pytest.raises(MetaApiDemoBlocked):
            run(adapter.submit(MT5OrderRequest(
                "changed-account", "EURUSD", "UP", .01, 1.1052, 1.10
            )))
        assert not [call for call in connection.calls if call[0] == "buy"]
        run(adapter.close())


def test_cloud_disconnection_rejects_position_read_without_broker_call():
    connection = Connection()
    with ledger() as path:
        adapter = MetaApiCloudAdapter(Account(), connection, ledger_path=path)
        assert run(adapter.connect())
        connection.terminal_state.connected_to_broker = False
        with pytest.raises(MetaApiDemoBlocked, match="BROKER_DISCONNECTED"):
            run(adapter.positions())
        run(adapter.close())
