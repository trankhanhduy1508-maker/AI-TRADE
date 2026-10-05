# Preregistered Portfolio Trend Suite — 2026-09-27

## Why a second suite exists

The first preregistered suite returned `NO_VALIDATION_CANDIDATE`.
Its final 20% holdout was not opened by that suite.

This second suite tests a different hypothesis family:
**diversified multi-horizon trend with validation-selected markets**.

The selection rule below is frozen before any TF-008/009/010 result is computed.

## Common execution contract

- daily closed-bar signals;
- review every 21 bars;
- order at next bar open;
- fixed emergency stop = 4 ATR(20) from entry;
- gap-through-stop fills at the worse bar open;
- one position per market;
- no pyramiding;
- no profit target;
- after stop, wait until next scheduled review;
- synthetic friction stress at 10 and 20 bps round trip;
- no broker order.

Chronological split per instrument:
- first 60%: history/warm-up;
- middle 20%: validation + market selection;
- final 20%: holdout opened only for one selected candidate.

## TF-008A — Multi-horizon TSMOM vote

Signals:
- 63-bar return sign;
- 126-bar return sign;
- 252-bar return sign.

Direction:
- long if at least 2/3 are positive;
- short if at least 2/3 are negative.

Review:
- every 21 bars.

## TF-009A — Diversified trend signal ensemble

Signals:
- 21-bar return sign;
- 252-bar return sign;
- SMA10 vs SMA200 sign.

Direction:
- majority vote 2/3.

Review:
- every 21 bars.

## TF-010A — 6-month TSMOM

Signal:
- sign of 126-bar return.

Review:
- every 21 bars.

## Validation market-selection rule

For each candidate separately, a market is eligible only when:
1. validation net R > 0 at 10 bps;
2. validation net R > 0 at 20 bps;
3. validation has at least 3 completed trades.

The candidate is portfolio-eligible only when selected markets include:
- at least 6 total markets;
- at least 2 FX markets;
- at least 1 commodity (Gold or Oil);
- at least 1 crypto (BTC or ETH);
- at least 1 equity index (US30, NAS100, US500).

Portfolio aggregation:
- equal risk weight across selected markets;
- realized trade R is divided by selected market count;
- events are ordered chronologically;
- portfolio drawdown is computed from the combined R event stream.

Additional validation requirements:
- portfolio net R > 0 at 10 bps;
- portfolio net R > 0 at 20 bps;
- 10-bps portfolio net R / max drawdown R > 0.5;
- no single market contributes more than 40% of total positive market R.

If multiple candidates pass, selection order:
1. higher 10-bps portfolio net R / max drawdown;
2. more selected markets;
3. lower contribution concentration.

## Final holdout rule

Only the one validation-selected candidate and its frozen selected-market set are evaluated on the last 20%.

Holdout passes only if:
1. aggregate portfolio net R > 0 at 10 bps;
2. aggregate portfolio net R > 0 at 20 bps;
3. at least 60% of selected markets are individually positive at 10 bps;
4. at least one FX, one commodity, one crypto, and one index remain positive;
5. portfolio net R / max drawdown > 0.5 at 10 bps;
6. no single market contributes > 40% of total positive market R.

No holdout pass can approve account-level risk or broker execution.
