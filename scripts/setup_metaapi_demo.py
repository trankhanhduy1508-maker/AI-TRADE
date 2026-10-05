"""Provision or reuse a MetaApi cloud account for an MT5 DEMO login.

Secrets are read only from environment variables and are never written to repo.
"""

from __future__ import annotations

import asyncio
import os
import sys


async def main() -> int:
    required = {
        "METAAPI_TOKEN": os.getenv("METAAPI_TOKEN", "").strip(),
        "MT5_DEMO_LOGIN": os.getenv("MT5_DEMO_LOGIN", "").strip(),
        "MT5_DEMO_PASSWORD": os.getenv("MT5_DEMO_PASSWORD", "").strip(),
        "MT5_DEMO_SERVER": os.getenv("MT5_DEMO_SERVER", "").strip(),
    }
    missing = [key for key, value in required.items() if not value]
    if missing:
        print("CONFIG_BLOCKED: missing " + ", ".join(missing), flush=True)
        return 78
    if "demo" not in required["MT5_DEMO_SERVER"].lower():
        print("SAFETY_BLOCKED: MT5_DEMO_SERVER must contain DEMO", flush=True)
        return 77

    from metaapi_cloud_sdk import MetaApi

    api = MetaApi(required["METAAPI_TOKEN"])
    accounts = await api.metatrader_account_api.get_accounts_with_infinite_scroll_pagination()
    account = next(
        (
            item
            for item in accounts
            if str(item.login) == required["MT5_DEMO_LOGIN"]
            and str(item.server) == required["MT5_DEMO_SERVER"]
            and str(item.platform).lower() == "mt5"
        ),
        None,
    )
    if account is None:
        account = await api.metatrader_account_api.create_account(
            account={
                "name": "AI-TRADE DEMO",
                "type": "cloud-g1",
                "login": required["MT5_DEMO_LOGIN"],
                "password": required["MT5_DEMO_PASSWORD"],
                "server": required["MT5_DEMO_SERVER"],
                "platform": "mt5",
                "application": "MetaApi",
                "magic": 260927,
                "reliability": "regular",
            }
        )
    await account.deploy()
    await account.wait_connected()
    print(f"METAAPI_ACCOUNT_ID={account.id}")
    print(f"server={account.server} platform={account.platform} state={account.state}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
