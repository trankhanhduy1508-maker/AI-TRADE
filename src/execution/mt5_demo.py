"""Small, fail-closed DEMO execution primitives for the MT5 adapter.

The module deliberately does not accept or persist credentials. The caller owns
the already-authenticated terminal session; only non-sensitive account and
trade identifiers are journaled.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Iterable


class DemoExecutionError(RuntimeError):
    """Raised whenever the DEMO-only safety contract is not met."""


def ensure_demo_account(account: Any) -> dict[str, Any]:
    """Validate account context before a request can create broker risk."""
    if hasattr(account, "_asdict"):
        data = account._asdict()
    elif isinstance(account, dict):
        data = dict(account)
    else:
        data = vars(account)
    mode = data.get("trade_mode")
    server = str(data.get("server", ""))
    is_demo = mode in (0, "0", "DEMO", "demo") or "demo" in server.lower()
    if not is_demo or mode in (2, "2", "REAL", "real"):
        raise DemoExecutionError("DEMO account required; live trading is locked")
    if data.get("trade_allowed") is False or data.get("trade_expert") is False:
        raise DemoExecutionError("trade permission is disabled for DEMO account")
    return {"login": data.get("login"), "server": server, "trade_mode": mode}


class DemoExecutionJournal:
    """Append-only local journal with deterministic idempotency keys."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _events(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line]

    def prepare(self, symbol: str, side: str, volume: float) -> str:
        seed = f"{symbol.upper()}|{side.upper()}|{volume:.8f}"
        order_id = "DEMO-" + hashlib.sha256(seed.encode()).hexdigest()[:20]
        if not any(e.get("order_id") == order_id for e in self._events()):
            self.record(order_id, "prepared", {"symbol": symbol, "side": side, "volume": volume})
        return order_id

    def record(self, order_id: str, event: str, details: dict[str, Any] | None = None) -> None:
        payload = {"ts": time.time(), "order_id": order_id, "event": event, "details": details or {}}
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(payload, sort_keys=True) + "\n")

    def match_remote(self, order_id: str, remote_records: Iterable[dict[str, Any]]) -> bool:
        """Return true only when a broker record carries our exact idempotency key."""
        return any(order_id in str(record.get("comment", "")) for record in remote_records)
