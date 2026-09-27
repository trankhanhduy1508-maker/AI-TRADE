# CWS AI Trade — Admin UI Handoff

Use this file as the canonical handoff for the next chat/agent working on Founder/Admin UI.

## Repo / branch

Repo:
`trankhanhduy1508-maker/AI-TRADE`

Branch:
`codex/p0-covel-knowledge-audit`

Do not create another branch.

## Current product name

**CWS AI Trade**

## Current chart stack

TradingView Lightweight Charts v5.x is already integrated.

Do not replace it without a concrete technical reason.

## Current tracked markets

EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF, NZDUSD,
XAUUSD, USOIL, BTCUSD, ETHUSD, US30, NAS100, US500.

## Current required timeframes

M15 / M30 / H1 / H4 / D1

## Admin UI priority

Focus only on Founder/Admin UI:
- perceived load speed;
- chart quality;
- market switching;
- timeframe switching;
- selected-position overlay;
- lot;
- floating P/L;
- SL;
- TP when real;
- Entry;
- current price;
- useful admin layout.

Google Login/customer onboarding is explicitly out of scope for this handoff.

## Performance rule

Do not block first paint on:
- chart library;
- journal;
- research metrics;
- admin tables;
- slow remote market requests.

Render shell first, then hydrate progressively.

## Chart rule

The chart should behave more like a professional trading terminal:
- practical bar spacing;
- auto-scale;
- pinch/drag/zoom;
- responsive resize;
- market/timeframe switching without whole-page reload;
- selected position lines/markers.

## Price-to-P&L helper

Prototype a horizontal target-price helper:
- selected price;
- delta vs Entry;
- estimated P/L only when symbol contract metadata is available;
- label estimate clearly;
- otherwise show "P/L chưa đủ dữ liệu để tính chính xác".

## Data integrity

Never fake:
- Entry;
- SL;
- TP;
- Lot;
- P/L;
- current position.

If data is unavailable, render unavailable state.

## Safety

Do not alter:
- live-money locks;
- broker execution gates;
- The5ers gates;
- risk approval.

This is UI/observability work only.
