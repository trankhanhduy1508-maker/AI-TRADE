from datetime import datetime, timezone
from types import SimpleNamespace

from src.execution.mt5_runtime import (
    collect_market_state,
    runtime_risk_context,
    runtime_snapshot,
    verified_demo_risk_context,
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


def _demo_mt5():
    mt5 = MT5()
    mt5.account = SimpleNamespace(
        login=123456, server="MetaQuotes-Demo", trade_mode=0,
        currency="USD", equity=995.0, balance=1000.0,
    )
    mt5.account_info = lambda: mt5.account
    mt5.positions = []
    mt5.positions_get = lambda: tuple(mt5.positions)
    mt5.info.trade_tick_size = .00001
    mt5.info.trade_tick_value_loss = 1.0
    return mt5


def _market(mt5):
    return collect_market_state(
        mt5, symbol="EURUSD", timeframe=15, count=2, magic=260926
    )


def test_broker_risk_context_uses_account_wide_closed_and_floating_losses():
    mt5 = _demo_mt5()
    market = _market(mt5)
    context = verified_demo_risk_context(
        mt5, expected_login="123456", expected_server="MetaQuotes-Demo",
        symbol="EURUSD", market=market,
    )
    # Other-strategy closed loss is included, plus five negative floating USD.
    assert context.daily_loss == -110.0
    assert context.account_equity == 995.0
    assert context.tick_size == .00001
    assert context.tick_value_per_lot == 1.0
    assert context.account_currency == "USD"


def test_broker_risk_context_counts_all_positions_and_symbol_lot_exposure():
    mt5 = _demo_mt5()
    mt5.deals = []
    mt5.positions = [
        SimpleNamespace(symbol="EURUSD", volume=.01),
        SimpleNamespace(symbol="USDJPY", volume=.02),
    ]
    ctx = verified_demo_risk_context(
        mt5, expected_login="123456", expected_server="MetaQuotes-Demo",
        symbol="EURUSD", market=_market(mt5),
    )
    assert ctx.open_positions == 2
    assert ctx.current_symbol_volume == .01
    assert ctx.daily_loss == -5.0


def test_broker_risk_context_fails_closed_on_switched_account():
    import pytest
    mt5 = _demo_mt5()
    market = _market(mt5)
    original_symbol_info = mt5.symbol_info

    def switch_account(symbol):
        mt5.account.login = 654321
        return original_symbol_info(symbol)

    mt5.symbol_info = switch_account
    with pytest.raises(RuntimeError, match="BROKER_DEMO_IDENTITY_MISMATCH"):
        verified_demo_risk_context(
            mt5, expected_login="123456", expected_server="MetaQuotes-Demo",
            symbol="EURUSD", market=market,
        )


def test_broker_risk_context_fails_closed_on_unknown_tick_or_positions():
    import pytest
    mt5 = _demo_mt5()
    market = _market(mt5)
    mt5.info.trade_tick_value_loss = 0.0
    with pytest.raises(RuntimeError, match="BROKER_LOSS_TICK_VALUE_INVALID"):
        verified_demo_risk_context(
            mt5, expected_login="123456", expected_server="MetaQuotes-Demo",
            symbol="EURUSD", market=market,
        )
    mt5.info.trade_tick_value_loss = 1.0
    mt5.positions_get = lambda: None
    with pytest.raises(RuntimeError, match="BROKER_POSITIONS_UNAVAILABLE"):
        verified_demo_risk_context(
            mt5, expected_login="123456", expected_server="MetaQuotes-Demo",
            symbol="EURUSD", market=market,
        )
