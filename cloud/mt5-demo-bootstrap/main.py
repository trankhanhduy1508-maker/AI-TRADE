import asyncio
import json
import os
import sys
from typing import Any

from pymt5 import MT5WebClient, DemoAccountRequest

WS_URI = "wss://web.metatrader.app/terminal"


def emit(event: str, **fields: Any) -> None:
    safe = {"event": event, **fields}
    print(json.dumps(safe, separators=(",", ":"), ensure_ascii=False), flush=True)


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def request_from_env() -> DemoAccountRequest:
    return DemoAccountRequest(
        first_name=env("MT5_FIRST_NAME"),
        second_name=env("MT5_SECOND_NAME"),
        email=env("MT5_EMAIL"),
        phone="",
        group=env("MT5_DEMO_GROUP"),
        deposit=float(env("MT5_DEMO_DEPOSIT", "100000")),
        leverage=int(env("MT5_DEMO_LEVERAGE", "100")),
        agreements=1,
        country=env("MT5_COUNTRY", "VN"),
        domain="web.metatrader.app",
        email_confirm_code=int(env("MT5_EMAIL_CODE", "0") or 0),
        phone_confirm_code=0,
        utm_source="ai-trade-cloud",
        utm_campaign="mt5-demo-bootstrap",
    )


async def bootstrap() -> int:
    request = request_from_env()
    if not request.first_name or not request.second_name or not request.email:
        emit("CONFIG_BLOCKED", missing="name_or_email")
        return 2

    cid_hex = env("MT5_CLIENT_ID_HEX")
    if len(cid_hex) != 32:
        emit("CONFIG_BLOCKED", missing="MT5_CLIENT_ID_HEX")
        return 2
    try:
        cid = bytes.fromhex(cid_hex)
    except ValueError:
        emit("CONFIG_BLOCKED", invalid="MT5_CLIENT_ID_HEX")
        return 2

    emit(
        "BOOTSTRAP_START",
        mode="DEMO_ONLY",
        server="MetaQuotes-Demo",
        real_money=False,
        broker_orders=False,
    )

    async with MT5WebClient(uri=WS_URI, timeout=30) as client:
        verification = await client.request_opening_verification(
            request,
            build=5687,
            cid=cid,
        )
        emit(
            "VERIFICATION_STATUS",
            email_required=bool(verification.email),
            phone_required=bool(verification.phone),
            email_code_present=bool(request.email_confirm_code),
        )

        if verification.phone:
            emit("BLOCKED", reason="PHONE_VERIFICATION_REQUIRED")
            return 3

        if verification.email and not request.email_confirm_code:
            emit("BLOCKED", reason="EMAIL_VERIFICATION_REQUIRED")
            return 4

        if verification.email and request.email_confirm_code:
            submitted = await client.submit_opening_verification(
                request,
                cid=cid,
                initialize=False,
            )
            emit(
                "VERIFICATION_SUBMITTED",
                email_ok=bool(submitted.email),
                phone_ok=bool(submitted.phone),
            )
            if not submitted.email:
                emit("BLOCKED", reason="EMAIL_VERIFICATION_REJECTED")
                return 5

        result = await client.open_demo_account(
            request,
            cid=cid,
            initialize=False,
        )
        if not result.success:
            emit("DEMO_CREATE_FAILED", code=int(result.code))
            return 6

        login = int(result.login)
        password = str(result.password)
        if login <= 0 or not password:
            emit("DEMO_CREATE_FAILED", reason="MISSING_CREDENTIALS")
            return 6

        emit(
            "DEMO_CREATED",
            login=login,
            password_exposed=False,
            investor_password_exposed=False,
        )

    async with MT5WebClient(uri=WS_URI, timeout=30) as client:
        await client.login(login=login, password=password, cid=cid)
        account = await client.get_account()
        terminal = await client.terminal_info()

        emit(
            "DEMO_VERIFIED",
            login=login,
            server=str(account.get("server") or account.get("server_name") or terminal.get("server") or ""),
            company=str(account.get("company") or terminal.get("company") or ""),
            currency=str(account.get("currency") or ""),
            balance=float(account.get("balance") or 0.0),
            leverage=int(account.get("leverage") or 0),
            trade_allowed=bool(account.get("trade_allowed", False)),
            read_only=bool(account.get("is_read_only", False)),
            live_money=False,
            broker_orders=False,
        )

        # Keep the verified DEMO session alive. No order is sent by this bootstrap worker.
        while True:
            await asyncio.sleep(300)
            try:
                account = await client.get_account()
                emit(
                    "DEMO_HEARTBEAT",
                    login=login,
                    balance=float(account.get("balance") or 0.0),
                    trade_allowed=bool(account.get("trade_allowed", False)),
                    broker_orders=False,
                )
            except Exception as exc:
                emit("HEARTBEAT_ERROR", error=type(exc).__name__)
                return 7


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(bootstrap()))
    except KeyboardInterrupt:
        raise SystemExit(0)
    except Exception as exc:
        emit("FATAL", error=type(exc).__name__, detail=str(exc)[:240])
        raise
