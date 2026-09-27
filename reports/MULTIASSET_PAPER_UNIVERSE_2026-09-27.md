# Multi-Asset Autonomous Paper Universe — 2026-09-27

## Trạng thái

**PAPER AUTONOMY ACTIVE — broker execution vẫn fail-closed.**

Cloud runtime:
- Supabase Edge Function: `ai-trade-multiasset-paper`
- status: ACTIVE
- cron job: `ai-trade-multiasset-paper-daily`
- schedule: `30 1 * * *` UTC
- job id: `4`
- broker orders: false
- pyramiding: false

## Universe hiện tại — 13 thị trường

Forex:
- EURUSD
- GBPUSD
- USDJPY
- AUDUSD
- USDCAD
- USDCHF
- NZDUSD

Cross-asset:
- XAUUSD / Gold
- BTCUSD / Bitcoin
- USOIL / WTI Oil
- US30 / Dow Jones
- NAS100 / Nasdaq 100
- US500 / S&P 500

Yahoo research proxies:
- EURUSD=X
- GBPUSD=X
- USDJPY=X
- AUDUSD=X
- CAD=X
- CHF=X
- NZDUSD=X
- GC=F
- BTC-USD
- CL=F
- ^DJI
- ^NDX
- ^GSPC

## Cost provenance

`RESEARCH_PROXY`:
- EURUSD
- GBPUSD
- USDJPY
- AUDUSD
- Gold
- Bitcoin
- WTI Oil

`GROSS_ONLY` until broker-aligned cost evidence exists:
- USDCAD
- USDCHF
- NZDUSD
- US30
- NAS100
- US500

`GROSS_ONLY` results must never be presented as net profitability.

## Runtime evidence

Initialization probe:
- HTTP 200
- Supabase pg_net request id: 30
- universeSize: 13
- 13/13 symbols returned `WARMED`
- no historical trades backfilled
- zero broker orders

Idempotency probe:
- HTTP 200
- Supabase pg_net request id: 31
- 13/13 symbols returned `NO_NEW_CLOSED_BAR`
- no duplicate entries/trades were created

## Execution gate

Added DB-level runtime guard:
- `ai_trade.runtime_config.risk_profile_approved boolean default false`

Supabase `ai-trade-tick` upgraded to version 4:
- disabled runtime remains `DISABLED`;
- if someone enables the runtime while risk profile is unapproved, it returns `RISK_PROFILE_NOT_APPROVED` before broker execution.

This prevents old placeholder spread/daily-loss values from becoming de facto production policy.

## Read-only broker universe preflight

Supabase Edge Function:
- `ai-trade-demo-preflight`
- status: ACTIVE
- version: 1

Purpose:
- connect only to a MetaApi-hosted MT5 DEMO account;
- read `getSymbols()`;
- resolve broker-specific aliases for all 13 instruments;
- persist mapping to `ai_trade.broker_symbol_map`;
- never place an order;
- require MT5 + DEMO account mode;
- live-money remains locked.

Broker aliases include examples:
- Gold: XAUUSD / GOLD
- Oil: USOIL / WTI / XTIUSD
- US30: US30 / DJ30 / DJI / DOW
- Nasdaq: NAS100 / USTEC / NDX / NASDAQ
- S&P 500: US500 / SPX500 / SP500 / SPX

The attempt to invoke this broker-facing preflight from the current agent environment was blocked by the platform safety layer. No bypass was attempted.

## Source

Canonical branch:
`codex/p0-covel-knowledge-audit`

Files:
- `supabase/functions/ai-trade-multiasset-paper/index.ts`
- `supabase/functions/ai-trade-multiasset-paper/deno.json`
- `supabase/functions/ai-trade-demo-preflight/index.ts`
- `supabase/functions/ai-trade-demo-preflight/deno.json`

## Gate

Current multi-asset status:

`13-market paper autonomy = ACTIVE`

`MT5 DEMO broker execution = LOCKED`

`LIVE = HARD LOCKED`

No hard risk profile is promoted from research evidence.
