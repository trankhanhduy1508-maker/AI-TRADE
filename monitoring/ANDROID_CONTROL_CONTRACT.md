# Android Monitoring and Control Contract

## Status

Code-verified local state and signed-command core contract. No Android app,
network endpoint, credential, or remote-control listener is enabled yet.

## Public health shape

`RuntimeHealth.to_public_dict()` exposes only operational state:

- `mode`: currently `DEMO` is the only mode that can be ready for new entries;
- `mt5_connected`;
- `state_known`;
- `reconciled`;
- `data_fresh`;
- `risk_allowed`;
- `heartbeat_fresh`;
- `new_entries_paused`;
- `kill_switch_active`;
- `last_error` without credentials;
- derived `ready_for_new_entries`.

The system is not ready when any fail-closed condition is true. In particular,
MT5 connectivity alone is not readiness: position reconciliation, fresh data,
independent risk approval, and a fresh engine heartbeat are also required.
Android is a control plane and must not be a dependency for the engine
heartbeat.

## Control rules

`ControlPlaneState` persists pause/kill state in SQLite. New installations
default to `new_entries_paused=true` and `kill_switch_active=true`. Pausing and
kill activation require a reason; resuming new entries requires an explicit
operator note. Resetting the kill switch remains a separate authorized
operation and is not exposed as an automatic action.

Every local state transition is now appended to the same SQLite store's
`control_events` table with command, `LOCAL` source, note, and UTC timestamp.
`read_events()` is the provider-neutral audit read path. The authenticated
control core accepts only HMAC-signed commands, persists request IDs to reject
replays across restarts, tags accepted commands as `ANDROID_HMAC`, and returns
the public health shape. It supports pause, resume, and kill activation;
remote kill reset is intentionally not supported. No network caller is
trusted or enabled by this contract.

## Remaining implementation gates

- transport/API endpoint and Android client;
- external secret provisioning/rotation and device authorization;
- authorization/audit of every remote command;
- TLS/secret management without repository credentials;
- real MT5 heartbeat and account-mode reporting;
- offline/reconnect behavior and 24/7 deployment tests.
