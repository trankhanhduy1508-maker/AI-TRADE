# TF-003 / TF-004 multi-asset sensitivity round - 2026-08-22

## Purpose and preregistration

This round tests a small, fixed sensitivity grid that was defined before the
results were summarized. It is a robustness check, not a search for the best
equity curve and not permission to select a strategy for MT5.

- Data: the same seven closed-bar daily research proxies used in the prior
  report, approximately 2021-08-21 through the 2026-08-22 cutoff.
- Markets: EURUSD, GBPUSD, USDJPY, AUDUSD, Gold (`GC=F`), BTC-USD and Oil
  (`CL=F`). These are research proxies, not broker execution symbols.
- Cost model: `research_multi_asset_assumption_v1.json`, provenance
  `UNVERIFIED`; it is not a broker-aligned or live-ready cost model.
- OOS: chronological 70% / 30% split, seven markets x six variants = 42
  cases.
- Walk-forward: six expanding-history folds per case, 50% initial history and
  10% test windows, seven markets x six variants = 42 cases.
- Metrics: R is measured against each trade's initial entry-to-stop risk.
  Results are signal-level research metrics, not account returns.

Grid:

| Family | Variants |
|---|---|
| TF-003 | initial stop/reward-risk variants 1.0R, 1.5R and 2.0R |
| TF-004 | channel variants 10, 20 and 40 bars |

No variant was removed after observing an individual market result. All 84
cases completed without a strategy execution failure. The first harness
attempt was rejected before producing results because temporary JSON specs
contained a UTF-8 BOM; the files were normalized and every case was rerun.

## OOS results

Summary across the seven markets:

| Variant | Positive cases / 7 | Net R sum | Mean expectancy R | Worst case DD R |
|---|---:|---:|---:|---:|
| TF-003 RR 1.0 | 1 | -20.172 | -0.105 | 13.946 |
| TF-003 RR 1.5 | 3 | -10.544 | -0.078 | 11.789 |
| TF-003 RR 2.0 | 1 | 2.832 | 0.022 | 8.280 |
| TF-004 channel 10 | 2 | 4.500 | 0.073 | 17.442 |
| TF-004 channel 20 | 4 | 26.126 | 0.338 | 8.390 |
| TF-004 channel 40 | 3 | 20.819 | 1.282 | 9.901 |

OOS net R by market (all rows are reported; no cherry-picking):

| Variant | EURUSD | GBPUSD | USDJPY | AUDUSD | Gold | BTC | Oil |
|---|---:|---:|---:|---:|---:|---:|---:|
| TF-003 RR 1.0 | -3.686 | -1.396 | -12.011 | -0.780 | -1.278 | 1.329 | -2.350 |
| TF-003 RR 1.5 | 4.665 | 0.901 | -9.413 | -3.076 | 3.825 | -2.864 | -4.581 |
| TF-003 RR 2.0 | -1.476 | -0.050 | -2.401 | -0.198 | 10.782 | -2.318 | -1.508 |
| TF-004 channel 10 | 12.061 | -7.002 | -5.511 | -17.442 | 30.977 | -3.487 | -5.096 |
| TF-004 channel 20 | 15.504 | -7.261 | -3.051 | -2.463 | 15.879 | 4.082 | 3.435 |
| TF-004 channel 40 | 9.401 | -6.826 | -0.617 | -7.208 | 25.548 | -2.784 | 3.306 |

## Walk-forward results

Summary across 42 test folds per variant:

| Variant | Positive folds / 42 | Net R sum | Worst case DD R | Trades |
|---|---:|---:|---:|---:|
| TF-003 RR 1.0 | 17 | -34.609 | 9.971 | 379 |
| TF-003 RR 1.5 | 16 | -20.800 | 9.747 | 277 |
| TF-003 RR 2.0 | 15 | -18.145 | 10.853 | 228 |
| TF-004 channel 10 | 16 | 95.508 | 12.201 | 360 |
| TF-004 channel 20 | 12 | 65.192 | 10.146 | 189 |
| TF-004 channel 40 | 8 | -67.777 | 12.910 | 128 |

Walk-forward net R sum and positive folds by market:

| Variant | EURUSD | GBPUSD | USDJPY | AUDUSD | Gold | BTC | Oil |
|---|---|---|---|---|---|---|---|
| TF-003 RR 1.0 | -4.711 / 3 | -3.172 / 3 | -12.504 / 1 | -11.725 / 1 | 9.078 / 5 | -3.672 / 4 | -7.902 / 0 |
| TF-003 RR 1.5 | 0.318 / 3 | -6.080 / 3 | -6.888 / 1 | -15.333 / 2 | 13.026 / 4 | 3.194 / 3 | -9.037 / 0 |
| TF-003 RR 2.0 | -0.993 / 4 | -12.951 / 1 | -0.153 / 1 | -21.343 / 0 | 21.330 / 5 | 0.647 / 3 | -4.682 / 1 |
| TF-004 channel 10 | 5.553 / 2 | -18.638 / 1 | 115.924 / 3 | -20.635 / 1 | 33.417 / 5 | -7.398 / 2 | -12.715 / 2 |
| TF-004 channel 20 | 36.882 / 2 | -13.464 / 1 | 49.359 / 1 | -17.696 / 1 | 5.543 / 2 | 4.652 / 3 | -0.084 / 2 |
| TF-004 channel 40 | -24.146 / 1 | -9.555 / 1 | -11.156 / 1 | -22.802 / 0 | -6.004 / 0 | 4.626 / 3 | 1.260 / 2 |

Each cell is `net R sum / positive folds` for six folds. A positive aggregate
is not treated as robust if it is concentrated in one market or a small
number of folds.

## Analysis and learning

1. The grid confirms market dependence. TF-003 RR variants remain negative in
   aggregate walk-forward across this basket, although Gold and BTC are more
   promising than the FX/Oil subset. That is not enough to promote TF-003.
2. TF-004 channel 10 and channel 20 are positive in aggregate walk-forward,
   but the result is concentrated: USDJPY contributes 115.924R to channel 10,
   while AUDUSD, GBPUSD, Oil and BTC are negative. This is a concentration
   warning, not a portfolio-ready result.
3. TF-004 channel 20 is the only variant positive in both aggregate OOS and
   walk-forward. Its OOS result is positive in four of seven markets (EURUSD,
   Gold, BTC and Oil), while GBPUSD, USDJPY and AUDUSD remain negative. That
   is not broad cross-market robustness.
4. Higher apparent expectancy can coincide with few trades and high
   concentration. TF-004 channel 40 has the highest mean OOS expectancy but
   is negative in aggregate walk-forward and therefore fails the stability
   check.
5. A win rate near 30% is not sufficient by itself. The acceptance signal is
   positive net/expectancy R with acceptable drawdown and stability across
   time folds, cost assumptions and markets. This round does not establish
   that standard for a general multi-asset system.

## Gate decision

The sensitivity round is **RESEARCH / UNVERIFIED**. It does not authorize
parameter promotion, paper/demo forward execution, or live trading. No
strategy rule or risk limit was changed based on this result.

Next independent work: run a separately held-out time segment and a
broker-aligned cost/contract review before considering any strategy variant
for a controlled MT5 demo forward harness. MT5 runtime reliability, recovery,
risk, kill switch, persistent state and monitoring gates remain mandatory.
