# CWS AI Trade — Collaboration & Secret Protection V2

Status: canonical collaboration/security architecture.

This supersedes the earlier blanket "Zero Repo Access" idea.

## Founder intent

CWS AI Trade must be able to scale from one Founder to many engineers without exposing:
- trading secrets;
- AI-derived lessons;
- research/backtest know-how;
- broker/customer credentials;
- production secrets.

The correct model is **role-based least privilege**, not "nobody can touch the repo".

## Core principle

Different people get different surfaces.

Not everyone gets everything.
Not everyone gets nothing.

Access is granted by workstream, responsibility, and trust level.

---

## 1. External partner / temporary collaborator

Examples:
- designer;
- contractor;
- agency;
- outside advisor;
- short-term developer;
- broker integration partner.

Default access:
- NO direct access to proprietary Core;
- NO research/backtest vault;
- NO production secrets;
- NO customer financial-account data.

They receive:
- task-specific sandbox;
- sanitized API contracts;
- mock data;
- screenshots/wireframes;
- isolated package or component;
- staging API with redacted responses.

Their output enters CWS AI Trade through review, tests, and an internal merge.

This is where **Zero Repo Access** remains the default.

---

## 2. Internal product engineer

May access:
- CWS AI Trade App;
- dashboard;
- Google login;
- billing;
- account settings;
- public/sanitized service contracts;
- staging environment.

Does not automatically receive:
- proprietary strategy source;
- research corpus;
- private trading lessons;
- production Vault;
- broker credentials.

---

## 3. Internal backend/platform engineer

May access:
- application backend;
- service interfaces;
- auth;
- non-secret schemas;
- staging infrastructure;
- observability relevant to assigned services.

Production access must be separately granted.

No default access to proprietary research unless the job requires it.

---

## 4. Quant / AI research engineer

May access:
- assigned research workspace;
- sanitized/de-identified market/trading datasets;
- experiment harness;
- backtest/forward-validation evidence needed for the assigned project.

Must not receive raw customer identity data.

Promotion to production remains a separate permission.

---

## 5. Core strategy engineer

Small trusted group only.

May access:
- strategy runtime;
- AI trading lessons;
- private research;
- risk heuristics;
- promotion gates;
- model/strategy versioning.

Even this role does NOT automatically get:
- production secrets;
- customer broker passwords;
- billing admin.

---

## 6. Security / release owner

Very small group.

Controls:
- production deployment;
- secret rotation;
- Vault access policy;
- release promotion;
- incident response;
- protected branches;
- environment permissions.

Ordinary engineers should not need persistent production credentials.

---

# Recommended repository/service structure

## A. CWS AI Trade App

Shareable with product engineers.

Contains:
- customer frontend;
- Google login UX;
- dashboard;
- chart;
- billing UI;
- account settings;
- sanitized API clients;
- tests with synthetic data.

## B. CWS AI Trade Platform

Backend/product services.

Contains:
- auth;
- user profile;
- entitlement/quota;
- MT5 account binding metadata;
- billing;
- notification;
- safe API gateway.

## C. CWS AI Trade Core Private

Highly restricted.

Contains:
- proprietary strategy runtime;
- strategy-selection logic;
- risk engine;
- private AI lessons;
- research conclusions;
- promotion rules;
- execution policy.

App/Platform talk to Core through a narrow authenticated interface.

## D. CWS AI Trade Research Vault

Restricted to Founder + approved research team.

Contains:
- backtests;
- failed experiments;
- market-regime observations;
- training/replay evidence;
- post-trade lessons;
- datasets prepared for research.

This is the highest-value intellectual-property layer.

## E. CWS AI Trade Infra Private

Contains:
- production infra definitions;
- security policy;
- deployment configuration;
- secret references;
- incident procedures.

No plaintext secrets in Git.

---

# How large engineering organizations scale

The scaling mechanism is **ownership**, not universal access.

Each team owns a bounded service/module:
- App team;
- Identity team;
- MT5/Broker Integration team;
- Data team;
- Quant Research team;
- Core Strategy team;
- Security/Release team.

An engineer normally works inside their service boundary and consumes other teams through stable APIs/contracts.

## Pull-request flow

engineer branch
-> tests
-> code review
-> CODEOWNER approval
-> CI/security checks
-> staging
-> release approval
-> production

Direct production mutation by ordinary contributors is prohibited.

## Secrets flow

developer
-> receives temporary/scoped credential if required
-> secret manager injects it at runtime
-> credential expires/rotates

Do not distribute shared permanent passwords.

---

# Proprietary learning protection

Treat the following as trade-secret material:
- AI-derived trading lessons;
- failure-pattern knowledge;
- market-regime observations;
- backtest conclusions;
- strategy-selection logic;
- promotion-gate evidence;
- risk heuristics;
- research datasets;
- customer-derived de-identified telemetry used for strategy research.

These should never be present in collaborator-facing mock packages.

A product engineer can build a chart using:
`GET /positions`

without needing to know how the signal was generated.

That separation is the security boundary.

---

# Important limitation

No architecture can guarantee that a trusted engineer with legitimate access to source code cannot remember or copy what they are allowed to read.

The practical defense is:
- minimize access;
- segment repositories/services;
- log access;
- use contractual/IP protections;
- keep the most valuable Core knowledge available only to the smallest trusted group.

The goal is scalable collaboration with bounded exposure, not absolute secrecy through technical fantasy.
