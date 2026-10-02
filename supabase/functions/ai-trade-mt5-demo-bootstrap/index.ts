import postgres from "npm:postgres@3.4.9";
import WebSocket from "npm:ws@8.18.0";
import { Buffer } from "node:buffer";
import {
  createCipheriv,
  createDecipheriv,
  randomBytes,
} from "node:crypto";

const sql = postgres(Deno.env.get("SUPABASE_DB_URL")!, {
  prepare: false,
  max: 1,
  connect_timeout: 10,
  idle_timeout: 20,
});

const WS_URI = "wss://web.metatrader.app/terminal";
const ORIGIN = "https://web.metatrader.app";
const INITIAL_KEY_OBFUSCATED =
  "13ef13b2b76dd8:5795gdcfb2fdc1ge85bf768f54773d22fff996e3ge75g5:75";

const CMD_BOOTSTRAP = 0;
const CMD_GET_ACCOUNT = 3;
const CMD_VERIFY_CODE = 27;
const CMD_LOGIN = 28;
const CMD_INIT = 29;
const CMD_OPEN_DEMO = 30;
const CMD_SEND_VERIFY_CODES = 40;

type Frame = { command: number; code: number; body: Buffer };

type RequestBody = {
  mode?: "transport_probe" | "open_demo" | "open_demo_alias" | "open_demo_temp";
  first_name?: string;
  second_name?: string;
  email?: string;
  phone?: string;
  email_code?: number | string;
  phone_code?: number | string;
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

async function authorized(req: Request) {
  const rows = await sql`select secret from ai_trade.cron_auth where id=1`;
  const expected = String(rows[0]?.secret ?? "");
  return Boolean(expected) &&
    (req.headers.get("x-ai-trade-cron") ?? "") === expected;
}

function decodeInitialKey(): Buffer {
  let decoded = "";
  for (const ch of INITIAL_KEY_OBFUSCATED) {
    const code = ch.charCodeAt(0);
    if (code === 28) decoded += "&";
    else if (code === 23) decoded += "!";
    else decoded += String.fromCharCode(code - 1);
  }
  return Buffer.from(decoded, "hex");
}

function encrypt(key: Buffer, data: Buffer): Buffer {
  const cipher = createCipheriv(
    key.length === 32 ? "aes-256-cbc" : key.length === 24 ? "aes-192-cbc" : "aes-128-cbc",
    key,
    Buffer.alloc(16),
  );
  return Buffer.concat([cipher.update(data), cipher.final()]);
}

function decrypt(key: Buffer, data: Buffer): Buffer {
  const decipher = createDecipheriv(
    key.length === 32 ? "aes-256-cbc" : key.length === 24 ? "aes-192-cbc" : "aes-128-cbc",
    key,
    Buffer.alloc(16),
  );
  return Buffer.concat([decipher.update(data), decipher.final()]);
}

function u16(v: number): Buffer {
  const b = Buffer.alloc(2);
  b.writeUInt16LE(v, 0);
  return b;
}

function i16(v: number): Buffer {
  const b = Buffer.alloc(2);
  b.writeInt16LE(v, 0);
  return b;
}

function u32(v: number): Buffer {
  const b = Buffer.alloc(4);
  b.writeUInt32LE(v >>> 0, 0);
  return b;
}

function u64(v: number | bigint): Buffer {
  const b = Buffer.alloc(8);
  b.writeBigUInt64LE(BigInt(v), 0);
  return b;
}

function f64(v: number): Buffer {
  const b = Buffer.alloc(8);
  b.writeDoubleLE(v, 0);
  return b;
}

function fixedString(value: string, size: number): Buffer {
  const out = Buffer.alloc(size);
  const raw = Buffer.from(value, "utf16le");
  raw.subarray(0, size).copy(out);
  return out;
}

function fixedBytes(value: Buffer, size: number): Buffer {
  const out = Buffer.alloc(size);
  value.subarray(0, size).copy(out);
  return out;
}

function decodeFixedString(value: Buffer): string {
  let end = 0;
  while (end + 1 < value.length) {
    if (value[end] === 0 && value[end + 1] === 0) break;
    end += 2;
  }
  return value.subarray(0, end).toString("utf16le");
}

function commandPacket(command: number, payload = Buffer.alloc(0)): Buffer {
  return Buffer.concat([randomBytes(2), u16(command), payload]);
}

function packOuter(encrypted: Buffer): Buffer {
  const h = Buffer.alloc(8);
  h.writeUInt32LE(encrypted.length, 0);
  h.writeUInt32LE(1, 4);
  return Buffer.concat([h, encrypted]);
}

function parseOuter(raw: Buffer): Buffer {
  if (raw.length < 8) throw new Error("OUTER_FRAME_TOO_SHORT");
  const n = raw.readUInt32LE(0);
  if (n !== raw.length - 8) throw new Error("OUTER_FRAME_LENGTH_MISMATCH");
  return raw.subarray(8);
}

function parseFrame(plain: Buffer): Frame {
  if (plain.length < 5) throw new Error("INNER_FRAME_TOO_SHORT");
  return {
    command: plain.readUInt16LE(2),
    code: plain.readUInt8(4),
    body: plain.subarray(5),
  };
}

class MT5Socket {
  ws: WebSocket | null = null;
  key = decodeInitialKey();
  serverBuild = 0;
  pending = new Map<number, {
    resolve: (v: Frame) => void;
    reject: (e: Error) => void;
    timer: number;
  }>();

  async connect() {
    await new Promise<void>((resolve, reject) => {
      const ws = new WebSocket(WS_URI, {
        headers: { Origin: ORIGIN },
        perMessageDeflate: false,
      });
      this.ws = ws;
      ws.binaryType = "arraybuffer";
      ws.once("open", () => resolve());
      ws.once("error", (e) => reject(e instanceof Error ? e : new Error(String(e))));
      ws.on("message", (data) => {
        try {
          const raw = Buffer.isBuffer(data)
            ? data
            : Buffer.from(data as ArrayBuffer);
          const encrypted = parseOuter(raw);
          const plain = decrypt(this.key, encrypted);
          const frame = parseFrame(plain);
          const p = this.pending.get(frame.command);
          if (p) {
            clearTimeout(p.timer);
            this.pending.delete(frame.command);
            p.resolve(frame);
          }
        } catch (e) {
          // Parsing failures are not surfaced with secret payloads.
        }
      });
      ws.on("close", () => {
        for (const [, p] of this.pending) {
          clearTimeout(p.timer);
          p.reject(new Error("WS_CLOSED"));
        }
        this.pending.clear();
      });
    });

    const bootstrap = await this.send(CMD_BOOTSTRAP, Buffer.alloc(64), 15000);
    if (bootstrap.code !== 0) throw new Error("BOOTSTRAP_CODE_" + bootstrap.code);
    if (bootstrap.body.length < 98) {
      throw new Error("BOOTSTRAP_BODY_TOO_SHORT_" + bootstrap.body.length);
    }
    this.serverBuild = bootstrap.body.readUInt16LE(0);
    this.key = Buffer.from(bootstrap.body.subarray(66));
    if (![16, 24, 32].includes(this.key.length)) {
      throw new Error("BOOTSTRAP_KEY_LENGTH_" + this.key.length);
    }
  }

  send(command: number, payload = Buffer.alloc(0), timeoutMs = 15000): Promise<Frame> {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return Promise.reject(new Error("WS_NOT_OPEN"));
    }
    if (this.pending.has(command)) {
      return Promise.reject(new Error("COMMAND_ALREADY_PENDING_" + command));
    }
    return new Promise<Frame>((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(command);
        reject(new Error("COMMAND_TIMEOUT_" + command));
      }, timeoutMs) as unknown as number;
      this.pending.set(command, { resolve, reject, timer });
      const inner = commandPacket(command, payload);
      const encrypted = encrypt(this.key, inner);
      this.ws!.send(packOuter(encrypted));
    });
  }

  close() {
    try {
      this.ws?.close();
    } catch {}
  }
}

