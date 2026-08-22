import pytest

from src.backtest.engine import run_backtest
from src.backtest.types import Signal
from src.backtest.spec import strategy_spec_from_dict
from src.rule_engine.types import Bar


def _spec(**overrides):
    values = {
        "strategy_id": "TEST",
        "risk_mode": "SIGNAL_ONLY",
        "provenance": {"test": "IMPLEMENTATION_DERIVATION"},
        "stop_lookback_bars": 1,
    }
    values.update(overrides)
    return strategy_spec_from_dict(values)


def _bar(number, open_, high, low, close, closed=True):
    return Bar(
        timestamp=f"2026-01-01T00:{number:02d}:00Z",
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=100,
        closed=closed,
    )


def test_engine_rejects_unclosed_input_bar():
    with pytest.raises(ValueError, match="closed"):
        run_backtest(
            [_bar(0, 100, 101, 99, 100, closed=False)],
            _spec(),
            lambda history, spec: None,
        )


def test_engine_never_exposes_future_bars_to_signal_evaluator():
    seen_lengths = []

    def evaluator(history, spec):
        seen_lengths.append(len(history))
        assert history[-1].timestamp == f"2026-01-01T00:{len(history)-1:02d}:00Z"
        return None

    bars = [_bar(0, 100, 101, 99, 100), _bar(1, 101, 102, 100, 101)]
    run_backtest(bars, _spec(), evaluator)

    assert seen_lengths == [1, 2]


def test_engine_uses_stop_first_when_stop_and_target_are_both_hit():
    bars = [
        _bar(0, 100, 100.5, 99.5, 100),
        _bar(1, 100, 101, 99, 100),
        _bar(2, 100, 102, 98, 100),
    ]
    calls = 0

    def evaluator(history, spec):
        nonlocal calls
        if calls == 0:
            calls += 1
            return Signal(direction="UP", stop_price=99.0, score=100.0)
        calls += 1
        return None

    result = run_backtest(bars, _spec(), evaluator)

    assert len(result.trades) == 1
    assert result.trades[0].exit_reason == "STOP"
    assert result.trades[0].exit_price == 99.0


def test_engine_does_not_open_overlapping_positions_and_calculates_kpis():
    bars = [
        _bar(0, 100, 100.5, 99.5, 100),
        _bar(1, 100, 101, 99.5, 100.5),
        _bar(2, 100.5, 102, 100.5, 101.5),
        _bar(3, 101.5, 102, 101, 101.5),
        _bar(4, 101.5, 101.5, 101.5, 101.5),
    ]

    def evaluator(history, spec):
        if len(history) in (1, 2):
            return Signal(direction="UP", stop_price=99.0, score=100.0)
        return None

    result = run_backtest(bars, _spec(), evaluator)

    assert len(result.trades) == 1
    assert result.trades[0].exit_reason == "TARGET"
    assert result.metrics["trade_count"] == 1
    assert result.metrics["win_rate"] == 1.0
    assert result.metrics["net_pnl_price"] == pytest.approx(1.5)
    assert result.metrics["max_drawdown_price"] == pytest.approx(0.0)


def test_engine_does_not_reenter_on_the_bar_that_exits_a_position():
    bars = [
        _bar(0, 100, 100.5, 99.5, 100),
        _bar(1, 100, 102, 99.5, 101),
        _bar(2, 101, 101.5, 100.5, 101),
    ]

    def evaluator(history, spec):
        if len(history) in (1, 2):
            return Signal(direction="UP", stop_price=99.0, score=100.0)
        return None

    result = run_backtest(bars, _spec(), evaluator)

    assert len(result.trades) == 1
    assert result.open_position is None


def test_channel_trailing_exit_ratchets_from_prior_bars_only():
    bars = [
        _bar(0, 100, 101, 95, 100),
        _bar(1, 100, 105, 100, 104),
        _bar(2, 104, 106, 99, 103),
    ]

    def evaluator(history, spec):
        if len(history) == 1:
            return Signal(direction="UP", stop_price=90.0, score=100.0)
        return None

    result = run_backtest(
        bars,
        _spec(exit_model="CHANNEL_TRAILING", exit_lookback_bars=1),
        evaluator,
    )

    assert len(result.trades) == 1
    assert result.trades[0].exit_reason == "TRAILING_STOP"
    assert result.trades[0].stop_price == pytest.approx(100.0)
    assert result.trades[0].target_price is None
