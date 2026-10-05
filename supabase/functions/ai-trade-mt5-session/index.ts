
import postgres from "npm:postgres@3.4.9";
import {corsHeaders} from "./web-origin.mjs";

const sql = postgres(Deno.env.get("SUPABASE_DB_URL")!, {
  prepare:false, max:1, connect_timeout:10, idle_timeout:20
});
const ROOT = Deno.env.get("SUPABASE_URL")!;
const REMEMBER_TTL_SECONDS = 31_536_000; // 365 days, renewed on successful use

const json = (body: unknown, status=200) => new Response(JSON.stringify(body), {
  status,
  headers: {
    "content-type":"application/json; charset=utf-8",
    "cache-control":"no-store",
    "x-content-type-options":"nosniff"
  }
});

async function sha256Hex(value:string){
  const bytes = new TextEncoder().encode(value);
  const digest = new Uint8Array(await crypto.subtle.digest("SHA-256", bytes));
  return Array.from(digest, b => b.toString(16).padStart(2,"0")).join("");
}

function token(){
  const bytes = new Uint8Array(32);
  crypto.getRandomValues(bytes);
  return btoa(String.fromCharCode(...bytes))
    .replaceAll("+","-").replaceAll("/","_").replaceAll("=","");
}

function validLogin(v:unknown){
  return typeof v === "number" && Number.isSafeInteger(v)
    && v >= 10000 && v <= 999999999999999;
}

function safeError(status:string){
  const allowed = new Set([
    "SERVER_NOT_FOUND","INVALID_LOGIN_OR_PASSWORD","INVESTOR_READ_ONLY",
    "ADDITIONAL_AUTH_REQUIRED","TERMINAL_NOT_READY","TIMEOUT",
    "BRIDGE_UNAVAILABLE","ACCOUNT_INFO_UNAVAILABLE","INVALID_REQUEST",
    "DEMO_ACCOUNT_REQUIRED","ACCOUNT_IDENTITY_MISMATCH","SESSION_INVALID",
    "SESSION_EXPIRED","SECRET_STORE_FAILURE"
  ]);
  return allowed.has(status) ? status : "BRIDGE_UNAVAILABLE";
}

async function cronSecret(){
  const rows = await sql`select secret from ai_trade.cron_auth where id=1`;
  const value = String(rows[0]?.secret ?? "");
  if(!value) throw new Error("BRIDGE_UNAVAILABLE");
  return value;
}

async function verifier(payload:unknown){
  const secret = await cronSecret();
  const response = await fetch(ROOT + "/functions/v1/ai-trade-mt5-demo-validate", {
    method:"POST",
    headers:{"content-type":"application/json","x-ai-trade-cron":secret},
    body:JSON.stringify(payload),
    cache:"no-store",
    signal:AbortSignal.timeout(120000)
  });
  const data = await response.json().catch(() => ({}));
  return {response, data};
}

async function snapshot(login:number){
  const {response,data} = await verifier({
    login:String(login), readback:"investor_snapshot"
  });
  if(!response.ok || data?.verified !== true || data?.status !== "DEMO_VERIFIED"
      || data?.mode !== "DEMO" || data?.server !== "MetaQuotes-Demo"
      || String(data?.login) !== String(login)
      || data?.readbackSource !== "MT5_INVESTOR_BROKER"
      || data?.readOnly !== true
      || data?.credentialScope !== "INVESTOR_READ_ONLY"
      || data?.brokerOrders !== false || data?.liveMoneyLocked !== true
      || typeof data?.balance !== "number" || !Number.isFinite(data.balance)
      || typeof data?.equity !== "number" || !Number.isFinite(data.equity)){
    throw new Error("ACCOUNT_INFO_UNAVAILABLE");
  }
  return data;
}

