# CWS AutoTrade — BLIND R0 report and failure journal (2026-09-29)

**Decision:** UNPROVEN. No evidence of an independently verified trading edge. Do not deploy to LIVE or DEMO-send; forward paper not yet observed.

## Immutable evidence chain
- Preregistration commit (before reading old TF performance): `9041d3de3122abfb41ef8ab2f0fca12f114307cf`.
- Code/QA one-shot launch commit: `08febee552c905cbd96dc21943c81cf9167dee0a`.
- Ingestion/data hashes/splits committed **before historical OOS**: `3d071818bdda0ea575eced6bed3a1185e384e0ab`.
- Report commit: `a7a8855d84371faf3ce93ae394e80c32b800c0f4`.
- Cloud evidence: https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36566712493 ; 14 offline regression tests x Smoke, Runtime, Fault = 42 observed passing test executions; all workflow steps successful.
- Exact source manifest: `research/manifests/CWS_BLIND_R0_2026-09-29.json`, containing source URLs, raw and normalized SHA-256, raw bar counts and fixed chronological cutpoints. Actual raw provider data are NOT committed to this public repository, only temporary workflow artifact.
- Full machine-readable metrics: `research/results/CWS_BLIND_R0_2026-09-29.json`. This markdown is generated from that file, without selecting favourable markets.

## Coverage and non-promotional interpretation
- Fixed universe: 28 instruments x native H4/D1 = 56 required rows; 30 exploratory market/timeframe datasets successfully ingested and evaluated. 26 H4 rows are `DATA_UNAVAILABLE_NATIVE_H4`, primarily because Yahoo does not provide native four-hour candles; no proxy is mislabelled as broker H4.
- 307 completed historical OOS trades *summed across different/correlated markets*; this is **NOT** 307 independent observations.
- 17 rows have positive observed expectancy in R, 13 negative, but **zero** rows meet prereg minimum 30 completed OOS trades and **zero** have untouched forward data.
- 25 rows have `GROSS_ONLY` cost evidence, 5 have research cost assumptions; zero have verified broker execution costs. Profit/cost columns are native instrument price units, not USD account PnL. Never add FX, metal, commodity, share and index point units.
- Historical OOS is `HISTORICAL_REUSED_NOT_INDEPENDENT` across evaluated rows because previous CWS studies may have used overlapping instrument/date data. TF-004/TF-014 results were not read before R0 prereg commit.
- No paper forward period starting 2026-09-30 is available at the 2026-09-29 study cutoff. Nothing here establishes deployable expectancy.

## Per-market historical OOS (descriptive only)
Net price = instrument native price units per simulated unit, **not** currency account returns. RR = realised mean winning R / absolute mean losing R; n/a when no wins/losses. Max DD is bar-marked R units, not percent capital. PF is based on native price-unit trades; undefined with zero gross losses.

