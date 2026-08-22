# Channel-Trailing Exit Model

## Goal

Add an explicit optional channel-trailing exit to the deterministic signal-only
engine. Preserve the existing fixed-R/R behavior by default and evaluate a new
TF-004 comparison strategy without changing risk limits or execution code.

## Fixed design

1. Add `exit_model=FIXED_RR` as the backward-compatible default and
   `exit_model=CHANNEL_TRAILING` as the new explicit mode.
2. In channel mode, do not create a profit target. On each later closed bar,
   derive the candidate stop from the preceding `exit_lookback_bars` bars,
   excluding the current bar; ratchet it only in the favorable direction.
3. Check the ratcheted stop against the current bar using the existing
   conservative stop-first ambiguity policy. Use `TRAILING_STOP` as the exit
   reason.
4. Keep all outcomes in price units. Do not add sizing, leverage, capital PnL,
   or risk-limit changes.
5. Add TF-004 as the same fixed time-series momentum signal with a declared
   channel-trailing exit. It is a separate hypothesis and must be tested from
   the committed spec without post-result tuning.

## Verification gates

- Tests fail before implementation for optional targets and trailing ratchet
  behavior.
- Existing full suite remains green, proving FIXED_RR compatibility.
- New evaluator/engine tests prove current-bar exclusion and monotonic stop
  ratcheting.
- Six fixed IS/OOS runs are recorded with the same research cost profile.
- Results remain preliminary until broker/demo data and cost evidence exist.
