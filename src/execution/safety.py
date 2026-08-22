"""Persistent kill switch and independent fail-closed entry gate."""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sqlite3


class KillSwitchStore:
    def __init__(self, path: str | Path):
        self._connection = sqlite3.connect(str(path))
        self._connection.execute(
            "CREATE TABLE IF NOT EXISTS kill_switch (id INTEGER PRIMARY KEY, active INTEGER NOT NULL, reason TEXT NOT NULL, updated_at TEXT NOT NULL)"
        )
        self._connection.commit()

    def is_active(self) -> bool:
        row = self._connection.execute(
            "SELECT active FROM kill_switch WHERE id = 1"
        ).fetchone()
        return row is None or bool(row[0])

    def activate(self, reason: str) -> None:
        self._set(True, reason)

    def deactivate(self, operator_note: str) -> None:
        if not operator_note.strip():
            raise ValueError("operator_note is required")
        self._set(False, operator_note)

    def _set(self, active: bool, reason: str) -> None:
        self._connection.execute(
            "INSERT INTO kill_switch(id, active, reason, updated_at) VALUES(1, ?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET active=excluded.active, reason=excluded.reason, updated_at=excluded.updated_at",
            (int(active), reason, datetime.now(timezone.utc).isoformat()),
        )
        self._connection.commit()

    def close(self) -> None:
        self._connection.close()


@dataclass(frozen=True)
class SafetySnapshot:
    connected: bool
    data_fresh: bool
    state_known: bool
    reconciled: bool
    risk_allowed: bool
    manual_pause: bool = False


@dataclass(frozen=True)
class GateDecision:
    allowed: bool
    reasons: tuple[str, ...]


class SafetyGate:
    def __init__(self, kill_switch: KillSwitchStore):
        self._kill_switch = kill_switch

    def evaluate(self, snapshot: SafetySnapshot) -> GateDecision:
        reasons: list[str] = []
        if self._kill_switch.is_active():
            reasons.append("KILL_SWITCH_ACTIVE")
        if not snapshot.connected:
            reasons.append("MT5_DISCONNECTED")
        if not snapshot.data_fresh:
            reasons.append("STALE_DATA")
        if not snapshot.state_known:
            reasons.append("UNKNOWN_STATE")
        if not snapshot.reconciled:
            reasons.append("UNRECONCILED_POSITIONS")
        if not snapshot.risk_allowed:
            reasons.append("RISK_POLICY_BLOCK")
        if snapshot.manual_pause:
            reasons.append("MANUAL_PAUSE")
        return GateDecision(allowed=not reasons, reasons=tuple(reasons))
