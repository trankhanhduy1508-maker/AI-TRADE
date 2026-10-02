# CWS AUTOTRADE — MT5 CLOUD ONBOARDING BLOCKER EVIDENCE — 2026-10-02

## Scope

Repository: `trankhanhduy1508-maker/AI-TRADE`

Branch: `codex/p0-covel-knowledge-audit`

Starting checkpoint supplied by Founder:
`a3c52cce569deeaf6f0aac1839f779b11b38e7c8`

Goal remains:
- deterministic/frozen strategy engine;
- no LLM BUY/SELL decisions in runtime;
- DEMO only;
- broker-authoritative verification required before calling execution PASS;
- live/funded money HARD LOCKED.

## Runtime grounding

Supabase project:
`oziktadfeenydvgobudr` — region `ap-south-1`.

Current deployed bootstrap:
- function: `ai-trade-mt5-demo-bootstrap`;
- version: **7**;
- ezbr sha256: `873adfafa0e67ec2218e4de0c9f0f090076053484cfbbc4f485c8b8206a9fb4e`;
- GitHub source parity with deployed v7: **TRUE**;
- GitHub blob SHA for `supabase/functions/ai-trade-mt5-demo-bootstrap/index.ts`:
  `cec8443e9c4cad9fee16b92f7abcc66306140ae3`.

No runtime downgrade was deployed.

An attempted v8 safety-forward patch was blocked by the connector safety layer before deployment. Deployed v7 and GitHub parity were therefore left unchanged.

## MetaQuotes transport evidence

Direct WebTerminal transport remains healthy:

- WebSocket bootstrap: PASS;
- server build: **6231**;
- AES session key length: **32 bytes**;
- `brokerOrders=false`;
- `liveMoneyLocked=true`.

Therefore the new-DEMO blocker is not the initial WebSocket/AES transport.

## cmd 27 probe matrix

A read-only onboarding verification probe was run without cmd 30 account creation.

Build/CID matrix:
- server build 6231 + deterministic CID -> code 1;
- build 0 + deterministic CID -> code 1;
- server build 6231 + random CID -> code 1;
- build 0 + random CID -> code 1.

Payload variations were also tested:
- baseline;
- reserved `example.com` email;
- group `demoforex`;
- group `forex`;
- group `demo`;
- empty country;
- empty domain;
- empty UTM;
- agreements=0;
- minimal `demoforex` payload.

All returned broker verification **code 1**.

This rules out the tested build/CID and common opening-field variants as the primary explanation.

## Independent cloud-region evidence

### 1. Supabase / Mumbai

Public WebTerminal config endpoint returned:

- status: `DEMO_HANDSHAKE_BLOCKED`;
- version: 5;
- enabled: **false**;
- hasKey: true;
- hasToken: **false**;
- demoType: `[]`;
- demoLeverage: `[100,50,33,25,10,1]`;
- geo country: `IN`;
- geo city: `Mumbai`.

### 2. Render / Singapore

Service:
`cws-mt5-verify-free`

Plan:
Free, Singapore, auto-deploy OFF.

Stateless pinned-pymt5 opening probe returned:

- status: `VERIFICATION_REJECTED`;
- code: **1**;
- accountCreated: false;
- brokerOrders: false;
- liveMoneyLocked: true.

Its startup WebTerminal config probe returned:

- status: `DEMO_HANDSHAKE_BLOCKED`;
- version: 5;
- enabled: **false**;
- hasKey: true;
- hasToken: **false**;
- demoType: `[]`;
- demoLeverage: `[100,50,33,25,10,1]`;
- geo country: `SG`;
- geo city: `Singapore`.

### 3. Render / Oregon

Temporary free diagnostic service:
`cws-mt5-config-probe-oregon`

Plan:
Free, Oregon, auto-deploy OFF.

Startup config probe returned:

- status: `DEMO_HANDSHAKE_BLOCKED`;
- version: 5;
- enabled: **false**;
- hasKey: true;
- hasToken: **false**;
- demoType: `[]`;
- demoLeverage: `[100,50,33,25,10,1]`;
- geo country: `US`.

