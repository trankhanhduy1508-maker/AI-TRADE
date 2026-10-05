"""Persistent append-only execution audit events without sensitive fields."""

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any


@dataclass(frozen=True)
class AuditEvent:
    event_type: str
    result: str
    details: dict[str, Any]
    client_order_id: str | None = None


class AppendOnlyAuditLog:
    def __init__(self, path: str | Path):
        self._connection = sqlite3.connect(str(path))
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                result TEXT NOT NULL,
                client_order_id TEXT,
                details_json TEXT NOT NULL
            )
            """
        )
        self._connection.commit()

    def append(self, event: AuditEvent) -> None:
        if not event.event_type.strip() or not event.result.strip():
            raise ValueError("event_type and result are required")
        self._reject_sensitive(event.details)
        details_json = json.dumps(event.details, sort_keys=True, separators=(",", ":"))
        self._connection.execute(
            "INSERT INTO audit_events(timestamp, event_type, result, client_order_id, details_json) VALUES (?, ?, ?, ?, ?)",
            (
                datetime.now(timezone.utc).isoformat(),
                event.event_type,
                event.result,
                event.client_order_id,
                details_json,
            ),
        )
        self._connection.commit()

    def read_all(self) -> tuple[AuditEvent, ...]:
        rows = self._connection.execute(
            "SELECT event_type, result, client_order_id, details_json FROM audit_events ORDER BY id"
        ).fetchall()
        return tuple(
            AuditEvent(
                event_type=row[0],
                result=row[1],
                client_order_id=row[2],
                details=json.loads(row[3]),
            )
            for row in rows
        )

    def close(self) -> None:
        self._connection.close()

    @classmethod
    def _reject_sensitive(cls, value: Any) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                normalized = str(key).lower().replace("-", "_")
                if any(token in normalized for token in ("api_key", "secret", "password", "token", "private_key")):
                    raise ValueError("sensitive fields are forbidden in audit details")
                cls._reject_sensitive(nested)
        elif isinstance(value, (list, tuple)):
            for nested in value:
                cls._reject_sensitive(nested)
