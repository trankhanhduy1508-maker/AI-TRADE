"""Stateless MT5 DEMO verifier for Render Free.

This service is deliberately tiny: authenticate one HTTPS request, open one
MetaQuotes WebTerminal session through the pinned pymt5 client, read account
state, return a sanitized response, then close. It stores no broker password,
session token, file, database state, or trading authority.
"""

from __future__ import annotations

import asyncio
import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from pymt5 import DemoAccountRequest, MT5WebClient
from pymt5.constants import CMD_VERIFY_CODE

MAX_BODY = 2048


async def verify_mt5(login: int, password: str) -> dict[str, object]:
    async with MT5WebClient(timeout=30) as client:
        await client.login(login=login, password=password, auto_heartbeat=False)
        account = await client.account_info()

    if not account:
        return {"ok": False, "status": "ACCOUNT_INFO_UNAVAILABLE", "verified": False}

    server = str(account.get("server_name") or account.get("server") or "")
    account_type = int(account.get("account_type", -1))
    is_demo = bool(account.get("is_demo", account_type == 1))
    balance = float(account.get("balance", 0.0) or 0.0)
    equity = float(account.get("equity", balance) or balance)
    currency = str(account.get("currency") or account.get("account_currency") or "USD")
    trade_allowed = bool(account.get("trade_allowed", False))
    read_only = bool(account.get("is_read_only", False) or not trade_allowed)

    verified = is_demo and server == "MetaQuotes-Demo"
    return {
        "ok": True,
        "status": "DEMO_VERIFIED" if verified else "ACCOUNT_NOT_ACCEPTED_AS_DEMO",
        "verified": verified,
        "login": str(login),
        "accountType": account_type,
        "server": server,
        "mode": "DEMO" if verified else "UNKNOWN",
        "balance": balance,
        "equity": equity,
        "currency": currency,
        "tradeAllowed": trade_allowed,
        "readOnly": read_only,
        "passwordExposed": False,
        "brokerOrders": False,
        "liveMoneyLocked": True,
        "source": "RENDER_PYMT5_FALLBACK",
    }



async def probe_opening(email: str, group: str = "") -> dict[str, object]:
    """Probe MetaQuotes DEMO onboarding verification without creating an account."""
    cid = os.urandom(16)
    request = DemoAccountRequest(
        first_name="AI",
        second_name="Trade",
        email=email,
        group=group,
        country="VN",
        deposit=100000.0,
        leverage=100,
        agreements=1,
        domain="web.metatrader.app",
        utm_campaign="mt5-demo-bootstrap",
        utm_source="ai-trade-cloud",
    )

    async with MT5WebClient(timeout=30) as client:
        await client.init_session(cid=cid)
        payload = client._build_opening_verification_payload(
            request=request,
            build=0,
            cid=cid,
        )
        result = await client.transport.send_command(CMD_VERIFY_CODE, payload)

    return {
        "ok": result.code == 0,
        "status": "VERIFICATION_READY" if result.code == 0 else "VERIFICATION_REJECTED",
        "code": int(result.code),
        "emailRequired": bool(result.body[0]) if result.code == 0 and len(result.body) > 0 else None,
        "phoneRequired": bool(result.body[1]) if result.code == 0 and len(result.body) > 1 else None,
        "accountCreated": False,
        "brokerOrders": False,
        "liveMoneyLocked": True,
        "source": "RENDER_SINGAPORE_PYMT5_PROBE",
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "CWSMT5Verifier/1.0"

    @staticmethod
    def token() -> str:
        return os.getenv("AI_TRADE_TRIGGER_TOKEN", "").strip()

    def authorized(self) -> bool:
        expected = self.token()
        supplied = self.headers.get("authorization", "")
        return bool(expected) and supplied.startswith("Bearer ") and hmac.compare_digest(
            supplied[7:], expected
        )

    def respond(self, status: int, payload: dict[str, object]) -> None:
        raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("cache-control", "no-store")
        self.send_header("x-content-type-options", "nosniff")
        self.send_header("content-length", str(len(raw)))
        self.end_headers()
        try:
            self.wfile.write(raw)
        except (BrokenPipeError, ConnectionResetError):
            pass

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
        if self.path.rstrip("/") in ("", "/health"):
            self.respond(
                200,
                {
                    "status": "READY",
                    "stateless": True,
                    "demo_only": True,
                    "live_money_locked": True,
                    "storage": False,
                },
            )
            return
        self.respond(404, {"status": "NOT_FOUND"})

    def do_POST(self) -> None:
        path = self.path.rstrip("/")
        if path not in ("/mt5-verify", "/mt5-opening-probe"):
            self.respond(404, {"status": "NOT_FOUND"})
            return
        if not self.authorized():
            self.respond(401, {"status": "UNAUTHORIZED"})
            return

        try:
            length = int(self.headers.get("content-length", "0"))
        except ValueError:
            length = 0
        if length < 2 or length > MAX_BODY:
            self.respond(400, {"status": "INVALID_REQUEST"})
            return

        try:
            body = json.loads(self.rfile.read(length))

            if path == "/mt5-opening-probe":
                email = body.get("email")
                group = body.get("group", "")
                if (
                    not isinstance(email, str)
                    or not 3 <= len(email) <= 128
                    or "@" not in email
                    or any(ord(ch) < 32 or ord(ch) == 127 for ch in email)
                    or group not in ("", "demoforex", "forex", "demo")
                ):
                    raise ValueError
                result = asyncio.run(probe_opening(email, group))
                self.respond(200, result)
                return

            server = body.get("server")
            login = int(body.get("login"))
            password = body.get("password")
            if (
                server != "MetaQuotes-Demo"
                or login < 10000
                or login > 999999999999999
                or not isinstance(password, str)
                or not 4 <= len(password) <= 32
                or any(ord(ch) < 32 or ord(ch) == 127 for ch in password)
            ):
                raise ValueError
            result = asyncio.run(verify_mt5(login, password))
            password = ""
            self.respond(200 if result.get("verified") else 401, result)
        except Exception as exc:
            # Never echo exception text because broker libraries may include secrets.
            print(f"REQUEST_FAIL {type(exc).__name__}", flush=True)
            self.respond(
                401,
                {
                    "ok": False,
                    "status": "REQUEST_REJECTED",
                    "verified": False,
                    "brokerOrders": False,
                    "liveMoneyLocked": True,
                },
            )

    def log_message(self, fmt: str, *args: object) -> None:
        print("HTTP", fmt % args, flush=True)


def main() -> None:
    port = int(os.getenv("PORT", "10000"))
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
