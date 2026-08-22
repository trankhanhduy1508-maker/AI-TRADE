# P1 Deterministic Backtest Engine Evidence — 2026-08-22

## Scope

P1 implements the first machine-readable TF-001 contract and a deterministic,
closed-bar, signal-only backtest foundation. It does not implement MT5
execution, capital risk, leverage, lot sizing, or live trading.

## Repository changes

- `strategies/TF_001_BREAKOUT_PULLBACK.json` records entry timing, stop/target
  derivation, score threshold, ambiguity policy, and provenance labels.
- `src/backtest/spec.py` validates the machine-readable contract and rejects
  non-`SIGNAL_ONLY` modes or missing provenance.
- `src/backtest/engine.py` provides dependency-injected signal evaluation,
  current/past-bar-only history, later-bar-only exits, one-open-position
  protection, conservative `STOP_FIRST` handling, open-position end state, and
  price-unit KPIs.
- `scripts/fetch_yahoo_chart.py` is a local reproducibility helper. It does not
  commit downloaded market data or treat Yahoo as a broker execution feed.

## Verification

- Backtest contract tests: **8 passed**.
- Complete repository suite: **163 passed** using
  `python -m pytest -q -p no:cacheprovider tests`.
- Covered invariants: unclosed-bar rejection, no future-bar exposure, no
  overlapping positions, deterministic stop-first ambiguity, spec validation,
  and KPI calculation.
- The first direct script invocation exposed a `sys.path` entrypoint defect;
  it was fixed and rerun successfully. No risk or live behavior was involved.

## Local historical-data feasibility check

Data was fetched on 2026-08-22 from the public Yahoo chart endpoint using the
reproducibility helper. Yahoo's official help page describes Finance data as
informational and identifies ICE as the global currency-rate provider:
<https://help.yahoo.com/kb/finance/SLN2310.html>.

The downloaded files were kept outside the repository at
`C:\Users\Administrator\AppData\Local\Temp\ai-trade-p1-data-20260822` and
were not committed.

| Symbol | Interval | Retrieved rows | Clean bars | Invalid removed | Duplicates | Outliers |
|---|---:|---:|---:|---:|---:|---:|
| EURUSD=X | 1D | 1205 | 1173 | 32 | 0 | 0 |
| GBPUSD=X | 1D | 1205 | 1180 | 25 | 0 | 0 |
| USDJPY=X | 1D | 1205 | 1139 | 66 | 0 | 0 |
| EURUSD=X | 1H | 12343 | 12343 | 0 | 0 | 0 |
| GBPUSD=X | 1H | 12344 | 12344 | 0 | 0 | 0 |
| USDJPY=X | 1H | 12259 | 12259 | 0 | 0 | 0 |

The 1D data produced zero qualifying TF-001 trades on all three full samples.
That is a strategy/data/adapter observation, not evidence of profitability or
failure.

Bounded 1H smoke runs over the first 1000 cleaned bars completed successfully:

| Symbol | Trades | Win rate | Net price PnL | Max price drawdown | End open |
|---|---:|---:|---:|---:|---:|
| EURUSD=X | 13 | 23.08% | -0.016554 | 0.018491 | yes |
| GBPUSD=X | 28 | 32.14% | -0.022776 | 0.034581 | yes |
| USDJPY=X | 16 | 43.75% | 1.804496 | 5.244484 | yes |

These are bounded diagnostic runs, not in-sample/out-of-sample evidence. They
use price-unit results, zero slippage in the current spec, and no capital
normalization; they must not be used to claim an edge.

## Incremental-adapter milestone

The point-in-time cache now confirms each swing once, only after its right-hand
window is available. Prefix parity against the original full-scan trend and
structure rules passed, and the stateful adapter matched the full-scan adapter
at every tested prefix.

- Focused incremental tests: **3 passed**.
- Full repository suite after integration: **166 passed**.
- cProfile before the change: trend detection consumed about 1.74 seconds of
  a 2.13-second 1,000-bar run. After the change, the full 12k-bar EURUSD 1H
  run completed in 1.352 seconds.

Fresh full-sample runs over the same locally downloaded files:

| Symbol | Interval | Bars | Trades | Win rate | Net price PnL | Max DD price | Runtime s | Open |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| EURUSD=X | 1D | 1173 | 0 | 0.00% | 0.000000 | 0.000000 | 0.588 | no |
| GBPUSD=X | 1D | 1180 | 0 | 0.00% | 0.000000 | 0.000000 | 0.397 | no |
| USDJPY=X | 1D | 1139 | 0 | 0.00% | 0.000000 | 0.000000 | 0.599 | no |
| EURUSD=X | 1H | 12343 | 183 | 38.80% | 0.055380 | 0.041893 | 2.127 | yes |
| GBPUSD=X | 1H | 12344 | 250 | 43.60% | 0.142325 | 0.068091 | 2.350 | yes |
| USDJPY=X | 1H | 12259 | 237 | 40.51% | 5.211449 | 11.354988 | 2.197 | yes |

These runs are full-sample diagnostics, not IS/OOS evidence. They use the
current signal-only price-unit contract, zero slippage, and no commission or
swap model; price-unit results are not comparable across symbols.

## Blocker and next action

The previous full 1H attempt exposed an O(n²)-style runtime bottleneck; the
incremental cache removed that blocker without changing parity-tested trend or
structure semantics.

The chronological IS/OOS and explicit proxy-cost milestone is now recorded in
`backtests/TF001_FX_IS_OOS_2026-08-22.md`. H001 remains unvalidated because all
hourly OOS samples were net negative after costs. Next: independently specify
an alternative Trend Following translation or obtain broker/demo data, then
repeat OOS validation. Live money remains locked by governance.

The cost/partition focused tests pass (**10 passed**) and the complete
repository suite passes (**168 passed**).
