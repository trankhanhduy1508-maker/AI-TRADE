# Core-only web app — 2026-10-05

Founder asked for a simple interface containing the core first, and authorized automatic simulated trading without a requested trade-count limit.

The Sites Worker now uses core.html: status, four compact position/result counts, open orders and collapsed closed history. No chart, chat, knowledge import, manual portfolio, broker login form or multi-page menu on this screen. Existing Android/legacy source is retained, but those scripts are not loaded by the core web page. Obsolete PWA navigation shortcuts are removed for the Worker build. Core HTML is included in the service-worker revision.

Ran the existing training arena immediately through its authenticated endpoint (request 350). HTTP 200, opened=0, closed=0, marked=14, positionsOpen=14, tradesClosed=2, errors=[]. Persisted successful run at 2026-10-05 11:04:09 UTC / 18:04:09 Asia/Saigon. No new signal, so no extra trades were fabricated or force-opened. Existing daily automation remains active; no duplicate schedule or paid service added. This is simulation only, no broker orders.

Verification: ten paper feed/Worker tests passed; core shell build succeeded, every paper client DOM target exists, only core scripts are loaded, and PWA has no obsolete shortcuts. Native private deployment verifies publication; browser visual QA has not been performed.
