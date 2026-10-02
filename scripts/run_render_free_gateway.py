"""Tiny on-demand HTTP gateway for Render Free.

Render stays stateless and only runs one cloud AutoTrade cycle when explicitly
triggered. Broker order submission remains fail-closed in the underlying runner.
"""

from __future__ import annotations

import asyncio
import hmac
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from run_metaapi_cloud_autotrade import main as run_cloud_once


_RUN_LOCK = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    server_version = "CWSAutoTradeRenderFree/1.0"

    def _json(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("cache-control", "no-store")
        self.send_header("x-content-type-options", "nosniff")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self) -> bool:
        expected = os.getenv("AI_TRADE_TRIGGER_TOKEN", "").strip()
        if not expected:
            return False
        supplied = self.headers.get("authorization", "")
        prefix = "Bearer "
        if not supplied.startswith(prefix):
            return False
        return hmac.compare_digest(supplied[len(prefix):], expected)

    def do_GET(self) -> None:
        if self.path.rstrip("/") == "/health":
            self._json(
                200,
                {
                    "status": "READY",
                    "mode": "RENDER_FREE_ON_DEMAND",
                    "demo_only": True,
                    "live_money_locked": True,
                    "order_send_enabled": False,
                    "trigger_configured": bool(
                        os.getenv("AI_TRADE_TRIGGER_TOKEN", "").strip()
                    ),
                },
            )
            return
        self._json(404, {"status": "NOT_FOUND"})

    def do_POST(self) -> None:
        if self.path.rstrip("/") != "/run-once":
            self._json(404, {"status": "NOT_FOUND"})
            return
        if not self._authorized():
            configured = bool(os.getenv("AI_TRADE_TRIGGER_TOKEN", "").strip())
            self._json(
                401 if configured else 503,
                {"status": "UNAUTHORIZED" if configured else "TRIGGER_NOT_CONFIGURED"},
            )
            return
        if not _RUN_LOCK.acquire(blocking=False):
            self._json(409, {"status": "BUSY"})
            return
        try:
            os.environ["AI_TRADE_ONCE"] = "YES"
            rc = asyncio.run(run_cloud_once())
            if rc == 0:
                self._json(
                    200,
                    {
                        "status": "DONE",
                        "demo_only": True,
                        "live_money_locked": True,
                        "order_send_enabled": False,
                    },
                )
            elif rc == 78:
                self._json(503, {"status": "CONFIG_BLOCKED"})
            else:
                self._json(500, {"status": "RUNNER_FAILED", "code": rc})
        except Exception as exc:
            print(f"RUN_ONCE_ERROR {type(exc).__name__}", flush=True)
            self._json(500, {"status": "RUNNER_ERROR"})
        finally:
            _RUN_LOCK.release()

    def log_message(self, fmt: str, *args: object) -> None:
        print("HTTP", fmt % args, flush=True)


def main() -> None:
    port = int(os.getenv("PORT", "10000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(
        f"READY port={port} mode=RENDER_FREE_ON_DEMAND "
        "demo_only=true live_money_locked=true",
        flush=True,
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
