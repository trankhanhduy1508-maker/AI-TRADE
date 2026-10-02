# TF-013A Forward Promotion Gate — 2026-09-27

## Purpose

This gate evaluates only true forward trades generated after the TF-013A forward checkpoint.

It does not approve:
- account-level risk;
- The5ers automation;
- live/funded execution;
- broker order routing.

The gate is frozen before TF-013A has any closed forward trade.

## Evidence source

Canonical source:
`ai_trade.forward_shadow_trades`

Execution consistency source:
`ai_trade.shadow_broker_orders`
and
`ai_trade.shadow_broker_runs`

Historical backtest results are not mixed into this score.

## States

### COLLECTING

Use while any of these are true:
- fewer than 50 closed forward trades;
- fewer than 120 calendar days since the first closed forward trade;
- fewer than 8 markets have at least one closed forward trade.

No promotion decision is allowed in COLLECTING.

### FORWARD_REJECT

After minimum evidence is reached, reject if any required gate below fails.

### FORWARD_CANDIDATE

After minimum evidence is reached, candidate status requires every gate below to pass.

This is still research-only. It is not permission to send a broker order.

## Frozen candidate gates

At synthetic 10 bps:
1. aggregate net R > 0;
2. expectancy R > 0;
3. profit factor R > 1.0;
4. return / max-drawdown R > 0.5;
5. at least 5 markets have positive cumulative R;
6. no single market contributes more than 40% of total positive market R.

At synthetic 20 bps:
7. aggregate net R > 0.

Execution integrity:
8. zero shadow-broker bars flagged MULTI_MUTATION_SAME_BAR;
9. zero duplicate client_order_id rows by database invariant;
10. every shadow entry has visible_stop=true.

## Important boundary

The thresholds above are research-quality gates, not account-risk limits.

No MAX_SPREAD_POINTS, MAX_DAILY_LOSS_DEMO, MAX_TOTAL_VOLUME_DEMO, or monetary risk value is approved by this document.

If TF-013A reaches FORWARD_REJECT, do not retune TF-013A and keep its ID. A materially changed method must receive a new preregistered strategy ID.
