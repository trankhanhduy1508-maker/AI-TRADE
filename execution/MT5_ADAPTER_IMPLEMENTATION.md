# MT5 Adapter Implementation Boundary

## Status

This is a code-verified safety boundary, not an MT5 integration claim. The
optional `MetaTrader5` package and a broker terminal/account are not required
for the test path and no credentials are stored in the repository.

## Official API evidence

- MetaQuotes documents `initialize()` as the Python call that establishes a
  terminal connection: <https://www.mql5.com/en/docs/python_metatrader5/mt5initialize_py>.
- `order_check()` performs a basic funds/request check, but MetaQuotes notes
  that a successful check does not guarantee execution:
  <https://www.mql5.com/en/docs/python_metatrader5/mt5ordercheck_py>.
- `order_send()` returns a trade result whose `retcode` must be interpreted;
  calling the function successfully is not equivalent to execution:
  <https://www.mql5.com/en/docs/python_metatrader5/mt5ordersend_py>.
- The server return-code registry distinguishes completion, partial completion,
  connection failure, trading disabled, invalid stops and other states:
  <https://www.mql5.com/en/docs/constants/errorswarnings/enum_trade_return_codes>.

## Implemented invariants

`src/execution/mt5_adapter.py` currently provides:

- `DISABLED` as the default execution mode; disabled submission never calls
  `initialize()` or `order_send()`.
- `LIVE` mode is hard-locked and raises `TradingDisabledError`, regardless of
  the send flag.
- `DEMO` submission requires an explicit injected terminal and
  `allow_order_send=True`; this code path is not enabled by configuration in
  the repository.
- `order_check()` must return retcode `0` before `order_send()` is called.
- `10009` maps to `FILLED`, `10010` to `PARTIAL`, and all other send retcodes
  are recorded as `REJECTED` pending a fuller broker mapping.
- A SQLite `OrderIntentLedger` records `SUBMITTING` before any terminal call.
  The same `client_order_id` is suppressed after restart until reconciliation,
  preventing an ambiguous timeout from becoming a duplicate order.
- The adapter uses dependency injection and never imports a secret, account
  password, or private key.

## Current boundary and blockers

- No MT5 terminal, broker symbol metadata, demo account, tick stream, or
  broker-specific cost evidence is available in this workspace.
- Therefore no terminal integration test, demo forward run, reconnect test
  against a real server, or realistic cost validation is claimed.
- Risk engine, kill switch, reconciliation service, monitoring, and persistent
  portfolio state remain separate required workstreams before any demo/live
  readiness decision.
- No live-money execution can be enabled by this adapter implementation.

The follow-on safety contracts in `src/execution/recovery.py` and
`src/execution/safety.py` now cover disconnect/reconciliation gating and a
persistent kill switch. They still require an external broker/demo integration
test and do not replace the independent risk engine.

`src/execution/coordinator.py` is the only tested handoff path in this layer:
it evaluates `SafetyGate` first and calls the adapter only when the independent
policy snapshot is allowed. A blocked signal is returned as `GATE_BLOCKED` and
never reaches `order_check()` or `order_send()`.

When configured, `src/execution/audit.py` records the coordinator decision and
broker result in an append-only SQLite event stream. Sensitive field names are
rejected before persistence; the audit stream is not a credential store.

## Verification

`tests/execution/` verifies disabled fail-closed behavior, live lock,
check-before-send, persistent duplicate suppression, reconnect gating, exact
reconciliation, and kill-switch persistence with local fakes. Real MT5/demo
verification remains an external-account blocker and must not be simulated as
passed.
