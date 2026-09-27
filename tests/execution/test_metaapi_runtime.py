import asyncio
from datetime import datetime, timezone

from src.execution.metaapi_runtime import closed_bars, daily_pnl


class Account:
    async def get_historical_candles(self, **kwargs):
        return [
            {
                "time": "2026-09-27T00:30:00+00:00",
                "open": 1.0,
                "high": 1.2,
                "low": .9,
                "close": 1.1,
                "tickVolume": 10,
            },
            {
                "time": "2026-09-27T00:45:00+00:00",
                "open": 1.1,
                "high": 1.3,
                "low": 1.0,
                "close": 1.2,
                "tickVolume": 12,
            },
            {
                "time": "2026-09-27T01:00:00+00:00",
                "open": 1.2,
                "high": 1.4,
                "low": 1.1,
                "close": 1.3,
                "tickVolume": 8,
            },
        ]


class Storage:
    def get_deals_by_time_range(self, start, end):
        return [
            {"magic": 260927, "profit": -4, "commission": -1, "swap": 0, "fee": 0},
            {"magic": 999, "profit": 100, "commission": 0, "swap": 0, "fee": 0},
        ]


class Connection:
    history_storage = Storage()


def test_metaapi_closed_bars_exclude_current_forming_candle():
    result = asyncio.run(
        closed_bars(
            Account(),
            symbol="EURUSD",
            timeframe="15m",
            count=3,
            now=datetime(2026, 9, 27, 1, 10, tzinfo=timezone.utc),
        )
    )
    assert len(result) == 2
    assert result[-1].timestamp.startswith("2026-09-27T00:45:00")


def test_metaapi_daily_pnl_only_counts_bot_magic():
    pnl = daily_pnl(
        Connection(),
        magic=260927,
        now=datetime(2026, 9, 27, 2, 0, tzinfo=timezone.utc),
    )
    assert pnl == -5
