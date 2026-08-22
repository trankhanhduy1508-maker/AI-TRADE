from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile

from src.execution.recovery import (
    PersistentRecoveryState,
    RecoveryState,
    reconcile_positions,
)
from src.execution.safety import KillSwitchStore, SafetyGate, SafetySnapshot


@contextmanager
def _db_path():
    handle = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
    path = Path(handle.name)
    handle.close()
    path.unlink(missing_ok=True)
    try:
        yield path
    finally:
        path.unlink(missing_ok=True)


def test_reconnect_requires_exact_position_reconciliation():
    state = RecoveryState()

    state.connection_lost()
    assert not state.can_open_new_risk()

    state.connection_restored(reconcile_positions({"p1"}, {"p1"}))
    assert state.can_open_new_risk()

    state.connection_lost()
    state.connection_restored(reconcile_positions({"p1"}, {"p2"}))
    assert not state.can_open_new_risk()


def test_recovery_state_persists_across_reopen_and_fails_closed_on_loss():
    with _db_path() as path:
        first = PersistentRecoveryState(path)
        first.connection_restored(reconcile_positions({"p1"}, {"p1"}))
        assert first.can_open_new_risk()
        first.close()

        second = PersistentRecoveryState(path)
        assert not second.can_open_new_risk()
        second.connection_restored(reconcile_positions({"p1"}, {"p1"}))
        assert second.can_open_new_risk()
        second.connection_lost()
        assert not second.can_open_new_risk()
        second.close()

        third = PersistentRecoveryState(path)
        assert not third.can_open_new_risk()
        third.close()


def test_recovery_state_reports_stale_heartbeat():
    with _db_path() as path:
        state = PersistentRecoveryState(path)
        future = datetime.now(timezone.utc) + timedelta(seconds=1)
        assert state.is_stale(max_age_seconds=0, now=future)
        state.close()


def test_safety_gate_is_fail_closed_for_unknown_operational_state():
    with _db_path() as path:
        store = KillSwitchStore(path)
        gate = SafetyGate(store)

        decision = gate.evaluate(
            SafetySnapshot(
                connected=True,
                data_fresh=True,
                state_known=False,
                reconciled=True,
                risk_allowed=True,
            )
        )

        assert not decision.allowed
        assert "UNKNOWN_STATE" in decision.reasons
        store.close()


def test_kill_switch_persists_and_requires_explicit_reset():
    with _db_path() as path:
        first = KillSwitchStore(path)
        assert first.is_active()
        first.deactivate("demo operator test")
        first.activate("repeated order errors")
        first.close()

        second = KillSwitchStore(path)
        assert second.is_active()
        decision = SafetyGate(second).evaluate(
            SafetySnapshot(True, True, True, True, True)
        )
        assert not decision.allowed
        assert "KILL_SWITCH_ACTIVE" in decision.reasons
        second.deactivate("explicit test reset")
        assert not second.is_active()
        second.close()
