# MT5 Runtime Validation — 2026-08-22

## Scope

This milestone validates the official MetaTrader 5 desktop runtime and Python
package boundary without credentials, broker access, order submission, or
live-money activation.

## Evidence

- Host: Windows 10 build 19045, Python 3.12.10 x64.
- Official terminal installer: `mt5setup.exe`, downloaded from the CDN linked
  by MetaTrader documentation.
- Installer SHA-256:
  `AC1651F02DD17EE5F61D68F13DA4A8FB9CE6576ECC9F3A5C3685FDCB5D642F7C`.
- Installer Authenticode: `Valid`; signer `MetaQuotes Ltd.`.
- Installed `terminal64.exe`: build `5.0.0.6140`, Authenticode `Valid`, signer
  `MetaQuotes Ltd.`.
- Official Python package: `MetaTrader5==5.0.6090` with NumPy `2.5.2`,
  installed only in a temporary untracked runtime.
- Read-only `mt5.initialize()` probes were run with and without an explicit
  portable terminal path, with 1–30 second timeouts. Both returned:
  `(-10005, 'IPC timeout')`; no `order_check()` or `order_send()` call was made.
- Terminal logs show build 6140 started and completed its MQL5 compilation.
  The second isolated portable copy also reported an MCP port collision on
  `127.0.0.1:22346`; this is an environment issue, not demo-account evidence.

## Interpretation

The official terminal is installed and starts, but Python IPC is not yet a
validated integration. The observed package/terminal versions are different
(`5.0.6090` vs build `6140`), and no broker server or demo account is
configured. This is explicitly **BLOCKED / UNVALIDATED**, not a successful demo
connection and not a reason to enable live trading.

The implementation therefore keeps the Python MT5 adapter fail-closed and
continues the independent native-MQL5 and offline paper workstreams. A future
demo milestone must separately prove account authorization, read-only data
access, `order_check()`, and a controlled demo fill.

## Post-Founder-login read-only discovery

After the Founder granted permission to test the demo account, a fresh
read-only discovery checked all four currently running terminal processes and
the standard MetaQuotes profile locations. The four processes were isolated
temporary terminals created for this project; no separate Founder terminal
process or executable was discoverable in the checked installation roots.

The fresh Python probes returned:

- original isolated terminal: `(-6, 'Terminal: Authorization failed')`;
- isolated user terminal: `(-10005, 'IPC timeout')`;
- two isolated tester terminals: `(-10005, 'IPC timeout')`.

No account info, server, symbol tick, `order_check()`, or `order_send()` data
was obtained. Terminal logs also contained an authorization failure for the
placeholder MetaQuotes-Demo context. The Founder demo login therefore remains
not observable from this agent's terminal boundary; this is a technical
discovery blocker, not evidence that the Founder account itself is invalid.

## Official references

- [MetaTrader 5 download](https://www.metatrader5.com/en/download)
- [Platform installation](https://www.metatrader5.com/en/terminal/help/start_advanced/installation)
- [Platform start and portable/configuration mode](https://www.metatrader5.com/en/terminal/help/start_advanced/start)
- [MetaTrader Python integration](https://www.mql5.com/en/docs/python_metatrader5)
- [Python `initialize`](https://www.mql5.com/en/docs/python_metatrader5/mt5initialize_py)

## Safety status

- Live-money trading: locked.
- No credentials or account identifiers stored.
- No power-state transition performed.
- No broker order sent.
