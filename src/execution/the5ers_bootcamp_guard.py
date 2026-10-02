"""The5ers Bootcamp challenge guard.

This module does not choose trades. It only enforces challenge constraints and
automation-approval requirements before any MT5 DEMO challenge order may pass.

Rules snapshot: 2026-09-27. Re-verify official The5ers rules before activation.
"""

from dataclasses import dataclass
from enum import IntEnum
import math


class BootcampPhase(IntEnum):
    STEP_1 = 1
    STEP_2 = 2
    STEP_3 = 3


@dataclass(frozen=True)
class BootcampPhaseRules:
    phase: BootcampPhase
    initial_balance: float
    profit_target_pct: float = 0.06
    max_loss_pct: float = 0.05

    @property
    def target_balance(self) -> float:
        return self.initial_balance * (1.0 + self.profit_target_pct)

    @property
    def loss_floor(self) -> float:
        return self.initial_balance * (1.0 - self.max_loss_pct)


BOOTCAMP_RULES = {
    BootcampPhase.STEP_1: BootcampPhaseRules(BootcampPhase.STEP_1, 5_000.0),
    BootcampPhase.STEP_2: BootcampPhaseRules(BootcampPhase.STEP_2, 10_000.0),
    BootcampPhase.STEP_3: BootcampPhaseRules(BootcampPhase.STEP_3, 15_000.0),
}


@dataclass(frozen=True)
class BootcampSnapshot:
    phase: BootcampPhase
    balance: float
    equity: float
    automation_approval_verified: bool
    stop_loss_visible: bool
    account_is_demo: bool
    account_trade_mode: str = "ACCOUNT_TRADE_MODE_DEMO"

    def __post_init__(self) -> None:
        for value in (self.balance, self.equity):
            if not math.isfinite(value) or value <= 0:
                raise ValueError("balance/equity must be finite and positive")


@dataclass(frozen=True)
class BootcampRiskIntent:
    """Projected account-currency loss if the new order hits its visible SL."""

    projected_loss_at_stop: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.projected_loss_at_stop):
            raise ValueError("projected_loss_at_stop must be finite")
        if self.projected_loss_at_stop <= 0:
            raise ValueError("projected_loss_at_stop must be positive")


@dataclass(frozen=True)
class BootcampDecision:
    allowed: bool
    reasons: tuple[str, ...]
    target_balance: float
    loss_floor: float
    remaining_loss_budget: float
    progress_to_target: float
    projected_equity_at_stop: float | None = None


class BootcampGuard:
    """Fail-closed challenge guard, separate from the generic strategy risk engine."""

    def evaluate(
        self,
        snapshot: BootcampSnapshot,
        intent: BootcampRiskIntent | None = None,
    ) -> BootcampDecision:
        rules = BOOTCAMP_RULES[snapshot.phase]
        reasons: list[str] = []

        if not snapshot.account_is_demo:
            reasons.append("BOOTCAMP_DEMO_ACCOUNT_REQUIRED")
        if snapshot.account_trade_mode != "ACCOUNT_TRADE_MODE_DEMO":
            reasons.append("BOOTCAMP_DEMO_TRADE_MODE_REQUIRED")
        if not snapshot.automation_approval_verified:
            reasons.append("AUTOMATION_APPROVAL_REQUIRED")
        if not snapshot.stop_loss_visible:
            reasons.append("VISIBLE_STOP_LOSS_REQUIRED")

        floor = rules.loss_floor
        target = rules.target_balance
        current_reference = min(snapshot.balance, snapshot.equity)

        if snapshot.equity <= floor:
            reasons.append("MAX_LOSS_REACHED")
        if snapshot.balance <= floor:
            reasons.append("MAX_LOSS_REACHED")

        remaining_loss_budget = max(0.0, current_reference - floor)
        projected_equity_at_stop: float | None = None
        if intent is not None:
            projected_equity_at_stop = snapshot.equity - intent.projected_loss_at_stop
            if projected_equity_at_stop <= floor:
                reasons.append("PROJECTED_STOP_BREACHES_MAX_LOSS")
            if intent.projected_loss_at_stop > remaining_loss_budget:
                reasons.append("INTENT_EXCEEDS_REMAINING_LOSS_BUDGET")

        target_distance = max(0.0, target - rules.initial_balance)
        achieved = max(0.0, snapshot.balance - rules.initial_balance)
        progress = 1.0 if target_distance == 0 else min(1.0, achieved / target_distance)

        # De-duplicate while preserving deterministic order.
        unique = tuple(dict.fromkeys(reasons))
        return BootcampDecision(
            allowed=not unique,
            reasons=unique,
            target_balance=target,
            loss_floor=floor,
            remaining_loss_budget=remaining_loss_budget,
            progress_to_target=progress,
            projected_equity_at_stop=projected_equity_at_stop,
        )

    def status(self, snapshot: BootcampSnapshot) -> BootcampDecision:
        """Read-only status path: approval/SL still reported, but no risk intent exists."""
        return self.evaluate(snapshot, None)
