# AI-TRADE — Historical Research to True Forward Shadow — 2026-09-27

## Outcome

The project did not force a historical PASS.

Instead it moved through:
1. maximum TF-004 robustness testing;
2. preregistered alternative strategy suites;
3. sealed holdout;
4. rolling causal OOS;
5. true forward-only shadow trading.

No broker order was sent.
No live/funded path was unlocked.
No hard-risk number was auto-approved.

## Historical research ladder

### TF-004

Maximum robustness validation covered:
- 14 markets;
- longest practical public daily history (~10 to ~99 years);
- OOS / walk-forward;
- 27 parameter combinations;
- cost stress through 5x;
- regimes and start-date sensitivity;
- 1D / 3D / 5D;
- 2,000-path Monte Carlo;
- next-open execution;
- gap-aware stops;
- winner concentration;
- crypto feed cross-check;
- 1H / approximate 4H validation.

Verdict:
`NOT VALIDATED FOR AUTONOMOUS DEMO`.

### First preregistered suite

Candidates:
- TF-005A
- TF-006A
- TF-007A

Runtime request #79:
`NO_VALIDATION_CANDIDATE`.

Final 20% holdout was not opened.

### Diversified portfolio suite

Candidates:
- TF-008A
- TF-009A
- TF-010A

Runtime request #80:
`NO_VALIDATION_CANDIDATE`.

All three produced positive validation portfolio R, but every candidate failed at least one preregistered breadth/concentration gate.

No gate was relaxed after results.

### TF-011A sealed holdout

TF-011A changed portfolio construction only and froze its selected markets before the final holdout.

Runtime request #81:
`HOLDOUT_FAIL`.

Despite the fail:
- 10 bps portfolio: +5.4044R
- max drawdown: 1.8641R
- return/drawdown: 2.899
- 20 bps portfolio: +5.1472R
- 6/9 markets positive
- 3/4 classes positive

Fail reasons:
- market contribution dominance 37.29% > 30%
- class contribution dominance 53% > 50%

### TF-012A rolling causal OOS

Each test year selected markets using only the prior five full years.

Runtime request #82:
`ROLLING_OOS_FAIL`.

Evidence:
- 17 rolling OOS years
- 10 bps aggregate: +5.7656R
- max drawdown: 2.0453R
- return/drawdown: 2.819
- 20 bps aggregate: +4.9992R
- latest five years: +1.9668R

Fail reasons:
- 8/17 positive years = 47.06% < 60%
- only 2/4 class sleeves positive
- class dominance 63.87% > 50%
- market dominance 35.30% > 30%

Conclusion:
continuing to adjust historical gates or parameters until a PASS would be overfit.

## Generic MT5 DEMO cloud investigation

Official MetaTrader documentation confirms demo accounts exist and can be opened without funding.

Official MetaApi documentation provides an MT5 DEMO-account creation API, but its REST API requires a MetaApi authorization token.

Runtime secret-presence diagnostic request #83:
- METAAPI_TOKEN: missing
- METAAPI_ACCOUNT_ID: missing
- secret values were not exposed

Additional cloud paths tested:
- Replit cloud app: blocked by `requires_active_subscription`; no purchase made.
- Firecrawl interactive browser: blocked by insufficient credits.
- Firecrawl browser-agent probe: source could not initialize due invalid browser token.
- Plugin directory: no relevant installed/installable MT5/MetaApi connector was discovered.

Therefore an actual external MT5/MetaApi account cannot be legitimately created from the currently authorized cloud surfaces without either:
- an interactive browser/account signup path, or
- a MetaApi account token supplied through its Web application.

No identity was fabricated and no CAPTCHA/OTP/KYC was bypassed.

## TF-013A true forward shadow

Preregistered:
- `research/TF_013A_FORWARD_SHADOW_PROTOCOL_2026-09-27.md`
- `strategies/TF_013A_FORWARD_DIVERSIFIED_TREND.json`

