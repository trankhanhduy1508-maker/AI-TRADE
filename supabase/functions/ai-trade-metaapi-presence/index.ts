import postgres from "npm:postgres@3.4.9";

const sql=postgres(Deno.env.get("SUPABASE_DB_URL")!,{prepare:false,max:1,connect_timeout:10,idle_timeout:20});
const json=(b:unknown,s=200)=>new Response(JSON.stringify(b),{status:s,headers:{"content-type":"application/json; charset=utf-8"}});

async function authorized(req:Request){
  const rows=await sql`select secret from ai_trade.cron_auth where id=1`;
  const expected=String(rows[0]?.secret??"");
  return Boolean(expected)&&(req.headers.get("x-ai-trade-cron")??"")===expected;
}

Deno.serve(async(req)=>{
  if(!(await authorized(req))) return json({ok:false,status:"UNAUTHORIZED"},401);
  const hasToken=Boolean(Deno.env.get("METAAPI_TOKEN")?.trim());
  const hasAccountId=Boolean(Deno.env.get("METAAPI_ACCOUNT_ID")?.trim());
  return json({
    ok:true,
    status:hasToken&&hasAccountId?"METAAPI_CONFIG_PRESENT":"METAAPI_CONFIG_MISSING",
    hasMetaApiToken:hasToken,
    hasMetaApiAccountId:hasAccountId,
    secretValuesExposed:false,
    brokerOrders:false,
    liveMoneyLocked:true
  });
});