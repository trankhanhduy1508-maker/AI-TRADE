"""Authenticated, replay-safe control protocol core for a future Android transport."""

from dataclasses import dataclass
import hashlib
import hmac
import json
from typing import Callable

from src.control_plane.state import ControlPlaneState, RuntimeHealth


@dataclass(frozen=True)
class SignedControlRequest:
    request_id: str
    command: str
    note: str
    nonce: str
    signature: str

    def __post_init__(self) -> None:
        if not self.request_id.strip():
            raise ValueError("request_id is required")
        if not self.command.strip():
            raise ValueError("command is required")
        if not self.nonce.strip():
            raise ValueError("nonce is required")

    @classmethod
    def signed(
        cls,
        *,
        secret: str,
        request_id: str,
        command: str,
        note: str,
        nonce: str,
    ) -> "SignedControlRequest":
        unsigned = cls(request_id, command, note, nonce, "")
        return cls(
            request_id=request_id,
            command=command,
            note=note,
            nonce=nonce,
            signature=unsigned.signature_for(secret),
        )

    def signature_for(self, secret: str) -> str:
        if not secret:
            raise ValueError("secret is required")
        payload = json.dumps(
            {
                "command": self.command,
                "nonce": self.nonce,
                "note": self.note,
                "request_id": self.request_id,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


class AuthenticatedControlPlane:
    """Apply only signed, one-time commands; no network listener is created."""

    def __init__(
        self,
        state: ControlPlaneState,
        *,
        secret: str,
        health_provider: Callable[[], RuntimeHealth],
    ):
        if not secret:
            raise ValueError("secret is required")
        self._state = state
        self._secret = secret
        self._health_provider = health_provider

    def handle(self, request: SignedControlRequest) -> dict[str, object]:
        expected = request.signature_for(self._secret)
        if not hmac.compare_digest(expected, request.signature):
            return {"status": "AUTHENTICATION_FAILED"}
        if not self._state.claim_remote_request(request.request_id):
            return {"status": "REPLAY_REJECTED"}
        try:
            self._state.apply_authenticated_command(
                request.command,
                request.note,
                source="ANDROID_HMAC",
            )
        except ValueError:
            return {"status": "INVALID_COMMAND"}
        return {
            "status": "APPLIED",
            "health": self._health_provider().to_public_dict(),
        }
