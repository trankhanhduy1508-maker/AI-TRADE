"""Fail-closed connection recovery and broker reconciliation contracts."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import math
from pathlib import Path
import sqlite3


@dataclass(frozen=True)
class ReconciliationResult:
    reconciled: bool
    missing_broker_positions: frozenset[str]
    unknown_broker_positions: frozenset[str]


def reconcile_positions(
    local_position_ids: set[str], broker_position_ids: set[str]
) -> ReconciliationResult:
    missing = frozenset(local_position_ids - broker_position_ids)
    unknown = frozenset(broker_position_ids - local_position_ids)
    return ReconciliationResult(
        reconciled=not missing and not unknown,
        missing_broker_positions=missing,
        unknown_broker_positions=unknown,
    )


class RecoveryState:
    def __init__(self):
        self.connected = False
        self.reconciled = False

    def connection_lost(self) -> None:
        self.connected = False
        self.reconciled = False

    def connection_restored(self, result: ReconciliationResult) -> None:
        self.connected = True
        self.reconciled = result.reconciled

    def can_open_new_risk(self) -> bool:
        return self.connected and self.reconciled


class PersistentRecoveryState:
    """Persist recovery gates so a process restart cannot assume safety."""

    def __init__(self, db_path: str | Path):
        self._connection = sqlite3.connect(str(db_path))
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS recovery_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                connected INTEGER NOT NULL CHECK (connected IN (0, 1)),
                reconciled INTEGER NOT NULL CHECK (reconciled IN (0, 1)),
                updated_at TEXT NOT NULL
            )
            """
        )
        self._connection.execute(
            """
            INSERT OR IGNORE INTO recovery_state
                (id, connected, reconciled, updated_at)
            VALUES (1, 0, 0, ?)
            """,
            (self._now(),),
        )
        self._connection.commit()
        self._load()
        # A new process must not inherit permission to open broker risk.
        self.connected = False
        self.reconciled = False
        self._persist()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _load(self) -> None:
        row = self._connection.execute(
            "SELECT connected, reconciled, updated_at FROM recovery_state WHERE id = 1"
        ).fetchone()
        if row is None:
            raise RuntimeError("recovery state row missing")
        self.connected = bool(row[0])
        self.reconciled = bool(row[1])
        self.updated_at = datetime.fromisoformat(row[2])

    def _persist(self) -> None:
        updated_at = self._now()
        self.updated_at = datetime.fromisoformat(updated_at)
        self._connection.execute(
            """
            UPDATE recovery_state
            SET connected = ?, reconciled = ?, updated_at = ?
            WHERE id = 1
            """,
            (int(self.connected), int(self.reconciled), updated_at),
        )
        self._connection.commit()

    def connection_lost(self) -> None:
        self.connected = False
        self.reconciled = False
        self._persist()

    def connection_restored(self, result: ReconciliationResult) -> None:
        self.connected = True
        self.reconciled = result.reconciled
        self._persist()

    def can_open_new_risk(self) -> bool:
        return self.connected and self.reconciled

    def heartbeat(self) -> None:
        """Persist liveness without changing connection or reconciliation gates."""
        self._persist()

    def is_stale(
        self,
        *,
        max_age_seconds: float,
        now: datetime | None = None,
    ) -> bool:
        if not math.isfinite(max_age_seconds) or max_age_seconds < 0:
            raise ValueError("max_age_seconds must be finite and non-negative")
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        return current - self.updated_at > timedelta(seconds=max_age_seconds)

    def close(self) -> None:
        self._connection.close()
