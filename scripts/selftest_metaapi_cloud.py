"""Cloud self-test for the MetaApi execution lane. No network secrets required."""

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from src.execution.metaapi_cloud import MetaApiCloudAdapter, MetaApiCloudConfig
from src.execution.metaapi_runtime import collect_metaapi_market_state
from src.execution.mt5_adapter import MT5OrderRequest, TradingDisabledError


class FakeTransport:
    def __init__(self):
        self.account_type = "ACCOUNT_TRADE_MODE_DEMO"
        self.positions_payload = []
        self.trade_calls = []

    def request(self, method, url, *, token, body=None, timeout=30.0):
        if url.endswith("/account-information?refreshTerminalState=true"):
            return {"type": self.account_type, "tradeAllowed": True, "server": "Cloud-Demo"}
        if "/positions?refreshTerminalState=true" in url:
            return self.positions_payload
        if "/current-price" in url:
            return {"symbol": "EURUSD", "bid": 1.1050, "ask": 1.1052, "time": "2026-09-27T01:00:00.000Z"}
        if "/specification" in url:
            return {"symbol": "EURUSD", "tickSize": 0.0001, "minVolume": 0.01, "maxVolume": 1.0, "volumeStep": 0.01, "digits": 5}
        if "/historical-market-data/" in url:
            return [
                {"time": "2026-09-27T00:15:00.000Z", "open": 1.10, "high": 1.11, "low": 1.09, "close": 1.101, "tickVolume": 50},
                {"time": "2026-09-27T00:30:00.000Z", "open": 1.101, "high": 1.112, "low": 1.10, "close": 1.105, "tickVolume": 70},
            ]
        if "/history-deals/time/" in url:
            return [{"magic": 260926, "profit": -4, "commission": -1, "swap": 0}]
        if url.endswith("/trade"):
            self.trade_calls.append(body)
            action = body["actionType"]
            return {
                "numericCode": 10009,
                "stringCode": "TRADE_RETCODE_DONE",
                "orderId": "77" if action.startswith("ORDER_TYPE_") else None,
                "positionId": "42" if action.startswith("POSITION_") else None,
                "message": "Request completed",
            }
        raise AssertionError(f"unexpected fake request: {method} {url} {body}")


def main() -> None:
    with TemporaryDirectory() as tmp:
        transport = FakeTransport()
        adapter = MetaApiCloudAdapter(
            MetaApiCloudConfig("demo-account", "not-a-real-token"),
            ledger_path=Path(tmp) / "intents.sqlite",
            allow_order_send=True,
            transport=transport,
        )
        assert adapter.connect()

        order = MT5OrderRequest(
            "cloud-entry",
            "EURUSD",
            "UP",
            0.01,
            1.1052,
            stop_loss=1.09,
            take_profit=None,
            magic=260926,
        )
        first = adapter.submit(order)
        duplicate = adapter.submit(order)
        assert first.status == "FILLED"
        assert duplicate.status == "DUPLICATE_SUPPRESSED"
        assert len(transport.trade_calls) == 1
        assert transport.trade_calls[0]["magic"] == 260926
        assert transport.trade_calls[0]["stopLoss"] == 1.09

        transport.positions_payload = [{
            "id": "42",
            "type": "POSITION_TYPE_BUY",
            "symbol": "EURUSD",
            "magic": 260926,
            "openPrice": 1.1,
            "currentPrice": 1.105,
            "stopLoss": 1.09,
            "takeProfit": 1.12,
            "volume": 0.02,
            "clientId": "AI_demo_1",
        }]
        position = adapter.positions()[0]
        trailed = adapter.modify_position(
            "42",
            client_order_id="trail",
            stop_loss=1.101,
            take_profit=1.12,
        )
        assert trailed.status == "FILLED"
        try:
            widened = adapter.modify_position(
                "42",
                client_order_id="widen",
                stop_loss=1.08,
                take_profit=1.12,
            )
            assert widened.status == "RISK_REJECTED"
        except Exception:
            raise AssertionError("widen-stop rejection must be deterministic")

        partial_volume = adapter.normalize_partial_volume(position, 0.5)
        assert partial_volume == 0.01
        partial = adapter.close_position("42", client_order_id="partial", volume=partial_volume)
        assert partial.status == "FILLED"

        market = collect_metaapi_market_state(
            adapter,
            symbol="EURUSD",
            timeframe="15m",
            count=10,
            magic=260926,
        )
        assert len(market.bars) == 2
        assert round(market.spread_points, 6) == 2.0
        assert market.daily_pnl == -5.0

        adapter.close()

        live_transport = FakeTransport()
        live_transport.account_type = "ACCOUNT_TRADE_MODE_REAL"
        live = MetaApiCloudAdapter(
            MetaApiCloudConfig("live-account", "not-a-real-token"),
            ledger_path=Path(tmp) / "live.sqlite",
            transport=live_transport,
        )
        try:
            live.connect()
        except TradingDisabledError:
            pass
        else:
            raise AssertionError("LIVE account must be rejected")
        finally:
            live.close()

    print("METAAPI_CLOUD_SELFTEST_PASS")


if __name__ == "__main__":
    main()
