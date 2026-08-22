"""Point-in-time time-series momentum signal adapter.

This module is a small AI-TRADE implementation derivation inspired by the
time-series momentum research cited in the strategy provenance. It is not a
claim that the cited paper specifies these exact operational parameters.
"""

from collections.abc import Sequence

from src.backtest.spec import StrategySpec
from src.backtest.types import Signal
from src.rule_engine.types import Bar


class TimeSeriesMomentumEvaluator:
    """Emit direction from a prior close comparison and a prior-bar stop."""

    def __call__(self, history: Sequence[Bar], spec: StrategySpec) -> Signal | None:
        if not history or not history[-1].closed:
            return None

        lookback = spec.lookback_bars
        stop_lookback = spec.stop_lookback_bars
        if len(history) <= lookback or len(history) <= stop_lookback:
            return None

        current = history[-1]
        reference = history[-lookback - 1].close
        prior = history[-stop_lookback - 1 : -1]
        if reference == current.close:
            return None

        if current.close > reference:
            stop = min(bar.low for bar in prior) - spec.stop_buffer_price
            direction = "UP"
        else:
            stop = max(bar.high for bar in prior) + spec.stop_buffer_price
            direction = "DOWN"

        return Signal(direction=direction, stop_price=stop, score=100.0)
