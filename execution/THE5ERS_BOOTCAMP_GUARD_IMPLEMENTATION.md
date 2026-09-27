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

Synthetic normal-state probe:
- request id 32
- balance/equity: 5000/5000
- projected SL loss: 50
- target: 5300
- floor: 4750
- remaining loss budget: 250
- decision: BLOCKED
- reasons:
  - BOOTCAMP_EXECUTION_DISABLED
  - AUTOMATION_APPROVAL_REQUIRED

Synthetic near-floor probe:
- request id 33
- balance/equity: 4800/4780
- projected SL loss: 40
- projected equity at SL: 4740
- remaining loss budget: 30
- decision: BLOCKED
- additional reasons:
  - PROJECTED_STOP_BREACHES_MAX_LOSS
  - INTENT_EXCEEDS_REMAINING_LOSS_BUDGET

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
