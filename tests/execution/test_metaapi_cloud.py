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

def test_cloud_account_snapshot_requires_complete_broker_data():
    conn = Connection()
    conn.terminal_state.account_information.update({
        "balance": 1000.0, "equity": 1025.5, "currency": "USD",
    })
    conn.terminal_state.positions = [{
        "id": "42", "type": "POSITION_TYPE_BUY", "symbol": "EURUSD",
        "volume": .02, "profit": 25.5, "stopLoss": 1.10, "takeProfit": 1.13,
        "openPrice": 1.11,
    }]
    with ledger() as path:
        adapter = MetaApiCloudAdapter(Account(), conn, ledger_path=path)
        snap = run(adapter.account_snapshot())
        assert snap.login == "123456"
        assert snap.server == "Broker-Demo"
        assert snap.balance == 1000.0
        assert snap.equity == 1025.5
        assert snap.positions[0].floating_pnl == 25.5
        assert ("sync",) in conn.calls
        assert not any(call[0] in {"buy", "modify", "close_position"} for call in conn.calls)
        run(adapter.close())


def test_cloud_unknown_positions_are_not_silently_treated_as_empty():
    conn = Connection()
    conn.terminal_state.positions = None
    with ledger() as path:
        adapter = MetaApiCloudAdapter(Account(), conn, ledger_path=path)
        with pytest.raises(MetaApiDemoBlocked, match="BROKER_POSITIONS_INCOMPLETE"):
            run(adapter.positions())
        run(adapter.close())


@pytest.mark.parametrize("ledger_path", [":memory:", ""])
def test_cloud_order_capable_adapter_requires_durable_ledger(ledger_path):
    with pytest.raises(TradingDisabledError, match="PERSISTENT_ORDER_LEDGER_REQUIRED"):
        MetaApiCloudAdapter(Account(), Connection(), allow_order_send=True,
                            ledger_path=ledger_path)


@pytest.mark.parametrize("stop_loss", [None, float("nan"), float("inf"), -float("inf"), 0.0, -1.0])
def test_cloud_direct_submit_rejects_missing_or_invalid_stop(stop_loss):
    conn = Connection()
    with ledger() as path:
        adapter = MetaApiCloudAdapter(Account(), conn, allow_order_send=True,
                                      ledger_path=path)
        result = run(adapter.submit(MT5OrderRequest(
            "cloud-no-protective-sl", "EURUSD", "UP", .01, 1.1052,
            stop_loss=stop_loss,
        )))
        assert (result.status, result.message) == (
            "RISK_REJECTED", "PROTECTIVE_STOP_REQUIRED"
        )
        assert not any(call[0] in {"buy", "connect"} for call in conn.calls)
        assert adapter._ledger.get("cloud-no-protective-sl") is None
        run(adapter.close())


@pytest.mark.parametrize("stop_loss", [None, float("nan"), float("inf"), 0.0])
def test_cloud_modify_rejects_invalid_protective_stop(stop_loss):
    conn = Connection()
    with ledger() as path:
        adapter = MetaApiCloudAdapter(Account(), conn, allow_order_send=True,
                                      ledger_path=path)
        result = run(adapter.modify_position(
            "42", client_order_id="cloud-bad-stop-modify", stop_loss=stop_loss,
        ))
        assert (result.status, result.message) == (
            "RISK_REJECTED", "PROTECTIVE_STOP_REQUIRED"
        )
        assert not any(call[0] in {"modify", "connect"} for call in conn.calls)
        assert adapter._ledger.get("cloud-bad-stop-modify") is None
        run(adapter.close())


def test_cloud_stale_precheck_cannot_double_send_with_shared_ledger():
    with ledger() as path:
        first_connection = Connection()
        second_connection = Connection()
        first = MetaApiCloudAdapter(Account(), first_connection,
                                    allow_order_send=True, ledger_path=path)
        second = MetaApiCloudAdapter(Account(), second_connection,
                                     allow_order_send=True, ledger_path=path)
        order = MT5OrderRequest("cloud-race", "EURUSD", "UP", .01, 1.1052, 1.10)
        assert run(first.submit(order)).status == "FILLED"
        original = second._duplicate_result
        checks = 0

        def stale_precheck(client_order_id):
            nonlocal checks
            checks += 1
            if checks == 1:
                return None
            return original(client_order_id)

        second._duplicate_result = stale_precheck
        assert run(second.submit(order)).status == "DUPLICATE_SUPPRESSED"
        assert checks == 2
        assert len([call for call in first_connection.calls if call[0] == "buy"]) == 1
        assert not [call for call in second_connection.calls if call[0] == "buy"]
        run(first.close())
        run(second.close())


def test_cloud_ambiguous_send_is_never_retried_after_restart():
    with ledger() as path:
        first_connection = Connection()

        async def timeout(*args):
            raise TimeoutError("broker acknowledgement unavailable")

        first_connection.create_market_buy_order = timeout
        first = MetaApiCloudAdapter(Account(), first_connection,
                                    allow_order_send=True, ledger_path=path)
        order = MT5OrderRequest("cloud-timeout", "EURUSD", "UP", .01, 1.1052, 1.10)
        result = run(first.submit(order))
        assert result.status == "AMBIGUOUS"
        assert first._ledger.get(order.client_order_id)[0] == "SUBMITTING"
        run(first.close())

        second_connection = Connection()
        second = MetaApiCloudAdapter(Account(), second_connection,
                                     allow_order_send=True, ledger_path=path)
        assert run(second.submit(order)).status == "DUPLICATE_SUPPRESSED"
        assert not [call for call in second_connection.calls if call[0] == "buy"]
        run(second.close())
