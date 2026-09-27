"""Persistent lifecycle state that prevents repeated partial/pyramid actions."""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sqlite3


@dataclass(frozen=True)
class ManagedPositionState:
    position_id: str
    strategy_id: str
    partial_done: bool
    pyramid_adds: int
    last_stop: float | None
    status: str


class PositionStateStore:
    def __init__(self, path: str | Path):
        self._connection = sqlite3.connect(str(path))
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS managed_positions (
                position_id TEXT PRIMARY KEY,
                strategy_id TEXT NOT NULL,
                partial_done INTEGER NOT NULL DEFAULT 0,
                pyramid_adds INTEGER NOT NULL DEFAULT 0,
                last_stop REAL,
                status TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        self._connection.commit()

    def ensure(self, position_id: str, strategy_id: str, last_stop: float | None = None) -> ManagedPositionState:
        if not position_id.strip() or not strategy_id.strip():
            raise ValueError("position_id and strategy_id are required")
        self._connection.execute(
            """
            INSERT INTO managed_positions(position_id, strategy_id, partial_done, pyramid_adds, last_stop, status, updated_at)
            VALUES (?, ?, 0, 0, ?, 'OPEN', ?)
            ON CONFLICT(position_id) DO NOTHING
            """,
            (position_id, strategy_id, last_stop, datetime.now(timezone.utc).isoformat()),
        )
        self._connection.commit()
        state = self.get(position_id)
        assert state is not None
        return state

    def get(self, position_id: str) -> ManagedPositionState | None:
        row = self._connection.execute(
            "SELECT position_id, strategy_id, partial_done, pyramid_adds, last_stop, status FROM managed_positions WHERE position_id=?",
            (position_id,),
        ).fetchone()
        if row is None:
            return None
        return ManagedPositionState(row[0], row[1], bool(row[2]), int(row[3]), row[4], row[5])

    def mark_partial_done(self, position_id: str) -> None:
        self._update(position_id, "partial_done=1")

    def record_pyramid_add(self, position_id: str) -> None:
        self._update(position_id, "pyramid_adds=pyramid_adds+1")

    def record_stop(self, position_id: str, stop: float) -> None:
        self._connection.execute(
            "UPDATE managed_positions SET last_stop=?, updated_at=? WHERE position_id=?",
            (stop, datetime.now(timezone.utc).isoformat(), position_id),
        )
        self._require_changed(position_id)

    def mark_closed(self, position_id: str) -> None:
        self._update(position_id, "status='CLOSED'")

    def _update(self, position_id: str, assignment: str) -> None:
        cursor = self._connection.execute(
            f"UPDATE managed_positions SET {assignment}, updated_at=? WHERE position_id=?",
            (datetime.now(timezone.utc).isoformat(), position_id),
        )
        self._connection.commit()
        if cursor.rowcount != 1:
            raise KeyError(position_id)

    def _require_changed(self, position_id: str) -> None:
        self._connection.commit()
        if self.get(position_id) is None:
            raise KeyError(position_id)

    def open_states(self, strategy_id: str | None = None) -> tuple[ManagedPositionState, ...]:
        if strategy_id is None:
            rows = self._connection.execute(
                "SELECT position_id, strategy_id, partial_done, pyramid_adds, last_stop, status FROM managed_positions WHERE status='OPEN' ORDER BY position_id"
            ).fetchall()
        else:
            rows = self._connection.execute(
                "SELECT position_id, strategy_id, partial_done, pyramid_adds, last_stop, status FROM managed_positions WHERE status='OPEN' AND strategy_id=? ORDER BY position_id",
                (strategy_id,),
            ).fetchall()
        return tuple(
            ManagedPositionState(row[0], row[1], bool(row[2]), int(row[3]), row[4], row[5])
            for row in rows
        )

    def reconcile_broker_positions(
        self,
        strategy_id: str,
        broker_positions: tuple[tuple[str, float | None], ...],
    ) -> None:
        """Treat a successful broker position snapshot as source of truth."""
        broker_ids = {position_id for position_id, _ in broker_positions}
        for position_id, last_stop in broker_positions:
            self.ensure(position_id, strategy_id, last_stop)
        for state in self.open_states(strategy_id):
            if state.position_id not in broker_ids:
                self.mark_closed(state.position_id)

    def close(self) -> None:
        self._connection.close()
