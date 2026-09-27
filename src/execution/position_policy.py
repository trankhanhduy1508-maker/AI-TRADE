"""Closed-bar position management policy with STOP_FIRST semantics."""

from dataclasses import dataclass
from enum import StrEnum
from collections.abc import Sequence

from src.execution.mt5_adapter import MT5Position
from src.execution.position_lifecycle import ExitMode, LifecyclePlan
from src.execution.position_state import ManagedPositionState
from src.rule_engine.types import Bar


class PositionAction(StrEnum):
    HOLD = "HOLD"
    TRAIL_STOP = "TRAIL_STOP"
    PARTIAL_CLOSE = "PARTIAL_CLOSE"
    FULL_CLOSE = "FULL_CLOSE"


@dataclass(frozen=True)
class PositionInstruction:
    action: PositionAction
    reason: str
    candidate_stop: float | None = None
    partial_fraction: float | None = None


def evaluate_position(
    position: MT5Position,
    bars: Sequence[Bar],
    plan: LifecyclePlan,
    state: ManagedPositionState,
) -> PositionInstruction:
    if not bars or not bars[-1].closed:
        return PositionInstruction(PositionAction.HOLD, "NO_CLOSED_BAR")
    current = bars[-1]

    if position.stop_loss is not None:
        if position.direction == "UP" and current.low <= position.stop_loss:
            return PositionInstruction(PositionAction.FULL_CLOSE, "STOP_HIT")
        if position.direction == "DOWN" and current.high >= position.stop_loss:
            return PositionInstruction(PositionAction.FULL_CLOSE, "STOP_HIT")

    target_hit = False
    if position.take_profit is not None:
        if position.direction == "UP":
            target_hit = current.high >= position.take_profit
        else:
            target_hit = current.low <= position.take_profit

    if target_hit and plan.exit_mode == ExitMode.FIXED_TP:
        return PositionInstruction(PositionAction.FULL_CLOSE, "TARGET_HIT")
    if target_hit and plan.exit_mode == ExitMode.PARTIAL_THEN_TRAIL and not state.partial_done:
        return PositionInstruction(
            PositionAction.PARTIAL_CLOSE,
            "PARTIAL_TARGET_HIT",
            partial_fraction=plan.partial_fraction,
        )

    if plan.exit_mode in {ExitMode.TRAILING_ONLY, ExitMode.PARTIAL_THEN_TRAIL}:
        if len(bars) <= plan.trailing_lookback:
            return PositionInstruction(PositionAction.HOLD, "TRAIL_LOOKBACK_NOT_READY")
        prior = bars[-plan.trailing_lookback - 1 : -1]
        if position.direction == "UP":
            candidate = min(bar.low for bar in prior)
            improves = position.stop_loss is None or candidate > position.stop_loss
            market_safe = candidate < current.close
        else:
            candidate = max(bar.high for bar in prior)
            improves = position.stop_loss is None or candidate < position.stop_loss
            market_safe = candidate > current.close
        if improves and market_safe:
            return PositionInstruction(PositionAction.TRAIL_STOP, "CHANNEL_RATCHET", candidate_stop=candidate)

    return PositionInstruction(PositionAction.HOLD, "NO_EXIT_ACTION")