| Market | TF | Trades | Win | Realised RR | Expectancy R | PF | Max DD R | Net price | Cost basis |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| AAPL | D1 | 8 | 62.5% | 1.25 | 0.385 | 1.63 | 4.95 | 24.15001 | Gross |
| AMZN | D1 | 11 | 45.5% | 1.29 | 0.041 | 0.69 | 4.94 | -26.41655 | Gross |
| AUDJPY | D1 | 11 | 18.2% | 3.15 | -0.153 | 0.62 | 6.62 | -5.50282 | Gross |
| AUDUSD | D1 | 14 | 14.3% | 1.64 | -0.513 | 0.19 | 10.42 | -0.12524 | Assumed |
| BTCUSD | D1 | 3 | 33.3% | 2.79 | 0.160 | 0.79 | 1.84 | -1764.20907 | Gross |
| BTCUSD | H4 | 7 | 28.6% | 3.71 | 0.317 | 1.27 | 3.85 | 2430.97907 | Gross |
| Brent | D1 | 13 | 30.8% | 2.14 | -0.022 | 0.71 | 7.93 | -10.06995 | Gross |
| Dow Jones | D1 | 12 | 50.0% | 1.36 | 0.132 | 1.03 | 5.30 | 185.23568 | Gross |
| ETHUSD | D1 | 2 | 50.0% | 3.52 | 1.261 | 3.42 | 2.10 | 832.48682 | Gross |
| ETHUSD | H4 | 5 | 20.0% | 7.62 | 0.536 | 1.23 | 3.62 | 62.73569 | Gross |
| EURCHF | D1 | 9 | 22.2% | 0.61 | -0.525 | 0.16 | 5.60 | -0.05743 | Gross |
| EURGBP | D1 | 13 | 0.0% | n/a | -0.737 | 0.00 | 10.10 | -0.10027 | Gross |
| EURJPY | D1 | 13 | 23.1% | 2.69 | -0.103 | 0.87 | 5.01 | -3.13775 | Gross |
| EURUSD | D1 | 9 | 22.2% | 3.77 | 0.039 | 1.20 | 3.45 | 0.01792 | Assumed |
| GBPJPY | D1 | 12 | 16.7% | 2.56 | -0.289 | 0.40 | 7.65 | -20.75918 | Gross |
| GBPUSD | D1 | 12 | 16.7% | 0.46 | -0.544 | 0.09 | 7.51 | -0.15802 | Assumed |
| GOOGL | D1 | 10 | 50.0% | 2.65 | 0.721 | 3.93 | 4.29 | 119.16954 | Gross |
| META | D1 | 8 | 50.0% | 1.86 | 0.432 | 1.43 | 4.34 | 56.84066 | Gross |
| MSFT | D1 | 7 | 42.9% | 2.62 | 0.416 | 2.48 | 2.84 | 87.08446 | Gross |
| NVDA | D1 | 10 | 50.0% | 5.15 | 1.522 | 2.35 | 3.65 | 57.55066 | Gross |
| NZDJPY | D1 | 12 | 25.0% | 0.57 | -0.514 | 0.18 | 6.57 | -15.65998 | Gross |
| NZDUSD | D1 | 14 | 14.3% | 0.73 | -0.484 | 0.13 | 6.94 | -0.10897 | Gross |
| Nasdaq 100 | D1 | 8 | 75.0% | 2.12 | 1.343 | 5.79 | 3.03 | 8309.18632 | Gross |
| S&P 500 | D1 | 11 | 54.5% | 2.39 | 0.731 | 2.39 | 3.52 | 1140.36183 | Gross |
| USDCAD | D1 | 16 | 12.5% | 1.76 | -0.517 | 0.22 | 8.48 | -0.14684 | Gross |
| USDCHF | D1 | 10 | 40.0% | 3.19 | 0.466 | 1.83 | 3.46 | 0.05565 | Gross |
| USDJPY | D1 | 11 | 27.3% | 2.34 | -0.048 | 0.92 | 5.14 | -1.01228 | Gross |
| WTI | D1 | 14 | 14.3% | 3.70 | -0.199 | 0.44 | 8.31 | -26.13729 | Assumed |
| XAGUSD | D1 | 12 | 16.7% | 12.12 | 1.152 | 2.13 | 24.89 | 20.63604 | Gross |
| XAUUSD | D1 | 10 | 40.0% | 6.43 | 1.661 | 3.29 | 6.30 | 1451.73789 | Assumed |

