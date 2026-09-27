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
const ALLOWED_PURPOSES=new Set(["preflight","technical_smoke","demo_forward"]);

const json=(body:unknown,status=200)=>new Response(JSON.stringify(body),{
  status,headers:{"content-type":"application/json; charset=utf-8"}
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
             ds.decrypted_secret as password
      from ai_trade.mt5_demo_accounts a
      join vault.decrypted_secrets ds on ds.id=a.password_secret_id
      where a.is_active=true and a.account_type='DEMO'
      order by a.last_verified_at desc nulls last,a.created_at desc
      limit 1
    `;
    const row=rows[0];
    if(!row || !row.password) return json({ok:false,status:"NO_ACTIVE_DEMO_CREDENTIAL"},404);
    const server=String(row.server??"");
    if(!server.toLowerCase().includes("demo")) return json({ok:false,status:"SERVER_NOT_DEMO"},403);

    return json({
      ok:true,
      status:"MT5_DEMO_LEASE",
      purpose,
      login:Number(row.account_login),
      server,
      accountType:"DEMO",
      password:String(row.password),
      brokerOrdersAllowed:purpose!=="preflight",
      liveMoneyLocked:true
    });
  }catch(error){
    return json({
      ok:false,status:"MT5_DEMO_LEASE_FAILED",
      error:error instanceof Error?error.name:"Error",
      detail:error instanceof Error?error.message.slice(0,200):String(error).slice(0,200)
    },500);
  }
});
