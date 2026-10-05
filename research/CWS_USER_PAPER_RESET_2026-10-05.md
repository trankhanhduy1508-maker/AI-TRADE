# Founder simulation reset — 2026-10-05

Explicit instruction: close all fourteen old paper orders, optionally remove them, then open three or four new ones. Preserved history instead of deleting it.

An atomic, locked, idempotent transaction closed 14 at last available marks with USER_CLOSE and created 4 manual paper re-entries at 2026-10-05 11:23:16 UTC: EURUSD SELL, USDJPY BUY, BTCUSD BUY, XAUUSD SELL. Directions came from existing engine positions, not a fresh signal. Initial risk distances were retained and stops rebased around new entry marks; gross R starts at zero. Quote timestamps remain unchanged and visible; gold/BTC marks are older than FX. These are simulated estimates, not broker fills. No MT5 orders.

Operation identifier FOUNDER_RESET_2026_10_05_1820 guards duplicate execution. Invalid count, missing recent marks or invalid replacement stops roll back everything. Verified 4 new positions, 14 USER_CLOSE trades and 18 journal events. Journal explicitly tags manualOverride and excludeFromStrategyEvaluation; forward-shadow validation tables were not changed. Historical trades are retained. The web history shows USER_CLOSE as Theo yêu cầu.

The daily arena continues across its existing 14-market universe and may open additional positions on subsequent runs; this request specifies an immediate four-position reset, not a permanent four-position cap. No new schedule or paid service.
