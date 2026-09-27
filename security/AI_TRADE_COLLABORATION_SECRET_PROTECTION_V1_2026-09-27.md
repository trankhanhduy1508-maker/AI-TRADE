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
