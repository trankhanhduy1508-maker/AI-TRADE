"""Data contracts for deterministic backtests.

These types intentionally describe price-unit outcomes only. They do not
contain account balance, leverage, lot sizing, or capital-risk decisions.
"""

from dataclasses import dataclass
from typing import Optional

from src.rule_engine.types import Bar


@dataclass(frozen=True)
class Signal:
    """A candidate emitted by a signal evaluator at a closed bar."""

    direction: str
    stop_price: float
    score: float
    target_price: Optional[float] = None


@dataclass(frozen=True)
class Trade:
    """One completed simulated position."""

    direction: str
    entry_timestamp: str
    exit_timestamp: str
    entry_price: float
    exit_price: float
    stop_price: float
    initial_stop_price: float
    target_price: Optional[float]
    pnl_price: float
    exit_reason: str
    gross_pnl_price: float = 0.0
    cost_price: float = 0.0
    holding_bars: int = 0


@dataclass(frozen=True)
class OpenPosition:
    """A position still open at the end of the available data."""

    direction: str
    entry_timestamp: str
    entry_price: float
    stop_price: float
    target_price: Optional[float]


@dataclass(frozen=True)
class BacktestResult:
    """Closed-trade results and transparent end-of-data state."""

    trades: tuple[Trade, ...]
    metrics: dict[str, float | int | None]
    open_position: Optional[OpenPosition] = None
