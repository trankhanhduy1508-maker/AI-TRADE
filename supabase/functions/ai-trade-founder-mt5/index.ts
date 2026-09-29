/**
 * CWS AI Trade: Founder-only MT5 DEMO account verification and read-only status.
 *
 * This endpoint requires a valid Supabase Auth Google session AND active Founder
 * entitlement. It never accepts public market orders, changes runtime_config,
 * exposes Vault secrets, or treats a past account verification as a live session.
 *
 * Only the already-authorized DEMO account stored in Supabase Vault is accepted.
 * Other brokers/accounts need separate verified adapter and security review.
 */
import postgres from "npm:postgres@3.4.9";
import { parseFounderDemoLogin } from "./demo-login-contract.mjs";

const sql=postgres(Deno.env.get("SUPABASE_DB_URL")!,{
  prepare:false,max:2,connect_timeout:10,idle_timeout:20
});
const URL_ROOT=Deno.env.get("SUPABASE_URL")??"https://oziktadfeenydvgobudr.supabase.co";
const API_KEY=Deno.env.get("SUPABASE_ANON_KEY")??"";
const ALLOWED_ORIGINS=new Set([
  "https://trankhanhduy1508-maker.github.io"
]);
const VERIFIED_TTL_MS=90_000;
const COMMON={"content-type":"application/json; charset=utf-8",
  "cache-control":"no-store, max-age=0","referrer-policy":"no-referrer",
  "x-content-type-options":"nosniff"};
