"""Deterministic position lifecycle rules layered above the broker adapter."""

from dataclasses import dataclass
from enum import StrEnum
import math

from src.execution.mt5_adapter import MT5BrokerAdapter, MT5OrderResult, MT5Position


class ExitMode(StrEnum):
    FIXED_TP = "FIXED_TP"
    TRAILING_ONLY = "TRAILING_ONLY"
    PARTIAL_THEN_TRAIL = "PARTIAL_THEN_TRAIL"


@dataclass(frozen=True)
class LifecyclePlan:
    exit_mode: ExitMode
    partial_fraction: float = 0.5
    max_pyramid_adds: int = 0
    trailing_lookback: int = 20

    def __post_init__(self) -> None:
        if not 0 < self.partial_fraction < 1:
            raise ValueError("partial_fraction must be between 0 and 1")
        if self.max_pyramid_adds < 0:
            raise ValueError("max_pyramid_adds must be non-negative")
        if self.trailing_lookback < 1:
            raise ValueError("trailing_lookback must be positive")


@dataclass(frozen=True)
class PyramidDecision:
    allowed: bool
    reason: str


class PositionLifecycleManager:
    """Manage winners only; never widen protective stops or martingale."""

    def __init__(self, adapter: MT5BrokerAdapter):
        self._adapter = adapter

    @staticmethod
    def is_winner(position: MT5Position, market_price: float) -> bool:
        if not math.isfinite(market_price) or market_price <= 0:
            return False
        if position.direction == "UP":
            return market_price > position.entry_price
        return market_price < position.entry_price

    @staticmethod
    def pyramid_decision(
        position: MT5Position,
        *,
        market_price: float,
        current_adds: int,
        max_adds: int,
        independent_risk_allowed: bool,
    ) -> PyramidDecision:
        if max_adds <= 0:
            return PyramidDecision(False, "PYRAMID_DISABLED")
        if current_adds >= max_adds:
            return PyramidDecision(False, "PYRAMID_LIMIT")
        if not independent_risk_allowed:
            return PyramidDecision(False, "RISK_GATE_BLOCKED")
        if not PositionLifecycleManager.is_winner(position, market_price):
            return PyramidDecision(False, "NOT_A_WINNER")
        return PyramidDecision(True, "WINNER_AND_RISK_ALLOWED")

    def trail_stop(
        self,
        position: MT5Position,
        *,
        client_order_id: str,
        candidate_stop: float,
        keep_take_profit: bool = True,
    ) -> MT5OrderResult:
        target = position.take_profit if keep_take_profit else None
        return self._adapter.modify_position(
            position.position_id,
            client_order_id=client_order_id,
            stop_loss=candidate_stop,
            take_profit=target,
        )

    def partial_close(
        self,
        position: MT5Position,
        *,
        client_order_id: str,
        fraction: float,
    ) -> MT5OrderResult:
        if not math.isfinite(fraction) or not 0 < fraction < 1:
            raise ValueError("fraction must be between 0 and 1")
        volume = self._adapter.normalize_partial_volume(position, fraction)
        return self._adapter.close_position(
            position.position_id,
            client_order_id=client_order_id,
            volume=volume,
        )

    def full_close(self, position: MT5Position, *, client_order_id: str) -> MT5OrderResult:
        return self._adapter.close_position(position.position_id, client_order_id=client_order_id)
