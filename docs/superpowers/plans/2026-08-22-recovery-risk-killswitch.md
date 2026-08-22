# Recovery, Reconciliation, and Kill-Switch Contracts

## Goal

Implement offline-verifiable safety contracts required before autonomous MT5
operation. These contracts do not choose position size or alter project hard
risk limits.

## Fixed design

1. Treat connection loss, unknown state, stale data, failed reconciliation,
   manual pause, and active kill switch as hard blocks for new entries.
2. After reconnect, allow new entries only after broker/local position sets
   reconcile exactly.
3. Persist kill-switch state in SQLite; missing state means active/blocked.
4. Keep risk limits outside this component: the gate consumes a boolean
   `risk_allowed` from an independent policy engine and never increases it.
5. Add tests for fail-closed defaults, reconnect gating, mismatch blocking,
   persistent activation, and manual reset.