async function clientId(email: string): Promise<Buffer> {
  const raw = new TextEncoder().encode("ai-trade-mt5-demo|" + email.toLowerCase());
  const digest = await crypto.subtle.digest("SHA-256", raw);
  return Buffer.from(digest).subarray(0, 16);
}

function buildInitPayload(cid: Buffer): Buffer {
  return Buffer.concat([
    u32(0),
    fixedString("", 64),
    fixedString("", 128),
    fixedBytes(cid, 16),
    fixedString("", 64),
    fixedString("", 64),
    u64(0),
    fixedString("", 128),
    u32(0),
    fixedString("", 256),
    u64(0),
  ]);
}

function buildBasePayload(
  firstName: string,
  secondName: string,
  email: string,
  phone: string,
  emailCode: number,
  phoneCode: number,
): Buffer {
  const fullName = [firstName, secondName].filter(Boolean).join(" ");
  return Buffer.concat([
    fixedString(fullName.slice(0, 128), 256),
    fixedString("", 128),
    fixedString("", 64),
    fixedString("VN", 64),
    fixedString("", 64),
    fixedString("", 64),
    fixedString("", 32),
    fixedString("", 256),
    fixedString(phone.slice(0, 32), 64),
    fixedString(email.slice(0, 64), 128),
    f64(100000),
    u32(100),
    u32(0),
    u32(1),
    fixedString("web.metatrader.app", 128),
    fixedString("mt5-demo-bootstrap", 64),
    fixedString("ai-trade-cloud", 64),
    u32(emailCode),
    u32(phoneCode),
    fixedString(firstName.slice(0, 64), 128),
    fixedString(secondName.slice(0, 64), 128),
    u32(1),
  ]);
}

