# AI-TRADE — Public / Private Security Boundary

## Critical current fact

As of 2026-09-27, GitHub repository `trankhanhduy1508-maker/AI-TRADE` is PUBLIC.

Therefore:
- every committed file is readable by anyone;
- CODEOWNERS does not protect confidentiality;
- branch protection does not protect confidentiality;
- hiding credentials in another branch does not protect confidentiality.

## Public-safe material

May remain public if Founder chooses:
- generic dashboard UI;
- non-secret frontend components;
- sanitized API contracts;
- generic documentation;
- mock fixtures with no customer data;
- installation instructions without secrets.

## Must be private

Do not place in a public repository:
- proprietary research corpus;
- detailed strategy research notes that constitute trade secrets;
- private experiment evidence not intended for disclosure;
- customer trading history tied to identity;
- broker credentials;
- MT5 master/investor passwords;
- API keys/tokens;
- Supabase service-role credentials;
- Vault exports;
- private partner commercial terms;
- security recovery material.

## Recommended target architecture

### Repo A — AI-TRADE-App
Can be shared with UI/product collaborators.
Contains:
- dashboard;
- Google login UI;
- billing UI;
- sanitized API contracts;
- tests with synthetic fixtures.

### Repo B — AI-TRADE-Core-Private
Founder-only or very small trusted team.
Contains:
- proprietary strategy/runtime;
- research engine;
- promotion gates;
- private lessons/evidence;
- risk engine.

### Service boundary
App talks to Core only through a narrow authenticated API.

Collaborators can build the app without receiving Core source.

## Current required action

Before inviting an untrusted collaborator:
1. make the existing repository private OR create a new private Core repository;
2. move strategy/research/private evidence behind the private boundary;
3. rotate any secret that was ever committed;
4. only then grant least-privilege collaborator access.

This is a security requirement, not an optional cleanup.
