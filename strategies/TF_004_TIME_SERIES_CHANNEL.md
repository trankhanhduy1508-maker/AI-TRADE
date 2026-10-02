# TF-004 Time-Series Momentum with Channel-Trailing Exit

## Status

- [x] Hypothesis specified
- [x] Deterministic evaluator and exit model implemented and unit-tested
- [ ] Backtest validated on a defined market/timeframe
- [ ] MT5 demo validated

TF-004 is a separate comparison strategy. It shares TF-003's fixed price-only
entry signal but changes the exit model explicitly; its result must not be
merged with TF-003's evidence.

## Rules

- Entry: compare the current closed-bar close with the close 20 bars earlier;
  go `UP` when higher and `DOWN` when lower.
- Initial stop: opposite extreme of the preceding five bars, excluding the
  signal bar.
- Exit: no fixed profit target. On each later bar, ratchet the stop only in the
  favorable direction using the lowest low (long) or highest high (short) of
  the preceding 20 bars, excluding the current bar. Exit when the current bar
  touches the ratcheted stop.
- Ambiguity: `STOP_FIRST` remains conservative when applicable.

The 20/5 windows are implementation derivations. They are not claimed as
parameters specified by Covel or by the cited time-series momentum paper.

## Evidence boundary

Public Covel author material supports the general price-first, reactive,
loss-limiting and profit-running philosophy only. The independent research
paper supports time-series momentum as an empirical prior only. TF-004 remains
signal-only, price-unit, preliminary research and cannot authorize MT5/demo or
live execution.