function buildLoginPayload(login: bigint, password: string, cid: Buffer): Buffer {
  return Buffer.concat([
    u32(0),
    fixedString(password.slice(0, 32), 64),
    fixedString("", 128),
    fixedBytes(cid, 16),
    fixedString("", 64),
    fixedString("", 64),
    u64(0),
    fixedString("", 128),
    u32(0),
    fixedString("", 256),
    u64(login),
    Buffer.alloc(160),
    u64(0),
  ]);
}

function parseOpenAccount(body: Buffer) {
  if (body.length < 76) throw new Error("OPEN_ACCOUNT_RESPONSE_TOO_SHORT_" + body.length);
  return {
    code: body.readUInt32LE(0),
    login: body.readBigInt64LE(4),
    password: decodeFixedString(body.subarray(12, 44)),
    investorPassword: decodeFixedString(body.subarray(44, 76)),
  };
}

function parseAccountMain(body: Buffer) {
  if (body.length < 739) throw new Error("ACCOUNT_RESPONSE_TOO_SHORT_" + body.length);
  const accountType = body.readUInt8(0);
  const rights = body.readInt32LE(1);
  const balance = body.readDoubleLE(9);
  const currency = decodeFixedString(body.subarray(25, 89));
  const leverage = body.readUInt32LE(93);
  const server = decodeFixedString(body.subarray(355, 483));
  const company = decodeFixedString(body.subarray(483, 739));
  return {
    accountType,
    balance,
    currency,
    leverage,
    server,
    company,
    tradeAllowed: (rights & 4) === 0,
    isReadOnly: (rights & 512) !== 0,
    isDemo: accountType === 1,
  };
}

