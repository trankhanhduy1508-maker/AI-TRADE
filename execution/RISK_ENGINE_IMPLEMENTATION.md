# Independent Risk Engine

`src/execution/risk.py` is an independent, deterministic policy layer between
validated strategy output and a broker adapter.

It blocks an order when any of these conditions fail:

- volume exceeds the configured hard maximum;
- current open positions are already at the maximum;
- spread exceeds the configured maximum;
- daily loss has reached the configured maximum;
- market context is non-finite;
- stop loss or target is missing or on the wrong side of the entry price.

The `ExecutionCoordinator` invokes it after the persistent kill/safety gate and
before `adapter.submit()`. A configured engine with no `RiskContext` blocks
with `RISK_CONTEXT_MISSING`; this prevents a caller from accidentally bypassing
the independent policy.

This is a policy contract, not a selection or optimization mechanism. Limits
are explicit constructor inputs and are never increased by strategy results.
The current repository does not activate live execution.