async function connect(req:Request){
  const n = Number(req.headers.get("content-length") ?? 0);
  if(!Number.isFinite(n) || n > 2048) return json({
    status:"INVALID_REQUEST", auto_trade:"OFF", order_send_enabled:false, orders_sent:0
  },413);

  let body:any;
  try { body = await req.json(); } catch { body = null; }
  if(!body || typeof body !== "object" || Array.isArray(body)
      || body.server !== "MetaQuotes-Demo"
      || !validLogin(body.login)
      || typeof body.password !== "string"
      || body.password.length < 4 || body.password.length > 32
      || /[\u0000-\u001F\u007F]/.test(body.password)
      || typeof body.remember !== "boolean"){
    return json({status:"INVALID_REQUEST",auto_trade:"OFF",
      order_send_enabled:false,orders_sent:0},400);
  }

  const login = Number(body.login);
  const suppliedPassword = body.password;
  body.password = undefined;

  const existingBinding=await sql`
    select source from ai_trade.mt5_demo_accounts
    where account_login=${login}::bigint
    limit 1
  `;
  let pendingBinding=false;
  if(!existingBinding[0]){
    const seed=await sql`
      select password_secret_id
      from ai_trade.mt5_demo_accounts
      where password_secret_id is not null
      order by last_verified_at desc nulls last,created_at desc
      limit 1
    `;
    if(!seed[0]?.password_secret_id){
      return json({status:"BRIDGE_UNAVAILABLE",auto_trade:"OFF",
        order_send_enabled:false,orders_sent:0},503);
    }
    await sql`
      insert into ai_trade.mt5_demo_accounts(
        account_login,server,account_type,password_secret_id,
        investor_password_secret_id,source,source_run_id,
        last_verified_at,is_active
      ) values(
        ${login}::bigint,'MetaQuotes-Demo','DEMO',
        ${seed[0].password_secret_id}::uuid,null,
        'android_pending',null,null,true
      )
    `;
    pendingBinding=true;
  }

  let response:Response|null=null;
  let data:any={};
  let verificationAttempts=0;
  const loginCodes:number[]=[];
  for(let attempt=1;attempt<=3;attempt++){
    const result=await verifier({
      login:String(login), readback:"founder_verify", verifyPassword:suppliedPassword
    });
    response=result.response;
    data=result.data;
    verificationAttempts=attempt;
    const code=Number(data?.loginCode);
    if(Number.isInteger(code)&&code>=0&&code<=255) loginCodes.push(code);
    if(response.ok && data?.verified===true && data?.status==="DEMO_VERIFIED") break;
    if(data?.status!=="LOGIN_REJECTED" || attempt===3) break;
    await new Promise(resolve=>setTimeout(resolve,attempt*750));
  }
  if(!response) throw new Error("BRIDGE_UNAVAILABLE");

  if(!response.ok || data?.verified !== true || data?.status !== "DEMO_VERIFIED"
      || data?.accountType !== 1 || data?.server !== "MetaQuotes-Demo"
      || String(data?.login) !== String(login)
      || data?.brokerOrders !== false || data?.liveMoneyLocked !== true){
    if(pendingBinding){
      await sql`delete from ai_trade.mt5_demo_accounts
        where account_login=${login}::bigint and source='android_pending'`;
    }
    const mapped = data?.status === "LOGIN_REJECTED"
      ? "INVALID_LOGIN_OR_PASSWORD"
      : data?.status === "NO_METAQUOTES_DEMO_CREDENTIAL"
      ? "SERVER_NOT_FOUND"
      : "BRIDGE_UNAVAILABLE";
    const lastLoginCode=loginCodes.length?loginCodes[loginCodes.length-1]:null;
    if(mapped==="INVALID_LOGIN_OR_PASSWORD"){
      const details={
        verification_attempts:verificationAttempts,
        broker_login_code:lastLoginCode,
        login_digits:String(login).length,
        password_length:suppliedPassword.length,
        client:String(req.headers.get("x-cws-client")??"").slice(0,64),
        client_version:String(req.headers.get("x-cws-client-version")??"").slice(0,64)
      };
      await sql`insert into ai_trade.events(event_type,result,details)
        values('mt5_login_rejected','LOGIN_REJECTED',${JSON.stringify(details)}::jsonb)`;
    }
    return json({
      status:safeError(mapped),
      verification_attempts:verificationAttempts,
      broker_login_code:lastLoginCode,
      login_digits:String(login).length,
      password_length:suppliedPassword.length,
      auto_trade:"OFF",order_send_enabled:false,orders_sent:0
    }, mapped==="INVALID_LOGIN_OR_PASSWORD"?401:503);
  }

  const tradePermission = data?.readOnly === true || data?.tradeAllowed !== true
    ? "READ_ONLY" : "TRADING_ALLOWED";
  const balance=Number(data?.balance);
  const equity=balance;
  const currency=String(data?.currency??"USD");
  if(!Number.isFinite(balance)||balance<0||!Number.isFinite(equity)
      ||!/^[A-Z]{3,8}$/.test(currency)){
    if(pendingBinding){
      await sql`delete from ai_trade.mt5_demo_accounts
        where account_login=${login}::bigint and source='android_pending'`;
    }
    return json({status:"ACCOUNT_INFO_UNAVAILABLE",auto_trade:"OFF",
      order_send_enabled:false,orders_sent:0},503);
  }

  const sessionId = token();
  const hash = await sha256Hex(sessionId);
  const ttlSeconds = body.remember ? REMEMBER_TTL_SECONDS : 900;

  await sql`
    insert into ai_trade.mt5_app_sessions(
      token_hash,account_login,server,trade_permission,remember,expires_at,
      balance,equity,currency
    ) values(
      ${hash},${login}::bigint,'MetaQuotes-Demo',${tradePermission},
      ${body.remember},now() + make_interval(secs => ${ttlSeconds}),
      ${balance},${equity},${currency}
    )
  `;
  if(pendingBinding){
    await sql`delete from ai_trade.mt5_demo_accounts
      where account_login=${login}::bigint and source='android_pending'`;
  }

  return json({
    status: tradePermission === "READ_ONLY" ? "CONNECTED_READ_ONLY" : "CONNECTED",
    session_id: sessionId,
    account:{
      login, server:"MetaQuotes-Demo", trade_mode:"DEMO",
      trade_permission:tradePermission,
      balance, equity
    },
    auto_trade:"OFF", order_send_enabled:false, orders_sent:0
  });
}