Strategy:
- 14 markets
- daily closed bars
- 21-day return + 252-day return + SMA10/200 majority vote
- monthly review
- next-bar-open entry/reversal
- fixed emergency stop 4 ATR(20)
- gap-aware stop
- no target
- no pyramiding

Critical forward rule:
**historical bars warm indicators only. Historical trades are never backfilled.**

Supabase:
- function: `ai-trade-forward-shadow` v1
- state: `ai_trade.forward_shadow_state`
- trades: `ai_trade.forward_shadow_trades`
- run journal: `ai_trade.forward_shadow_runs`

Runtime request #84:
- 14/14 WARMED
- 0 historical trades
- brokerOrders=false
- liveMoneyLocked=true

Immediate repeat request #85:
- 14/14 NO_NEW_CLOSED_BAR
- 0 duplicate trades
- persistent state retained

Autonomous cron:
- job: `ai-trade-forward-shadow-daily`
- schedule: `15 3 * * *` UTC
- active: true

Forward metrics record:
- gross R
- synthetic 10 bps R
- synthetic 20 bps R

## Current boundary

The historical research request has been pushed to a point where further tuning is more likely to create data-mining bias than independent evidence.

The system is now collecting real forward evidence autonomously.

External MT5 DEMO execution remains blocked by missing legitimate account/API authorization, not by missing trading code.

The5ers challenge execution remains independently blocked by:
- written automation approval not verified;
- risk profile not Founder/evidence approved.

Live/funded money remains hard locked.


## MT5 MetaQuotes DEMO canonical account recovered — 2026-09-27

A previously completed cloud path was rediscovered in runtime evidence. Do not create another demo account unless this canonical account is explicitly retired.

Canonical registry:
- account_login: `113247784`
- server: `MetaQuotes-Demo`
- account_type: `DEMO`
- active: true
- master password secret: present in Supabase Vault
- investor password secret: present in Supabase Vault
- source: `github-actions-oidc`
- source run: `36309825439`
- last_verified_at: `2026-09-27T09:35:13.658419+00:00`

GitHub Actions run `36309825439`, job `108593487045`:
- workflow job: `protocol-probe`
- conclusion: SUCCESS
- transport probe: MT5_PROTOCOL_READY
- WebTerminal server build: 6230
- demo creation: SUCCESS
- login: 113247784
- server: MetaQuotes-Demo
- is_demo: true
- is_real: false
- trade_allowed: true
- balance: 100000.0 demo units
- leverage: 100
- credentials stored to Supabase Vault
- password/investor password were not printed

Current direct Deno protocol probe also independently passed:
- request #116
- `MT5_PROTOCOL_READY`
- server build 6230
- AES session key 32 bytes
- initCode=0
- no account creation
- no broker order

Canonical cloud functions:
- `ai-trade-mt5-demo-bootstrap` v6 ACTIVE
- `ai-trade-mt5-vault-ingest` v1 ACTIVE
- `ai-trade-mt5-protocol-probe` v5 ACTIVE
- `ai-trade-mt5-demo-validate` v2 ACTIVE
- `ai-trade-forward-shadow` v1 ACTIVE

A temporary manual credential-onboarding path created during continuation was disabled after canonical Vault state was found. Its one-time tokens were revoked and redundant temporary tables removed.

### Execution boundary

A direct attempt from the current ChatGPT tool surface to log into the MT5 account was blocked by the platform safety layer. No attempt was made to bypass that block via alternate payloads or indirect execution.

Therefore:
- MT5 DEMO account creation = COMPLETE with runtime evidence.
- MT5 DEMO credentials = securely stored in Supabase Vault.
- direct broker-order execution from this chat = not executed.
- forward-only TF-013A shadow journal remains the active autonomous validation path.

Current TF-013A:
- state rows: 14
- closed forward trades: 0
- run rows: 2
- cron: `15 3 * * *` UTC, ACTIVE.

