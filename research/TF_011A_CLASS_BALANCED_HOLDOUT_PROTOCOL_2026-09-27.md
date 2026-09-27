# TF-011A Class-Balanced Trend Portfolio — Final Holdout Protocol

## Development history

The preregistered portfolio suite did not open final holdout because no candidate met every validation gate.

TF-009A nevertheless produced a validation-selected market set under the already-frozen rule:
- GBPUSD
- USDJPY
- XAUUSD
- USOIL
- BTCUSD
- ETHUSD
- US30
- NAS100
- US500

The failure was portfolio concentration:
positive contribution dominance = 0.4065, above the frozen 0.40 gate.

This new strategy changes **portfolio construction only**.
The signal, execution model, selected market set, and stop model are frozen from TF-009A validation evidence.

This document is committed before TF-011A final holdout is computed.

## Strategy ID

TF-011A-CLASS-BALANCED-TREND

## Frozen signal

Same as TF-009A:
- sign of 21-bar return;
- sign of 252-bar return;
- SMA10 vs SMA200 sign;
- majority vote 2 of 3;
- review every 21 bars.

Execution:
- signal on closed bar;
- enter/reverse next bar open;
- fixed emergency stop = 4 ATR(20);
- gap-aware stop fill;
- no pyramiding;
- no target.

## Frozen market set

FX:
- GBPUSD
- USDJPY

Commodities:
- XAUUSD
- USOIL

Crypto:
- BTCUSD
- ETHUSD

Indices:
- US30
- NAS100
- US500

No market may be added or removed after seeing holdout.

## Portfolio weights

Each asset class receives 25% of normalized research risk.

Within each class, equal weight:
- FX: 12.5% each
- Commodities: 12.5% each
- Crypto: 12.5% each
- Indices: 8.333...% each

These are normalized research weights, not account-risk approvals.

## Final holdout

Use only the final 20% of each instrument's longest-practical public daily history.

Synthetic friction:
- 10 bps round trip
- 20 bps round trip

## Holdout PASS criteria

TF-011A passes historical holdout only if all are true:

1. class-balanced portfolio net R > 0 at 10 bps;
2. class-balanced portfolio net R > 0 at 20 bps;
3. return/max-drawdown > 0.5 at 10 bps;
4. at least 6/9 markets are individually positive at 10 bps;
5. at least 3/4 asset-class subportfolios are positive at 10 bps;
6. no single market contributes more than 30% of total positive weighted contribution;
7. no single class contributes more than 50% of total positive weighted contribution.

A PASS is historical research evidence only.
It cannot approve live/funded execution, The5ers automation, or account risk.
