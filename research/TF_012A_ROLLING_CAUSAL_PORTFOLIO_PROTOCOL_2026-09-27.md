# TF-012A Rolling Causal Trend Portfolio — Preregistered Protocol

## Research lineage

TF-004 failed execution robustness.
The first preregistered fixed-rule suite failed validation.
The diversified portfolio suite failed its concentration gate.
TF-011A produced positive final-holdout portfolio R but failed the preregistered market/class concentration gates.

TF-012A changes the validation design itself:
**every test year is out-of-sample relative to a trailing 5-year market-selection window.**

This protocol is frozen before TF-012A is run.

## Strategy ID

TF-012A-ROLLING-CAUSAL-TREND

## Alpha signal

Fixed TF-009A signal:
- 21-bar return sign;
- 252-bar return sign;
- SMA10 vs SMA200 sign;
- majority vote 2/3;
- review every 21 bars;
- next-open execution;
- emergency stop = 4 ATR(20);
- gap-aware stop;
- no pyramiding;
- no target.

## Annual causal market selection

For each calendar test year Y:

Training window:
- Y-5-01-01 through Y-1-12-31.

For every market with enough historical data:
- simulate the fixed signal at 10 bps synthetic round-trip friction;
- market is eligible only if:
  - at least 5 completed training trades;
  - trailing 5-year net R > 0;
  - trailing 5-year net R / max drawdown R > 0.5.

The eligible set is frozen before test-year Y begins.

No test-year result can influence its own selection.

## Research portfolio weights

Four sleeves:
- FX: 25%
- Commodities: 25%
- Crypto: 25%
- Equity indices: 25%

Within a sleeve:
- equal weight across eligible markets;
- hard research weight cap per market = 12.5%;
- unused sleeve capacity stays in cash;
- a class with no eligible market stays fully in cash.

These are normalized research weights, not account-risk approval.

## Test period

Calendar years 2010 through the last available year.

Assets may join only after they have enough trailing history.

Each calendar year starts flat.
This makes yearly OOS attribution explicit and reproducible.

Synthetic friction:
- 10 bps round trip;
- 20 bps round trip.

## PASS criteria

TF-012A passes the rolling historical validation only if all are true:

1. at least 12 completed OOS calendar years;
2. aggregate OOS portfolio net R > 0 at 10 bps;
3. aggregate OOS portfolio net R > 0 at 20 bps;
4. 10-bps aggregate net R / max drawdown R > 1.0;
5. at least 60% of OOS years have positive net R at 10 bps;
6. cumulative 10-bps R over the latest 5 completed/available test years > 0;
7. at least 3 of 4 asset-class sleeves have positive cumulative 10-bps contribution;
8. no single market contributes > 30% of total positive weighted R;
9. no single asset class contributes > 50% of total positive weighted R.

No parameter or threshold may be changed after seeing TF-012A results while retaining the TF-012A ID.

A PASS remains research evidence only and does not approve broker execution or account risk.
