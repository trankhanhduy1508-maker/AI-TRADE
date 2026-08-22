from contextlib import contextmanager
from pathlib import Path
import tempfile

from src.execution.coordinator import ExecutionCoordinator
from src.execution.audit import AppendOnlyAuditLog
from src.execution.mt5_adapter import MT5OrderRequest, MT5OrderResult
from src.execution.risk import (
    IndependentRiskEngine,
    RiskContext,
    RiskLimits,
)
from src.execution.safety import KillSwitchStore, SafetyGate, SafetySnapshot


class FakeAdapter:
    def __init__(self):
        self.calls = 0

    def submit(self, order):
        self.calls += 1
        return MT5OrderResult(order.client_order_id, "FILLED", "broker-1", 10009)


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


def _order():
    return MT5OrderRequest("intent-1", "EURUSD", "UP", 0.01, 1.1)


def _snapshot(**changes):
    values = {
        "connected": True,
        "data_fresh": True,
        "state_known": True,
        "reconciled": True,
        "risk_allowed": True,
    }
    values.update(changes)
    return SafetySnapshot(**values)


def test_coordinator_blocks_before_adapter_when_kill_switch_is_active():
    with _db_path() as path:
        store = KillSwitchStore(path)
        adapter = FakeAdapter()

        outcome = ExecutionCoordinator(adapter, SafetyGate(store)).submit(
            _order(), _snapshot()
        )

        assert outcome.status == "GATE_BLOCKED"
        assert "KILL_SWITCH_ACTIVE" in outcome.reasons
        assert adapter.calls == 0
        store.close()


def test_coordinator_passes_only_after_explicit_gate_clear():
    with _db_path() as path:
        store = KillSwitchStore(path)
        store.deactivate("demo coordinator test")
        adapter = FakeAdapter()

        outcome = ExecutionCoordinator(adapter, SafetyGate(store)).submit(
            _order(), _snapshot()
        )

        assert outcome.status == "FILLED"
        assert outcome.reasons == ()
        assert adapter.calls == 1
        store.close()


def test_coordinator_does_not_override_independent_risk_policy():
    with _db_path() as path:
        store = KillSwitchStore(path)
        store.deactivate("risk gate test")
        adapter = FakeAdapter()

        outcome = ExecutionCoordinator(adapter, SafetyGate(store)).submit(
            _order(), _snapshot(risk_allowed=False)
        )

        assert outcome.status == "GATE_BLOCKED"
        assert "RISK_POLICY_BLOCK" in outcome.reasons
        assert adapter.calls == 0
        store.close()


def test_coordinator_persists_blocked_event_without_secrets():
    with _db_path() as path:
        store = KillSwitchStore(path)
        audit = AppendOnlyAuditLog(path)
        outcome = ExecutionCoordinator(
            FakeAdapter(), SafetyGate(store), audit
        ).submit(_order(), _snapshot())

        assert outcome.status == "GATE_BLOCKED"
        event = audit.read_all()[0]
        assert event.event_type == "execution_blocked"
        assert event.client_order_id == "intent-1"
        audit.close()
        store.close()


def _risk_engine():
    return IndependentRiskEngine(
        RiskLimits(
            max_volume=0.01,
            max_open_positions=1,
            max_spread_points=20.0,
            max_daily_loss=100.0,
        )
    )


def _risk_order(volume=0.01):
    return MT5OrderRequest(
        "risk-intent",
        "EURUSD",
        "UP",
        volume,
        1.1,
        stop_loss=1.09,
        take_profit=1.12,
    )


def _risk_context(**changes):
    values = {"open_positions": 0, "spread_points": 10.0, "daily_loss": 0.0}
    values.update(changes)
    return RiskContext(**values)


def test_coordinator_runs_independent_risk_engine_before_adapter():
    with _db_path() as path:
        store = KillSwitchStore(path)
        store.deactivate("risk engine coordinator test")
        adapter = FakeAdapter()
        coordinator = ExecutionCoordinator(
            adapter, SafetyGate(store), risk_engine=_risk_engine()
        )

        outcome = coordinator.submit(
            _risk_order(volume=0.02), _snapshot(), _risk_context()
        )

        assert outcome.status == "RISK_BLOCKED"
        assert "MAX_VOLUME" in outcome.reasons
        assert adapter.calls == 0
        store.close()


def test_coordinator_requires_context_when_risk_engine_is_configured():
    with _db_path() as path:
        store = KillSwitchStore(path)
        store.deactivate("risk context coordinator test")
        adapter = FakeAdapter()
        coordinator = ExecutionCoordinator(
            adapter, SafetyGate(store), risk_engine=_risk_engine()
        )

        outcome = coordinator.submit(_risk_order(), _snapshot())

        assert outcome.status == "RISK_BLOCKED"
        assert outcome.reasons == ("RISK_CONTEXT_MISSING",)
        assert adapter.calls == 0
        store.close()


def test_coordinator_passes_valid_order_through_independent_risk_engine():
    with _db_path() as path:
        store = KillSwitchStore(path)
        store.deactivate("valid risk context coordinator test")
        adapter = FakeAdapter()
        coordinator = ExecutionCoordinator(
            adapter, SafetyGate(store), risk_engine=_risk_engine()
        )

        outcome = coordinator.submit(
            _risk_order(), _snapshot(), _risk_context()
        )

        assert outcome.status == "FILLED"
        assert adapter.calls == 1
        store.close()
