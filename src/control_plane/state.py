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
        self._connection.commit()

    def new_entries_paused(self) -> bool:
        return self._read("new_entries_paused", default=True)

    def kill_switch_active(self) -> bool:
        return self._read("kill_switch_active", default=True)

    def pause_new_entries(self, reason: str) -> None:
        self._write("new_entries_paused", True, reason)

    def resume_new_entries(self, operator_note: str) -> None:
        if not operator_note.strip():
            raise ValueError("operator_note is required")
        self._write("new_entries_paused", False, operator_note)

    def activate_kill_switch(self, reason: str) -> None:
        self._write("kill_switch_active", True, reason)

    def close(self) -> None:
        self._connection.close()

    def _read(self, key: str, *, default: bool) -> bool:
        row = self._connection.execute(
            "SELECT value FROM control_state WHERE key = ?", (key,)
        ).fetchone()
        return default if row is None else bool(row[0])

    def _write(self, key: str, value: bool, note: str) -> None:
        self._connection.execute(
            "INSERT INTO control_state(key, value, note, updated_at) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, note=excluded.note, updated_at=excluded.updated_at",
            (key, int(value), note, datetime.now(timezone.utc).isoformat()),
        )
        self._connection.commit()


@dataclass(frozen=True)
class RuntimeHealth:
    mode: str
    mt5_connected: bool
    state_known: bool
    new_entries_paused: bool
    kill_switch_active: bool
    last_error: str | None = None

    @property
    def ready_for_new_entries(self) -> bool:
        return (
            self.mode == "DEMO"
            and self.mt5_connected
            and self.state_known
            and not self.new_entries_paused
            and not self.kill_switch_active
        )

    def to_public_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["ready_for_new_entries"] = self.ready_for_new_entries
        return payload
