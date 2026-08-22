# TF-003 Time-Series Momentum

## Status

- [x] Hypothesis specified
- [x] Deterministic evaluator implemented and unit-tested
- [ ] Backtest validated on a defined market/timeframe
- [ ] MT5 demo validated

This is an independent research baseline. It is not presented as a literal
Covel book rule or as a replication of the cited academic paper.

## 1. Hypothesis

Price persistence may provide a simple reactive trend signal: go long when the
current closed-bar close is above the close `lookback_bars` bars earlier, and
short when it is below. This operationalizes price-first, reactive,
less-discretionary principles from Covel's public author material and is
separately motivated by the time-series momentum evidence cited in the
knowledge provenance registry.

## 2. Market and timeframe

The initial experiment is limited to the same three Yahoo Finance FX proxies
and daily/hourly bars used for TF-001. Results must not be generalized to other
markets, brokers, or timeframes.

## 3. Trend and entry conditions

At closed bar `i`:

1. Require at least `lookback_bars + 1` bars.
2. Compare `close[i]` with `close[i - lookback_bars]`.
3. Emit `UP` when the current close is higher, `DOWN` when lower, and no signal
   when equal.
4. The comparison uses only the current closed bar and historical closes; no
   future bar is accessible.

The default `lookback_bars=20` is an AI-TRADE implementation derivation. It is
not claimed as a parameter specified by Covel or by the cited paper.

## 4. Confirmation

None. The purpose of this baseline is to isolate a simple price-only signal
from TF-001's multi-rule scoring stack.

## 5. Stop loss

For a long signal, stop at the minimum low of the preceding five bars. For a
short signal, stop at the maximum high of the preceding five bars. The signal
bar is excluded. No capital position sizing is performed by this strategy.

## 6. Exit

The current signal-only engine applies its declared fixed `reward_risk=1.5`
target and `STOP_FIRST` ambiguous-bar policy. This fixed target is an
implementation limitation of the current engine, not a Covel claim. A future
channel/trailing-exit experiment must be specified and tested separately.

## 7. No-trade conditions

Do not signal before the lookback and stop windows are available, on an equal
lookback comparison, or when the current bar is not closed. Invalid stop
geometry is rejected by the common engine.

## 8. Data and validation

Use `backtests/BACKTEST_STANDARD.md`, point-in-time evaluation, chronological
IS/OOS splits, and the committed research cost profile. Cost assumptions remain
`UNVERIFIED` until broker-specific/demo evidence exists.

## 9. Provenance boundary

- Public Covel material: `VERIFIED_FROM_AUTHOR` for principles only.
- Moskowitz, Ooi, and Pedersen paper: `VERIFIED_FROM_PRIMARY_RESEARCH` for the
  independent empirical prior only.
- Signal, stop, lookback, target, and scope: `IMPLEMENTATION_DERIVATION` or
  `UNVERIFIED` as labeled in the JSON spec.
- This strategy does not authorize MT5 demo or live trading.
