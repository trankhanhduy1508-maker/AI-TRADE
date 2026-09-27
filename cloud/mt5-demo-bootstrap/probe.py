# temporary PR transport probe trigger
import asyncio, json
from pymt5 import MT5WebClient

async def main():
    result={"ok":False,"status":"START","demo_created":False,"broker_orders":False}
    try:
        async with MT5WebClient(uri="wss://web.metatrader.app/terminal", timeout=20) as client:
            init=await client.init_session()
            result={
                "ok": bool(init.code==0),
                "status": "MT5_PROTOCOL_READY" if init.code==0 else "INIT_REJECTED",
                "server_build": int(client.transport.server_build or 0),
                "bootstrap_ready": bool(client.transport.is_ready),
                "init_code": int(init.code),
                "demo_created": False,
                "broker_orders": False,
                "live_money_locked": True,
            }
    except Exception as exc:
        result={
            "ok":False,
            "status":"MT5_PROTOCOL_PROBE_FAILED",
            "error":type(exc).__name__,
            "detail":str(exc)[:300],
            "demo_created":False,
            "broker_orders":False,
            "live_money_locked":True,
        }
    print(json.dumps(result,separators=(",",":")))
    raise SystemExit(0 if result.get("ok") else 2)

asyncio.run(main())
