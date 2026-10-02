# AI-TRADE — Risk Profile Approval Packet 2026-09-27

## Purpose

This packet exists so a DEMO risk profile can be approved from explicit evidence instead of inheriting historical placeholders.

It does not approve any number by itself.

## Current runtime state

- risk_profile_approved: false
- risk_profile_approval_evidence: NULL
- risk_profile_approved_at: NULL
- max_total_volume_demo: NULL
- max_pyramid_adds: 0
- automation_approval_verified: false
- readiness: BLOCKED_APPROVAL
- live/funded execution: HARD LOCKED

## Evidence already available

### Strategy robustness

TF-004 cloud risk lab:
- OOS 70/30
- expanding walk-forward 50/10
- cost stress 0x / 1x / 1.5x / 2x
- EURUSD / GBPUSD / USDJPY
- conclusion: FAIL_CLOSED

This evidence does not justify promoting:
- MAX_SPREAD_POINTS
- MAX_DAILY_LOSS_DEMO
- MAX_TOTAL_VOLUME_DEMO

### Pyramiding

Winner-only one-add historical test worsened net-R and/or drawdown on EURUSD, GBPUSD and USDJPY.

Decision:
- pyramiding remains OFF
- max_pyramid_adds = 0

### Firm constraint

For The5ers Bootcamp challenge:
- Step 1 initial balance: 5000
- profit target: +6%
- absolute max-loss floor: 4750

The 5% firm floor is not a per-trade risk recommendation.

## Required approval fields

The following must be explicitly supplied and approved before risk_profile_approved can become true:

- MAX_SPREAD_POINTS:
- MAX_DAILY_LOSS_DEMO:
- MAX_TOTAL_VOLUME_DEMO:
- approval evidence reference:
- approved by:
- approved at:

No field may be auto-filled from legacy runtime defaults.

## Evidence still required before a defensible proposal

1. Broker-aligned DEMO symbol specifications.
2. Broker-aligned spread observations.
3. Broker commission/swap/slippage evidence where applicable.
4. Margin and tick-value geometry for the actual The5ers DEMO account.
5. Forward paper sample large enough to compare historical vs forward drift.
6. Founder decision on acceptable account-level risk budget.

## Safety invariant

Until all required evidence exists and a human approval is recorded:

`risk_profile_approved=false`

The runtime DB constraint rejects a boolean-only approval without:
- non-empty evidence;
- approval timestamp;
- positive MAX_TOTAL_VOLUME_DEMO.

This packet must not be interpreted as permission to send an order.
