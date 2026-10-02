# AI-TRADE Cloud Runtime Evidence — 2026-09-27

## Goal

Remove the Windows/desktop MT5 dependency and run the autonomous MT5 DEMO bot entirely in cloud infrastructure.

## Production runtime

AppDeploy application: `AI-TRADE Cloud`

Status dashboard:
`https://ai-trade-cloud-vpwo6l.v2.appdeploy.ai/`

Scheduler:
- name: `trade-tick`
- cadence: every 5 minutes
- latest observed deployment: `ready`
- latest observed cron result: `success`
- failure_count: `0`

QA:
- frontend errors: none
- backend errors: none
- network errors: none
- web/mobile snapshots produced by AppDeploy QA.

## Broker bridge

MetaApi JavaScript SDK `29.3.3`.

Runtime requires:
- MT5
- broker server name containing `demo`
- MetaApi account information type `ACCOUNT_TRADE_MODE_DEMO`
- `tradeAllowed=true`
- no investor/read-only mode.

No LIVE-money branch exists in the production runtime.

## Automated lifecycle

`closed bar -> signal -> spread/daily-loss gate -> entry -> broker SL -> trailing / partial -> winner pyramid -> hold / exit management`

Implemented safeguards:
- 0.01 maximum base DEMO lot;
- mandatory initial protective stop;
- deterministic intent IDs;
- bounded persisted intent history;
- ambiguous submit state retained rather than blindly retried;
- only positions with bot magic number are managed;
- partial close normalized to broker volume grid;
- impossible partial close falls back to keeping the protective stop and removing TP for trailing;
- stop ratchet never intentionally widens risk;
- winner pyramid is only allowed on MT5 netting accounts;
- pyramid requires current position to be profitable;
- original stop must already protect at least breakeven;
- current signal must remain in same direction;
- max pyramid adds defaults to one;
- total DEMO volume is capped by the configured add count.

## Staging evidence

Supabase staging proved the no-PC scheduler path before production AppDeploy:
- Edge Function `ai-trade-tick` ACTIVE;
- cron job ran successfully every minute;
- private runtime recorded `DISABLED` while locked;
- explicit credential-gate probe recorded `CONFIG_BLOCKED` for missing MetaApi credentials;
- staging was returned to `enabled=false`, `demo_send_enabled=false`.

## Current gate

Broker DEMO runtime cannot be marked PASS until the out-of-band secrets are supplied:

1. `METAAPI_TOKEN`
2. `MT5_DEMO_LOGIN`
3. `MT5_DEMO_PASSWORD`
4. `MT5_DEMO_SERVER`
5. `AI_TRADE_DEMO_ENABLE`

Secrets must not be pasted into chat or committed to GitHub.

After secrets are attached, evidence still required before declaring broker-runtime PASS:
- MetaApi account deploy/connect;
- account type DEMO verified;
- market data/candles verified;
- one controlled DEMO entry with broker-side SL;
- trailing modify;
- partial or safe partial fallback;
- duplicate suppression;
- restart/state persistence;
- winner pyramid only if all gates are naturally met.