async function verifyLogin(
  login: bigint,
  password: string,
  cid: Buffer,
) {
  const c = new MT5Socket();
  try {
    await c.connect();
    const logged = await c.send(CMD_LOGIN, buildLoginPayload(login, password, cid), 20000);
    if (logged.code !== 0) throw new Error("LOGIN_CODE_" + logged.code);
    const acct = await c.send(CMD_GET_ACCOUNT, Buffer.alloc(0), 20000);
    if (acct.code !== 0) throw new Error("ACCOUNT_CODE_" + acct.code);
    return parseAccountMain(acct.body);
  } finally {
    c.close();
  }
}

async function persistVerified(
  login: bigint,
  password: string,
  investorPassword: string,
  email: string,
  account: ReturnType<typeof parseAccountMain>,
) {
  await sql`
    insert into ai_trade.mt5_demo_credentials(
      id,login,server,email,password_cipher,investor_password_cipher,
      is_demo,verified,account_type,balance,currency,leverage,trade_allowed,
      created_at,verified_at,updated_at
    )
    select
      1,${login.toString()}::bigint,${account.server},${email},
      pgp_sym_encrypt(${password}, secret::text),
      pgp_sym_encrypt(${investorPassword}, secret::text),
      true,true,${account.accountType},${account.balance},${account.currency},
      ${account.leverage},${account.tradeAllowed},now(),now(),now()
    from ai_trade.cron_auth where id=1
    on conflict (id) do update set
      login=excluded.login,
      server=excluded.server,
      email=excluded.email,
      password_cipher=excluded.password_cipher,
      investor_password_cipher=excluded.investor_password_cipher,
      is_demo=true,
      verified=true,
      account_type=excluded.account_type,
      balance=excluded.balance,
      currency=excluded.currency,
      leverage=excluded.leverage,
      trade_allowed=excluded.trade_allowed,
      verified_at=now(),
      updated_at=now()
  `;
}


type TempMailbox = {
  address: string;
  password: string;
  accountId: string;
  token: string;
};

async function getVerifiedDemoSummary() {
  const rows = await sql`
    select login,server,verified,account_type,balance,currency,leverage,trade_allowed
    from ai_trade.mt5_demo_credentials
    where id=1 and verified=true and is_demo=true
  `;
  if (!rows[0]) return null;
  return {
    login: String(rows[0].login),
    server: String(rows[0].server ?? ""),
    accountType: Number(rows[0].account_type ?? -1),
    balance: Number(rows[0].balance ?? 0),
    currency: String(rows[0].currency ?? ""),
    leverage: Number(rows[0].leverage ?? 0),
    tradeAllowed: Boolean(rows[0].trade_allowed),
  };
}

async function mailTmJson(
  url: string,
  init: RequestInit = {},
  okStatuses: number[] = [200],
) {
  const response = await fetch(url, init);
  if (!okStatuses.includes(response.status)) {
    const body = (await response.text()).slice(0, 240);
    throw new Error("MAILTM_HTTP_" + response.status + "_" + body.replace(/\\s+/g, " "));
  }
  return await response.json();
}

async function mailTmToken(address: string, password: string): Promise<string> {
  const payload = await mailTmJson(
    "https://api.mail.tm/token",
    {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ address, password }),
    },
    [200],
  );
  const token = String(payload?.token ?? "");
  if (!token) throw new Error("MAILTM_TOKEN_MISSING");
  return token;
}

async function loadStoredMailbox(): Promise<TempMailbox | null> {
  const rows = await sql`
    select m.address,
           pgp_sym_decrypt(m.password_cipher, c.secret::text) as password,
           m.provider_account_id
    from ai_trade.mt5_demo_mailbox m
    cross join ai_trade.cron_auth c
    where m.id=1 and m.active=true and c.id=1
  `;
  if (!rows[0]) return null;
  const address = String(rows[0].address ?? "");
  const password = String(rows[0].password ?? "");
  const accountId = String(rows[0].provider_account_id ?? "");
  if (!address || !password) return null;
  try {
    const token = await mailTmToken(address, password);
    return { address, password, accountId, token };
  } catch {
    await sql`update ai_trade.mt5_demo_mailbox set active=false,updated_at=now() where id=1`;
    return null;
  }
}

