# MT5 WebTerminal Demo Protocol Research — 2026-09-27

## Scope

Research-only reverse engineering of the **official public MetaTrader WebTerminal client** to determine whether AI-TRADE can create and connect a generic MT5 DEMO account from cloud infrastructure without a local PC.

Hard boundaries:

- DEMO only.
- No live/funded trading.
- No fabricated identity.
- No CAPTCHA/OTP bypass.
- No password/token committed to GitHub.
- No broker order sent.
- Any account-creation path must fail closed if identity confirmation is required.

## Official WebTerminal bootstrap

Observed public bootstrap:

`https://trade.mql5.com/trade?version=5`

Current assets redirect/use:

`https://metatraderweb.app`

Observed bootstrap configuration:

- `trade_server = MetaQuotes-Demo`
- `login = 0`
- `version = 5`
- `script_version = 134347398560000000`
- GWT node candidates include `6,5,3,2,1,8,4`

Current shared JavaScript bundle:

`https://metatraderweb.app/trade/res/js/mt4.en.js?t=134347398560000000`

The historical filename `mt4.en.js` currently contains shared logic for MT4 and MT5 WebTerminal flows.

## Server discovery

Public endpoints observed in the official client:

- `GET https://metatraderweb.app/trade/servers?version=5&all=1`
- `GET https://metatraderweb.app/trade/suggest?all=1`

The MT5 list includes `MetaQuotes-Demo` and many public broker DEMO/Trial servers.

Examples observed:

- MetaQuotes-Demo
- FPMarkets-Demo
- Eightcap-Demo
- Alpari-MT5-Demo
- Deriv-Demo
- BlackBullMarkets-Demo
- Ava-Demo 1-MT5
- XM.COM-Demo
- Exness-MT5Trial
- FBS-Demo
- Darwinex-Demo

Presence in the directory does **not** prove that WebTerminal registration is enabled for the current egress.

## Pre-account handshake

The official client performs an HTTP form POST before opening the registration WebSocket:

`POST https://metatraderweb.app/trade/json`

Content-Type:

`application/x-www-form-urlencoded`

Fields:

- `login=0`
- `trade_server=<server>`
- `version=5`
- optional `demo_type`
- optional `demo_leverage`
- optional `gwt=<nearest GWT node suffix>`

Expected response fields can include:

- `enabled`
- `signal_server`
- `trade_server`
- `version`
- `company`
- `key`
- `token`
- `ssl`
- `demo_type`
- `demo_leverage`
- `geo`
- `ping`
- `gwt_servers`

The WebTerminal proceeds to account registration only when the returned capability state permits it and an authorization token is available.

## WebSocket stage

When accepted, the client opens:

`wss://<signal_server>/`

Observed framing:

Outer frame:
- uint32 payload length at offset 0, little-endian
- uint32 constant 1 at offset 4, little-endian
- payload begins at offset 8

Inner command frame:
- random byte at offset 0
- random byte at offset 1
- uint16 command ID at offset 2, little-endian
- payload begins after the 4-byte command header

Response handling:
- outer 8 bytes stripped first
- response command is uint16 at offset 2 LE
- response status/error byte at offset 4
- command payload starts after byte 5

Observed logical command aliases in the minified client:
- token/auth command: `Rq`
- MT5 initialization: `Pq`
- MT4 initialization: `Mq`
- account-group / demo-type metadata: `Qm`
- MT5 demo-create: `Sk`
- MT4 demo-create: `Ok`
- confirmation follow-up: `Rm`

The numeric command constants were not needed for the current fail-closed handshake gate and have not been promoted into execution code.

## Account form

Observed WebTerminal form fields:

- first name
- second name
- email
- phone country code
- phone number
- hedge/netting selection
- account type/group
- deposit
- leverage
- terms/acceptance checkbox

The client serializes the MT5 registration payload into a fixed-size binary structure (observed allocation: 1660 bytes).

Fields visible in the serializer include:

- combined first/second name
- group/account type
- email/phone-related fields
- deposit as Float64
- leverage as Uint32
- flags
- host/company strings
- confirmation-related fields

## Confirmation behavior

The official client explicitly handles confirmation failures:

- error 7: invalid email confirmation code
- error 8: invalid phone confirmation code

UI strings observed include:

- Email confirmation
- Phone confirmation
- confirmation code sent to specified address
- confirmation code sent to specified phone number

Account-type flags are inspected by the UI to determine whether an email and/or phone confirmation step is required.

AI-TRADE rule:

**Never fabricate an email/phone identity or bypass a confirmation step.**

If the selected demo server requires a code, execution must stop at that identity boundary.

## Registration result

For the MT5 demo-create response, the client parses:

- error/result code
- login
- account password
- investor password

Success is indicated by a zero error code.

Passwords/tokens must never be written to GitHub, ordinary logs, chat messages, or public probe endpoints.

## Runtime evidence from current cloud egress

Supabase project:

`oziktadfeenydvgobudr`

Region:

`ap-south-1` (Mumbai)

Observed WebTerminal geo metadata also resolved the Edge Function egress to Mumbai, India.

Capability probes:

- MetaQuotes-Demo
- FPMarkets-Demo
- Eightcap-Demo
- Deriv-Demo
- Alpari-MT5-Demo
- Exness-MT5Trial
- BlackBullMarkets-Demo
- XM.COM-Demo
- and additional public DEMO servers

Common result:

- HTTP 200
- server metadata resolves
- `key` is returned
- `enabled=false`
- no authorization `token`
- signal server resolves to `gwt6.mql5.com:443`

Variants tested:

- with and without `gwt=6`
- GET bootstrap before POST
- session cookie retained
- corrected cookie parsing
- browser-like User-Agent, Origin, Referer, Fetch headers

Result remained unchanged.

Conclusion:

**The current Supabase Mumbai egress is not being granted a WebTerminal authorization token.**

This is an external WebTerminal capability/egress blocker, not a missing POST field in the current client implementation.

## Other cloud paths tested

- Replit: requires active subscription.
- Firecrawl interactive browser: insufficient credits.
- Firecrawl browser-agent: browser initialization authorization failure.
- AppDeploy: daily credit limit.
- Railway agent: account usage quota reached.
- Hugging Face Jobs: HTTP 402 before the probe ran.
- Local sandbox Wine path: package/download network unavailable.
- Existing second Supabase project: same ap-south-1 region.
- GitHub connector: no Codespaces or workflow-dispatch write surface exposed.
- No relevant installed MT5/MetaApi connector.
- TinyFish live cloud browser was discovered as a potentially suitable connector, but it is not currently connected.

## Engineering decision

Do not keep modifying the trading strategy or weaken risk gates while infrastructure access is unresolved.

Keep:

- TF-013A forward shadow running autonomously.
- brokerOrders=false.
- liveMoneyLocked=true.
- MT5 demo connector in HANDSHAKE_ONLY/fail-closed mode until a legitimate WebTerminal token or legitimate MT5 demo credential is available.

Once an accepted egress or real demo credential exists, the next implementation layer is:

1. authenticated handshake;
2. confirm `enabled=true` and DEMO-only account type;
3. secret-store credentials;
4. read-only account connection;
5. reconcile quotes/account state;
6. only then enable protective-stop DEMO order tests under separate approval gates.

No live-money path is implied by this protocol work.
