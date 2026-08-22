# Native MQL5 EA Boundary

## Purpose

`mql5/Experts/AITradeTrendFollowingEA.mq5` is the first native terminal
boundary for TF-003. It is intentionally a small deterministic breakout EA so
the terminal path can be tested independently from the Python IPC package.

Signal semantics:

- evaluate only after a new closed bar;
- long when the last closed close is above the prior `BreakoutLookback` highs;
- short when it is below the prior `BreakoutLookback` lows;
- use ATR-based fixed stop and reward multiple;
- use a fixed `DemoLots` input capped at `0.01`.

This is an implementation boundary, not evidence that TF-003 is profitable or
live-ready.

## Hard safety gates

Every order path requires all of the following:

1. `EnableDemoTrading` is explicitly set to `true` (default is `false`).
2. `ACCOUNT_TRADE_MODE` is exactly `ACCOUNT_TRADE_MODE_DEMO`.
3. The terminal is connected and terminal trading is allowed.
4. The fixed demo lot and strategy inputs pass local validation.
5. The current spread is within the configured bound.

The native boundary also has independent operational controls:

- missing `AITrade\\kill_switch.flag` is an active kill switch; only the exact
  common-file value `DISARMED` clears it;
- missing `AITrade\\entries_paused.flag` pauses new entries; only the exact
  value `RESUMED` clears it;
- the common `AITrade\\native_audit.csv` sink must be writable before an entry;
- order intent and result records are appended around each `CTrade` call.

There is no real-account branch in this EA. It must not be used as a reason to
unlock live money. Persistent kill-switch, reconciliation, duplicate-order
ledger, audit sink, and Android control remain separate required workstreams.

## Compile evidence

Compiled with the official MetaEditor 64-bit executable from terminal build
6140 using the documented command-line compiler and the terminal's MQL5 include
directory:

- `Result: 0 errors, 0 warnings`
- `cpu='X64 Regular'`
- generated EX5 SHA-256 begins with:
  `763F95CB0E0F5D98A593EB1FCD7B79157FED61FB3637180F90FA97B971F...`

The EX5 and compiler log are local build artifacts and are ignored by Git; the
MQ5 source is the reviewable artifact.

Official compiler reference:

- [MetaEditor external compiler integration](https://www.metatrader5.com/en/metaeditor/help/beginning/integration_ide)

## Demo activation status

No EA was attached to a chart, no account was selected, no `order_check` or
`order_send` equivalent was invoked, and no broker/demo order was submitted.
The current status is **compiled / not runtime-validated / not demo-active**.
