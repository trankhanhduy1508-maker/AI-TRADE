"""Independent, conservative order-risk policy."""

from dataclasses import dataclass
import math

from src.execution.mt5_adapter import MT5OrderRequest


@dataclass(frozen=True)
class RiskLimits:
    max_volume: float
    max_open_positions: int
    max_spread_points: float
    max_daily_loss: float
    max_total_volume_per_symbol: float | None = None

    def __post_init__(self) -> None:
        if not math.isfinite(self.max_volume) or self.max_volume <= 0:
            raise ValueError("max_volume must be finite and positive")
        if self.max_open_positions < 1:
            raise ValueError("max_open_positions must be positive")
        if not math.isfinite(self.max_spread_points) or self.max_spread_points < 0:
            raise ValueError("max_spread_points must be finite and non-negative")
        if not math.isfinite(self.max_daily_loss) or self.max_daily_loss < 0:
            raise ValueError("max_daily_loss must be finite and non-negative")
        if self.max_total_volume_per_symbol is not None and (
            not math.isfinite(self.max_total_volume_per_symbol)
            or self.max_total_volume_per_symbol <= 0
        ):
            raise ValueError("max_total_volume_per_symbol must be finite and positive")


@dataclass(frozen=True)
class RiskContext:
    open_positions: int
    spread_points: float
    daily_loss: float
    current_symbol_volume: float = 0.0
    increases_existing_position: bool = False

    def __post_init__(self) -> None:
        if self.open_positions < 0:
            raise ValueError("open_positions must be non-negative")
        if not math.isfinite(self.current_symbol_volume) or self.current_symbol_volume < 0:
            raise ValueError("current_symbol_volume must be finite and non-negative")


@dataclass(frozen=True)
class RiskDecision:
    allowed: bool
    reasons: tuple[str, ...] = ()


class IndependentRiskEngine:
    """Apply hard limits without changing them for strategy performance."""

    def __init__(self, limits: RiskLimits):
        self._limits = limits

    def evaluate(self, order: MT5OrderRequest, context: RiskContext) -> RiskDecision:
        reasons: list[str] = []
        numeric_values = [order.volume, order.price, context.spread_points, context.daily_loss]
        if not all(math.isfinite(value) for value in numeric_values):
            reasons.append("INVALID_CONTEXT")

        if order.volume > self._limits.max_volume:
            reasons.append("MAX_VOLUME")
        if (
            context.open_positions >= self._limits.max_open_positions
            and not context.increases_existing_position
        ):
            reasons.append("MAX_OPEN_POSITIONS")
        if (
            self._limits.max_total_volume_per_symbol is not None
            and context.current_symbol_volume + order.volume
            > self._limits.max_total_volume_per_symbol
        ):
            reasons.append("MAX_SYMBOL_VOLUME")
        if context.spread_points > self._limits.max_spread_points:
            reasons.append("MAX_SPREAD")
        if context.daily_loss <= -self._limits.max_daily_loss:
            reasons.append("MAX_DAILY_LOSS")

        direction = order.direction.upper()
        if order.stop_loss is None:
            reasons.append("MISSING_STOPS")
        elif not math.isfinite(order.stop_loss):
            reasons.append("INVALID_CONTEXT")
        elif direction == "UP" and order.stop_loss >= order.price:
            reasons.append("INVALID_STOPS")
        elif direction == "DOWN" and order.stop_loss <= order.price:
            reasons.append("INVALID_STOPS")

        # Fixed TP is optional because TRAILING_ONLY and PARTIAL_THEN_TRAIL are
        # first-class. Capital protection still requires a broker-side SL.
        if order.take_profit is not None:
            if not math.isfinite(order.take_profit):
                reasons.append("INVALID_CONTEXT")
            elif direction == "UP" and order.take_profit <= order.price:
                reasons.append("INVALID_TARGET")
            elif direction == "DOWN" and order.take_profit >= order.price:
                reasons.append("INVALID_TARGET")

        return RiskDecision(allowed=not reasons, reasons=tuple(reasons))
