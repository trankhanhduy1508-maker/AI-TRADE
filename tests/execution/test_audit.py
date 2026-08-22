from contextlib import contextmanager
from pathlib import Path
import tempfile

import pytest

from src.execution.audit import AuditEvent, AppendOnlyAuditLog


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


def test_audit_events_are_persistent_and_ordered():
    with _db_path() as path:
        first = AppendOnlyAuditLog(path)
        first.append(AuditEvent("execution_started", "SUCCESS", {"mode": "DEMO"}))
        first.append(AuditEvent("execution_blocked", "REJECTED", {"reason": "KILL_SWITCH_ACTIVE"}))
        first.close()

        second = AppendOnlyAuditLog(path)
        events = second.read_all()
        assert [event.event_type for event in events] == [
            "execution_started",
            "execution_blocked",
        ]
        assert events[1].details["reason"] == "KILL_SWITCH_ACTIVE"
        second.close()


def test_audit_log_rejects_sensitive_fields():
    with _db_path() as path:
        log = AppendOnlyAuditLog(path)
        with pytest.raises(ValueError, match="sensitive"):
            log.append(AuditEvent("bad", "ERROR", {"api_key": "never"}))
        log.close()
