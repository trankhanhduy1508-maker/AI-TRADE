from contextlib import contextmanager
from pathlib import Path
import tempfile

from src.control_plane.remote import AuthenticatedControlPlane, SignedControlRequest
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


def _health() -> RuntimeHealth:
    return RuntimeHealth(
        mode="DEMO",
        mt5_connected=False,
        state_known=False,
        reconciled=False,
        data_fresh=False,
        risk_allowed=False,
        heartbeat_fresh=False,
        new_entries_paused=True,
        kill_switch_active=True,
    )


def _request(secret: str, request_id: str, command: str, note: str) -> SignedControlRequest:
    return SignedControlRequest.signed(
        secret=secret,
        request_id=request_id,
        command=command,
        note=note,
        nonce=f"nonce-{request_id}",
    )


def test_authenticated_android_command_applies_and_is_audited():
    secret = "test-only-secret"
    with _db_path() as path:
        state = ControlPlaneState(path)
        service = AuthenticatedControlPlane(state, secret=secret, health_provider=_health)

        response = service.handle(_request(secret, "r-1", "ACTIVATE_KILL_SWITCH", "android stop"))

        assert response["status"] == "APPLIED"
        assert response["health"]["kill_switch_active"] is True
        assert state.read_events()[-1]["source"] == "ANDROID_HMAC"
        state.close()


def test_invalid_signature_is_rejected_without_state_change():
    with _db_path() as path:
        state = ControlPlaneState(path)
        service = AuthenticatedControlPlane(state, secret="correct", health_provider=_health)
        request = _request("wrong", "r-2", "PAUSE_NEW_ENTRIES", "tampered")

        response = service.handle(request)

        assert response == {"status": "AUTHENTICATION_FAILED"}
        assert state.new_entries_paused() is True
        assert state.read_events() == ()
        state.close()


def test_replay_request_id_is_rejected_persistently():
    secret = "test-only-secret"
    with _db_path() as path:
        first = ControlPlaneState(path)
        service = AuthenticatedControlPlane(first, secret=secret, health_provider=_health)
        request = _request(secret, "r-3", "PAUSE_NEW_ENTRIES", "stale data")

        assert service.handle(request)["status"] == "APPLIED"
        first.close()

        second = ControlPlaneState(path)
        service = AuthenticatedControlPlane(second, secret=secret, health_provider=_health)
        response = service.handle(request)

        assert response == {"status": "REPLAY_REJECTED"}
        assert len(second.read_events()) == 1
        second.close()
