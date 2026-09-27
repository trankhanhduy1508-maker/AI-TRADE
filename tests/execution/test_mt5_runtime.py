from datetime import datetime, timezone
from types import SimpleNamespace

from src.execution.mt5_runtime import (
    collect_market_state,
    runtime_risk_context,
    runtime_snapshot,
)


class MT5:
    def __init__(self):
        self.tick = SimpleNamespace(bid=1.1, ask=1.1002, time=1_700_000_000)
        self.info = SimpleNamespace(point=.0001)
        self.deals = [
            SimpleNamespace(magic=260926, profit=-4, commission=-1, swap=0, fee=0),
            SimpleNamespace(magic=99, profit=-100, commission=0, swap=0, fee=0),
        ]

    def copy_rates_from_pos(self, symbol, timeframe, start, count):
        assert start == 1
        return [
            {"time": 1700000000, "open": 1.0, "high": 1.1, "low": .9, "close": 1.05, "tick_volume": 10},
            {"time": 1700000060, "open": 1.05, "high": 1.2, "low": 1.0, "close": 1.1, "tick_volume": 12},
        ]

    def symbol_info_tick(self, symbol): return self.tick
    def symbol_info(self, symbol): return self.info
    def history_deals_get(self, start, end): return tuple(self.deals)
    def last_error(self): return (0, "ok")


def test_runtime_reads_closed_bars_spread_and_only_our_daily_pnl():
    mt5 = MT5()
    market = collect_market_state(
        mt5, symbol="EURUSD", timeframe=15, count=2, magic=260926
    )
    assert len(market.bars) == 2
    assert all(bar.closed for bar in market.bars)
    assert round(market.spread_points, 6) == 2.0
    assert market.daily_pnl == -5.0
    context = runtime_risk_context(own_open_positions=0, market=market)
    assert context.daily_loss == -5.0


def test_runtime_snapshot_marks_old_tick_stale():
    mt5 = MT5()
    market = collect_market_state(
        mt5, symbol="EURUSD", timeframe=15, count=2, magic=260926
    )
    now = datetime.fromtimestamp(1_700_000_500, timezone.utc)
    snapshot = runtime_snapshot(
        market=market, now=now, reconciled=True, max_tick_age_seconds=120
    )
    assert not snapshot.data_fresh
