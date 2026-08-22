# Android Monitoring and Control Contract

## Status

Code-verified local state contract only. No Android app, network endpoint,
credential, or remote-control channel is enabled yet.

## Public health shape

`RuntimeHealth.to_public_dict()` exposes only operational state:

- `mode`: currently `DEMO` is the only mode that can be ready for new entries;
- `mt5_connected`;
- `state_known`;
- `new_entries_paused`;
- `kill_switch_active`;
- `last_error` without credentials;
- derived `ready_for_new_entries`.

The system is not ready when any fail-closed condition is true. Android is a
control plane and must not be a dependency for the engine heartbeat.

## Control rules

`ControlPlaneState` persists pause/kill state in SQLite. New installations
default to `new_entries_paused=true` and `kill_switch_active=true`. Pausing and
kill activation require a reason; resuming new entries requires an explicit
operator note. Resetting the kill switch remains a separate authorized
operation and is not exposed as an automatic action.

Every local state transition is now appended to the same SQLite store's
`control_events` table with command, `LOCAL` source, note, and UTC timestamp.
`read_events()` is the provider-neutral audit read path. No network caller is
trusted or enabled by this contract.

## Remaining implementation gates

- authenticated API and Android client;
- authorization/audit of every remote command;
- TLS/secret management without repository credentials;
- real MT5 heartbeat and account-mode reporting;
- offline/reconnect behavior and 24/7 deployment tests.
