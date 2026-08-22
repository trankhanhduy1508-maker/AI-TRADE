"""Chronological validation helpers for IS/OOS backtests."""

from collections.abc import Callable, Sequence

from src.backtest.costs import CostModel
from src.backtest.engine import SignalEvaluator, run_backtest
from src.backtest.spec import StrategySpec
from src.backtest.types import BacktestResult
from src.rule_engine.types import Bar


EvaluatorFactory = Callable[[], SignalEvaluator]


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
