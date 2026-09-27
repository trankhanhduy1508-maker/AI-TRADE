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
