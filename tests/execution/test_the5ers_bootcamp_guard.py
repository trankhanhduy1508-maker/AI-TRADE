from datetime import datetime, timedelta, timezone

from src.execution.prop_firm_compliance import (
    CompliancePolicy,
    ComplianceSnapshot,
    PropFirmComplianceGate,
)
from src.execution.the5ers_bootcamp_guard import (
    BOOTCAMP_RULES,
    BootcampGuard,
    BootcampPhase,
    BootcampRiskIntent,
    BootcampSnapshot,
)


def test_bootcamp_phase_numbers_match_canonical_challenge():
    assert BOOTCAMP_RULES[BootcampPhase.STEP_1].target_balance == 5300
    assert BOOTCAMP_RULES[BootcampPhase.STEP_1].loss_floor == 4750
    assert BOOTCAMP_RULES[BootcampPhase.STEP_2].target_balance == 10600
    assert BOOTCAMP_RULES[BootcampPhase.STEP_2].loss_floor == 9500
    assert BOOTCAMP_RULES[BootcampPhase.STEP_3].target_balance == 15900
    assert BOOTCAMP_RULES[BootcampPhase.STEP_3].loss_floor == 14250


def test_bootcamp_guard_blocks_without_written_automation_approval():
    decision = BootcampGuard().evaluate(
        BootcampSnapshot(
            phase=BootcampPhase.STEP_1,
            balance=5000,
            equity=5000,
            automation_approval_verified=False,
            stop_loss_visible=True,
            account_is_demo=True,
        ),
        BootcampRiskIntent(50),
    )
    assert not decision.allowed
    assert "AUTOMATION_APPROVAL_REQUIRED" in decision.reasons


def test_bootcamp_guard_blocks_projected_floor_breach():
    decision = BootcampGuard().evaluate(
        BootcampSnapshot(
            phase=BootcampPhase.STEP_1,
            balance=4800,
            equity=4780,
            automation_approval_verified=True,
            stop_loss_visible=True,
            account_is_demo=True,
        ),
        BootcampRiskIntent(40),
    )
    assert not decision.allowed
    assert decision.loss_floor == 4750
    assert decision.remaining_loss_budget == 30
    assert "PROJECTED_STOP_BREACHES_MAX_LOSS" in decision.reasons
    assert "INTENT_EXCEEDS_REMAINING_LOSS_BUDGET" in decision.reasons


def test_bootcamp_guard_allows_only_when_all_hard_conditions_pass():
    decision = BootcampGuard().evaluate(
        BootcampSnapshot(
            phase=BootcampPhase.STEP_1,
            balance=5100,
            equity=5090,
            automation_approval_verified=True,
            stop_loss_visible=True,
            account_is_demo=True,
        ),
        BootcampRiskIntent(100),
    )
    assert decision.allowed
    assert decision.projected_equity_at_stop == 4990
    assert round(decision.progress_to_target, 4) == round(100 / 300, 4)


def test_compliance_gate_is_deterministic_not_human_impersonation():
    now = datetime(2026, 9, 27, tzinfo=timezone.utc)
    gate = PropFirmComplianceGate(
        CompliancePolicy(timeframe_seconds=900, retry_backoff_seconds=30)
    )
    blocked = gate.evaluate(
        ComplianceSnapshot(
            bar_id="2026-09-27T00:00Z",
            bar_closed=True,
            intents_on_bar=1,
            last_intent_at=now - timedelta(seconds=10),
            now=now,
            written_automation_approval=True,
            visible_stop_loss=True,
        )
    )
    assert not blocked.allowed
    assert "ONE_INTENT_PER_BAR" in blocked.reasons
    assert "DETERMINISTIC_COOLDOWN" in blocked.reasons


def test_compliance_gate_requires_closed_bar_and_visible_stop():
    now = datetime(2026, 9, 27, tzinfo=timezone.utc)
    gate = PropFirmComplianceGate(CompliancePolicy(timeframe_seconds=900))
    decision = gate.evaluate(
        ComplianceSnapshot(
            bar_id="bar",
            bar_closed=False,
            intents_on_bar=0,
            last_intent_at=None,
            now=now,
            written_automation_approval=True,
            visible_stop_loss=False,
        )
    )
    assert not decision.allowed
    assert decision.reasons == ("VISIBLE_STOP_LOSS_REQUIRED", "CLOSED_BAR_REQUIRED")