async function persistMailbox(mailbox: Omit<TempMailbox, "token">) {
  await sql`
    insert into ai_trade.mt5_demo_mailbox(
      id,provider,address,password_cipher,provider_account_id,active,created_at,updated_at
    )
    select 1,'mail.tm',${mailbox.address},
           pgp_sym_encrypt(${mailbox.password}, c.secret::text),
           ${mailbox.accountId},true,now(),now()
    from ai_trade.cron_auth c where c.id=1
    on conflict(id) do update set
      provider='mail.tm',
      address=excluded.address,
      password_cipher=excluded.password_cipher,
      provider_account_id=excluded.provider_account_id,
      active=true,
      updated_at=now()
  `;
}

async function createTempMailbox(): Promise<TempMailbox> {
  const existing = await loadStoredMailbox();
  if (existing) return existing;

  const domainsPayload = await mailTmJson("https://api.mail.tm/domains?page=1", {}, [200]);
  const domains = Array.isArray(domainsPayload?.["hydra:member"])
    ? domainsPayload["hydra:member"]
        .filter((x: any) => Boolean(x?.isActive) && !Boolean(x?.isPrivate) && String(x?.domain ?? ""))
        .map((x: any) => String(x.domain))
    : [];
  if (!domains.length) throw new Error("MAILTM_NO_ACTIVE_PUBLIC_DOMAIN");

  let lastError = "MAILTM_CREATE_FAILED";
  for (const domain of domains.slice(0, 5)) {
    const local = "aitrade-" + randomBytes(8).toString("hex");
    const address = local + "@" + domain;
    const password = randomBytes(24).toString("base64url");
    try {
      const account = await mailTmJson(
        "https://api.mail.tm/accounts",
        {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ address, password }),
        },
        [201],
      );
      const accountId = String(account?.id ?? "");
      if (!accountId) throw new Error("MAILTM_ACCOUNT_ID_MISSING");
      const token = await mailTmToken(address, password);
      await persistMailbox({ address, password, accountId });
      return { address, password, accountId, token };
    } catch (e) {
      lastError = e instanceof Error ? e.message : String(e);
    }
  }
  throw new Error(lastError);
}

function trustedMetaQuotesSender(address: string): boolean {
  const value = address.trim().toLowerCase();
  const at = value.lastIndexOf("@");
  const domain = at >= 0 ? value.slice(at + 1) : "";
  return [
    "mql5.com",
    "metaquotes.net",
    "metaquotes.com",
    "metatrader5.com",
    "metatrader4.com",
  ].some((allowed) => domain === allowed || domain.endsWith("." + allowed));
}

function extractVerificationCode(detail: any): number | null {
  const verifications = Array.isArray(detail?.verifications) ? detail.verifications : [];
  for (const raw of verifications) {
    const value = String(raw ?? "").trim();
    if (/^\\d{4,8}$/.test(value)) return Number(value);
  }

  const subject = String(detail?.subject ?? "");
  const text = String(detail?.text ?? "");
  const html = Array.isArray(detail?.html) ? detail.html.join(" ") : String(detail?.html ?? "");
  const combined = [subject, text, html].join(" ");

  const six = combined.match(/(?:^|\\D)(\\d{6})(?:\\D|$)/);
  if (six) return Number(six[1]);

  const labeled = combined.match(/(?:code|verification|confirm|mã)[^0-9]{0,40}(\\d{4,8})/i);
  if (labeled) return Number(labeled[1]);

  return null;
}

