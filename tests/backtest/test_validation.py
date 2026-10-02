import pytest

from src.backtest.costs import CostModel
from src.backtest.engine import run_backtest
from src.backtest.spec import strategy_spec_from_dict
from src.backtest.types import Signal
from src.rule_engine.types import Bar


def _spec():
    return strategy_spec_from_dict(
        {
            "strategy_id": "TEST",
            "risk_mode": "SIGNAL_ONLY",
            "provenance": {"test": "IMPLEMENTATION_DERIVATION"},
            "stop_lookback_bars": 1,
        }
    )


def _bars(count=6):
    return [
        Bar(
            timestamp=f"2026-01-01T00:{index:02d}:00Z",
            open=100 + index,
            high=102 + index,
            low=99 + index,
            close=101 + index,
            volume=100,
        )
        for index in range(count)
    ]


def test_cost_model_reconciles_gross_slippage_and_explicit_costs():
    bars = [
        Bar("2026-01-01T00:00:00Z", 100, 100.5, 99.5, 100, 100),
        Bar("2026-01-01T00:01:00Z", 100, 102, 99.5, 101, 100),
    ]
    costs = CostModel(
        profile_id="test-costs",
        spread_price=0.2,
        commission_price=0.1,
        slippage_price=0.05,
        swap_price_per_bar=0.01,
    )

    result = run_backtest(
        bars,
        _spec(),
        lambda history, spec: Signal("UP", stop_price=99, score=100),
        cost_model=costs,
    )

    trade = result.trades[0]
    assert trade.gross_pnl_price == pytest.approx(1.5)
    assert trade.cost_price == pytest.approx(0.41)
    assert trade.pnl_price == pytest.approx(1.09)
    assert result.metrics["gross_pnl_price"] == pytest.approx(1.5)
    assert result.metrics["total_cost_price"] == pytest.approx(0.41)


def test_is_oos_runner_warms_up_but_gates_oos_entries_at_split():
    from src.backtest.validation import run_is_oos

    bars = _bars()
    split_index = 3

    def evaluator_factory():
        return lambda history, spec: Signal("UP", stop_price=history[-1].close - 2, score=100)

    is_result, oos_result = run_is_oos(
        bars,
        _spec(),
        evaluator_factory,
        split_index=split_index,
        cost_model=CostModel.zero(),
    )

    assert is_result.trades
    assert all(
        trade.entry_timestamp >= bars[split_index].timestamp
        for trade in oos_result.trades
    )
    assert oos_result.trades
    assert oos_result.trades[0].entry_timestamp == bars[split_index].timestamp


def test_walk_forward_uses_expanding_history_and_non_overlapping_oos_windows():
    from src.backtest.validation import run_walk_forward

    bars = _bars(9)

    def evaluator_factory():
        return lambda history, spec: Signal(
            "UP", stop_price=history[-1].close - 2, score=100
        )

    folds = run_walk_forward(
        bars,
        _spec(),
        evaluator_factory,
        train_bars=3,
        test_bars=2,
        cost_model=CostModel.zero(),
    )

    assert [(fold.train_end, fold.test_end) for fold in folds] == [
        (3, 5),
        (5, 7),
        (7, 9),
    ]
    assert all(
        trade.entry_timestamp >= bars[fold.train_end].timestamp
        for fold in folds
        for trade in fold.result.trades
    )
