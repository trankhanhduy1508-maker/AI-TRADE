"""Ultra-thin on-demand gateway for Render Free.

Render does no trading work itself. It authenticates one request, calls the
server-authoritative Supabase AI-TRADE tick once, returns a small safe result,
then becomes idle again.
"""

from __future__ import annotations

import hmac
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import error, request


_RUN_LOCK = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    server_version = "CWSAutoTradeRenderFree/2.0"

    def _json(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("cache-control", "no-store")
        self.send_header("x-content-type-options", "nosniff")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            # The caller may time out during a Render Free cold start.
            # The upstream tick has already completed; never turn a closed
            # client socket into a second application failure.
            pass

    @staticmethod
    def _token() -> str:
        return os.getenv("AI_TRADE_TRIGGER_TOKEN", "").strip()

    def _authorized(self) -> bool:
        expected = self._token()
        supplied = self.headers.get("authorization", "")
        if not expected or not supplied.startswith("Bearer "):
            return False
        return hmac.compare_digest(supplied[7:], expected)

    def do_HEAD(self) -> None:
        if self.path.rstrip("/") in ("", "/health"):
            self.send_response(200)
            self.send_header("cache-control", "no-store")
            self.send_header("content-length", "0")
            self.end_headers()
            return
        self.send_response(404)
        self.send_header("content-length", "0")
        self.end_headers()

    def do_GET(self) -> None:
        if self.path.rstrip("/") == "/health":
            self._json(
                200,
                {
                    "status": "READY",
                    "mode": "RENDER_FREE_THIN_PROXY",
                    "stateless": True,
                    "demo_only": True,
                    "live_money_locked": True,
                    "render_trading_logic": False,
                    "trigger_configured": bool(self._token()),
                    "upstream_configured": bool(
                        os.getenv("AI_TRADE_SUPABASE_TICK_URL", "").strip()
                    ),
                },
            )
            return
        self._json(404, {"status": "NOT_FOUND"})

    def do_POST(self) -> None:
        if self.path.rstrip("/") != "/run-once":
            self._json(404, {"status": "NOT_FOUND"})
            return

        token = self._token()
        upstream = os.getenv("AI_TRADE_SUPABASE_TICK_URL", "").strip()
        if not token or not upstream:
            self._json(503, {"status": "CONFIG_BLOCKED"})
            return
        if not self._authorized():
            self._json(401, {"status": "UNAUTHORIZED"})
            return
        if not _RUN_LOCK.acquire(blocking=False):
            self._json(409, {"status": "BUSY"})
            return

        try:
            req = request.Request(
                upstream,
                data=b"{}",
                method="POST",
                headers={
                    "content-type": "application/json",
                    "x-ai-trade-cron": token,
                    "user-agent": "cws-autotrade-render-free/2",
                },
            )
            try:
                with request.urlopen(req, timeout=120) as response:
                    status_code = int(response.status)
                    raw = response.read(64 * 1024)
            except error.HTTPError as exc:
                status_code = int(exc.code)
                raw = exc.read(64 * 1024)

            try:
                data = json.loads(raw.decode("utf-8"))
            except Exception:
                data = {}

            safe = {
                "status": str(data.get("status", "UPSTREAM_ERROR")),
                "ok": bool(data.get("ok", False)),
                "live_money_locked": bool(data.get("liveMoneyLocked", True)),
                "render_trading_logic": False,
            }
            self._json(200 if 200 <= status_code < 300 else 502, safe)
        except Exception as exc:
            print(f"UPSTREAM_ERROR {type(exc).__name__}", flush=True)
            self._json(502, {"status": "UPSTREAM_UNAVAILABLE"})
        finally:
            _RUN_LOCK.release()

    def log_message(self, fmt: str, *args: object) -> None:
        print("HTTP", fmt % args, flush=True)


def main() -> None:
    port = int(os.getenv("PORT", "10000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(
        f"READY port={port} mode=RENDER_FREE_THIN_PROXY "
        "stateless=true demo_only=true live_money_locked=true",
        flush=True,
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