## H4 exceptions
- AAPL H4: DATA_UNAVAILABLE_NATIVE_H4; public Yahoo daily observations are not sufficient for a native four-hour execution study.
- AMZN H4: DATA_UNAVAILABLE_NATIVE_H4; public Yahoo daily observations are not sufficient for a native four-hour execution study.
- AUDJPY H4: DATA_UNAVAILABLE_NATIVE_H4; public Yahoo daily observations are not sufficient for a native four-hour execution study.
- AUDUSD H4: DATA_UNAVAILABLE_NATIVE_H4; public Yahoo daily observations are not sufficient for a native four-hour execution study.
- Brent H4: DATA_UNAVAILABLE_NATIVE_H4; public Yahoo daily observations are not sufficient for a native four-hour execution study.
- Dow Jones H4: DATA_UNAVAILABLE_NATIVE_H4; public Yahoo daily observations are not sufficient for a native four-hour execution study.
- EURCHF H4: DATA_UNAVAILABLE_NATIVE_H4; public Yahoo daily observations are not sufficient for a native four-hour execution study.
- EURGBP H4: DATA_UNAVAILABLE_NATIVE_H4; public Yahoo daily observations are not sufficient for a native four-hour execution study.
- EURJPY H4: DATA_UNAVAILABLE_NATIVE_H4; public Yahoo daily observations are not sufficient for a native four-hour execution study.
- EURUSD H4: DATA_UNAVAILABLE_NATIVE_H4; public Yahoo daily observations are not sufficient for a native four-hour execution study.
- GBPJPY H4: DATA_UNAVAILABLE_NATIVE_H4; public Yahoo daily observations are not sufficient for a native four-hour execution study.
- GBPUSD H4: DATA_UNAVAILABLE_NATIVE_H4; public Yahoo daily observations are not sufficient for a native four-hour execution study.
- GOOGL H4: DATA_UNAVAILABLE_NATIVE_H4; public Yahoo daily observations are not sufficient for a native four-hour execution study.
- META H4: DATA_UNAVAILABLE_NATIVE_H4; public Yahoo daily observations are not sufficient for a native four-hour execution study.
- MSFT H4: DATA_UNAVAILABLE_NATIVE_H4; public Yahoo daily observations are not sufficient for a native four-hour execution study.
- NVDA H4: DATA_UNAVAILABLE_NATIVE_H4; public Yahoo daily observations are not sufficient for a native four-hour execution study.
- NZDJPY H4: DATA_UNAVAILABLE_NATIVE_H4; public Yahoo daily observations are not sufficient for a native four-hour execution study.
- NZDUSD H4: DATA_UNAVAILABLE_NATIVE_H4; public Yahoo daily observations are not sufficient for a native four-hour execution study.
- Nasdaq 100 H4: DATA_UNAVAILABLE_NATIVE_H4; public Yahoo daily observations are not sufficient for a native four-hour execution study.
- S&P 500 H4: DATA_UNAVAILABLE_NATIVE_H4; public Yahoo daily observations are not sufficient for a native four-hour execution study.
- USDCAD H4: DATA_UNAVAILABLE_NATIVE_H4; public Yahoo daily observations are not sufficient for a native four-hour execution study.
- USDCHF H4: DATA_UNAVAILABLE_NATIVE_H4; public Yahoo daily observations are not sufficient for a native four-hour execution study.
- USDJPY H4: DATA_UNAVAILABLE_NATIVE_H4; public Yahoo daily observations are not sufficient for a native four-hour execution study.
- WTI H4: DATA_UNAVAILABLE_NATIVE_H4; public Yahoo daily observations are not sufficient for a native four-hour execution study.
- XAGUSD H4: DATA_UNAVAILABLE_NATIVE_H4; public Yahoo daily observations are not sufficient for a native four-hour execution study.
- XAUUSD H4: DATA_UNAVAILABLE_NATIVE_H4; public Yahoo daily observations are not sufficient for a native four-hour execution study.