Note: the diagnostic script's `source` string still says
`RENDER_SINGAPORE_WEBTERMINAL_CONFIG`; the actual Oregon evidence is identified by
the Render service region plus returned geo country `US`. Do not use that static source
label as the region authority.

## Conclusion: current cloud blocker

Three independent cloud/datacenter egresses now agree:

- Mumbai;
- Singapore;
- Oregon / US.

For each tested cloud egress, MetaQuotes WebTerminal account-opening configuration returns:

- `enabled=false`;
- `hasToken=false`;
- `demoType=[]`.

At the protocol level, cmd 27 correspondingly returns broker code 1.

Therefore the current blocker is:

**METAQUOTES PUBLIC WEBTERMINAL DEMO ONBOARDING IS NOT GRANTED TO THE TESTED CLOUD/DATACENTER EGRESS PATHS.**

This does not prove that MetaQuotes DEMO creation is globally unavailable to a normal residential/mobile/desktop client. It only establishes that the tested autonomous cloud paths cannot currently obtain the WebTerminal demo-onboarding grant.

No CAPTCHA, OTP, phone identity, or upstream restriction was bypassed.

## New DEMO account state

Current database evidence:

- verified new DEMO credential rows: **0**.

Therefore:
- new MetaQuotes DEMO created: **NO**;
- broker-authoritative readback of a new account: **NO**;
- broker DEMO order sent: **NO**;
- broker order/position readback: **NO**;
- restart/reconnect execution recovery: **BLOCKED_BY_NO_NEW_VERIFIED_DEMO**.

Do not call paper/shadow/DB state a broker fill.

## Deterministic TF-013A state

Strategy remains:
`TF-013A-FORWARD-DIVERSIFIED-TREND`.

No trading-brain rebuild was performed.

Current true-forward state has **6 pending directions**:
- 5 UP;
- 1 DOWN.

These are pending next-bar-open transitions in the forward lane, not broker orders.

Frozen rules remain unchanged:
- RETURN_21 sign;
- RETURN_252 sign;
- SMA10 vs SMA200;
- majority vote 2/3;
- 1D closed-bar decision;
- next-bar-open transition;
- ATR(20);
- emergency stop 4 ATR;
- no pyramiding;
- no historical trade backfill.

Promotion gate remains untouched.

## Existing executor remains fail-closed

Current `ai_trade.runtime_config` still reports:

- strategy_id: `TF_004_TIME_SERIES_CHANNEL`;
- timeframe: `15m`;
- enabled: false;
- demo_send_enabled: false;
- risk_profile_approved: false;
- max_total_volume_demo: **NULL**.

Current THE5ERS readiness:
- `BLOCKED_APPROVAL`;
- automation_approval_verified: false;
- risk_profile_approved: false;
- execution_enabled: false;
- demo_send_enabled: false.

No attempt was made to invent `MAX_TOTAL_VOLUME_DEMO`.

No attempt was made to relabel the old TF_004 executor as TF-013A execution.

## Safety state

Still mandatory:
- server-authoritative DEMO gate;
- visible stop;
- risk gate;
- kill switch;
- order-intent dedupe;
- no pyramiding;
- no duplicate fake fills;
- encrypted credentials only;
- no secrets in GitHub/log/APK;
- live/funded money HARD LOCKED.

## Legal continuation

The next valid path is one of:

1. MetaQuotes WebTerminal later grants DEMO onboarding to an autonomous cloud egress; then rerun config -> cmd 27 -> verification -> cmd 30 and require broker-authoritative account readback.

2. Create one legitimate MetaQuotes DEMO through a human-authorized normal client path (for example MT5 mobile/desktop on a non-blocked network), using genuine required identity/phone verification without bypass. Then ingest the resulting DEMO credential securely and verify it broker-authoritatively before execution integration.

Only after a verified DEMO exists should the execution lane be connected to the frozen TF-013A engine.

Before any broker send, explicit risk approval including `MAX_TOTAL_VOLUME_DEMO` is still required. It must not be guessed.

## PASS status

Overall requested broker DEMO execution: **NOT PASS — BLOCKED UPSTREAM**.

This is a real blocker checkpoint, not a fake PASS.

Paper/training/shadow evidence remains paper/shadow evidence only.

Live/funded money remains **HARD LOCKED**.
