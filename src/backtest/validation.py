"""Chronological validation helpers for IS/OOS backtests."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from src.backtest.costs import CostModel
from src.backtest.engine import SignalEvaluator, run_backtest
from src.backtest.spec import StrategySpec
from src.backtest.types import BacktestResult
from src.rule_engine.types import Bar


EvaluatorFactory = Callable[[], SignalEvaluator]


@dataclass(frozen=True)
class WalkForwardFold:
    train_end: int
    test_end: int
    result: BacktestResult


def run_is_oos(
    bars: Sequence[Bar],
    spec: StrategySpec,
    evaluator_factory: EvaluatorFactory,
    split_index: int,
    cost_model: CostModel | None = None,
) -> tuple[BacktestResult, BacktestResult]:
    """Run fixed-rule IS and warm-up-aware chronological OOS simulations.

    The IS run ends at ``split_index``. The OOS evaluator receives the full
    prior closed-bar history for state warm-up, but its signals are accepted
    only from ``split_index`` onward. A fresh evaluator prevents state leakage
    from the IS run.
    """

    if not 0 < split_index < len(bars):
        raise ValueError("split_index must be inside the bar range")

    is_result = run_backtest(
        bars[:split_index],
        spec,
        evaluator_factory(),
        cost_model=cost_model,
        signal_start_index=0,
        signal_end_index=split_index,
    )
    oos_result = run_backtest(
        bars,
        spec,
        evaluator_factory(),
        cost_model=cost_model,
        signal_start_index=split_index,
        signal_end_index=len(bars),
    )
    return is_result, oos_result


def run_walk_forward(
    bars: Sequence[Bar],
    spec: StrategySpec,
    evaluator_factory: EvaluatorFactory,
    train_bars: int,
    test_bars: int,
    cost_model: CostModel | None = None,
) -> tuple[WalkForwardFold, ...]:
    """Run fixed, expanding-history OOS windows without parameter tuning.

    Each fold accepts signals only in its test window. The evaluator receives
    all bars from the beginning through that window's end so point-in-time
    indicators can warm up without leaking future information. This helper
    reports research evidence; it does not select parameters or size capital.
    """

    if train_bars < 1 or test_bars < 1:
        raise ValueError("train_bars and test_bars must be positive")
    if train_bars >= len(bars):
        raise ValueError("train_bars must leave at least one test bar")

    folds: list[WalkForwardFold] = []
    train_end = train_bars
    while train_end < len(bars):
        test_end = min(train_end + test_bars, len(bars))
        result = run_backtest(
            bars[:test_end],
            spec,
            evaluator_factory(),
            cost_model=cost_model,
            signal_start_index=train_end,
            signal_end_index=test_end,
        )
        folds.append(
            WalkForwardFold(
                train_end=train_end,
                test_end=test_end,
                result=result,
            )
        )
        train_end = test_end
    return tuple(folds)
