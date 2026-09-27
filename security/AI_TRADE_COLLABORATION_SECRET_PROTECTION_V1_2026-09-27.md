## Founder rule — Zero Repo Access Collaboration

This rule overrides the earlier assumption that ordinary collaborators may work inside the main repository.

External partners / collaborators must **not** receive direct read access to the proprietary CWS AI Trade repository or Core source.

### Collaboration model

Use a one-way external contribution boundary:

External collaborator
-> Collaboration Gateway / shared workspace
-> submits idea, UI artifact, API proposal, test case, or isolated code snippet
-> Founder/AI review
-> internal implementation into CWS AI Trade
-> sanitized result / API contract returned outward

The collaborator does not:
- clone the Core repository;
- browse repository history;
- read private strategy source;
- inspect research/backtest lessons;
- access trading journals used as proprietary learning data;
- access Supabase/Vault/broker credentials;
- deploy production;
- directly merge to protected branches.

### What collaborators may receive

Only task-specific, sanitized material:
- public/synthetic API contracts;
- mock data;
- screenshots;
- wireframes;
- isolated UI package;
- redacted error logs;
- acceptance criteria;
- test fixtures with no proprietary signal logic.

### Proprietary learning vault

The following are treated as trade-secret material:
- AI-derived trading lessons;
- backtest/post-trade research conclusions;
- failure-pattern knowledge;
- market-regime observations;
- strategy-selection logic;
- promotion-gate evidence;
- private risk heuristics;
- customer-derived de-identified trading telemetry used for research.

These materials must live behind a Founder-controlled private boundary and must never be included in collaborator-facing packages.

### Integration rule

External code is treated as **untrusted input**.

It must be:
1. received outside the Core repo;
2. scanned/reviewed;
3. tested against sanitized contracts;
4. rewritten or cherry-picked internally where appropriate;
5. committed by an authorized internal actor.

No external contributor receives a path back into Core.

### Preferred surfaces

A collaborator-facing surface may be:
- a separate public/private "Contributor Sandbox" repository containing no proprietary Core;
- a ticket/spec system;
- a plugin/workspace that exposes only narrow project contracts;
- a staging API with sanitized responses.

The Core repository remains invisible.

# CWS AI Trade — Collaboration & Secret/Know-How Protection V1

Status: security architecture draft.

Founder requirement:
multiple developers may collaborate, but no collaborator should automatically gain access to:
- production secrets;
- broker credentials;
- customer financial-account credentials;
- proprietary research corpus;
- strategy notebooks/evidence not needed for their task;
- deployment authority.

## Principle: least privilege by workstream

Split access by role.

### UI developer
May access:
- dashboard frontend;
- mocked schemas;
- design tokens;
- public API contracts.

Must not access:
- Vault;
- broker credentials;
- proprietary strategy implementation;
- private research datasets.

### Backend/product developer
May access:
- product APIs;
- non-secret schemas;
- staging data or sanitized fixtures.

Must not automatically access:
- production Vault;
- live broker credentials;
- strategy research corpus.

### Quant/research collaborator
May access only the research package necessary for assigned experiments.
Raw customer identity data must be excluded.

### Release/security owner
Controls:
- protected branch merges;
- production deployment;
- secret rotation;
- Vault access;
- strategy release/promotion.

## Repository architecture

Recommended separation:

`app/`
- customer UI
- dashboard
- auth UI
- billing UI

`contracts/`
- sanitized API schemas/interfaces

`strategy_runtime/`
- versioned execution interface
- minimal runtime package

`research_private/`
- proprietary research, experiments, lessons, private evidence
- restricted access repository or restricted workspace

`infra_private/`
- deployment/security configuration
- restricted

Do not assume a single Git repository is an adequate security boundary for highly sensitive know-how.

## Secrets

Never put in Git:
- MT5 passwords;
- API keys;
- Supabase service role;
- broker tokens;
- private datasets;
- access tokens.

Use Vault/secrets manager and environment-scoped permissions.

## Git collaboration controls

Use:
- private repository;
- role-based collaborator permissions;
- protected main/release branches;
- pull requests;
- required reviews;
- CODEOWNERS for sensitive paths;
- no direct production deploy for ordinary contributors;
- separate staging/prod secrets;
- audit logs;
- secret scanning.

## IP protection reality

No technical system can guarantee that a person who legitimately reads proprietary source code can never copy what they saw.

Therefore the strongest practical design is:
- collaborators receive only the minimum code/data required;
- proprietary strategy logic and research are isolated behind an API or separate private repo/service;
- most UI/product collaborators never receive the core strategy source at all.

The goal is not “trust everyone.”
The goal is “they never receive what they do not need.”
