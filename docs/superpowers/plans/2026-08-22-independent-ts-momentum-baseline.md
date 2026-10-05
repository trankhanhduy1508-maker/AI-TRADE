# Independent Time-Series Momentum Baseline

## Goal

Add one deterministic strategy translation independent of TF-001 so the
research path can test whether the current negative result is specific to the
rule-engine translation. This is a research baseline only; it does not change
risk limits or authorize MT5/live execution.

## Evidence boundary

- Covel public author material supports price-first, reactive, less-discretionary
  trend-following principles.
- Moskowitz, Ooi, and Pedersen provide independent primary research on
  time-series momentum across liquid futures/forwards and multiple horizons.
- The operational lookback, stop window, and fixed reward/risk value below are
  AI-TRADE implementation derivations. They are not claimed as Covel book
  parameters or as a replication of the paper.

## Fixed design

1. Add `TF-003-TIME-SERIES-MOMENTUM` machine-readable and human-readable specs.
2. Emit `UP` when the current closed-bar close is above the close exactly
   `lookback_bars` bars earlier; emit `DOWN` when below; emit no signal when
   equal or insufficient history exists.
3. Derive a stop from the opposite extreme of the preceding
   `stop_lookback_bars` bars, excluding the signal bar.
4. Reuse the existing signal-only engine, one-open-position policy, fixed
   reward/risk exit, cost model, and chronological IS/OOS runner. No capital,
   leverage, or risk-limit changes.
5. Add a CLI strategy-model dispatch and unit tests proving no lookahead,
   deterministic direction, and valid stops.
6. Run the same six fixed-profile IS/OOS experiments used for TF-001. Do not
   retune after seeing results. Record the result as preliminary until cost
   assumptions and broker data are verified.

## Verification gates

- TDD tests fail before implementation and pass after implementation.
- Full test suite passes.
- Six reproducible runs use the committed data, fixed split, and committed
  cost profile.
- Research and status docs record provenance, limitations, and actual output.
- Secret scan, whitespace check, commit, and push complete before handoff.
