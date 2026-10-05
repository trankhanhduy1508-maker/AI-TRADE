"""Deterministic, signal-only historical backtest components."""

from src.backtest.engine import run_backtest
from src.backtest.spec import load_strategy_spec, strategy_spec_from_dict

__all__ = ["load_strategy_spec", "run_backtest", "strategy_spec_from_dict"]
