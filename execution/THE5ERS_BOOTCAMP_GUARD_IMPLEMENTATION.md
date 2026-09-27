# The5ers Bootcamp Guard — Implementation 2026-09-27

## Scope

Bootcamp challenge only. Không áp dụng funded stage.

Official rules snapshot used by the guard:
- Step 1: $5,000 -> target $5,300 -> max-loss floor $4,750.
- Step 2: $10,000 -> target $10,600 -> max-loss floor $9,500.
- Step 3: $15,000 -> target $15,900 -> max-loss floor $14,250.
- Challenge daily pause: none.
- Evaluation time: unlimited.
- Visible stop loss required for automated trades.
- Current The5ers terms require prior written approval for Automated Trading Software.

## Components

Python:
- `src/execution/the5ers_bootcamp_guard.py`
- `src/execution/prop_firm_compliance.py`
- `tests/execution/test_the5ers_bootcamp_guard.py`

Supabase:
- Edge Function `ai-trade-the5ers-bootcamp-guard`
- `ai_trade.prop_program_config`
- `ai_trade.prop_guard_events`

## Runtime defaults

Current config:
- provider: THE5ERS
- program: BOOTCAMP
- phase: 1
- initial_balance: 5000
- profit_target_pct: 0.06
- max_loss_pct: 0.05
- automation_approval_verified: false
- enabled: false

The guard is therefore intentionally fail-closed.

## Evidence

Synthetic normal-state probes:
- request #32 established the original guard baseline.
- request #35 verified monitor v2 at balance/equity 5000/5000 with projected SL loss 50.
- target: 5300; floor: 4750; remaining loss budget: 250.
- projected equity at SL: 4950; projected remaining budget: 200.
- alert: NORMAL.
- decision: BLOCKED by:
  - BOOTCAMP_EXECUTION_DISABLED
  - AUTOMATION_APPROVAL_REQUIRED

Synthetic near-floor probes:
- request #33 established the original floor-breach baseline.
- request #36 verified monitor v2 at balance/equity 4800/4780 with projected SL loss 40.
- projected equity at SL: 4740; remaining loss budget: 30.
- projected remaining budget: 0.
- alert: PROJECTED_STOP_BREACH.
- decision: BLOCKED with:
  - BOOTCAMP_EXECUTION_DISABLED
  - AUTOMATION_APPROVAL_REQUIRED
  - PROJECTED_STOP_BREACHES_MAX_LOSS
  - INTENT_EXCEEDS_REMAINING_LOSS_BUDGET

Cloud integration:
- ai-trade-the5ers-bootcamp-guard v2 is ACTIVE.
- ai-trade-tick v6 checks evidence-backed unified readiness before broker access.
- request #37 returned BLOCKED_APPROVAL, tradingActivated=false, liveMoneyLocked=true.
- durable ai_trade.compliance_intents enforces one intent per (strategy_id, symbol, closed bar).
- same-bar partial close + TP removal was split: TP removal is deferred to the next closed bar.
- every broker mutation path reserves a compliance intent with visible-SL and written-approval checks.
- projected entry loss uses broker lossTickValue and tickSize; unavailable broker loss geometry fails closed.

Python core regression:
- Bootcamp guard core tests PASS.
- Prop-firm compliance core tests PASS.

## Compliance Mode

Compliance Mode is deliberately not anti-detection stealth.

Allowed:
- closed-bar decisions;
- exactly one intent per bar;
- deterministic cooldown;
- visible broker-side SL;
- bounded retry/backoff;
- audit trail;
- written automation approval gate.

Forbidden:
- random delay to imitate a human;
- fake mouse/keyboard behavior;
- device/browser fingerprint spoofing;
- stealth SL;
- HFT/tick scalping;
- arbitrage prohibited by the firm;
- bypassing anti-abuse or account-review systems.

## Activation gate

Bootcamp challenge execution may only become eligible when all of the following are true:
1. current official rules re-verified;
2. written automation approval evidence exists;
3. MT5 account is verified DEMO challenge account;
4. visible SL is attached;
5. Bootcamp Guard passes projected worst-case loss;
6. generic SafetyGate + Risk Engine pass;
7. Compliance Mode passes;
8. broker symbol/contract preflight passes.

No live/funded-money auto execution is unlocked by this document.


## Unified readiness gate

Supabase view:
`ai_trade.bootcamp_readiness`

Current runtime state:
- provider: THE5ERS
- program: BOOTCAMP
- phase: 1
- target_balance: 5300
- loss_floor: 4750
- automation_approval_verified: false
- execution_enabled: false
- risk_profile_approved: false
- demo_send_enabled: false
- readiness: `BLOCKED_APPROVAL`

Readiness precedence:
1. BLOCKED_APPROVAL
2. BLOCKED_RISK_PROFILE
3. BLOCKED_EXECUTION_DISABLED
4. BLOCKED_DEMO_SEND_DISABLED
5. ELIGIBLE_FOR_DEMO_PREFLIGHT

This is a readiness status only. `ELIGIBLE_FOR_DEMO_PREFLIGHT` still does not mean an order may be sent; broker/account/symbol/stop/compliance gates must pass afterward.


## Evidence-backed governance

Supabase migration `20260927041836_ai_trade_evidence_backed_approval_gates` makes the boolean flags insufficient by themselves:

- `automation_approval_verified=true` requires non-empty written-approval evidence plus a verification timestamp.
- `risk_profile_approved=true` requires non-empty risk-approval evidence, an approval timestamp, and a positive approved `max_total_volume_demo`.
- The legacy spread/daily-loss configuration values are not Founder-approved merely because rows already contain defaults; the unified readiness gate remains blocked until real risk evidence is recorded.
- `max_total_volume_demo` is currently NULL.
- `max_pyramid_adds=0`; no pyramiding promotion exists.

Constraint probes attempted to set the approval booleans true without evidence and were rejected by database check constraints. Final flags remained false.

## Read-only DEMO preflight v2

`ai-trade-demo-preflight` now checks unified readiness before reading broker credentials or contacting MetaApi.

It no longer calls `account.deploy()`. If an eventually eligible MetaApi account is not already deployed, preflight returns `METAAPI_ACCOUNT_NOT_DEPLOYED` without mutating account state.

Current runtime probe #40 returns `BLOCKED_APPROVAL`; therefore broker symbol/contract preflight has deliberately not run yet.
