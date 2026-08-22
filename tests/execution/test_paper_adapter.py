from contextlib import contextmanager
from pathlib import Path
import tempfile

from src.execution.mt5_adapter import MT5OrderRequest
from src.execution.paper_adapter import PaperBrokerAdapter
from src.execution.audit import AppendOnlyAuditLog
from src.execution.coordinator import ExecutionCoordinator
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


def _order(client_order_id="paper-1"):
    return MT5OrderRequest(client_order_id, "EURUSD", "UP", 0.01, 1.1)


def test_paper_adapter_fills_deterministically_and_suppresses_duplicates():
    with _db_path() as path:
        adapter = PaperBrokerAdapter(path)
        first = adapter.submit(_order())
        duplicate = adapter.submit(_order())

        assert first.status == "FILLED"
        assert first.broker_order_id == "paper:paper-1"
        assert duplicate.status == "DUPLICATE_SUPPRESSED"
        assert len(adapter.open_orders()) == 1
        adapter.close()


def test_paper_adapter_keeps_stop_and_target_in_position_state():
    with _db_path() as path:
        adapter = PaperBrokerAdapter(path)
        order = MT5OrderRequest(
            "paper-2", "USDJPY", "DOWN", 0.01, 150.0, 151.0, 148.0
        )
        adapter.submit(order)
        position = adapter.open_orders()[0]

        assert position["symbol"] == "USDJPY"
        assert position["stop_loss"] == 151.0
        assert position["take_profit"] == 148.0
        adapter.close()


def test_paper_adapter_runs_through_safety_gate_and_audit_log():
    with _db_path() as path:
        kill_switch = KillSwitchStore(path)
        kill_switch.deactivate("paper integration test")
        adapter = PaperBrokerAdapter(path)
        audit = AppendOnlyAuditLog(path)
        outcome = ExecutionCoordinator(adapter, SafetyGate(kill_switch), audit).submit(
            _order("paper-3"),
            SafetySnapshot(True, True, True, True, True),
        )

        assert outcome.status == "FILLED"
        assert [event.event_type for event in audit.read_all()] == [
            "order_submission"
        ]
        audit.close()
        adapter.close()
        kill_switch.close()
