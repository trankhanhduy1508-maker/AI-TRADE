"""Prop-firm compliance timing guard.

Purpose: prevent machine-speed/HFT-like behavior and duplicate automation.
It MUST NOT be used to impersonate a human or bypass anti-abuse detection.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import math


@dataclass(frozen=True)
class CompliancePolicy:
    timeframe_seconds: int
    max_intents_per_bar: int = 1
    retry_backoff_seconds: int = 30

    def __post_init__(self) -> None:
        if self.timeframe_seconds < 60:
            raise ValueError("timeframe_seconds must be >= 60")
        if self.max_intents_per_bar != 1:
            raise ValueError("prop compliance requires exactly one intent per bar")
        if self.retry_backoff_seconds < 1:
            raise ValueError("retry_backoff_seconds must be positive")


@dataclass(frozen=True)
class ComplianceSnapshot:
    bar_id: str
    bar_closed: bool
    intents_on_bar: int
    last_intent_at: datetime | None
    now: datetime
    written_automation_approval: bool
    visible_stop_loss: bool

    def __post_init__(self) -> None:
        if not self.bar_id.strip():
            raise ValueError("bar_id is required")
        if self.intents_on_bar < 0:
            raise ValueError("intents_on_bar must be non-negative")
        if self.now.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        if self.last_intent_at is not None and self.last_intent_at.tzinfo is None:
            raise ValueError("last_intent_at must be timezone-aware")


@dataclass(frozen=True)
class ComplianceDecision:
    allowed: bool
    reasons: tuple[str, ...]


class PropFirmComplianceGate:
    """Deterministic compliance guard. No random jitter or stealth behavior."""

    def __init__(self, policy: CompliancePolicy):
        self._policy = policy

    def evaluate(self, snapshot: ComplianceSnapshot) -> ComplianceDecision:
        reasons: list[str] = []

        if not snapshot.written_automation_approval:
            reasons.append("WRITTEN_AUTOMATION_APPROVAL_REQUIRED")
        if not snapshot.visible_stop_loss:
            reasons.append("VISIBLE_STOP_LOSS_REQUIRED")
        if not snapshot.bar_closed:
            reasons.append("CLOSED_BAR_REQUIRED")
        if snapshot.intents_on_bar >= self._policy.max_intents_per_bar:
            reasons.append("ONE_INTENT_PER_BAR")

        if snapshot.last_intent_at is not None:
            elapsed = (snapshot.now - snapshot.last_intent_at).total_seconds()
            if not math.isfinite(elapsed) or elapsed < 0:
                reasons.append("INVALID_INTENT_CLOCK")
            elif elapsed < self._policy.retry_backoff_seconds:
                reasons.append("DETERMINISTIC_COOLDOWN")

        return ComplianceDecision(
            allowed=not reasons,
            reasons=tuple(dict.fromkeys(reasons)),
        )
