"""Shared data types for the Rule Engine (rule_engine/*.md specs).

Every RULE_00X module returns a RuleResult so the scoring/decision-flow
orchestrator (scoring.py) can aggregate them uniformly.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Bar:
    """One OHLCV candle. `closed` is False only for the current, still-forming
    bar — rule modules must never make decisions based on an unclosed bar
    (see backtests/POINT_IN_TIME_AI_BACKTEST.md, chống look-ahead bias)."""

    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    closed: bool = True


@dataclass
class RuleResult:
    """Output of a single RULE_00X evaluation."""

    rule_id: str
    status: str
    score: float
    max_score: float
    reject: bool = False
    detail: dict[str, Any] = field(default_factory=dict)
