# CWS AI Trade — Admin / Founder UI Intent V1

Date: 2026-09-28
Status: canonical Founder UI direction.

## Scope

This document is specifically for the **Founder/Admin interface**.

Do not mix this scope with customer Google Login work.

## Primary goals

### 1. Instant perceived load

Founder considers current dashboard too slow.

Target UX:
- shell renders immediately;
- no blank screen;
- cached last-known state may appear immediately;
- live data refreshes in background;
- expensive modules do not block first paint;
- chart loads independently from the rest of the dashboard.

Admin UI must feel ready immediately even on mobile.

### 2. TradingView-class chart as the center of the interface

Use TradingView Lightweight Charts official open-source library or an equivalent technically justified charting layer.

Requirements:
- smooth pan;
- pinch zoom on mobile;
- mouse wheel zoom on desktop;
- responsive resize;
- sensible autoscale;
- visible candles at practical width;
- do not compress an excessive history range into one screen.

### 3. Full tracked market selector

Admin must be able to switch among all currently tracked CWS AI Trade markets:

Forex:
- EURUSD
- GBPUSD
- USDJPY
- AUDUSD
- USDCAD
- USDCHF
- NZDUSD

Commodities:
- XAUUSD
- USOIL

Crypto:
- BTCUSD
- ETHUSD

Indices:
- US30
- NAS100
- US500

Selecting a market must update chart + selected market position context without reloading the full dashboard.

### 4. Timeframe selector

Required:
- M15
- M30
- H1
- H4
- D1

Future-compatible:
- architecture should allow adding M1, M5, W1, MN1 later without rebuilding the module.

### 5. Position overlay on chart

When a selected market has an open/current position, show directly on chart:
- BUY or SELL marker;
- Entry line;
- Stop Loss line;
- Take Profit line if strategy really has one;
- Lot / Volume;
- current price;
- floating P/L if available;
- floating R if available.

Do not invent Take Profit when the strategy has no TP.

### 6. Horizontal price/value projection

Founder wants a horizontal helper that can answer:
"If price reaches this level, approximately how many dollars is the position up/down?"

Desired interaction:
- movable horizontal price line or crosshair-selected level;
- show target price;
- show approximate delta from entry;
- where enough account/contract metadata exists, estimate P/L in account currency.

If exact contract size / tick value / symbol specification is unavailable:
- show clearly that the P/L is estimated or unavailable;
- never fabricate dollar P/L.

### 7. Admin-first information hierarchy

Founder/Admin UI is not the same as customer UI.

Priority order:
1. system status;
2. current open positions;
3. central chart;
4. market selector;
5. lot / P&L / risk;
6. forward/research status;
7. tester/account controls;
8. lower-priority diagnostics.

Do not put Google Login/customer onboarding work into this task.

### 8. One codebase, modular admin surface

Do not fork a second codebase just for Admin.

Use:
- shared data modules;
- role-based rendering;
- admin-specific modules;
- independent rollback boundaries.

## Acceptance criteria

- first paint appears immediately with no blank wait;
- market selector contains all 14 tracked markets;
- timeframe selector contains M15/M30/H1/H4/D1;
- chart is smooth on Android/mobile;
- chart auto-fits candles at useful density;
- BUY/SELL/Entry/SL/TP/Lot information is visible for selected position;
- no fake TP or fake P/L;
- switching market/timeframe does not reload entire dashboard;
- Admin-specific controls remain separate from customer login scope;
- no live-money gate is changed by this UI work.
