import { createRemoteJWKSet, jwtVerify } from "npm:jose@6.1.0";
import postgres from "npm:postgres@3.4.9";

const sql=postgres(Deno.env.get("SUPABASE_DB_URL")!,{
  prepare:false,max:1,connect_timeout:10,idle_timeout:20
});

const JWKS=createRemoteJWKSet(
  new URL("https://token.actions.githubusercontent.com/.well-known/jwks")
);
const ISSUER="https://token.actions.githubusercontent.com";
const AUDIENCE="ai-trade-mt5-vault";
const REPOSITORY="trankhanhduy1508-maker/AI-TRADE";
const ACTOR="trankhanhduy1508-maker";
const WORKFLOW="MT5 Demo Protocol Probe";
const PR_REF_PREFIX="refs/pull/2/";

const json=(body:unknown,status=200)=>new Response(JSON.stringify(body),{
  status,
  headers:{"content-type":"application/json; charset=utf-8"}
});

function bearer(req:Request){
  const h=req.headers.get("authorization")??"";
  return h.startsWith("Bearer ")?h.slice(7).trim():"";
}

Deno.serve(async(req)=>{
  try{
    if(req.method!=="POST") return json({ok:false,status:"METHOD_NOT_ALLOWED"},405);
    const token=bearer(req);
    if(!token) return json({ok:false,status:"MISSING_OIDC"},401);

    const verified=await jwtVerify(token,JWKS,{
      issuer:ISSUER,
      audience:AUDIENCE,
    });
    const p=verified.payload as Record<string,unknown>;

    if(
      p.repository!==REPOSITORY ||
      p.actor!==ACTOR ||
      p.event_name!=="pull_request" ||
      typeof p.ref!=="string" ||
      !p.ref.startsWith(PR_REF_PREFIX) ||
      p.workflow!==WORKFLOW
    ){
      return json({
        ok:false,
        status:"OIDC_CLAIM_REJECTED",
        repository:p.repository??null,
        event_name:p.event_name??null,
        workflow:p.workflow??null,
        ref:p.ref??null,
      },403);
    }

    const body=await req.json() as {
      login?:number|string;
      server?:string;
      password?:string;
      investorPassword?:string;
      accountType?:string;
      runId?:string;
    };

    const login=Number(body.login);
    const server=String(body.server??"").trim();
    const password=String(body.password??"");
    const investorPassword=String(body.investorPassword??"");
    const accountType=String(body.accountType??"").toUpperCase();
    const runId=String(body.runId??"");

    if(
      !Number.isSafeInteger(login) || login<=0 ||
      !server || !server.toLowerCase().includes("demo") ||
      accountType!=="DEMO" ||
      password.length<4
    ){
      return json({ok:false,status:"INVALID_DEMO_PAYLOAD"},400);
    }

    if(String(p.run_id??"")!==runId){
      return json({ok:false,status:"RUN_ID_MISMATCH"},403);
    }

    await sql`
      select ai_trade.upsert_mt5_demo_account(
        ${login}::bigint,
        ${server},
        ${password},
        ${investorPassword},
        'github-actions-oidc',
        ${runId}
      )
    `;

    return json({
      ok:true,
      status:"MT5_DEMO_CREDENTIALS_STORED",
      login,
      server,
      passwordStoredInVault:true,
      passwordExposed:false,
      brokerOrders:false,
      liveMoneyLocked:true,
    });
  }catch(error){
    return json({
      ok:false,
      status:"MT5_DEMO_CREDENTIAL_INGEST_FAILED",
      error:error instanceof Error?error.name:"Error",
      detail:error instanceof Error?error.message.slice(0,240):String(error).slice(0,240),
      passwordExposed:false,
      brokerOrders:false,
      liveMoneyLocked:true,
    },500);
  }
});
