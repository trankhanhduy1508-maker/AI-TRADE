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
    max_risk_per_trade_fraction: float | None = None
    max_daily_loss_fraction: float | None = None
    required_account_currency: str | None = None

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
        for name in ("max_risk_per_trade_fraction", "max_daily_loss_fraction"):
            value = getattr(self, name)
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, (float, int))
                or not math.isfinite(value) or not 0 < value <= 1
            ):
                raise ValueError(f"{name} must be a finite fraction in (0, 1]")
        if self.required_account_currency is not None and (
            not isinstance(self.required_account_currency, str)
            or not self.required_account_currency.strip()
        ):
            raise ValueError("required_account_currency must be a nonempty string")


@dataclass(frozen=True)
class RiskContext:
    open_positions: int
    spread_points: float
    daily_loss: float
    current_symbol_volume: float = 0.0
    increases_existing_position: bool = False
    account_equity: float | None = None
    tick_size: float | None = None
    tick_value_per_lot: float | None = None
    account_currency: str | None = None

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

        # Optional broker-equity limits are strict whenever configured. Broker
        # tick value must be in the verified account currency per 1.0 lot;
        # callers cannot substitute pip guesses or an Android-supplied quote.
        use_fractional = (
            self._limits.max_risk_per_trade_fraction is not None
            or self._limits.max_daily_loss_fraction is not None
        )
        equity = context.account_equity
        equity_valid = (
            isinstance(equity, (int, float)) and not isinstance(equity, bool)
            and math.isfinite(equity) and equity > 0
        )
        if use_fractional and not equity_valid:
            reasons.append("BROKER_EQUITY_REQUIRED")
        if self._limits.required_account_currency is not None and (
            not isinstance(context.account_currency, str)
            or context.account_currency.upper()
            != self._limits.required_account_currency.upper()
        ):
            reasons.append("ACCOUNT_CURRENCY_MISMATCH")
        if equity_valid and self._limits.max_daily_loss_fraction is not None and (
            context.daily_loss <= -equity * self._limits.max_daily_loss_fraction
        ):
            reasons.append("MAX_DAILY_LOSS_FRACTION")
        if self._limits.max_risk_per_trade_fraction is not None:
            tick_size = context.tick_size
            tick_value = context.tick_value_per_lot
            metadata_valid = all(
                isinstance(value, (int, float))
                and not isinstance(value, bool)
                and math.isfinite(value) and value > 0
                for value in (tick_size, tick_value)
            )
            if not metadata_valid:
                reasons.append("BROKER_TICK_VALUE_REQUIRED")
            elif equity_valid and order.stop_loss is not None and (
                isinstance(order.stop_loss, (int, float))
                and math.isfinite(order.stop_loss) and order.stop_loss > 0
            ):
                estimated_stop_loss = (
                    abs(order.price - order.stop_loss)
                    / tick_size * tick_value * order.volume
                )
                if not math.isfinite(estimated_stop_loss) or (
                    estimated_stop_loss
                    > equity * self._limits.max_risk_per_trade_fraction
                ):
                    reasons.append("MAX_TRADE_STOP_RISK")

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
