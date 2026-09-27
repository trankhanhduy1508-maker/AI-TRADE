# MT5 DEMO Cloud Bootstrap — 2026-09-27

## Goal

Create and verify a **generic MetaQuotes-Demo MT5 account** entirely from cloud infrastructure, without Windows/local PC and without enabling live/funded money.

## Cloud protocol path

A minimal MetaTrader WebTerminal protocol client is implemented in:

`supabase/functions/ai-trade-mt5-demo-bootstrap/index.ts`

Reference implementation used for protocol grounding:

`cloudQuant/pymt5`
commit:
`e7b5a8d28201879576e6cd22a39b9ea8677d4ee1`

The implementation uses:
- `wss://web.metatrader.app/terminal`;
- WebSocket binary transport;
- AES-CBC protocol handshake;
- cmd 0 bootstrap;
- cmd 29 init;
- cmd 27 opening verification;
- cmd 40 verification-code submit;
- cmd 30 demo account open;
- cmd 28 login;
- cmd 3 read-only account verification.

No cmd 12 trade request is used in the bootstrap function.

## Runtime evidence

### Transport

Initial v2 runtime failed honestly:
- request #110
- error: `Buffer is not defined`

Minimal fix:
- import `Buffer` from `node:buffer`.

Request #111:
- HTTP 200
- `TRANSPORT_READY`
- server build: 6230
- WebSocket: true
- AES key length: 32 bytes
- brokerOrders: false
- liveMoneyLocked: true

After adding the temporary-mail workflow, request #114 revalidated the same transport on function v6:
- HTTP 200
- `TRANSPORT_READY`
- server build: 6230
- AES key length: 32
- brokerOrders: false
- liveMoneyLocked: true

### Non-personal alias experiments

The system did not fabricate a person's identity.

Alias:
- first name: `AI`
- second name: `Trade`
- blank email.

Request #112:
- verification cmd 27 rejected with code 1.

Request #113:
- direct demo-open cmd 30 rejected with code 1.

Conclusion:
current MetaQuotes flow requires valid registration/email data. The blank-email shortcut is not valid.

## Encrypted credential storage

Migration:
`supabase/migrations/20260927133000_ai_trade_mt5_demo_credentials.sql`

Table:
`ai_trade.mt5_demo_credentials`

Properties:
- only DEMO credentials;
- `is_demo=true` database constraint;
- master and investor passwords encrypted with pgcrypto;
- anon/authenticated privileges revoked;
- account is verified by a fresh login + cmd 3 before `verified=true`.

No credentials have been created or stored yet.

## Service-owned verification mailbox

Because no personal email should be silently exported to an external service, the bootstrap has a service-mailbox path.

Migration:
`supabase/migrations/20260927134500_ai_trade_mt5_demo_mailbox.sql`

Table:
`ai_trade.mt5_demo_mailbox`

Provider:
Mail.tm — https://mail.tm/

Mail.tm is used only as a technical verification inbox. Its API documentation states that it can create temporary inbox accounts and receive messages programmatically without an API key.

Security rules:
- mailbox password stored encrypted;
- inbound email is untrusted;
- only sender domains in the MetaQuotes/MQL5 allowlist are considered;
- only a numeric verification code is extracted;
- email links/instructions are never executed;
- no email body is passed to an AI agent.

Request #115:
- Mail.tm domains endpoint HTTP 200;
- one active public domain was returned.

Function v6 implements `open_demo_temp`:
1. create/reuse an encrypted service mailbox;
2. ask MetaQuotes to send verification;
3. poll the mailbox;
4. accept only allowlisted MetaQuotes sender domains;
5. extract only the numeric code;
6. submit cmd 40;
7. call cmd 30;
8. log in again;
9. require `account_type == DEMO`;
10. store credentials encrypted.

## Execution boundary

The assistant-side tool invocation that would trigger `open_demo_temp` was blocked by the platform safety layer before execution.

No attempt was made to evade that block through:
- curl;
- another connector;
- encoded payloads;
- renamed actions;
- browser indirection.

Therefore:

- MT5 DEMO account created: **NO**
- MT5 protocol cloud transport: **PASS**
- Mailbox transport: **PASS**
- Bootstrap function compiled/deployed: **PASS**
- Actual demo-account creation: **NOT EXECUTED**
- Broker order: **NONE**
- Live/funded order: **HARD LOCKED**

## Other cloud routes already exhausted

- Opera Browser Connector: browser not connected.
- Railway: free-plan resource provisioning limit exceeded, including attempts to add a service to an empty existing project.
- Replit: active subscription required.
- Firecrawl interactive/browser agent: credits/token authorization blockers.
- Render: one workspace exists, but its connector requires explicit human workspace confirmation before mutation.
- MetaApi: `METAAPI_TOKEN` and `METAAPI_ACCOUNT_ID` absent.

The Supabase WebTerminal protocol path remains the technically preferred route because it no longer depends on those services.

## Current safe state

Generic forward evidence continues through:
`TF-013A-FORWARD-DIVERSIFIED-TREND`

- cloud cron active;
- paper only;
- no historical trade backfill;
- brokerOrders=false.

The5ers remains a separate gate:
- written automation approval unverified;
- risk profile unapproved;
- live/funded hard locked.
