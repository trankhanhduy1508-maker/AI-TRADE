from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import tempfile

import pytest

from src.execution.metaapi_cloud import MetaApiCloudAdapter, MetaApiCloudConfig
from src.execution.mt5_adapter import MT5OrderRequest, TradingDisabledError


class FakeTransport:
    def __init__(self):
        self.calls = []
        self.account_type = "ACCOUNT_TRADE_MODE_DEMO"
        self.positions = [
            {
                "id": "42",
                "type": "POSITION_TYPE_BUY",
                "symbol": "EURUSD",
                "magic": 260926,
                "openPrice": 1.1,
                "currentPrice": 1.105,
                "stopLoss": 1.09,
                "takeProfit": 1.12,
                "volume": 0.02,
                "clientId": "AI_test_1",
            }
        ]

    def request(self, method, url, *, token, body=None, timeout=30.0):
        self.calls.append((method, url, body))
        if url.endswith("/account-information?refreshTerminalState=true"):
            return {
                "type": self.account_type,
                "tradeAllowed": True,
                "server": "Broker-Demo",
            }
        if "/positions?refreshTerminalState=true" in url:
            return self.positions
        if "/current-price" in url:
            return {
                "symbol": "EURUSD",
                "bid": 1.1050,
                "ask": 1.1052,
                "time": "2026-09-27T01:00:00.000Z",
            }
        if "/specification" in url:
            return {
                "symbol": "EURUSD",
                "tickSize": 0.0001,
                "minVolume": 0.01,
                "maxVolume": 1.0,
                "volumeStep": 0.01,
                "digits": 5,
            }
        if "/history-deals/time/" in url:
            return [
                {"magic": 260926, "profit": -4, "commission": -1, "swap": 0},
                {"magic": 99, "profit": -100, "commission": 0, "swap": 0},
            ]
        if "/historical-market-data/" in url:
            return [
                {
                    "time": "2026-09-27T00:30:00.000Z",
                    "open": 1.1, "high": 1.11, "low": 1.09, "close": 1.105,
                    "tickVolume": 100,
                }
            ]
        if url.endswith("/trade"):
            action = body["actionType"]
            if action == "ORDER_TYPE_BUY":
                return {"numericCode": 10009, "stringCode": "TRADE_RETCODE_DONE", "orderId": "77"}
            if action == "POSITION_MODIFY":
                return {"numericCode": 10009, "stringCode": "TRADE_RETCODE_DONE", "positionId": "42"}
            if action in {"POSITION_PARTIAL", "POSITION_CLOSE_ID"}:
                return {"numericCode": 10009, "stringCode": "TRADE_RETCODE_DONE", "positionId": "42"}
        raise AssertionError((method, url, body))


@contextmanager
def ledger_path():
    handle = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
    path = Path(handle.name)
    handle.close()
    path.unlink(missing_ok=True)
    try:
        yield path
    finally:
        path.unlink(missing_ok=True)


def adapter(transport, path, allow=True):
    return MetaApiCloudAdapter(
        MetaApiCloudConfig("account-1", "secret-token"),
        ledger_path=path,
        allow_order_send=allow,
        transport=transport,
    )


def test_cloud_adapter_hard_rejects_live_account():
    transport = FakeTransport()
    transport.account_type = "ACCOUNT_TRADE_MODE_REAL"
    with ledger_path() as path:
        cloud = adapter(transport, path)
        with pytest.raises(TradingDisabledError, match="DEMO"):
            cloud.connect()
        cloud.close()


def test_cloud_adapter_reads_owned_positions_and_demo_account():
    transport = FakeTransport()
    with ledger_path() as path:
        cloud = adapter(transport, path, allow=False)
        assert cloud.connect()
        positions = cloud.positions("EURUSD")
        assert positions[0].position_id == "42"
        assert positions[0].magic == 260926
        assert cloud.broker_position_ids(magic=260926) == {"42"}
        cloud.close()


def test_cloud_entry_is_duplicate_safe_and_sends_magic_sl_tp():
    transport = FakeTransport()
    transport.positions = []
    with ledger_path() as path:
        cloud = adapter(transport, path)
        order = MT5OrderRequest(
            "intent-cloud",
            "EURUSD",
            "UP",
            0.01,
            1.1052,
            stop_loss=1.09,
            take_profit=1.12,
            magic=260926,
        )
        first = cloud.submit(order)
        second = cloud.submit(order)
        trade_bodies = [call[2] for call in transport.calls if call[1].endswith("/trade")]
        assert first.status == "FILLED"
        assert second.status == "DUPLICATE_SUPPRESSED"
        assert len(trade_bodies) == 1
        assert trade_bodies[0]["magic"] == 260926
        assert trade_bodies[0]["stopLoss"] == 1.09
        assert trade_bodies[0]["takeProfit"] == 1.12
        cloud.close()


def test_cloud_modify_never_widens_stop_and_partial_close_is_supported():
    transport = FakeTransport()
    with ledger_path() as path:
        cloud = adapter(transport, path)
        cloud.connect()
        good = cloud.modify_position(
            "42", client_order_id="trail-good",
            stop_loss=1.101, take_profit=1.12
        )
        bad = cloud.modify_position(
            "42", client_order_id="trail-bad",
            stop_loss=1.08, take_profit=1.12
        )
        partial_volume = cloud.normalize_partial_volume(cloud.positions()[0], 0.5)
        partial = cloud.close_position(
            "42", client_order_id="partial", volume=partial_volume
        )
        assert good.status == "FILLED"
        assert bad.status == "RISK_REJECTED"
        assert partial.status == "FILLED"
        assert partial_volume == 0.01
        cloud.close()


def test_cloud_market_history_and_daily_pnl_use_magic_only():
    transport = FakeTransport()
    with ledger_path() as path:
        cloud = adapter(transport, path, allow=False)
        candles = cloud.historical_candles("EURUSD", "15m", limit=10)
        pnl = cloud.daily_pnl(
            magic=260926,
            now=datetime(2026, 9, 27, 1, 30, tzinfo=timezone.utc),
        )
        assert candles[0]["close"] == 1.105
        assert pnl == -5.0
        cloud.close()