async function sessionFrom(req:Request){
  const auth = req.headers.get("authorization") ?? "";
  if(!auth.startsWith("Bearer ")) throw new Error("SESSION_INVALID");
  const raw = auth.slice(7);
  if(raw.length < 40 || raw.length > 128) throw new Error("SESSION_INVALID");
  const hash = await sha256Hex(raw);
  const rows = await sql`
    select account_login,server,trade_permission,remember,expires_at,balance,equity,currency
    from ai_trade.mt5_app_sessions
    where token_hash=${hash} and revoked_at is null
    limit 1
  `;
  if(!rows[0]) throw new Error("SESSION_INVALID");
  if(new Date(rows[0].expires_at).getTime() <= Date.now()){
    await sql`update ai_trade.mt5_app_sessions set revoked_at=now()
      where token_hash=${hash} and revoked_at is null`;
    throw new Error("SESSION_EXPIRED");
  }
  await sql`update ai_trade.mt5_app_sessions
    set last_seen_at=now(),
        expires_at=case when remember
          then now() + make_interval(secs => ${REMEMBER_TTL_SECONDS})
          else expires_at end
    where token_hash=${hash}`;
  return {hash,row:rows[0]};
}

async function account(req:Request){
  const {row} = await sessionFrom(req);
  const login = Number(row.account_login);
  const balance=Number(row.balance);
  const equity=Number(row.equity);
  if(!Number.isFinite(balance)||!Number.isFinite(equity)){
    throw new Error("ACCOUNT_INFO_UNAVAILABLE");
  }
  return json({
    status: row.trade_permission === "READ_ONLY" ? "CONNECTED_READ_ONLY" : "CONNECTED",
    account:{
      login, server:String(row.server), trade_mode:"DEMO",
      trade_permission:String(row.trade_permission),
      balance, equity
    },
    auto_trade:"OFF", order_send_enabled:false, orders_sent:0
  });
}