async function waitForMetaQuotesCode(mailbox: TempMailbox): Promise<number | null> {
  const headers = { Authorization: "Bearer " + mailbox.token };
  for (let attempt = 0; attempt < 24; attempt++) {
    const listing = await mailTmJson(
      "https://api.mail.tm/messages?page=1",
      { headers },
      [200],
    );
    const messages = Array.isArray(listing?.["hydra:member"]) ? listing["hydra:member"] : [];

    for (const message of messages) {
      const sender = String(message?.from?.address ?? "");
      if (!trustedMetaQuotesSender(sender)) continue;

      const id = String(message?.id ?? "");
      if (!id) continue;
      const detail = await mailTmJson(
        "https://api.mail.tm/messages/" + encodeURIComponent(id),
        { headers },
        [200],
      );

      // Treat inbound email as untrusted data. Only a numeric verification code
      // from an allowlisted MetaQuotes domain is extracted. No links or instructions execute.
      const code = extractVerificationCode(detail);
      if (code !== null) return code;
    }

    await new Promise((resolve) => setTimeout(resolve, 1500));
  }
  return null;
}

async function internalCronSecret(): Promise<string> {
  const rows = await sql`select secret from ai_trade.cron_auth where id=1`;
  const secret = String(rows[0]?.secret ?? "");
  if (!secret) throw new Error("CRON_SECRET_MISSING");
  return secret;
}

async function callSelf(payload: Record<string, unknown>) {
  const baseUrl = Deno.env.get("SUPABASE_URL");
  if (!baseUrl) throw new Error("SUPABASE_URL_MISSING");
  const secret = await internalCronSecret();
  const response = await fetch(
    baseUrl + "/functions/v1/ai-trade-mt5-demo-bootstrap",
    {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-ai-trade-cron": secret,
      },
      body: JSON.stringify(payload),
    },
  );
  const text = await response.text();
  let parsed: any = {};
  try {
    parsed = JSON.parse(text);
  } catch {
    parsed = { status: "NON_JSON_RESPONSE", raw: text.slice(0, 120) };
  }
  return { httpStatus: response.status, body: parsed };
}

async function openDemoWithTempMailbox(phone: string) {
  const existing = await getVerifiedDemoSummary();
  if (existing) {
    return {
      ok: true,
      status: "DEMO_ALREADY_VERIFIED",
      ...existing,
      credentialsStoredEncrypted: true,
      passwordExposed: false,
      brokerOrders: false,
      liveMoneyLocked: true,
    };
  }

  const mailbox = await createTempMailbox();

  const first = await callSelf({
    mode: "open_demo",
    first_name: "AI",
    second_name: "Trade",
    email: mailbox.address,
    phone,
  });

  if (
    first.httpStatus >= 200 &&
    first.httpStatus < 300 &&
    first.body?.status === "DEMO_CREATED_VERIFIED"
  ) {
    return {
      ...first.body,
      mailboxProvider: "mail.tm",
      mailboxStoredEncrypted: true,
    };
  }

  if (first.body?.status !== "EMAIL_VERIFICATION_REQUIRED") {
    return {
      ok: false,
      status: "TEMP_MAIL_DEMO_OPEN_BLOCKED",
      upstreamStatus: String(first.body?.status ?? "UNKNOWN"),
      upstreamCode: first.body?.code ?? null,
      mailboxProvider: "mail.tm",
      mailboxStoredEncrypted: true,
      brokerOrders: false,
      liveMoneyLocked: true,
    };
  }

  const verificationCode = await waitForMetaQuotesCode(mailbox);
  if (verificationCode === null) {
    return {
      ok: false,
      status: "METAQUOTES_VERIFICATION_EMAIL_NOT_FOUND",
      mailboxProvider: "mail.tm",
      mailboxStoredEncrypted: true,
      brokerOrders: false,
      liveMoneyLocked: true,
    };
  }

  const second = await callSelf({
    mode: "open_demo",
    first_name: "AI",
    second_name: "Trade",
    email: mailbox.address,
    phone,
    email_code: verificationCode,
  });

  return {
    ...second.body,
    httpStatus: second.httpStatus,
    mailboxProvider: "mail.tm",
    mailboxStoredEncrypted: true,
    verificationCodeExposed: false,
    brokerOrders: false,
    liveMoneyLocked: true,
  };
}

