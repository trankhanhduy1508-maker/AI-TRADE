# CWS AutoTrade — BLIND R0 preregistration (2026-09-29)

**STATE: FROZEN BEFORE INSPECTION OF TF-004 / TF-014 PERFORMANCE.**
**Parent SHA:** `29548aae06c7d068d0c0aed37a8ae0ddb978271d`
**Branch:** `codex/p0-covel-knowledge-audit`
**Purpose:** research and paper only. Do not invoke MT5 order-send, LIVE/DEMO-send, disable auth, or bypass kill-switch.
**Prior-work contamination:** Old TF-004/TF-014 market/date ranges may overlap. No old data or previously observed result qualifies as untouched independent holdout. Do not inspect old performance until this document is committed.

## R0 research question and falsifiable hypothesis
For each of the 28 predefined instruments on native H4 and D1 separately, test whether a *single frozen, long/short where executable, time-series channel-breakout with trend filter, ATR initial risk and channel trailing exit* produces positive after-cost expectancy, and compare it against cash/flat and a legally obtainable corresponding buy-and-hold benchmark. No guaranteed positive result. This is a *new test protocol*, not an inference of prior TF results.

Motivation only, not evidence that this implementation will work: Moskowitz, Ooi & Pedersen (2012), Time series momentum, Journal of Financial Economics, DOI 10.1016/j.jfineco.2011.11.003; Bailey et al. (2017), The Probability of Backtest Overfitting, DOI 10.21314/JCF.2016.322. Use lawful accessible copies; do not reproduce book chapters.

## Frozen universe and native timeframes
FX (13): EURUSD GBPUSD USDJPY AUDUSD USDCAD USDCHF NZDUSD EURJPY GBPJPY EURGBP AUDJPY EURCHF NZDJPY.
Crypto (2): BTCUSD ETHUSD.
Metals (2): XAUUSD XAGUSD.
Energy (2): WTI Brent.
US benchmarks and stocks (9): S&P 500 Nasdaq 100 Dow Jones AAPL MSFT NVDA AMZN GOOGL META.
Each H4 and D1 is a separate experiment; no substitution of D1/weekly/4h proxy for native H4. Source symbols must carry an explicit provider and instrument type (Yahoo cash/index, futures continuous contract, CFD, MT5 broker, spot). A futures proxy is *not* MT5 CFD execution evidence. Spot vs future and cash index vs tradable vehicle are separate records. Skip unsupported combinations and mark DATA_UNAVAILABLE, never fill missing bars synthetically.

## Exact frozen rules: R0-CHANNEL-55-20-ATR
Indicators use only complete bars: SMA(200) of closes; 55-bar channel of *prior* highs/lows excluding current signal bar; Wilder ATR(20) of complete bars including signal bar; 20-bar *prior* low/high trailing channel.
- At signal bar t close, LONG if close[t] > max(high[t-55:t]) and close[t] > SMA200[t]; SHORT if close[t] < min(low[t-55:t]) and close[t] < SMA200[t]. No crossover requirement, but one position per instrument; no same-bar re-entry. Short is unavailable for unborrowable spot stocks/cash indexes, and must be labelled UNEXECUTABLE when no shorting vehicle/costs are documented.
- Submit for execution only at bar t+1 OPEN. Reject if the next open invalidates initial stop. LONG initial stop = close[t] - 2.5*ATR20[t]; SHORT initial stop = close[t] + 2.5*ATR20[t]. Never impose a take-profit or fixed RR.
- Once a position exists, protective stop for bar t is the maximum (LONG) or minimum (SHORT) of previous stop and the 20-bar channel computed from bars strictly before t. A more adverse gap through stop exits at the opening price, not the stop price. On intrabar stop touch use stop price with adverse slippage. On entry bar, evaluate stop after open. Never infer favourable intrabar chronology from OHLC.
- The same frozen rules apply across H4 and D1; no per-market parameter tuning. If a position persists at the end of a window, include mark-to-market unrealized PnL in equity/DD. Do not transfer the position as a fresh trade or omit it.
- Time-of-day/session/timezone must be explicit. Indicators must not receive an unclosed bar or a future quote.