async function disconnect(req:Request){
  const {hash} = await sessionFrom(req);
  await sql`update ai_trade.mt5_app_sessions
    set revoked_at=now(),last_seen_at=now()
    where token_hash=${hash} and revoked_at is null`;
  return json({status:"DISCONNECTED",auto_trade:"OFF",
    order_send_enabled:false,orders_sent:0});
}


async function brokers(){
  const rows=await sql`
    select enabled,demo_send_enabled,risk_profile_approved
    from ai_trade.runtime_config
    where id=1
    limit 1
  `;
  const cfg=rows[0]??{};
  const providerReady=Boolean(
    Deno.env.get("METAAPI_TOKEN")?.trim()
    && Deno.env.get("METAAPI_ACCOUNT_ID")?.trim()
  );
  const blockers:string[]=[];
  if(cfg.enabled!==true) blockers.push("RUNTIME_DISABLED");
  if(cfg.demo_send_enabled!==true) blockers.push("DEMO_SEND_DISABLED");
  if(cfg.risk_profile_approved!==true) blockers.push("RISK_NOT_APPROVED");
  if(!providerReady) blockers.push("PROVIDER_NOT_READY");
  const demoAutoTradeReady=blockers.length===0;
  return json({
    status:"OK",
    brokers:[
      {
        id:"metaquotes",
        name:"MetaQuotes Ltd.",
        servers:[
          {server:"MetaQuotes-Demo",mode:"DEMO",supported:true}
        ]
      }
    ],
    provider_ready:providerReady,
    demo_autotrade_ready:demoAutoTradeReady,
    demo_autotrade_blockers:blockers,
    control_plane:"SERVER_AUTHORITATIVE",
    render_required:false,
    live_money_locked:true,
    order_send_enabled:demoAutoTradeReady,
    orders_sent:0
  });
}

async function handle(req:Request){
  try{
    const path = new URL(req.url).pathname;
    if(req.method==="GET" && path.endsWith("/mt5/brokers")) return await brokers();
    if(req.method==="POST" && path.endsWith("/mt5/session/connect")) return await connect(req);
    if(req.method==="GET" && path.endsWith("/mt5/session/account")) return await account(req);
    if(req.method==="POST" && path.endsWith("/mt5/session/disconnect")) return await disconnect(req);
    return json({status:"NOT_FOUND",auto_trade:"OFF",
      order_send_enabled:false,orders_sent:0},404);
  }catch(error){
    const raw = error instanceof Error ? error.message : "BRIDGE_UNAVAILABLE";
    const status = safeError(raw);
    const code = status==="SESSION_INVALID"||status==="SESSION_EXPIRED" ? 401
      : status==="INVALID_REQUEST" ? 400 : 503;
    return json({status,auto_trade:"OFF",order_send_enabled:false,orders_sent:0},code);
  }
}

Deno.serve(async(req)=>{
 const origin=req.headers.get('origin')??'';
 const cors=corsHeaders(origin);
 if(origin&&!cors)return json({status:'WEB_ORIGIN_NOT_ALLOWED',order_send_enabled:false},403);
 if(req.method==='OPTIONS')return new Response(null,{status:cors?204:403,headers:cors??{}});
 const response=await handle(req);
 if(!cors)return response; // Preserve the existing native Android contract.
 const headers=new Headers(response.headers);
 for(const [k,v] of Object.entries(cors))headers.set(k,String(v));
 return new Response(response.body,{status:response.status,headers});
});
