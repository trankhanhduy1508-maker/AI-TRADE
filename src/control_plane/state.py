"""Persistent, fail-closed control-plane state and public health snapshot."""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any


class ControlPlaneState:
    """Local source of truth for pause/kill controls, safe across restart."""

    def __init__(self, path: str | Path):
        self._connection = sqlite3.connect(str(path))
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS control_state (
                key TEXT PRIMARY KEY,
                value INTEGER NOT NULL,
                note TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS control_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command TEXT NOT NULL,
                source TEXT NOT NULL,
                note TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS remote_requests (
                request_id TEXT PRIMARY KEY,
                accepted_at TEXT NOT NULL
            )
            """
        )
        self._connection.commit()

    def new_entries_paused(self) -> bool:
        return self._read("new_entries_paused", default=True)

    def kill_switch_active(self) -> bool:
        return self._read("kill_switch_active", default=True)

    def pause_new_entries(self, reason: str) -> None:
        if not reason.strip():
            raise ValueError("reason is required")
        self._write("new_entries_paused", True, reason, "PAUSE_NEW_ENTRIES")

    def resume_new_entries(self, operator_note: str) -> None:
        if not operator_note.strip():
            raise ValueError("operator_note is required")
        self._write(
            "new_entries_paused", False, operator_note, "RESUME_NEW_ENTRIES"
        )

    def activate_kill_switch(self, reason: str) -> None:
        if not reason.strip():
            raise ValueError("reason is required")
        self._write("kill_switch_active", True, reason, "ACTIVATE_KILL_SWITCH")

    def read_events(self) -> tuple[dict[str, str], ...]:
        rows = self._connection.execute(
            "SELECT command, source, note, created_at FROM control_events "
            "ORDER BY id ASC"
        ).fetchall()
        return tuple(
            {
                "command": command,
                "source": source,
                "note": note,
                "created_at": created_at,
            }
            for command, source, note, created_at in rows
        )

    def claim_remote_request(self, request_id: str) -> bool:
        """Atomically accept a remote request ID once across restarts."""
        if not request_id.strip():
            raise ValueError("request_id is required")
        cursor = self._connection.execute(
            "INSERT OR IGNORE INTO remote_requests(request_id, accepted_at) VALUES (?, ?)",
            (request_id, datetime.now(timezone.utc).isoformat()),
        )
        self._connection.commit()
        return cursor.rowcount == 1

    def apply_authenticated_command(self, command: str, note: str, source: str) -> None:
        if source != "ANDROID_HMAC":
            raise ValueError("unsupported remote source")
        if command == "PAUSE_NEW_ENTRIES":
            self._write("new_entries_paused", True, note, command, source=source)
        elif command == "RESUME_NEW_ENTRIES":
            self._write("new_entries_paused", False, note, command, source=source)
        elif command == "ACTIVATE_KILL_SWITCH":
            self._write("kill_switch_active", True, note, command, source=source)
        else:
            raise ValueError("unsupported control command")

    def close(self) -> None:
        self._connection.close()

    def _read(self, key: str, *, default: bool) -> bool:
        row = self._connection.execute(
            "SELECT value FROM control_state WHERE key = ?", (key,)
        ).fetchone()
        return default if row is None else bool(row[0])

    def _write(
        self,
        key: str,
        value: bool,
        note: str,
        command: str,
        *,
        source: str = "LOCAL",
    ) -> None:
        if not source.strip():
            raise ValueError("source is required")
        if not note.strip():
            raise ValueError("note is required")
        now = datetime.now(timezone.utc).isoformat()
        self._connection.execute(
            "INSERT INTO control_state(key, value, note, updated_at) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, note=excluded.note, updated_at=excluded.updated_at",
            (key, int(value), note, now),
        )
        self._connection.execute(
            "INSERT INTO control_events(command, source, note, created_at) "
            "VALUES (?, ?, ?, ?)",
            (command, source, note, now),
        )
        self._connection.commit()


@dataclass(frozen=True)
class RuntimeHealth:
    mode: str
    mt5_connected: bool
    state_known: bool
    reconciled: bool
    data_fresh: bool
    risk_allowed: bool
    heartbeat_fresh: bool
    new_entries_paused: bool
    kill_switch_active: bool
    last_error: str | None = None

    @property
    def ready_for_new_entries(self) -> bool:
        return (
            self.mode == "DEMO"
            and self.mt5_connected
            and self.state_known
            and self.reconciled
            and self.data_fresh
            and self.risk_allowed
            and self.heartbeat_fresh
            and not self.new_entries_paused
            and not self.kill_switch_active
        )

    def to_public_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["ready_for_new_entries"] = self.ready_for_new_entries
        return payload