## Research integrity checklist
1. **IS, validation, chronological historical OOS:** computed at frozen 60/20/20 splits.
2. **Walk-forward:** four ordered folds confined to TRAIN+VALIDATION; no optimisation on historical OOS.
3. **Next-bar-open and gap-aware stops:** isolated simulator; no broker calls. Same-entry-bar stop tested.
4. **Spread/commission/slippage/swap:** applied only where explicit research proxy exists; never treated as broker-verified. Swap temporal unit restrictions prevent substituting D1 charge per H4 bar.
5. **2x/3x costs and 1 ATR adverse exit shock:** recorded; artificial shock is explicitly a stress scenario, not market data.
6. **Parameter neighbourhood sensitivity:** channel 50/60, trailing 18/22, ATR 2.25/2.75 on TRAIN+VALIDATION only. Frozen R0 parameters were NOT replaced with winning variants.
7. **Regimes and chronological years:** historical exit attribution, not future-aware entry features.
8. **Monte Carlo:** 10,000 cyclic contiguous five-trade block resamples seeded 20260929 on pre-holdout trades only. No statement of statistical power when samples are small.
9. **Largest winner:** pre-holdout result with biggest positive trade removed; record available in JSON.
10. **Baseline:** flat and source-matched passive price-return only. Index cash and rolling front-month futures are not themselves executable securities.
11. **Portfolio risk:** no account-currency or contract-multiplier conversion validated; only initial-stop-normalised R is reported. The 0.25%-per-position / 1%-combined cap is preregistered but not claimed as implemented live portfolio evidence.
12. **Independent forward:** NOT AVAILABLE. This is the primary missing gate.

## Failure analysis, source limitations and non-negotiable next actions
- Sample size: every evaluated row has fewer than 30 OOS completed trades. A large PF or RR on 2–12 trades is an observation, not an established edge.
- Source mismatch: Yahoo indicative FX, Yahoo futures and non-tradable cash indexes are not the same products as MT5 broker CFDs or executed futures; source licence and broker execution fee verification remain open.
- Corporate actions and roll: dividends, splits, cash-index replication and front-month futures contract rolls are not fully transaction-accounted; do not assert after-cost investor returns.
- Missing H4: acquire source-native H4 candles or register a *separate* explicitly-labelled one-hour-derived H4 study, with a new manifest before that new dataset's holdout is opened.
- No guaranteed cost-profile precision for Bitstamp or most markets; do not infer execution fills from displayed OHLC.
- Positive price-unit PnL and positive risk-normalised expectancy need not agree: per-trade initial-risk denominators differ. Neither is an account-equity ROI.
- **Freeze R0.** Do not tune its parameters on the opened historical OOS and rerun it. R1 may use TRAIN+VALIDATION failure analysis, but its efficacy claim requires an entirely new, later forward period and new preregistration.

## Permitted source-reading registry (not performance claims)
- Moskowitz, Ooi & Pedersen (2012), `Time series momentum`, JFE, DOI 10.1016/j.jfineco.2011.11.003: research motivation; their futures results do not establish R0 effectiveness on this universe.
- Bailey et al. (2017), `The Probability of Backtest Overfitting`, DOI 10.21314/JCF.2016.322: multiple testing/overfitting concern.
- David Aronson, `Evidence-Based Technical Analysis`, Wiley publisher introduction: https://onlinelibrary.wiley.com/doi/book/10.1002/9781118268315 ; objective rules and data-mining bias.
- Robert Carver, `Systematic Trading`, publisher: https://www.harriman-house.com/systematic-trading ; volatility targeting, position sizing, portfolios and fitting cautions.
- Larry Harris, `Trading and Exchanges`, Oxford: https://academic.oup.com/book/52292 ; bid/ask, order types, stops and market microstructure.
- Ernest Chan, `Quantitative Trading`, Wiley: https://onlinelibrary.wiley.com/doi/book/10.1002/9781119203377 ; backtest realistic execution and data cautions.
- Marcos López de Prado, `Advances in Financial Machine Learning`, Wiley (bibliographic): https://search.worldcat.org/title/Advances-in-financial-machine-learning/oclc/1024313524 ; concepts must be verified against accessible primary material before implementation.
No copyrighted chapters have been reproduced and no book proposition was assumed profitable without empirical testing.
