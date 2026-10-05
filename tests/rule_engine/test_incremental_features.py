"""Parity tests for point-in-time rule-engine feature caching."""

from src.backtest.spec import strategy_spec_from_dict
from src.rule_engine import market_structure, trend_detection
from src.rule_engine.incremental import PointInTimeRuleCache
from src.rule_engine.types import Bar


def _bars() -> list[Bar]:
    highs = [1, 2, 5, 3, 4, 7, 5, 6, 9, 7, 8, 10, 8, 11]
    lows = [0, -1, 1, 0, 2, 1, 3, 2, 4, 3, 5, 4, 6, 5]
    return [
        Bar(
            timestamp=f"2026-01-01T00:{index:02d}:00Z",
            open=(high + low) / 2,
            high=high,
            low=low,
            close=(high + low) / 2,
            volume=100,
        )
        for index, (high, low) in enumerate(zip(highs, lows))
    ]


def test_incremental_features_match_full_scan_at_every_closed_bar():
    bars = _bars()
    cache = PointInTimeRuleCache(n=2)

    for index in range(len(bars)):
        history = tuple(bars[: index + 1])
        cached = cache.update(history)
        direct_trend = trend_detection.evaluate(list(history), n=2)
        direct_levels = market_structure._find_last_swing_levels(list(history), n=2)

        assert cached.trend_result == direct_trend
        assert cached.swing_levels == direct_levels


def test_incremental_cache_waits_for_right_hand_swing_confirmation():
    bars = [
        Bar("2026-01-01T00:00:00Z", 0, 1, -1, 0, 100),
        Bar("2026-01-01T00:01:00Z", 1, 2, 0, 1, 100),
        Bar("2026-01-01T00:02:00Z", 5, 10, 4, 5, 100),
        Bar("2026-01-01T00:03:00Z", 2, 3, 1, 2, 100),
        Bar("2026-01-01T00:04:00Z", 3, 4, 2, 3, 100),
    ]
    cache = PointInTimeRuleCache(n=2)

    before_confirmation = cache.update(tuple(bars[:4]))
    after_confirmation = cache.update(tuple(bars))

    assert before_confirmation.swing_levels[0] is None
    assert after_confirmation.swing_levels[0] == 10


def test_stateful_adapter_matches_full_scan_adapter_at_each_prefix():
    from src.backtest.engine import RuleEngineSignalEvaluator, rule_engine_signal

    bars = _bars()
    spec = strategy_spec_from_dict(
        {
            "strategy_id": "TF-001",
            "risk_mode": "SIGNAL_ONLY",
            "stop_lookback_bars": 2,
            "provenance": {"test": "IMPLEMENTATION_DERIVATION"},
        }
    )
    cached_adapter = RuleEngineSignalEvaluator()

    for index in range(len(bars)):
        history = tuple(bars[: index + 1])
        assert cached_adapter(history, spec) == rule_engine_signal(history, spec)
