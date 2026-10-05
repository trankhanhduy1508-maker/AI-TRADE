# Signal watch and learning EPUB — 2026-10-05

Founder asks to monitor Nasdaq 100, S&P 500, Dow Jones 30, gold and oil, entering only at suitable signals; also requests an EPUB of actual integrated knowledge, backtest lessons and understandable diagrams. No immediate/manual new orders authorized in this step.

Arena v2 adds a pure entry gate and private watch table. Daily proxy records from the current UTC day are excluded using a conservative cutoff, not a broker-session calendar. Stale records (>96h) are blocked. After a manual closure, a newer bar and a change relative to the observed direction are required; the old trend does not automatically reseed positions. Existing positions are not stop-tested on a bar before their entry timestamp. Yahoo nulls are rejected instead of coerced to zero. No LLM runtime decisions, no broker orders, no new cron. Existing active daily schedule 03:35 UTC is retained.

Authenticated run request 352 returned HTTP 200, opened=0, closed=0, positionsOpen=4, errors=[]. Watch verification: NAS100, US500, US30, USOIL WAIT_NEW_BAR; XAUUSD POSITION_OPEN. Added a compact watch section to the private web app. Private deployment succeeded with source 416ecf6ad1b426491f92133c0b445606e3a4fed8. Thirteen paper/gate/Worker tests passed. Browser APP pass is not claimed.

EPUB: CWS_Hoc_Giao_Dich_Va_Bai_Hoc_Backtest_2026-10-05.epub. Fourteen chapters and six embedded SVG diagrams; authored Vietnamese explanations plus the first-party Masterbook synthesis and exact 12-principle hypothesis mapping. Distinguishes arena stop/reversal behavior from trailing research, manual re-entries from strategy signals, and historical document-reported Gold/BTC numbers from a new backtest. No claim to have ingested full commercial books or to have broker-net profitability. No credentials/account details.

Book QA: EPUB mimetype first and stored, ZIP integrity, XML parsing, all relative links and nav targets, Vietnamese text and six SVG figures passed. Figures rendered through Inkscape and visually reviewed. Saved EPUB successfully; source generator is reproducible in scripts/build_learning_epub.py. No historical market run was invented for publication.
