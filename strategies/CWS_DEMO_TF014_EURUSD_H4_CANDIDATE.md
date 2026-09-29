# CWS-DEMO-TF014-EURUSD-H4-V1 — Frozen deterministic research candidate

Date: 2026-09-29. **RESEARCH_CANDIDATE / broker_orders_approved=false**.
A candidate specification is not Founder approval or broker execution evidence.

## Purpose and construction

Reuse the repo's point-in-time time-series momentum implementation.
Only closed MT5 EURUSD H4 bars from the authenticated, bound DEMO broker
account may enter this signal. At least 60 chronological, finite, closed
bars are required. The last close versus 20 bars earlier determines UP
or DOWN; a stop uses the previous 10 closed bars (excluding the signal
bar). Flat or invalid input => ABSTAIN. A valid bar signal enters the
existing DemoAutoTradeEngine, not a new order-send bypass.

Exit: existing 20-bar channel trailing. No fixed take-profit, averaging
down, pyramiding, strategy self-promotion or LIVE mode. One position
per strategy and broker account, subject to reconciliation and the
independent risk gate. The original TF-004 historical run did **not**
validate autonomous DEMO; this variant must be independently tested,
not backfilled as TF-004 evidence.

## Proposed research safety limits

| Dimension | Frozen proposal |
|---|---:|
| Symbol / timeframe | EURUSD / broker-confirmed H4 |
| Per-order and per-symbol maximum | 0.01 lot |
| Maximum open positions | 1 |
| Broker spread maximum | 20 points (point units from broker) |
| Daily absolute loss | 100 USD |
| Daily equity-relative loss | 1% of verified broker equity |
| Initial broker-side stop exposure | 0.25% of verified equity |
| Add to winners / pyramiding | Disabled |
| Protective SL | Mandatory, finite, on correct side of entry |
| Kill switch | Existing persistent default-ON gate |
| Re-entry with unresolved intent | Blocked until broker reconciliation |

The two daily loss limits are independent; either can block. Account
currency must be verified USD. Broker-provided equity, tick size and
loss-side tick value **per lot in the account currency** are required
for the percentage stop calculation. No price-unit pip guess or client
supplied substitute is acceptable. Actual loss can exceed the computed
stop budget due to gaps, slippage, execution latency or broker changes.
These are proposal values for DEMO experiments, not tested capital
allocation advice or approval to enable runtime flags.

## Evidence ladder before enabled DEMO auto-send

1. Verify full rights/provenance and current broker EURUSD H4 feed,
   timestamp sequencing, tick value, spreads and historical costs.
2. Preregister and run independent historical 70/30 OOS, expanding
   walk-forward, broker cost/spread/slippage and next-open/gap stress.
3. Obtain forward-only paper results without backfilling trades.
4. Independently test authenticated Founder -> MT5 DEMO broker readback,
   protective SL order check, acknowledgement, restart and reconciliation.
5. Obtain Founder-approved risk/strategy evidence and explicit DEMO-send
   authorization. Do not alter LIVE/Production or native OAuth.
6. Sign release with the Founder-owned stable key outside GitHub;
   verify Android device install/update/recovery with retained data.

**Current status: source candidate only. No approved model, no DEMO
send gate, no release APK.** Never fabricate an approval or E2E PASS.
