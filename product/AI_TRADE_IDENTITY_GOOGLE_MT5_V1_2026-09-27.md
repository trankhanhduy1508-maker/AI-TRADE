# AI-TRADE — Identity, Google Login & MT5 Binding V1

Status: architecture direction.

## Login

Google Sign-In is the preferred first customer login.

Reasons:
- low onboarding friction;
- no SMS OTP cost;
- works for international expansion;
- users already understand the flow.

Phone verification can be added later for:
- account recovery;
- higher-risk actions;
- anti-abuse;
- regulated identity workflows.

Google identity alone is not a financial-account identity.

## Anti-abuse

Free quota must not be keyed only to Google email.

A user can own many Google accounts.

Quota/account eligibility should be associated with:
- AI-TRADE user id;
- and a normalized broker account identity.

Recommended MT5 identity key:
`broker/server + MT5 login`

The same MT5 identity must not receive unlimited new-user quota by being attached to new Google accounts.

## MT5 binding

Customer-facing configuration should feel familiar to MT5 users:
- broker/server;
- MT5 login/account number;
- account type;
- connection state.

Credential handling:
- never store MT5 master password in plaintext;
- never commit credentials to GitHub;
- use secrets/Vault;
- use read-only/investor credentials wherever read-only access is sufficient;
- trade-capable credentials only when execution is genuinely required and permitted.

Customer should see account metadata, not secrets.

Suggested visible fields:
- Broker
- Server
- MT5 account/login
- DEMO / REAL
- Connected / Disconnected
- Last verified
- Currency
- Balance / Equity when available

## Rebinding

If a customer changes Google identity:
- do not create a second independent free entitlement for the same MT5 identity;
- support an explicit transfer/rebind process;
- audit old/new owner mapping;
- require stronger verification for a REAL account.

## Separation of concerns

Google login = product identity.
MT5 account = trading-account identity.
Risk/billing = account-specific policy.
Secrets = Vault only.
