"""Independent, conservative order-risk policy.

This module is deliberately independent from strategy signals and broker
adapters. It rejects malformed or over-limit orders before an execution
coordinator is allowed to call an adapter.
"""

from dataclasses import dataclass
import math

from src.execution.mt5_adapter import MT5OrderRequest


@dataclass(frozen=True)
class RiskLimits:
    max_volume: float
    max_open_positions: int
    max_spread_points: float
    max_daily_loss: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.max_volume) or self.max_volume <= 0:
            raise ValueError("max_volume must be finite and positive")
        if self.max_open_positions < 1:
            raise ValueError("max_open_positions must be positive")
        if not math.isfinite(self.max_spread_points) or self.max_spread_points < 0:
            raise ValueError("max_spread_points must be finite and non-negative")
        if not math.isfinite(self.max_daily_loss) or self.max_daily_loss < 0:
            raise ValueError("max_daily_loss must be finite and non-negative")


@dataclass(frozen=True)
class RiskContext:
    open_positions: int
    spread_points: float
    daily_loss: float

    def __post_init__(self) -> None:
        if self.open_positions < 0:
            raise ValueError("open_positions must be non-negative")


@dataclass(frozen=True)
class RiskDecision:
    allowed: bool
    reasons: tuple[str, ...] = ()


class IndependentRiskEngine:
    """Apply hard limits without changing them for strategy performance."""

    def __init__(self, limits: RiskLimits):
        self._limits = limits

    def evaluate(
        self, order: MT5OrderRequest, context: RiskContext
    ) -> RiskDecision:
        reasons: list[str] = []
        numeric_values = [
            order.volume,
            order.price,
            context.spread_points,
            context.daily_loss,
        ]
        if not all(math.isfinite(value) for value in numeric_values):
            reasons.append("INVALID_CONTEXT")

        if order.volume > self._limits.max_volume:
            reasons.append("MAX_VOLUME")
        if context.open_positions >= self._limits.max_open_positions:
            reasons.append("MAX_OPEN_POSITIONS")
        if context.spread_points > self._limits.max_spread_points:
            reasons.append("MAX_SPREAD")
        if context.daily_loss <= -self._limits.max_daily_loss:
            reasons.append("MAX_DAILY_LOSS")

        direction = order.direction.upper()
        if order.stop_loss is None or order.take_profit is None:
            reasons.append("MISSING_STOPS")
        elif not math.isfinite(order.stop_loss) or not math.isfinite(order.take_profit):
            reasons.append("INVALID_CONTEXT")
        elif direction == "UP":
            if order.stop_loss >= order.price:
                reasons.append("INVALID_STOPS")
            if order.take_profit <= order.price:
                reasons.append("INVALID_TARGET")
        elif direction == "DOWN":
            if order.stop_loss <= order.price:
                reasons.append("INVALID_STOPS")
            if order.take_profit >= order.price:
                reasons.append("INVALID_TARGET")

        return RiskDecision(allowed=not reasons, reasons=tuple(reasons))