function respond(payload:unknown,code=200,origin=""){
  const headers:Record<string,string>={...COMMON};
  if(ALLOWED_ORIGINS.has(origin)){
    headers["access-control-allow-origin"]=origin;
    headers["vary"]="origin";
    headers["access-control-allow-methods"]="GET,POST,OPTIONS";
    headers["access-control-allow-headers"]="authorization,content-type,apikey";
  }
  return new Response(JSON.stringify(payload),{status:code,headers});
}
type Founder={id:number};
async function founder(req:Request):Promise<Founder|null>{
  if(!API_KEY)throw new Error("GOOGLE_AUTH_NOT_CONFIGURED");
  const token=(req.headers.get("authorization")??"").match(/^Bearer\s+([^\s]+)$/i)?.[1]??"";
  if(!token)return null;
  const u=await fetch(URL_ROOT+"/auth/v1/user",{
    headers:{apikey:API_KEY,Authorization:"Bearer "+token},
    cache:"no-store",signal:AbortSignal.timeout(12000)
  });
  if(!u.ok)return null;
  const data=await u.json().catch(()=>null);
  const uid=String(data?.id??"");
  if(!/^[a-f0-9-]{36}$/i.test(uid))return null;
  const rows=await sql`
    select d.id from ai_trade.dashboard_google_access g
    join ai_trade.dashboard_access_tokens d on d.id=g.access_token_id
    where g.user_id=${uid}::uuid and g.active=true
      and d.access_role='FOUNDER'
      and d.revoked_at is null and d.expires_at>now()
      and d.entitlement_state not in ('SUSPENDED','REVOKED')
    limit 1
  `;
  return rows[0]?{id:Number(rows[0].id)}:null;
}
async function status(id:number){
  const [binding]=await sql`
    select b.account_login,b.server,b.account_type,b.connection_state,
           b.last_verified_at,a.is_active
    from ai_trade.account_mt5_bindings b
    left join ai_trade.mt5_demo_accounts a
      on a.account_login=b.account_login and a.server=b.server
    where b.access_token_id=${id} and b.account_type='DEMO'
    limit 1
  `;
  const [gate]=await sql`
    select c.enabled,c.demo_send_enabled,c.risk_profile_approved,
           (select readiness from ai_trade.bootcamp_readiness
             where provider='THE5ERS' limit 1) as the5ers_readiness,
           (select count(*) from ai_trade.private_ml_baseline_runs
             where status='APPROVED' and broker_orders=true) as approved_models
    from ai_trade.runtime_config c where c.id=1
  `;
  const checked=binding?.last_verified_at?new Date(binding.last_verified_at):null;
  const fresh=!!checked&&Number.isFinite(checked.getTime())
    && (Date.now()-checked.getTime()>=0)
    && (Date.now()-checked.getTime()<VERIFIED_TTL_MS);
  // Stored CONNECTED is historical, not a live socket/heartbeat.
  const recentlyVerified=Boolean(binding?.is_active)
    && binding?.connection_state==="CONNECTED"&&fresh;
  return {
    ok:true,auth:"GOOGLE_FOUNDER",account:binding?{
      login:String(binding.account_login),server:String(binding.server),
      mode:"DEMO",recentlyVerified,verifiedAt:checked?.toISOString()??null,
      connectionStatus:recentlyVerified?"RECENT_DEMO_VERIFY":"STALE_OR_DISCONNECTED"
    }:null,
    trading:{status:"LOCKED",autoTradeActive:false,
      modelApproved:Number(gate?.approved_models??0)>0,
      riskApproved:gate?.risk_profile_approved===true,
      demoSendEnabled:gate?.demo_send_enabled===true,
      runtimeEnabled:gate?.enabled===true,
      the5ersReadiness:String(gate?.the5ers_readiness??"UNKNOWN"),
      brokerOrders:false,liveMoneyLocked:true}
  };
}
async function verifyStoredDemo(req:Request,id:number){
  const length=Number(req.headers.get("content-length")??0);
  if(length>1024)return {code:413,body:{ok:false,status:"PAYLOAD_TOO_LARGE"}};
  const raw=await req.text();
  if(raw.length>1024)return {code:413,body:{ok:false,status:"PAYLOAD_TOO_LARGE"}};
  let payload:unknown;
  try{payload=JSON.parse(raw)}catch{return {code:400,body:{ok:false,status:"INVALID_JSON"}}}
  let login:string,server:string,password:string;
  try{
    ({login,server,password}=parseFounderDemoLogin(payload));
  }catch{
    return {code:400,body:{ok:false,status:"INVALID_DEMO_CREDENTIAL_FORMAT"}};
  }
  // Require this exact account to be already linked to this Founder.
  // A broker login must use the supplied password, not a historical Vault match.
  const rows=await sql`
    select b.id from ai_trade.account_mt5_bindings b
    join ai_trade.mt5_demo_accounts a
      on a.account_login=b.account_login and a.server=b.server
    where b.access_token_id=${id}
      and b.account_login=${login}::bigint
      and b.server=${server} and b.account_type='DEMO'
      and a.account_type='DEMO' and a.is_active=true
    limit 1
  `;
  if(rows.length!==1){
    return {code:403,body:{ok:false,status:"FOUNDER_DEMO_NOT_LINKED",
      brokerOrders:false,liveMoneyLocked:true}};
  }
  // Re-verification invalidates historical CONNECTED even if broker times out.
  // No credential is stored in a table, Vault, a device or an application log.
  const disconnected=await sql`
    update ai_trade.account_mt5_bindings set
      connection_state='DISCONNECTED',last_verified_at=null,updated_at=now()
    where access_token_id=${id} and account_login=${login}::bigint
      and server=${server} and account_type='DEMO'
      and connection_state!='REVOKED'
    returning id
  `;
  if(disconnected.length!==1){
    return {code:409,body:{ok:false,status:"BINDING_CHANGED",
      brokerOrders:false,liveMoneyLocked:true}};
  }
  // Internal verifier authenticates on the real broker using transient input.
  // Its permitted broker commands are bootstrap/init/login/account only.
  const [cron]=await sql`select secret from ai_trade.cron_auth where id=1`;
  const secret=String(cron?.secret??"");
  if(!secret)return {code:503,body:{ok:false,status:"BROKER_VERIFIER_UNAVAILABLE"}};
  let data:Record<string,unknown>;
  try{
    const result=await fetch(URL_ROOT+"/functions/v1/ai-trade-mt5-demo-validate",{
      method:"POST",
      headers:{"content-type":"application/json","x-ai-trade-cron":secret},
      body:JSON.stringify({login,readback:"founder_verify",verifyPassword:password}),
      cache:"no-store",
      signal:AbortSignal.timeout(120000)
    });
    data=await result.json();
    if(!result.ok)throw new Error("BROKER_VERIFIER_UNAVAILABLE");
  }catch{
    return {code:503,body:{ok:false,status:"BROKER_VERIFICATION_UNAVAILABLE",
      brokerOrders:false,liveMoneyLocked:true}};
  }
  if(data.verified!==true||data.status!=="DEMO_VERIFIED"
      ||data.accountType!==1||data.server!==server
      ||String(data.login)!==login
      ||data.brokerOrders!==false||data.liveMoneyLocked!==true){
    return {code:403,body:{ok:false,status:"BROKER_DEMO_NOT_VERIFIED",
      brokerOrders:false,liveMoneyLocked:true}};
  }
  // Snapshot values must originate in the same fresh broker verifier response.
  // Missing data stays BLOCKED; never substitute historical database fields.
  if(typeof data.balance!=="number"||!Number.isFinite(data.balance)
      ||typeof data.currency!=="string"
      ||!/^[A-Z]{3,8}$/.test(data.currency)){
    return {code:503,body:{ok:false,status:"BROKER_READBACK_INCOMPLETE",
      brokerOrders:false,liveMoneyLocked:true}};
  }
  const updated=await sql`
    update ai_trade.account_mt5_bindings set
      connection_state='CONNECTED',last_verified_at=now(),updated_at=now()
    where access_token_id=${id}
      and account_login=${login}::bigint
      and server='MetaQuotes-Demo' and account_type='DEMO'
      and connection_state='DISCONNECTED'
    returning id
  `;
  if(updated.length!==1)return {code:409,body:{ok:false,status:"BINDING_CHANGED"}};
  return {code:200,body:{
    ok:true,status:"DEMO_VERIFIED_READ_ONLY",server:"MetaQuotes-Demo",
    login,verifiedAt:new Date().toISOString(),
    balance:data.balance,currency:data.currency,readbackSource:"MT5_DEMO_VERIFIER",
    equity:null,positions:null,
    passwordStoredOnDevice:false,passwordExposed:false,
    autoTradeActive:false,brokerOrders:false,liveMoneyLocked:true
  }};
}
/** One fresh broker read for the authenticated Founder's existing DEMO account. */
async function freshSnapshot(id:number){
  const [binding]=await sql`
    select b.account_login,b.server from ai_trade.account_mt5_bindings b
    join ai_trade.mt5_demo_accounts a
      on a.account_login=b.account_login and a.server=b.server
    where b.access_token_id=${id}
      and b.account_type='DEMO' and b.server='MetaQuotes-Demo'
      and a.account_type='DEMO' and a.is_active=true
    limit 1
  `;
  if(!binding)return {code:404,body:{ok:false,status:"FOUNDER_DEMO_NOT_LINKED",
    brokerOrders:false,liveMoneyLocked:true}};
  const login=String(binding.account_login);
  const [cron]=await sql`select secret from ai_trade.cron_auth where id=1`;
  const secret=String(cron?.secret??"");
  if(!secret)return {code:503,body:{ok:false,status:"BROKER_VERIFIER_UNAVAILABLE",
    brokerOrders:false,liveMoneyLocked:true}};
  let data:Record<string,unknown>;
  try{
    const response=await fetch(URL_ROOT+"/functions/v1/ai-trade-mt5-demo-validate",{
      method:"POST",
      headers:{"content-type":"application/json","x-ai-trade-cron":secret},
      body:JSON.stringify({login,readback:"investor_snapshot"}),
      cache:"no-store",signal:AbortSignal.timeout(120000)
    });
    if(!response.ok)throw new Error("UPSTREAM_UNAVAILABLE");
    data=await response.json();
  }catch{
    return {code:503,body:{ok:false,status:"BROKER_SNAPSHOT_UNAVAILABLE",
      brokerOrders:false,liveMoneyLocked:true}};
  }
  if(data.verified!==true||data.status!=="DEMO_VERIFIED"
      ||data.accountType!==1||data.mode!=="DEMO"
      ||data.server!==binding.server||String(data.login)!==login
      ||data.readbackSource!=="MT5_INVESTOR_BROKER"
      ||data.readOnly!==true||data.credentialScope!=="INVESTOR_READ_ONLY"
      ||data.brokerOrders!==false||data.liveMoneyLocked!==true
      ||typeof data.balance!=="number"||!Number.isFinite(data.balance)
      ||typeof data.equity!=="number"||!Number.isFinite(data.equity)
      ||typeof data.currency!=="string"||!/^[A-Z]{3,8}$/.test(data.currency)
      ||!Array.isArray(data.positions)||data.positions.length>1000){
    return {code:503,body:{ok:false,status:"FRESH_BROKER_DEMO_READBACK_FAILED",
      brokerOrders:false,liveMoneyLocked:true}};
  }
  // The broker must explicitly return the list; [] means zero positions.
  // Missing/null positions never become an empty or historical list.
  const tickets=new Set<string>();
  const positions:Record<string,unknown>[]=[];
  for(const item of data.positions){
    if(!item||typeof item!=="object"||Array.isArray(item)){
      return {code:503,body:{ok:false,status:"BROKER_POSITIONS_INVALID",
        brokerOrders:false,liveMoneyLocked:true}};
    }
    const p=item as Record<string,unknown>;
    if(typeof p.ticket!=="string"||!/^[1-9][0-9]{0,19}$/.test(p.ticket)
        ||tickets.has(p.ticket)
        ||typeof p.symbol!=="string"
        ||!/^[A-Za-z0-9._-]{2,32}$/.test(p.symbol)
        ||(p.side!=="BUY"&&p.side!=="SELL")
        ||typeof p.lot!=="number"||!Number.isFinite(p.lot)||p.lot<=0
        ||typeof p.pnl!=="number"||!Number.isFinite(p.pnl)
        ||typeof p.openPrice!=="number"||!Number.isFinite(p.openPrice)||p.openPrice<0
        ||typeof p.sl!=="number"||!Number.isFinite(p.sl)||p.sl<0
        ||typeof p.tp!=="number"||!Number.isFinite(p.tp)||p.tp<0){
      return {code:503,body:{ok:false,status:"BROKER_POSITIONS_INVALID",
        brokerOrders:false,liveMoneyLocked:true}};
    }
    tickets.add(p.ticket);
    positions.push({ticket:p.ticket,symbol:p.symbol,side:p.side,lot:p.lot,
      pnl:p.pnl,openPrice:p.openPrice,sl:p.sl,tp:p.tp});
  }
  const observed=typeof data.asOf==="string"?new Date(data.asOf):null;
  const age=observed?Date.now()-observed.getTime():Number.NaN;
  if(!Number.isFinite(age)||age < -5000||age > 120000){
    return {code:503,body:{ok:false,status:"BROKER_SNAPSHOT_STALE",
      brokerOrders:false,liveMoneyLocked:true}};
  }
  const updated=await sql`
    update ai_trade.account_mt5_bindings set
      connection_state='CONNECTED',last_verified_at=now(),updated_at=now()
    where access_token_id=${id}
      and account_login=${login}::bigint
      and server='MetaQuotes-Demo' and account_type='DEMO'
    returning id
  `;
  if(updated.length!==1)return {code:409,body:{ok:false,status:"BINDING_CHANGED"}};
  return {code:200,body:{
    ok:true,status:"DEMO_SNAPSHOT_READ_ONLY",
    login,server:"MetaQuotes-Demo",mode:"DEMO",
    balance:data.balance,currency:data.currency,
    equity:data.equity,positions,asOf:observed!.toISOString(),
    readbackSource:"MT5_INVESTOR_BROKER",
    autoTradeActive:false,brokerOrders:false,liveMoneyLocked:true
  }};
}

