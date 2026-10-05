from src.backtest.spec import strategy_spec_from_dict
from src.rule_engine.types import Bar
from src.strategies.time_series_momentum import TimeSeriesMomentumEvaluator


def _bar(index: int, close: float, low: float | None = None, high: float | None = None) -> Bar:
    return Bar(
        timestamp=f"2026-01-{index + 1:02d}T00:00:00+00:00",
        open=close,
        high=high if high is not None else close + 1,
        low=low if low is not None else close - 1,
        close=close,
        volume=100,
    )


def _spec(**overrides):
    raw = {
        "strategy_id": "TF-003",
        "risk_mode": "SIGNAL_ONLY",
        "signal_model": "TIME_SERIES_MOMENTUM",
        "lookback_bars": 3,
        "stop_lookback_bars": 2,
        "score_threshold": 0,
        "provenance": {"signal": "VERIFIED_FROM_PRIMARY_RESEARCH"},
    }
    raw.update(overrides)
    return strategy_spec_from_dict(raw)


def test_momentum_waits_for_lookback_and_uses_only_prior_stop_bars():
    bars = [
        _bar(0, 10, low=9, high=11),
        _bar(1, 11, low=10, high=12),
        _bar(2, 12, low=11, high=13),
        _bar(3, 14, low=13, high=15),
    ]

    signal = TimeSeriesMomentumEvaluator()(bars, _spec())

    assert signal is not None
    assert signal.direction == "UP"
    assert signal.stop_price == 10
    assert signal.score == 100


def test_momentum_emits_down_without_using_current_bar_low_for_stop():
    bars = [
        _bar(0, 20, low=19, high=21),
        _bar(1, 19, low=18, high=20),
        _bar(2, 18, low=17, high=19),
        _bar(3, 15, low=1, high=16),
    ]

    signal = TimeSeriesMomentumEvaluator()(bars, _spec())

    assert signal is not None
    assert signal.direction == "DOWN"
    assert signal.stop_price == 20


def test_momentum_rejects_unclosed_current_bar():
    bars = [
        _bar(0, 10),
        _bar(1, 11),
        _bar(2, 12),
        _bar(3, 14),
    ]
    bars[-1].closed = False

    signal = TimeSeriesMomentumEvaluator()(bars, _spec())

    assert signal is None