The5ers and risk gates remain independent:
- readiness: BLOCKED_APPROVAL
- automation_approval_verified: false
- risk_profile_approved: false
- demo_send_enabled: false
- max_total_volume_demo: NULL
- live/funded money: HARD LOCKED


## MT5-compatible shadow broker layer — 2026-09-27

Because the current ChatGPT tool surface blocks direct financial-account login/order execution, AI-TRADE now has an autonomous shadow broker layer instead of trying to bypass that restriction.

Runtime components:
- Edge Function: `ai-trade-shadow-broker-reconcile` v1 ACTIVE.
- Tables:
  - `ai_trade.shadow_broker_orders`
  - `ai_trade.shadow_broker_positions`
  - `ai_trade.shadow_broker_runs`
- Cron: `ai-trade-shadow-broker-reconcile-daily`
- Schedule: `20 3 * * *` UTC, five minutes after `ai-trade-forward-shadow-daily` at `15 3 * * *` UTC.

Execution model:
- mirrors only true TF-013A forward entries/exits;
- stable client_order_id makes reconciliation idempotent;
- every entry must carry a visible stop;
- one normalized synthetic volume unit is used only for execution lifecycle testing;
- account risk remains unapproved;
- no pyramiding;
- brokerOrders=false;
- liveMoneyLocked=true;
- reversal / multiple broker mutations on the same symbol+bar are flagged `MULTI_MUTATION_SAME_BAR`, not silently accepted.

Runtime request #120:
- status: `SHADOW_BROKER_RECONCILED`
- orders inserted: 0
- total shadow orders: 0
- open shadow positions: 0
- flagged bars: 0

Zero orders is expected and is not treated as a trading PASS: TF-013A has not yet produced a new forward trade since its warm checkpoint.

Idempotency self-test:
- first fixture insert: 1
- duplicate insert with same client_order_id: 0
- self-test rows after cleanup: 0

Access:
- anon SELECT on shadow_broker_orders: false
- authenticated SELECT on shadow_broker_orders: false

Supabase advisors after DDL did not report a new AI-TRADE-specific security finding for these tables. Existing advisor findings concern unrelated public CWS tables / pg_net placement / leaked-password protection.

This layer is an execution-rehearsal substitute, not a claim that real broker orders were sent.


## Autonomous TF-013A forward evaluator — 2026-09-27

A preregistered promotion gate now evaluates only true forward evidence.

Protocol:
`research/TF_013A_FORWARD_PROMOTION_GATE_2026-09-27.md`

States:
- `COLLECTING`
- `FORWARD_REJECT`
- `FORWARD_CANDIDATE`

Minimum evidence before any pass/reject decision:
- 50 closed forward trades;
- 120 elapsed calendar days from the first closed forward trade;
- 8 markets with at least one closed forward trade.

Frozen candidate gates at synthetic 10 bps:
- aggregate net R > 0;
- expectancy R > 0;
- profit factor R > 1;
- return/max-drawdown R > 0.5;
- at least 5 positive markets;
- single-market positive contribution dominance <= 40%.

Synthetic 20 bps:
- aggregate net R > 0.

Execution-integrity gates:
- zero same-bar multi-mutation flags;
- zero shadow entries without visible stop;
- duplicate client_order_id prevented by unique database constraint.

These are research evidence gates only. They do not approve account-level risk.

Runtime:
- Edge Function: `ai-trade-forward-evaluate` v1 ACTIVE.
- request #121: HTTP 200.
- current state: `COLLECTING`.
- closed trades: 0.
- integrity gates currently PASS.
- performance gates remain unevaluated/false because there is no forward sample yet.

Autonomous schedule:
- 03:15 UTC — forward signal engine.
- 03:20 UTC — shadow broker reconcile.
- 03:25 UTC — forward evaluator.

Canonical latest state:
`ai_trade.forward_validation_readiness`

The evaluator is deliberately read-only with respect to execution gates:
it never flips `risk_profile_approved`, `demo_send_enabled`, The5ers approval, or live/funded controls.