## Risk and portfolio / execution gates
Paper-only *illustrative* account policy: initial risk budget 0.25% of current marked equity per instrument, simultaneous total nominal stop-risk <=1% portfolio, max one position per symbol. Size from adverse entry-to-stop risk, contract multiplier, conversion to account currency, minimum lot/step, margin and a provider-specific cost profile. If these are unavailable, report price-unit/R-only simulation and block monetary PnL/risk assertions. No leverage inference or invented FX conversions. Trading-disabled and kill-switch gates stay intact.
Require provider-dated bid/ask/spread, commissions, slippage and (when applicable) swaps/financing; if missing, mark GROSS_ONLY or ASSUMED_COST, not VERIFIED_AFTER_COST. Stress at 2x and 3x documented all-in costs; separately add 1 ATR adverse gap scenario. Account for stock corporate actions/dividends, and futures roll/back-adjustment without calling continuous futures actual trade executions.

## Frozen data and isolation protocol
Before any R0 market-return evaluation, record provider URL/API, retrieval UTC, instrument type, original interval/timezone/session, first/last closed timestamp, bar count, timestamp monotonicity, missing/duplicate/OHLC-invalid counts, corporate action/roll treatment, cost snapshot and SHA-256 of the exact raw and normalized bytes. Never invent an absent price.
For each market/timeframe dataset as frozen at ingestion, sort by close timestamp, reserve chronological first 60% TRAIN, next 20% VALIDATION and final 20% HISTORICAL_OOS (floor-based cutpoints frozen before any performance calculation). No shuffle. Minimum 1,000 complete H4 or 500 D1 bars; otherwise INSUFFICIENT_DATA with no score. Historical holdout is classified HISTORICAL_REUSED unless an audited provenance log establishes that its source and timestamp range were never previously exposed. Do not claim independent validation from HISTORICAL_REUSED.
Freeze code/content hash, original provider and dataset hashes, test thresholds and split manifest in GitHub *before opening any nominal holdout*. Open HISTORICAL_OOS exactly once; after exposure, no tuning/re-running changed R0 against it. Truly independent forward paper data must have event timestamps >= 2026-09-30T00:00:00Z and must not have entered development. Every newly proposed R1+ change requires a new registered dataset interval and forward window; never reset the old holdout label.

## Predefined analyses, no post-hoc selection
For each instrument/timeframe: train and validation separately; chronological OOS; expanding walk-forward on TRAIN+VALIDATION only, 4 ordered folds of 10% of the pre-holdout dataset with preceding data for warm-up, no threshold selection; zero/verified/2x/3x costs as available; adverse gap-aware stop; 10% neighbourhood sensitivity for channel 55 (50/60), trailing 20 (18/22) and ATR 2.5 (2.25/2.75) on TRAIN+VALIDATION only, never used to choose a different R0 parameter; by-year/regime tables (regime determined using only past ATR/returns); bootstrap 10,000 contiguous 5-trade blocks with seed 20260929 on TRAIN+VALIDATION; biggest-winner removal on TRAIN+VALIDATION; flat and source-matched passive baseline. Explicitly label analyses that lack enough observations.
Report total/completed/open trades, win/loss/flat, average gain/loss, realized R (do not replace with preset RR), expectancy, gross/net of documented costs, PF (undefined if no gross losses), marked-equity max DD, OOS, walk-forward, cost-stress, negative cases and sample counts. Portfolio equity is in one currency only after documented conversions; never sum heterogeneous price-unit PnL.
Do not use TF-004/TF-014 old conclusions as signal features, sample selection, benchmark calibration or hyperparameters.

## Fixed evidence/promotion gate
No edge claim for any instrument with <30 closed OOS trades; mark insufficient precision, not a PASS. No independent-edge claim unless a never-exposed forward window has >=90 elapsed calendar days and >=100 aggregate closed forward-paper trades across this frozen universe, positive net after documented base and 2x costs, positive expectancy and non-inferior risk-adjusted performance to corresponding predeclared baseline, plus review of 10,000 block-bootstrap interval and worst-outlier dependence. These thresholds are evidentiary gates, not promises of future returns. Any shortfall => UNPROVEN, not automatic license to tune.

## Hard prerequisites to running R0
Current `src/backtest/spec.py` allows only CLOSE entries; `src/backtest/engine.py` opens at signal close and does not use gap-worse stop fills; and types/metrics express *price units*, not account equity. **Do not run R0 through those existing semantics.** Implement an isolated next-open/gap-aware/risk-marked evaluator or minimally amend a compatible research-only path with fail-closed tests. Smoke -> runtime -> fault validation; record actual command, environment, exit code, output hash and immutable GitHub commit.
Any unsuccessful data fetch, API permission failure, quota or test failure must remain visible in run ledger. This preregistration is immutable; subsequent implementation corrections require an explicit version and do not retroactively rehabilitate opened holdout.
