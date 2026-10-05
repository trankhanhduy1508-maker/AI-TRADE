# Preregistered Strategy Suite — 2026-09-27

## Purpose

TF-004 failed the maximum robustness gate because close-entry assumptions did not survive next-open + gap-aware execution broadly enough.

This document freezes the next research hypotheses **before any candidate result is computed**.

No candidate may be retuned after results and still keep the same strategy ID.

## Locked validation protocol

Universe:
EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF, NZDUSD, XAUUSD, USOIL, BTCUSD, ETHUSD, US30, NAS100, US500.

Daily longest-practical public history per instrument.

Chronological split:
- first 60%: development/warm history;
- next 20%: candidate selection validation;
- final 20%: locked final holdout.

The final 20% must not be computed for all candidates. It is opened only for the single validation-selected candidate.

Execution contract for every candidate:
- signal uses closed information only;
- order acts at next bar open;
- protective stop is fixed from information available before entry;
- gap through stop fills at the worse bar open;
- one position per instrument;
- no pyramiding;
- no same-bar entry/exit;
- no broker orders.

Universal synthetic friction stress is reported separately from broker-specific cost:
- 0 bps;
- 5 bps round trip;
- 10 bps round trip;
- 20 bps round trip.

These are research stresses, not broker cost claims.

## Candidate TF-005A — 12M TSMOM + emergency ATR stop

Hypothesis:
Long-horizon own-asset trend is more robust than TF-004's 20-bar direction signal.

Rules:
- strategy_id: TF-005A-TSMOM-12M
- momentum lookback: 252 daily bars
- signal: sign(close[t] / close[t-252] - 1)
- review/rebalance cadence: every 21 bars
- enter or reverse at next bar open
- ATR: 20 bars, Wilder-style true-range average approximation
- emergency stop distance: 4 ATR measured at signal bar
- no profit target
- no trailing stop
- between review points, only emergency stop may exit
- after a stop, wait until the next scheduled review before re-entry

Rationale:
12-month own-asset momentum is a published time-series momentum horizon; the wide ATR stop is a deployability/safety layer rather than the alpha source.

## Candidate TF-006A — Donchian 55/20 + ATR stop

Hypothesis:
Breakout confirmation can avoid TF-004's small stop-distance geometry.

Rules:
- strategy_id: TF-006A-DONCHIAN-55-20
- long signal: close > prior 55-bar high
- short signal: close < prior 55-bar low
- enter at next bar open
- initial emergency stop: 2 ATR(20)
- long exit signal: close < prior 20-bar low
- short exit signal: close > prior 20-bar high
- exit at next bar open unless protective stop occurs earlier
- no profit target
- no pyramiding

## Candidate TF-007A — MA 50/200 + ATR stop

Hypothesis:
A slow trend regime filter can reduce sensitivity to individual breakout timing.

Rules:
- strategy_id: TF-007A-MA-50-200
- long regime: SMA50 > SMA200
- short regime: SMA50 < SMA200
- enter/reverse at next bar open after regime change
- initial emergency stop: 3 ATR(20)
- otherwise hold until opposite regime
- no target
- no pyramiding

## Validation selection rule

Candidate selection uses **only the middle 20% validation slice**.

For each candidate compute per-market validation net R under:
- next-open execution;
- gap-aware stop;
- universal synthetic friction 10 bps round trip.

A candidate is eligible only if:
1. median validation net R across the 14 markets > 0;
2. at least 9/14 markets have positive validation net R;
3. at least 4/7 Forex markets have positive validation net R;
4. at least 4/7 cross-asset markets have positive validation net R;
5. aggregate positive R is not dominated >40% by one market.

If multiple candidates are eligible, select the candidate with:
1. highest number of positive markets;
2. then highest median market validation R;
3. then lowest median market drawdown R.

If no candidate is eligible, **do not open final holdout**. The suite fails and a new preregistered hypothesis family is required.

## Final holdout pass rule

Only the selected candidate is evaluated on the final 20%.

Pass requires:
1. median holdout net R > 0;
2. at least 9/14 markets positive;
3. at least 4/7 Forex and 4/7 cross-asset positive;
4. portfolio equal-market aggregate net R > 0 at 10 bps synthetic friction;
5. the same signs remain positive at 20 bps portfolio aggregate;
6. no single market contributes >40% of aggregate positive R.

A holdout pass is still research evidence only. It does not approve account risk or broker execution.
