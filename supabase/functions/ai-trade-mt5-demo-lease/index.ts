import { createRemoteJWKSet, jwtVerify } from "npm:jose@6.1.0";
import postgres from "npm:postgres@3.4.9";

const sql=postgres(Deno.env.get("SUPABASE_DB_URL")!,{
  prepare:false,max:1,connect_timeout:10,idle_timeout:20
});
const JWKS=createRemoteJWKSet(new URL("https://token.actions.githubusercontent.com/.well-known/jwks"));
const ISSUER="https://token.actions.githubusercontent.com";
const AUDIENCE="ai-trade-mt5-demo-lease";
const REPOSITORY="trankhanhduy1508-maker/AI-TRADE";
const ACTOR="trankhanhduy1508-maker";
const WORKFLOW="MT5 Demo Protocol Probe";
const PR_REF_PREFIX="refs/pull/2/";
// A preflight lease can never authorize order submission. A future DEMO
// execution lane needs a separate Founder-approved, server-enforced Risk Engine.
const ALLOWED_PURPOSES=new Set(["preflight"]);

const json=(body:unknown,status=200)=>new Response(JSON.stringify(body),{
  status,headers:{"content-type":"application/json; charset=utf-8",
    "cache-control":"no-store","x-content-type-options":"nosniff"}
});
const bearer=(req:Request)=>{
  const h=req.headers.get("authorization")??"";
  return h.startsWith("Bearer ")?h.slice(7).trim():"";
};

Deno.serve(async(req)=>{
  try{
    if(req.method!=="POST") return json({ok:false,status:"METHOD_NOT_ALLOWED"},405);
    const token=bearer(req);
    if(!token) return json({ok:false,status:"MISSING_OIDC"},401);

    const verified=await jwtVerify(token,JWKS,{issuer:ISSUER,audience:AUDIENCE});
    const p=verified.payload as Record<string,unknown>;
    if(
      p.repository!==REPOSITORY ||
      p.actor!==ACTOR ||
      p.event_name!=="pull_request" ||
      typeof p.ref!=="string" ||
      !p.ref.startsWith(PR_REF_PREFIX) ||
      p.workflow!==WORKFLOW
    ){
      return json({ok:false,status:"OIDC_CLAIM_REJECTED"},403);
    }

    const body=await req.json().catch(()=>({})) as {purpose?:string;runId?:string};
    const purpose=String(body.purpose??"");
    const runId=String(body.runId??"");
    if(!ALLOWED_PURPOSES.has(purpose)) return json({ok:false,status:"PURPOSE_REJECTED"},403);
    if(String(p.run_id??"")!==runId) return json({ok:false,status:"RUN_ID_MISMATCH"},403);

    const rows=await sql`
      select a.account_login,a.server,a.account_type,
             investor.decrypted_secret as investor_password
      from ai_trade.mt5_demo_accounts a
      left join vault.decrypted_secrets investor
        on investor.id=a.investor_password_secret_id
      where a.is_active=true and a.account_type='DEMO'
      order by a.last_verified_at desc nulls last,a.created_at desc
      limit 1
    `;
    const row=rows[0];
    if(!row || !row.investor_password) return json({
      ok:false,status:"NO_READ_ONLY_DEMO_CREDENTIAL",
      brokerOrdersAllowed:false,liveMoneyLocked:true
    },404);
    const server=String(row.server??"");
    if(!server.toLowerCase().includes("demo")) return json({ok:false,status:"SERVER_NOT_DEMO"},403);

    return json({
      ok:true,
      status:"MT5_DEMO_LEASE",
      purpose,
      login:Number(row.account_login),
      server,
      accountType:"DEMO",
      password:String(row.investor_password),
      credentialScope:"INVESTOR_READ_ONLY",
      brokerOrdersAllowed:false,
      liveMoneyLocked:true
    });
  }catch{
    // Never return Vault, JWT or SQL exception details to any caller.
    return json({ok:false,status:"MT5_DEMO_LEASE_FAILED",
      brokerOrdersAllowed:false,liveMoneyLocked:true},500);
  }
});
