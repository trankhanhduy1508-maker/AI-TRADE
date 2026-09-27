import asyncio
import json
import os
import urllib.parse
import urllib.request

from pymt5 import MT5WebClient, DemoAccountRequest
from pymt5.constants import CMD_OPEN_DEMO
from pymt5._parsers import _parse_open_account_result

WS_URI = "wss://web.metatrader.app/terminal"
INGEST_URL = "https://oziktadfeenydvgobudr.supabase.co/functions/v1/ai-trade-mt5-vault-ingest"
OIDC_AUD = "ai-trade-mt5-vault"


def emit(event, **fields):
    safe = {"event": event, **fields}
    print(json.dumps(safe, separators=(",", ":"), ensure_ascii=False), flush=True)


def get_oidc_token():
    base = os.environ["ACTIONS_ID_TOKEN_REQUEST_URL"]
    req_token = os.environ["ACTIONS_ID_TOKEN_REQUEST_TOKEN"]
    sep = "&" if "?" in base else "?"
    url = base + sep + urllib.parse.urlencode({"audience": OIDC_AUD})
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {req_token}"})
    with urllib.request.urlopen(req, timeout=15) as res:
        payload = json.loads(res.read().decode("utf-8"))
    token = str(payload.get("value") or "")
    if not token:
        raise RuntimeError("OIDC_TOKEN_MISSING")
    return token


def store_in_vault(token, *, login, server, password, investor_password):
    body = json.dumps({
        "login": int(login),
        "server": server,
        "password": password,
        "investorPassword": investor_password,
        "accountType": "DEMO",
        "runId": os.environ["GITHUB_RUN_ID"],
    }).encode("utf-8")
    req = urllib.request.Request(
        INGEST_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as res:
        result = json.loads(res.read().decode("utf-8"))
    if result.get("status") != "MT5_DEMO_CREDENTIALS_STORED":
        raise RuntimeError("VAULT_INGEST_NOT_CONFIRMED")
    return result


async def main():
    emit("CREATE_START", mode="METAQUOTES_DEMO_ONLY", broker_orders=False, live_money=False)

    request = DemoAccountRequest(
        first_name="AITrade",
        second_name="Demo",
        email="",
        phone="",
        group="",
        deposit=100000.0,
        leverage=100,
        agreements=1,
        country="VN",
        domain="web.metatrader.app",
        utm_source="ai-trade-cloud",
        utm_campaign="generic-demo-forward-validation",
    )

    async with MT5WebClient(uri=WS_URI, timeout=25) as client:
        await client.init_session()
        payload = client._build_opening_base_payload(request)
        raw = await client.transport.send_command(CMD_OPEN_DEMO, payload)
        body_len = len(raw.body or b"")
        diagnostic = {
            "event": "OPEN_DEMO_RAW",
            "command_code": int(raw.code),
            "body_len": body_len,
            "credential_shape": body_len >= 76,
        }
        if raw.code != 0 or body_len < 76:
            diagnostic["body_prefix_hex"] = (raw.body or b"")[:32].hex()
        print(json.dumps(diagnostic, separators=(",", ":")), flush=True)
        result = _parse_open_account_result(raw.body)

    emit(
        "OPEN_DEMO_RESULT",
        success=bool(result.success),
        code=int(result.code),
        login=int(result.login or 0),
        password_exposed=False,
        investor_password_exposed=False,
    )
    if raw.code != 0:
        raise RuntimeError(f"DEMO_COMMAND_REJECTED_HEADER_{raw.code}")
    if not result.success or int(result.login or 0) <= 0 or not result.password:
        raise RuntimeError(f"DEMO_CREATE_REJECTED_CODE_{result.code}_BODY_{body_len}")

    login = int(result.login)
    password = str(result.password)
    investor = str(result.investor_password or "")

    async with MT5WebClient(uri=WS_URI, timeout=25) as client:
        await client.login(login=login, password=password)
        account = await client.get_account()

    server = str(account.get("server") or account.get("server_name") or "")
    is_demo = bool(account.get("is_demo", False))
    is_real = bool(account.get("is_real", False))
    trade_allowed = bool(account.get("trade_allowed", False))
    balance = float(account.get("balance") or 0.0)
    leverage = int(account.get("leverage") or 0)

    emit(
        "DEMO_VERIFY",
        login=login,
        server=server,
        is_demo=is_demo,
        is_real=is_real,
        trade_allowed=trade_allowed,
        balance=balance,
        leverage=leverage,
        broker_orders=False,
        live_money=False,
    )

    if not is_demo or is_real or "demo" not in server.lower():
        raise RuntimeError("ACCOUNT_NOT_CONFIRMED_DEMO")

    oidc = get_oidc_token()
    stored = store_in_vault(
        oidc,
        login=login,
        server=server,
        password=password,
        investor_password=investor,
    )

    emit(
        "DEMO_STORED",
        login=login,
        server=server,
        password_stored_in_vault=bool(stored.get("passwordStoredInVault")),
        password_exposed=False,
        broker_orders=False,
        live_money=False,
    )


if __name__ == "__main__":
    asyncio.run(main())