Deno.serve(async (req) => {
  if (!(await authorized(req))) {
    return json({ ok: false, status: "UNAUTHORIZED" }, 401);
  }

  const body = await req.json().catch(() => ({})) as RequestBody;

  if (body.mode === "open_demo_temp") {
    const phone = String(body.phone ?? "").trim();
    if (!phone) {
      return json({
        ok: false,
        status: "PHONE_INPUT_REQUIRED",
        brokerOrders: false,
        liveMoneyLocked: true,
      }, 400);
    }
    if (!/^\+[1-9]\d{7,14}$/.test(phone)) {
      return json({
        ok: false,
        status: "INVALID_PHONE_FORMAT",
        phoneStored: false,
        brokerOrders: false,
        liveMoneyLocked: true,
      }, 400);
    }
    try {
      return json(await openDemoWithTempMailbox(phone));
    } catch (e) {
      return json({
        ok: false,
        status: "TEMP_MAIL_BOOTSTRAP_ERROR",
        error: e instanceof Error ? e.message : String(e),
        brokerOrders: false,
        liveMoneyLocked: true,
      }, 500);
    }
  }

  if (body.mode === "transport_probe") {
    const probe = new MT5Socket();
    try {
      await probe.connect();
      return json({
        ok: true,
        status: "TRANSPORT_READY",
        serverBuild: probe.serverBuild,
        ws: true,
        aesKeyLength: probe.key.length,
        brokerOrders: false,
        liveMoneyLocked: true,
      });
    } catch (e) {
      return json({
        ok: false,
        status: "TRANSPORT_ERROR",
        error: e instanceof Error ? e.message : String(e),
        brokerOrders: false,
        liveMoneyLocked: true,
      }, 500);
    } finally {
      probe.close();
    }
  }

  const aliasMode = body.mode === "open_demo_alias";
  const firstName = aliasMode ? "AI" : String(body.first_name ?? "").trim();
  const secondName = aliasMode ? "Trade" : String(body.second_name ?? "").trim();
  const email = aliasMode ? "" : String(body.email ?? "").trim().toLowerCase();
  const phone = aliasMode ? "" : String(body.phone ?? "").trim();
  const emailCode = Number(body.email_code ?? 0);
  const phoneCode = Number(body.phone_code ?? 0);

  if (!firstName || !secondName || (!aliasMode && (!email || !email.includes("@") || !phone))) {
    return json({
      ok: false,
      status: "IDENTITY_INPUT_REQUIRED",
      brokerOrders: false,
      liveMoneyLocked: true,
    }, 400);
  }
  if (!aliasMode && !/^\+[1-9]\d{7,14}$/.test(phone)) {
    return json({
      ok: false,
      status: "INVALID_PHONE_FORMAT",
      phoneStored: false,
      brokerOrders: false,
      liveMoneyLocked: true,
    }, 400);
  }
  if (!Number.isInteger(emailCode) || emailCode < 0) {
    return json({ ok: false, status: "INVALID_EMAIL_CODE" }, 400);
  }
  if (!Number.isInteger(phoneCode) || phoneCode < 0) {
    return json({ ok: false, status: "INVALID_PHONE_CODE" }, 400);
  }

  const cid = await clientId(email);
  const mt = new MT5Socket();

  try {
    await mt.connect();
    const init = await mt.send(CMD_INIT, buildInitPayload(cid), 20000);
    if (init.code !== 0) {
      return json({
        ok: false,
        status: "INIT_FAILED",
        code: init.code,
        brokerOrders: false,
        liveMoneyLocked: true,
      }, 502);
    }

    const base = buildBasePayload(firstName, secondName, email, phone, emailCode, phoneCode);

    if (!emailCode && !aliasMode) {
      const verificationPayload = Buffer.concat([
        i16(mt.serverBuild || 0),
        fixedBytes(cid, 16),
        base,
      ]);
      const vr = await mt.send(CMD_VERIFY_CODE, verificationPayload, 20000);
      if (vr.code !== 0) {
        return json({
          ok: false,
          status: "VERIFICATION_PROBE_FAILED",
          code: vr.code,
          brokerOrders: false,
          liveMoneyLocked: true,
        }, 502);
      }

      const emailRequired = Boolean(vr.body[0] ?? 0);
      const phoneRequired = Boolean(vr.body[1] ?? 0);

      if (phoneRequired) {
        return json({
          ok: true,
          status: "PHONE_VERIFICATION_REQUIRED",
          emailVerificationRequired: emailRequired,
          phoneVerificationRequired: true,
          brokerOrders: false,
          liveMoneyLocked: true,
        });
      }

      if (emailRequired) {
        return json({
          ok: true,
          status: "EMAIL_VERIFICATION_REQUIRED",
          emailVerificationRequired: true,
          phoneVerificationRequired: false,
          brokerOrders: false,
          liveMoneyLocked: true,
        });
      }
    } else if (emailCode) {
      const submitted = await mt.send(CMD_SEND_VERIFY_CODES, base, 20000);
      if (submitted.code !== 0) {
        return json({
          ok: false,
          status: "EMAIL_VERIFICATION_SUBMIT_FAILED",
          code: submitted.code,
          brokerOrders: false,
          liveMoneyLocked: true,
        }, 502);
      }
      const emailOk = Boolean(submitted.body[0] ?? 0);
      const phoneFlag = Boolean(submitted.body[1] ?? 0);
      if (!emailOk || phoneFlag) {
        return json({
          ok: true,
          status: "EMAIL_VERIFICATION_REJECTED",
          emailOk,
          phoneFlag,
          brokerOrders: false,
          liveMoneyLocked: true,
        });
      }
    }

    const opened = await mt.send(CMD_OPEN_DEMO, base, 25000);
    if (opened.code !== 0) {
      return json({
        ok: false,
        status: "OPEN_DEMO_TRANSPORT_FAILED",
        code: opened.code,
        brokerOrders: false,
        liveMoneyLocked: true,
      }, 502);
    }

    const accountResult = parseOpenAccount(opened.body);
    if (
      accountResult.code !== 0 ||
      accountResult.login <= 0n ||
      !accountResult.password
    ) {
      return json({
        ok: false,
        status: "OPEN_DEMO_REJECTED",
        code: accountResult.code,
        brokerOrders: false,
        liveMoneyLocked: true,
      }, 502);
    }

    const account = await verifyLogin(
      accountResult.login,
      accountResult.password,
      cid,
    );

    if (!account.isDemo) {
      return json({
        ok: false,
        status: "FAIL_CLOSED_NON_DEMO_ACCOUNT",
        accountType: account.accountType,
        brokerOrders: false,
        liveMoneyLocked: true,
      }, 409);
    }

    await persistVerified(
      accountResult.login,
      accountResult.password,
      accountResult.investorPassword,
      email,
      account,
    );

    return json({
      ok: true,
      status: "DEMO_CREATED_VERIFIED",
      login: accountResult.login.toString(),
      server: account.server,
      company: account.company,
      balance: account.balance,
      currency: account.currency,
      leverage: account.leverage,
      tradeAllowed: account.tradeAllowed,
      readOnly: account.isReadOnly,
      accountType: account.accountType,
      isDemo: account.isDemo,
      credentialsStoredEncrypted: true,
      passwordExposed: false,
      brokerOrders: false,
      liveMoneyLocked: true,
    });
  } catch (e) {
    return json({
      ok: false,
      status: "ERROR",
      error: e instanceof Error ? e.message : String(e),
      brokerOrders: false,
      liveMoneyLocked: true,
    }, 500);
  } finally {
    mt.close();
  }
});
