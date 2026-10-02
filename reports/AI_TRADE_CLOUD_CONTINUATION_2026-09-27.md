# AI-TRADE Cloud Continuation — 2026-09-27

## Scope

Continuation only from the existing checkpoint on branch `codex/p0-covel-knowledge-audit`.

No Windows/local PC, no PC Commander, no new branch, no live/funded-money execution, no stealth/evasion, no fake approval, and no invented hard-risk number.

## A. Source/runtime verification

Initial verified branch HEAD for this continuation:
`25cc2526d661102c6ab76d88eb4b10fb96a50dbd`.

A source/runtime drift was found:
- deployed Supabase `ai-trade-tick` v4 already enforced `risk_profile_approved`;
- the GitHub mirror of the same function was stale and lacked that gate.

Resolution:
- preserve the safer deployed behavior;
- synchronize GitHub forward;
- extend it with Bootcamp/compliance/evidence-backed gates.

## B. 13-market autonomous paper

Supabase Edge Function:
`ai-trade-multiasset-paper` v1.

Cron:
- job: `ai-trade-multiasset-paper-daily`
- schedule: `30 1 * * *` UTC
- active: true

Runtime probe #34:
- HTTP 200
- 13/13 `NO_NEW_CLOSED_BAR`
- persistent checkpoints retained
- no duplicate paper trade
- `brokerOrders=false`
- `pyramiding=false`

Current paper journal:
- 13 state rows
- 0 closed forward trades at this checkpoint

The cron had no scheduled-run history yet because it was created after the current day's 01:30 UTC slot. This is not presented as a cron execution PASS.

`GROSS_ONLY` markets remain gross-only and must not be represented as net profitability.

## C. Bootcamp monitor

`ai-trade-the5ers-bootcamp-guard` v2 adds read-only monitor fields:
- phase
- initial/target/floor
- progress to target
- distance to target/floor
- remaining loss budget
- projected equity at stop
- projected remaining loss budget
- candidate-relative near-floor state
- alert state

Runtime:
- #35: 5000/5000, projected SL loss 50 -> blocked by execution + approval gates; alert NORMAL.
- #36: 4800/4780, projected SL loss 40 -> projected equity 4740 -> correctly blocked for floor breach.
- #41: post-migration monitor regression -> HTTP 200, same fail-closed state.

No broker order path exists in the monitor.

## D. Prop Firm Compliance integration

Migration:
`20260927040939_ai_trade_compliance_intent_guard`.

Durable reservation:
`ai_trade.compliance_intents`
with unique key:
`(strategy_id, symbol, bar_stamp)`.

Purpose:
- closed-bar-only broker mutations;
- exactly one broker intent per strategy/symbol/bar;
- deterministic next-bar cooldown;
- visible SL required;
- written approval required;
- audit event for each compliance decision;
- no random human-like delay;
- no fake mouse/keyboard;
- no fingerprint/device spoofing;
- no stealth SL.

A duplicate reservation probe verified:
- first reservation: 1 row
- second same-bar reservation: 0 rows
- probe rows then explicitly cleaned; 0 remained.

Tick v6 static/runtime verification found 6 current broker mutation call sites and all 6 are behind `reserveComplianceIntent`.

A previous same-bar double mutation in `PARTIAL_THEN_TRAIL` was removed:
- partial close occurs on one closed bar;
- TP removal is deferred to the next closed bar.

## E. Current The5ers rules re-check

Official The5ers pages were re-checked on 2026-09-27.

Confirmed for the Bootcamp challenge:
- Step 1: 5000, target +6%, max loss 5%.
- Step 2: 10000, target +6%, max loss 5%.
- Step 3: 15000, target +6%, max loss 5%.
- challenge evaluation runs on demo accounts;
- unlimited evaluation time;
- no 3% daily pause during the three challenge phases;
- inactivity beyond 30 consecutive days may close the account;
- visible stop loss is required for automated trading;
- stealth stop loss is prohibited.

Current English Terms page displays last update Aug. 3, 2026 and still requires written notification plus prior written approval before Automated Trading Software is used.

The canonical rules snapshot was corrected. The earlier repo wording that described the Terms as dated 2026-09-23 was not retained.

## F. Written automation approval

Targeted Gmail searches for:
- The5ers / The5%ers
- approval / approved
- automation / automated
- EA / Expert Advisor
- Automated Trading Software

returned no matching written approval evidence.

Therefore:
`automation_approval_verified=false`.

No FAQ allowance was treated as written approval.

## G. Evidence-backed risk/approval governance

Migration:
`20260927041836_ai_trade_evidence_backed_approval_gates`.

Automation approval:
- boolean true is rejected unless non-empty approval evidence and verification timestamp exist.

Risk profile:
- boolean true is rejected unless non-empty risk evidence, approval timestamp, and positive `max_total_volume_demo` exist.

Constraint probes attempted the unsafe boolean-only transitions and the DB rejected them.

Current state:
- `automation_approval_verified=false`
- `automation_approval_evidence=NULL`
- `risk_profile_approved=false`
- `risk_profile_approval_evidence=NULL`
- `max_total_volume_demo=NULL`
- `max_pyramid_adds=0`
- `readiness=BLOCKED_APPROVAL`

Legacy config rows still contain older placeholder spread/daily-loss values. They are not Founder-approved policy and cannot activate execution while the evidence-backed readiness gate remains blocked.

Tick v6 removed the inherited hard-coded `volume > 0.01` execution cap as a pseudo-policy. Total volume now requires an explicitly approved `max_total_volume_demo`.

## H. MT5 DEMO Bootcamp preflight

`ai-trade-demo-preflight` v2:
- checks unified readiness before reading broker credentials or contacting MetaApi;
- no longer auto-deploys a MetaApi account;
- if eventually eligible but account is not already deployed, returns `METAAPI_ACCOUNT_NOT_DEPLOYED`.

Runtime #40:
- HTTP 200
- `BLOCKED_APPROVAL`
- `tradingActivated=false`
- `liveMoneyLocked=true`

Therefore the broker-facing DEMO preflight was deliberately not run. This is the correct blocker, not a preflight PASS.

## I. Controlled DEMO execution

Not reached.

Current hard blockers:
1. real written The5ers automation approval evidence;
2. Founder/evidence-approved risk profile, including total DEMO volume;
3. then explicit execution/demo-send gates;
4. then DEMO account/symbol/contract/margin preflight;
5. then Bootcamp Guard + generic safety/risk + compliance + duplicate/reconciliation gates.

Live/funded-money automation remains hard locked.

## Security note

The `ai_trade` schema currently does not grant schema usage or table SELECT/INSERT/UPDATE privileges to Supabase `anon` or `authenticated` roles.

RLS is not enabled on these private-schema tables, so RLS remains defense-in-depth work rather than a demonstrated public exposure at this checkpoint. No unrelated CWS public-schema security setting was changed.


## J. Written approval request sent

A real approval request was sent to The5ers Support at `help@the5ers.com`.

Subject:
`Request for written approval to use owner-developed automated trading software in Bootcamp`

Gmail sent message id:
`1a0e12ba86e3e300`

The request explicitly disclosed:
- owner-developed automated trading software;
- closed-bar-only decisions;
- one intent per strategy/symbol/bar;
- broker-visible protective stop loss;
- no stealth stop loss;
- no HFT/tick scalping;
- no prohibited arbitrage;
- no emulator;
- no copied third-party signals/shared third-party EA;
- duplicate suppression and audit trail;
- execution remains locked until written approval is verified.

Sending the request is NOT approval evidence. `automation_approval_verified` remains false until a written affirmative response is received and verified.
