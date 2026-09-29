"""Cloud-only MT5 DEMO broker preflight using an investor/read-only OIDC lease.

GitHub Actions produces an OIDC token scoped to this repository's trusted
PR #2 probe. Supabase checks the OIDC claims and issues the investor
credential from Vault for this ONE call. No secret is printed, persisted,
included in GitHub artifacts, pushed to GitHub, or passed via CLI arguments.
NO create/modify/close/order method is invoked under any circumstances.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import urllib.parse
import urllib.request

from src.execution.mt5_investor_readback_contract import (
    InvestorReadbackBlocked,
    investor_lease,
    check_broker_readback,
)

LEASE = (
    "https://oziktadfeenydvgobudr.supabase.co/functions/v1/"
    "ai-trade-mt5-demo-lease"
)
BROKER = "wss://web.metatrader.app/terminal"
AUDIENCE = "ai-trade-mt5-demo-lease"
GITHUB_OIDC_ENV = (
    "ACTIONS_ID_TOKEN_REQUEST_URL",
    "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
    "GITHUB_RUN_ID",
)


def investor_credentials() -> tuple[int, str, str]:
    if any(not os.environ.get(name) for name in GITHUB_OIDC_ENV):
        raise InvestorReadbackBlocked("TRUSTED_ACTIONS_OIDC_REQUIRED")
    oidc_url = os.environ["ACTIONS_ID_TOKEN_REQUEST_URL"]
    parsed = urllib.parse.urlsplit(oidc_url)
    host = (parsed.hostname or "").lower()
    # GitHub uses runner/region-specific *.actions.githubusercontent.com
    # endpoints; do not incorrectly pin one regional hostname.
    if (parsed.scheme != "https"
            or not (host == "actions.githubusercontent.com"
                    or host.endswith(".actions.githubusercontent.com"))
            or parsed.username is not None or parsed.password is not None):
        raise InvestorReadbackBlocked("UNTRUSTED_OIDC_ENDPOINT")
    delim = "&" if parsed.query else "?"
    target = oidc_url + delim + urllib.parse.urlencode({"audience": AUDIENCE})
    oidc = urllib.request.Request(
        target,
        headers={
            "Authorization": "Bearer "
                + os.environ["ACTIONS_ID_TOKEN_REQUEST_TOKEN"],
            "Accept": "application/json",
        },
        method="GET",
    )
    with urllib.request.urlopen(oidc, timeout=25) as response:
        if response.status != 200:
            raise InvestorReadbackBlocked("OIDC_ISSUE_FAILED")
        raw = response.read(16384)
    token = json.loads(raw).get("value")
    if not isinstance(token, str) or len(token) < 100:
        raise InvestorReadbackBlocked("OIDC_TOKEN_MISSING")
    req = urllib.request.Request(
        LEASE,
        data=json.dumps({
            "purpose": "preflight",
            "runId": os.environ["GITHUB_RUN_ID"],
        }, separators=(",", ":")).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Cache-Control": "no-store",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=40) as response:
        if response.status != 200:
            raise InvestorReadbackBlocked("INVESTOR_LEASE_DENIED")
        raw = response.read(8192)
    token = ""
    lease = json.loads(raw)
    result = investor_lease(lease)
    if isinstance(lease, dict):
        lease["password"] = None
    del lease
    return result


async def broker_preflight() -> dict[str, bool]:
    login, server, password = investor_credentials()
    # No INFO/DEBUG logs from the pinned third-party SDK. Avoid echoing
    # authentication/session/client state from this public CI job.
    logging.disable(logging.CRITICAL)
    from pymt5 import MT5WebClient
    try:
        async with MT5WebClient(
            uri=BROKER, timeout=30, auto_reconnect=False
        ) as client:
            await client.login(login=login, password=password)
            password = ""
            first = await client.get_account()
            if not isinstance(first, dict):
                raise InvestorReadbackBlocked("BROKER_ACCOUNT_NOT_AVAILABLE")
            if first.get("account_type") != 1 or first.get("server") != server:
                raise InvestorReadbackBlocked("BROKER_NOT_DEMO")
            data = await client.get_positions_and_orders()
            if not isinstance(data, dict) or "positions" not in data:
                raise InvestorReadbackBlocked("BROKER_POSITIONS_MISSING")
            result = check_broker_readback(
                first, data["positions"], login=login, server=server
            )
            last = await client.get_account()
            if (not isinstance(last, dict)
                or last.get("account_type") != 1
                or last.get("server") != server):
                raise InvestorReadbackBlocked("BROKER_ACCOUNT_CHANGED_DURING_READ")
            # Market equity can move during the positions call: requiring an
            # identical equity value would reject healthy market ticks.
            check_broker_readback(
                last, data["positions"], login=login, server=server
            )
            return result
    finally:
        password = ""


def main() -> int:
    result = {
        "ok": False, "status": "BROKER_DEMO_READBACK_BLOCKED",
        "balanceRead": False, "equityRead": False,
        "positionsRead": False, "brokerOrders": False,
        "liveMoneyLocked": True, "credentialsExposed": False,
    }
    try:
        accepted = asyncio.run(asyncio.wait_for(broker_preflight(), 115))
        result.update(accepted)
        result["ok"] = True
        result["status"] = "BROKER_DEMO_INVESTOR_READBACK_VERIFIED"
    except InvestorReadbackBlocked as error:
        # Only internal fixed-name gate codes are eligible for diagnostics.
        reasons = {
            "TRUSTED_ACTIONS_OIDC_REQUIRED", "UNTRUSTED_OIDC_ENDPOINT",
            "OIDC_ISSUE_FAILED", "OIDC_TOKEN_MISSING",
            "INVESTOR_LEASE_DENIED", "INVALID_INVESTOR_ONLY_LEASE",
            "BROKER_ACCOUNT_NOT_AVAILABLE", "BROKER_NOT_DEMO",
            "BROKER_POSITIONS_MISSING", "BROKER_ACCOUNT_CHANGED_DURING_READ",
            "BROKER_NOT_EXACT_DEMO", "BROKER_LOGIN_MISMATCH",
            "BROKER_INVESTOR_RIGHTS_MISSING",
            "BROKER_CURRENCY_INVALID", "BROKER_POSITIONS_UNAVAILABLE",
            "BROKER_POSITION_INCOMPLETE", "BROKER_POSITION_TICKET_INVALID",
            "BROKER_POSITION_SYMBOL_INVALID", "BROKER_POSITION_SIDE_INVALID",
            "BROKER_POSITION_VOLUME_INVALID", "BROKER_PROTECTIVE_PRICE_INVALID",
        }
        code = error.args[0] if error.args else ""
        result["safeReason"] = code if code in reasons else "INTERNAL_DEMO_GATE_BLOCKED"
    except Exception as error:
        # Never log repr(error), HTTP bodies, URL query values, account info
        # or SDK exceptions. Only the exception *class* is safe for CI logs.
        result["errorType"] = type(error).__name__
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
