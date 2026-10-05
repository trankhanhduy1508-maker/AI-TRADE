# Web app paper orders — 2026-10-05

Founder changed the immediate goal to seeing automatic simulated orders directly in the existing CWS AI Trade web app. This implementation consumes the existing TF-013A training arena; it does not submit broker orders or imply a validated profitable strategy.

Published owner-only Site: https://cws-autotrade-lab.trankhanhduy1508.chatgpt.site . Native deployment succeeded, source 53424c86d3a539647c50ddc6e8e4344a05533406, environment revision 1.

The main page loads open positions and the most recent 100 closed trades on entry, on return to the tab and every 60 seconds while visible. Source bot cadence remains daily. It shows entry, stop, mark, market timestamp and gross R, plus closed-trade history. Manual monetary portfolio is separately labeled and collapsed. R is not converted to lot, USD or account return. Commodity symbols represent futures proxies. Arena is not out-of-sample forward validation.

At verification: 14 open positions, 2 closed trades. Last bot run 2026-10-05 03:35 UTC. Refreshing the page does not refresh market prices or create orders. Missing/corrupt data is rejected; lost connectivity retains the previous table with an explicit warning.

Architecture: allowlisted existing shell embedded in a dependency-free Sites Worker; same-origin /api/paper-orders proxies a read-only Supabase function. Scoped key is server-only in Sites; the database stores only SHA-256. Reader table has RLS and no anon/authenticated grants. Public API rejects missing/wrong credentials. The feed has only arena fields, no MT5 passwords, accounts, owner data or candle dataset. No new subscription, VPS or paid service.

Validation: 10 new JS tests; 29 existing frontend tests; 11 static-builder tests passed. Live feed with scoped key returned HTTP 200 and 14/2 rows; missing key returned HTTP 401. Full local Worker → live feed → browser normalizer returned HTTP 200, 14 positions, 2 trades and zero rejected rows. Upstream timeout is 30s, client timeout 35s to accommodate observed cold-start/network latency; failures remain explicit. Deployment was verified by native successful status. Browser QA was not run because this custom Worker has no supported managed development preview. Do not claim browser APP pass or MT5 tickets.
