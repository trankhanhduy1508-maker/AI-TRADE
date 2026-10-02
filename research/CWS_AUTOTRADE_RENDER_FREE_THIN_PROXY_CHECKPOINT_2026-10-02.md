# CWS AUTOTRADE — RENDER FREE THIN PROXY CHECKPOINT — 2026-10-02

## Mục tiêu
Giảm công việc của Render.com Free xuống mức tối thiểu, giữ Supabase là source of truth và nơi thực thi logic AutoTrade hiện có.

## Kiến trúc đã triển khai
```text
Caller
  -> Render Free /run-once
       -> xác thực Bearer
       -> gọi đúng 1 lần Supabase ai-trade-tick
       -> trả kết quả rút gọn
  -> Supabase ai-trade-tick
       -> runtime/risk/compliance state
       -> MetaApi
       -> MT5 DEMO khi các gate được phép
```

Render KHÔNG:
- chạy vòng lặp polling;
- cài MetaApi SDK;
- giữ SQLite;
- giữ position/order/kill-switch state;
- chạy AI/model;
- tự quyết định risk/compliance;
- tự bật giao dịch;
- giữ live-money authority.

## Render service
- Name: `cws-autotrade-free`
- Service ID: `srv-davmj8psrm7s73cjbme0`
- Plan: `free`
- Region: `singapore`
- Auto-deploy: `off`
- Runtime: Python stdlib
- Build: `python -m compileall -q scripts/run_render_free_gateway.py`
- Start: `python scripts/run_render_free_gateway.py`
- URL: `https://cws-autotrade-free.onrender.com`

## Source
- Gateway: `scripts/run_render_free_gateway.py`
- Stable checkpoint commit for this implementation:
  `d6884145bba766db9def5c16611ba768888e7782`

## Runtime evidence
### Round 1 — Build/deploy
PASS.
Render deploy `dep-davml63ncjis73evjf80` reached `live`.
Build log: `Build successful`.

### Round 2 — Health
PASS.
`GET /health` returned HTTP 200:
- mode = `RENDER_FREE_THIN_PROXY`
- stateless = true
- demo_only = true
- live_money_locked = true
- render_trading_logic = false
- trigger_configured = true
- upstream_configured = true

### Round 3 — Authenticated run-once
PASS for thin-proxy/safe-block contract.
`POST /run-once` returned HTTP 200 with:
- status = `BLOCKED_APPROVAL`
- ok = true
- live_money_locked = true
- render_trading_logic = false

Supabase `ai_trade.events` recorded the same fresh tick:
- result = `BLOCKED_APPROVAL`
- symbol = EURUSD
- phase = 1
- approval = false
- riskProfileApproved = false
- executionEnabled = false
- demoSendEnabled = false

## Safety state
This checkpoint does NOT mark broker order execution PASS.
Current server-side gates remain fail-closed:
- runtime_config.enabled = false
- demo_send_enabled = false
- risk_profile_approved = false
- automation approval = false
- live money locked

Do not flip these gates as part of Render hosting work.

## Design rule
Do NOT keep Render awake with a periodic keep-alive.
Render should wake only when an authenticated execution request is actually needed.
The purpose of this service is to be a tiny stateless gateway, not a 24/7 trading brain.

Supabase remains source of truth for runtime state, risk/compliance, audit/events, positions/intents, and MetaApi integration.
