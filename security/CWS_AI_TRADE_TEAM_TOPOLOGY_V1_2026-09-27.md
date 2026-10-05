# CWS AI Trade — Team Topology V1

## Objective

Allow many engineers to contribute safely without giving every engineer access to all source, data, secrets, and trading know-how.

## Teams

### App Team
Owns:
- dashboard
- mobile/web UI
- charting
- customer settings

Consumes Core through contracts only.

### Identity & Account Team
Owns:
- Google login
- profile
- MT5 binding metadata
- quota/entitlement

No strategy access required.

### Broker Integration Team
Owns:
- MT5 connectivity adapters
- broker compatibility
- execution transport
- broker metadata

Does not own strategy decisions.

### Quant Research Team
Owns:
- research harness
- backtest
- forward validation
- experiment reports

No raw customer identity.

### Core Strategy Team
Owns:
- production strategy logic
- risk logic
- trading policy
- promotion gates

Smallest engineering group.

### Data/ML Team
Owns:
- telemetry pipelines
- de-identification
- feature datasets
- offline model/strategy research tooling

No direct permission to promote a strategy to production.

### Security/Release Team
Owns:
- production permissions
- secrets
- deployment gates
- audit
- incident response

## Rules

1. Service ownership is explicit.
2. Cross-team interaction uses APIs/contracts.
3. Production secrets are never stored in source repositories.
4. Research and customer identity datasets remain separated.
5. Strategy promotion requires independent review.
6. External contractors default to sandbox-only access.
7. Internal full-repo access is exceptional, not normal.
8. Access is reviewed and removed when no longer needed.

## Target architecture

Customer
-> CWS AI Trade App
-> Platform/API Gateway
-> Core Strategy Service
-> Broker Integration Service

Data path:
Execution events
-> protected telemetry
-> de-identification
-> Research Vault
-> candidate strategy
-> validation
-> controlled promotion

Billing/referral data never enters strategy decision inputs.
