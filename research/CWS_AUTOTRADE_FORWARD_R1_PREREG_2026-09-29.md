# CWS AutoTrade — R1-forward-only preregistration, 2026-09-29

**Status: LOCKED BEFORE FIRST ELIGIBLE FORWARD BAR.**
**Parent historical R0 report SHA:** `a7a8855d84371faf3ce93ae394e80c32b800c0f4`.
**R0 prereg SHA:** `9041d3de3122abfb41ef8ab2f0fca12f114307cf`.
**R0 historical OOS:** OPENED AND REUSED, permanently barred from R1 model selection or claims of independent success.
**R1 is operational and forward-only:** it does **not** reoptimize, rescore or introduce a variant of R0 rules after seeing R0 historical OOS.

## Falsifiable R1 hypothesis
The completely unchanged R0-CHANNEL-55-20-ATR signals (prior 55-bar channel, SMA200, ATR20 initial 2.5x, prior 20-bar channel trailing, next-bar-open and gap-worse stops, no fixed reward target) are *operationally feasible* on properly sourced instruments and can show after-cost forward-paper expectancy >0 without violating 0.25% initial account-equity risk per position and 1.00% combined nominal initial-stop risk, subject to realistic contract sizing and verified fees. This hypothesis may fail for every market.

## Precommitted entry and exit
Signal t on fully closed candles only; enter t+1 bar open if symbol is paper-eligible and gap does not invalidate the initial stop. Never enter at t close. Update trailing stops only using **strictly prior** completed bars. Use adverse-open fill if stop is gapped. Account for same-entry-bar stops conservatively, no favourable OHLC intrabar assumptions. No RR target. End-of-bar ledger includes unrealized mark-to-market positions, whether winning or losing. Only source-matched FX/currency conversion/contract multiplier/corporate action and broker fees permit account currency equity. Where missing: price-unit and risk-unit evidence only, `ACCOUNT_PNL_UNAVAILABLE`.

## Event clock, source and reproducibility
- Eligibility starts `2026-09-30T00:00:00Z` and only *actually observed* closed bars with source event timestamps after that threshold count as new independent forward observations. Their original OHLC open timestamps may precede threshold for initial indicator warm-up; such bars are never counted as forward trades or returns.
- Actual retrieval UTC, provider source URL, source symbol, asset class, trading session/timezone, original timeframe, bar **open and close UTC**, closed/completeness flag, upstream unique event ID and raw bytes hash must be recorded. Reject future-dated data, unclosed candles, duplicate/conflicting timestamp and missing required source periods. Source-native H4 from Bitstamp is eligible for crypto. Yahoo D1 is *indicative proxy* for FX and indices and not broker MT5 evidence. Missing 26 native H4 market feeds remain unavailable, not synthetically created.
- Source-close occurs no earlier than bar completion and no later than the real ingestion clock. If provider's candle-end timing cannot be verified, mark `SOURCE_TIME_UNVERIFIED` and quarantine.
- Every paper event is append-only and SHA-256 chained with prior event hash; store exact source snapshots or identify a legally permitted durable private repository. Public GitHub may store hashes/metadata, not restricted raw market feeds. Temporary one-day Actions artifacts **do not** meet long-term reproducibility.
- No automated future data collection is represented as enabled by this prereg. A subsequent authorized current session must start forward ingestion when actual new bars exist.

## Frozen paper risk gates
- One position per instrument, 0.25% of current **marked** equity as maximum intended loss to initial stop (not a guarantee under slippage/gap), total initial-stop loss across positions <=1% across the portfolio, no leverage used unless explicit margin/collateral profile.
- Determine order quantity from account equity, initial entry-to-stop distance, legally supported contract multiplier, FX conversion on the price's timestamp, lot step and minimum, notional leverage/margin and bid/ask commission/slippage/swap/financing. Round **down** to step. Reject when *any* required execution/risk input missing; never invent a quote or sizing convention.
- Cash indexes are nontradeable; label `PROXY_NONEXECUTABLE` until corresponding executable venue is verified. Do not paper-short cash indexes or spot equities without a documented shortable vehicle, borrowing/fees and calendar.
- Cost snapshots must be documented from correct provider and effective timestamp **before** paper signals. No zero-fee substitution. Maintain gross-only analysis separately; risk/cost promotions require net after verified broker/venue costs.
- Risk kill switch/rejection is fail-closed for stale feed, loss of auth, insufficient balance/margin, source regime/roll mismatch, contradictory data, per-symbol limit, total 1% risk, missing fee or FX conversion. Never call MT5 or exchange order-send (even DEMO); research events are local simulation records only.

## Fixed coverage and analysis
28 preregistered markets × H4/D1 = 56 independently-labelled cells. Unavailable cells remain visible. For each eligible cell record total closed/partial trades, win/loss/flat rate, average gain/loss, realized mean-win/mean-loss RR, realized R, expectancy, PF, broker-verified gross/net and modeled 2x/3x stress, yearly/regime performance, marked-equity max DD, early large-winner dependence, and source integrity. No cross-market summing of heterogeneous instrument price units. Benchmark is a source/vehicle-matched passive strategy, not fictitious directly tradable index. Walk-forward comparisons can be descriptive only until future data exists. Include *all* failed data fetches, rejected bars, false positives, and completed losing cases.

## Independent promotion gate and stopping rule
Do **not** claim positive independent edge unless >=90 elapsed days of genuinely new forward paper since earliest eligible event, >=100 aggregate closed forward trades without double-counting correlated portfolios, >=30 per instrument for any per-instrument claim, positive net after **documented** venue costs at base and 2x stress, no material source/fee/microstructure defect, preregistered baseline comparison, 10,000 five-trade block-bootstrap confidence review, outlier-removal review, and audited instrument/account conversion and risk gates. If one prerequisite is missing, status `UNPROVEN`; missing costs => `GROSS_ONLY_NO_NET_CLAIM`; missing source => `DATA_UNAVAILABLE`. An observed negative result is still retained, never back-selected away.

## Change control
R0 parameters and opened historical OOS never change or become new. Defect patches must carry a new code hash and clean proof on **synthetic fixtures or TRAIN+VALIDATION only**. A material signal rule change requires a newly preregistered R2 with a separately new forward window; previously seen R1 future data becomes *development* not another fresh holdout. LIVE and DEMO-send are expressly forbidden throughout this research.
