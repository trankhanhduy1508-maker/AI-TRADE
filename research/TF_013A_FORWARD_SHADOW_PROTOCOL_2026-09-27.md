# TF-013A Forward Shadow Protocol — 2026-09-27

## Purpose

Historical research reached diminishing returns and no strategy passed every preregistered promotion gate.

TF-013A exists to collect **true forward evidence** without broker execution.

No historical trade is backfilled.

Historical bars may be loaded only to warm indicators.

## Strategy

strategy_id:
`TF-013A-FORWARD-DIVERSIFIED-TREND`

Universe:
- EURUSD
- GBPUSD
- USDJPY
- AUDUSD
- USDCAD
- USDCHF
- NZDUSD
- XAUUSD
- USOIL
- BTCUSD
- ETHUSD
- US30
- NAS100
- US500

Signal:
- 21-bar return sign
- 252-bar return sign
- SMA10 vs SMA200 sign
- majority vote 2 of 3

Review:
- first newly processed closed trading bar of each UTC calendar month.

Execution simulation:
- signal is computed only after the review bar is closed;
- entry/reversal occurs at the next available bar open;
- emergency stop = 4 ATR(20) fixed at entry;
- a gap through stop exits at the worse bar open;
- no target;
- no pyramiding;
- one paper position per market.

Forward start:
- 2026-09-27 UTC checkpoint.
- first function run only warms state and sets the latest already-closed bar as processed.
- trades are generated only from later closed bars.

Friction reporting:
- gross R
- synthetic 10 bps round-trip friction R
- synthetic 20 bps round-trip friction R

Synthetic friction is research stress, not claimed broker cost.

Portfolio research weights:
- FX sleeve 25%
- Commodity sleeve 25%
- Crypto sleeve 25%
- Index sleeve 25%
- equal weight within each sleeve
- no account-money sizing

## Hard invariants

- brokerOrders=false
- liveMoneyLocked=true
- no MetaApi order call
- no The5ers challenge order
- no historical trade backfill
- no fake approval
- no account-risk approval
- every state transition is journaled

This forward journal can later be reconciled against a real generic MT5 DEMO account after a legitimate account and MetaApi connection exist.
