import json

print(json.dumps({
    "status":"DEMO_BOOTSTRAP_LOCKED_AFTER_SUCCESS",
    "demo_created":False,
    "broker_orders":False,
    "live_money_locked":True,
    "detail":"Existing MetaQuotes-Demo credentials are already stored in Supabase Vault; duplicate account creation is disabled."
},separators=(",",":")))
