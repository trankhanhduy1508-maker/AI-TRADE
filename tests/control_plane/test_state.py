from contextlib import contextmanager
from pathlib import Path
import tempfile

import pytest

from src.control_plane.state import ControlPlaneState, RuntimeHealth


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


def test_control_state_defaults_fail_closed_and_persists_pause():
    with _db_path() as path:
        first = ControlPlaneState(path)
        assert first.new_entries_paused()
        assert first.kill_switch_active()
        first.resume_new_entries("demo operator test")
        assert not first.new_entries_paused()
        first.close()

        second = ControlPlaneState(path)
        assert not second.new_entries_paused()
        second.pause_new_entries("stale data")
        assert second.new_entries_paused()
        second.close()


def test_resume_requires_explicit_operator_note():
    with _db_path() as path:
        state = ControlPlaneState(path)
        with pytest.raises(ValueError, match="operator_note"):
            state.resume_new_entries("")
        state.close()


def test_runtime_health_is_explicit_about_unknown_state():
    health = RuntimeHealth(
        mode="DEMO",
        mt5_connected=False,
        state_known=False,
        new_entries_paused=True,
        kill_switch_active=True,
        last_error="terminal missing",
    )

    assert not health.ready_for_new_entries
    assert health.to_public_dict()["state_known"] is False


def test_control_commands_are_persistently_audited():
    with _db_path() as path:
        state = ControlPlaneState(path)
        state.resume_new_entries("operator demo resume")
        state.pause_new_entries("stale heartbeat")
        state.activate_kill_switch("reconnect mismatch")

        events = state.read_events()

        assert [event["command"] for event in events] == [
            "RESUME_NEW_ENTRIES",
            "PAUSE_NEW_ENTRIES",
            "ACTIVATE_KILL_SWITCH",
        ]
        assert events[-1]["note"] == "reconnect mismatch"
        assert all(event["source"] == "LOCAL" for event in events)
        state.close()


def test_pause_and_kill_commands_require_reasons():
    with _db_path() as path:
        state = ControlPlaneState(path)
        with pytest.raises(ValueError, match="reason"):
            state.pause_new_entries("")
        with pytest.raises(ValueError, match="reason"):
            state.activate_kill_switch(" ")
        state.close()
