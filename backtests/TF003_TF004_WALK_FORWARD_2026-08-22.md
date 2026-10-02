# TF-003 / TF-004 Fixed Walk-Forward Evidence - 2026-08-22

## Method

- Runner: [`scripts/run_walk_forward.py`](../scripts/run_walk_forward.py)
- History: expanding from the beginning of each committed local sample.
- Fold geometry: fixed 50% initial history and 10% non-overlapping test
  windows; the last fold may be shorter when the sample does not divide
  evenly.
- Signals are accepted only inside each test window while the evaluator sees
  prior bars for point-in-time warm-up.
- No parameters were optimized, selected, or changed between folds.
- Cost profile:
  [`backtests/cost_profiles/research_fx_assumption_v1.json`](cost_profiles/research_fx_assumption_v1.json)
  (`UNVERIFIED` research proxy).
- All outputs are price-unit, signal-only results. Open positions at fold ends
  are not force-closed and are excluded from the closed-trade net shown here.

## Summary

`positive folds` counts folds with closed-trade net PnL greater than zero;
`fold net sum` is the arithmetic sum of each fold's reported closed-trade net.
Neither is a capital return or live-performance estimate.

| Strategy | Symbol | Interval | Folds | Positive folds | Fold net sum |
|---|---|---:|---:|---:|---:|
| TF-003 | EURUSD=X | 1D | 6 | 2 | -0.036302 |
| TF-003 | GBPUSD=X | 1D | 5 | 3 | -0.106003 |
| TF-003 | USDJPY=X | 1D | 6 | 3 | -3.581512 |
| TF-003 | EURUSD=X | 1H | 6 | 0 | -0.139022 |
| TF-003 | GBPUSD=X | 1H | 6 | 1 | -0.100132 |
| TF-003 | USDJPY=X | 1H | 6 | 2 | -1.946531 |
| TF-004 | EURUSD=X | 1D | 6 | 3 | 0.021977 |
| TF-004 | GBPUSD=X | 1D | 5 | 2 | -0.217567 |
| TF-004 | USDJPY=X | 1D | 6 | 1 | -29.989982 |
| TF-004 | EURUSD=X | 1H | 6 | 0 | -0.151568 |
| TF-004 | GBPUSD=X | 1H | 6 | 2 | -0.090530 |
| TF-004 | USDJPY=X | 1H | 6 | 3 | 3.623064 |

## Objective conclusion

The fixed walk-forward comparison does not establish robust cross-market or
cross-timeframe performance. Only two of twelve cases had a positive sum of
closed-trade fold nets, while EURUSD 1H had no positive fold for either
strategy. This is preliminary research evidence only: the feed and cost model
are not broker-verified, the test does not size capital, and open positions are
not force-closed at fold boundaries.

The result is preserved without retuning. It does not authorize paper, MT5
demo, or live-money execution, and it is not evidence against Trend Following
generally.

## Reproduction

For each committed CSV and strategy spec:

```text
python scripts/run_walk_forward.py --csv <csv> --spec <spec> --train-fraction 0.50 --test-fraction 0.10 --cost-profile backtests/cost_profiles/research_fx_assumption_v1.json --cost-key <symbol>
```
