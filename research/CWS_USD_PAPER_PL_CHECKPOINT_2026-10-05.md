# USD-first paper P/L — 2026-10-05

Founder approved the discussed table: per-order USD P/L before R, total gains, total losses, total net, with R secondary. Explicitly rejected a fixed dollar-per-R conversion. No trading or trailing-stop change requested.

Implemented a versioned retrospective paper sizing model PAPER_NOTIONAL_1000_V1. Initial reference notional is 1,000 USD per order, disclosed on the page. USD-quote instruments use quantity=1000/entry price, held fixed; USD-base FX uses 1000 base units and converts quote P/L to USD at mark/exit. Long/short USD P/L comes from price difference × quantity; risk_price and R do not enter that calculation. Quantity is displayed. This is synthetic reference exposure, not broker lots/contracts or account cash. Historical unsized orders are valued under the disclosed assumption, not misrepresented as actual fills. No fixed $25/R.

Read-only feed values all open positions and all historical closed orders, then slices only the displayed closed history to 100. All-history positive and negative totals stay separate, net combines open and closed, and R aggregates are secondary. Unknown/unsupported/nonfinite data invalidates totals instead of becoming zero. Source mark timestamps remain visible and unchanged.

Validation: 19 JS tests passed, including R independence, long/short and closed-price handling, USD-base conversion, 105-trade history totals, missing-data rejection and UI summary consistency. Worker build and USD-first headers/DOM targets passed. Live authenticated feed returned HTTP 200, 4 open, 16 closed, rejected=0, gains 96.5928239104596 USD, losses -50.58414904587162 USD, net 46.00867486458797 USD under the paper sizing model. Temporary scoped read credential removed after verification. Native private deployment succeeded with source d718ac49b16727eface54f41a06f62f6c0dd335a.

An optional repeat of static-builder pytest could not run because pytest is not installed in the current runtime; no pass claim. Actual changed-feature validation above succeeded. Browser visual APP pass is not claimed. No broker trades or new paid service.
