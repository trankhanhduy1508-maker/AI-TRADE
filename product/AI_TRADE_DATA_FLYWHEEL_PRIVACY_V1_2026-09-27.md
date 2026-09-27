# AI-TRADE — Data Flywheel & Privacy V1

Status: product/privacy design direction, not legal advice.

## Goal

Use consented product and trading telemetry to improve:
- strategy research;
- execution quality;
- product UX;
- support;
- optional personalization.

Do not allow production strategy to retrain itself directly from raw live user data.

## Three separate data purposes

### 1. AI improvement telemetry

Examples:
- symbol;
- timeframe;
- strategy id;
- entry/exit;
- spread;
- slippage;
- stop behavior;
- normalized R result;
- market regime tags;
- broker class;
- execution timing.

Prefer pseudonymized identifiers.

### 2. Product analytics

Examples:
- features used;
- dashboard sections opened;
- chart timeframes;
- journal usage;
- free quota usage;
- errors and latency.

### 3. Advertising / commercial personalization

Keep separate from AI improvement.

Do not sell or expose raw trading history, balances, credentials, or account identifiers to advertisers/brokers.

Any future advertising profile should use:
- explicit separate consent;
- coarse segments;
- aggregation/de-identification where possible;
- a user-accessible opt-out.

## Consent UX

Do not pre-check boxes.

Keep purposes distinct, for example:
- [ ] Allow de-identified trading telemetry to improve AI research.
- [ ] Allow product usage analytics to improve AI-TRADE.
- [ ] Allow personalized broker/offers/advertising.

The advertising consent must not be silently bundled into AI-improvement consent.

## Learning pipeline

Live telemetry
-> protected data warehouse
-> analysis / anomaly detection
-> candidate strategy
-> preregistration
-> backtest
-> walk-forward / holdout
-> paper
-> shadow
-> forward gate
-> versioned release

Never:
live user data -> direct self-edit of production strategy.

## Data minimization

Do not collect data because it “might be useful someday.”

Collect only fields tied to a stated product, research, security, or billing purpose.

Secrets and authentication material are never training data.