Deno.serve(async(req)=>{
  const origin=req.headers.get("origin")??"";
  if(origin&&!ALLOWED_ORIGINS.has(origin)){
    return respond({ok:false,status:"ORIGIN_NOT_ALLOWED"},403,origin);
  }
  if(req.method==="OPTIONS")return new Response(null,{status:204,headers:{
    "access-control-allow-origin":origin||"https://trankhanhduy1508-maker.github.io",
    "vary":"origin","access-control-allow-methods":"GET,POST,OPTIONS",
    "access-control-allow-headers":"authorization,content-type,apikey",
    "access-control-max-age":"600","cache-control":"no-store"
  }});
  if(!["GET","POST"].includes(req.method))
    return respond({ok:false,status:"METHOD_NOT_ALLOWED"},405,origin);
  try{
    const person=await founder(req);
    if(!person)return respond({ok:false,status:"GOOGLE_FOUNDER_REQUIRED"},401,origin);
    const path=new URL(req.url).pathname;
    if(req.method==="GET"&&path.endsWith("/status"))
      return respond(await status(person.id),200,origin);
    if(req.method==="POST"&&path.endsWith("/snapshot")){
      const value=await freshSnapshot(person.id);
      return respond(value.body,value.code,origin);
    }
    if(req.method==="POST"&&path.endsWith("/verify-demo")){
      const result=await verifyStoredDemo(req,person.id);
      return respond(result.body,result.code,origin);
    }
    return respond({ok:false,status:"NOT_FOUND"},404,origin);
  }catch(error){
    // Never return database errors, upstream request bodies, passwords or tokens.
    const authFailed=error instanceof Error&&error.message==="GOOGLE_AUTH_NOT_CONFIGURED";
    return respond({ok:false,status:authFailed?"AUTH_UNAVAILABLE":"REQUEST_FAILED",
      brokerOrders:false,liveMoneyLocked:true},authFailed?503:500,origin);
  }
});
