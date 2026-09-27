import postgres from "npm:postgres@3.4.9";

const sql=postgres(Deno.env.get("SUPABASE_DB_URL")!,{
  prepare:false,max:1,connect_timeout:10,idle_timeout:20
});
const json=(body:unknown,status=200)=>new Response(JSON.stringify(body),{
  status,headers:{"content-type":"application/json; charset=utf-8"}
});

async function authorized(req:Request){
  const rows=await sql`select secret from ai_trade.cron_auth where id=1`;
  const expected=String(rows[0]?.secret??"");
  return Boolean(expected)&&(req.headers.get("x-ai-trade-cron")??"")===expected;
}

function n(value:unknown){
  const parsed=Number(value);
  if(!Number.isFinite(parsed)) throw new Error("INVALID_NUMBER");
  return parsed;
}

Deno.serve(async(req)=>{
  try{
    if(!(await authorized(req))) return json({ok:false,status:"UNAUTHORIZED"},401);
    const body=await req.json().catch(()=>({}));
    const rows=await sql`
      select provider,program,phase,initial_balance,profit_target_pct,max_loss_pct,
             automation_approval_verified,enabled,rules_checked_at
      from ai_trade.prop_program_config
      where provider='THE5ERS'
    `;
    const cfg=rows[0];
    if(!cfg) throw new Error("BOOTCAMP_CONFIG_MISSING");

    const balance=n(body.balance);
    const equity=n(body.equity);
    const visibleStop=Boolean(body.visibleStop);
    const accountIsDemo=body.accountIsDemo===true;
    const projectedLoss=body.projectedLossAtStop==null?null:n(body.projectedLossAtStop);

    const initial=n(cfg.initial_balance);
    const target=initial*(1+n(cfg.profit_target_pct));
    const floor=initial*(1-n(cfg.max_loss_pct));
    const remaining=Math.max(0,Math.min(balance,equity)-floor);
    const projectedEquity=projectedLoss==null?null:equity-projectedLoss;

    const reasons:string[]=[];
    if(!cfg.enabled) reasons.push("BOOTCAMP_EXECUTION_DISABLED");
    if(!cfg.automation_approval_verified) reasons.push("AUTOMATION_APPROVAL_REQUIRED");
    if(!accountIsDemo) reasons.push("BOOTCAMP_DEMO_ACCOUNT_REQUIRED");
    if(!visibleStop) reasons.push("VISIBLE_STOP_LOSS_REQUIRED");
    if(balance<=floor||equity<=floor) reasons.push("MAX_LOSS_REACHED");
    if(projectedLoss!=null){
      if(projectedLoss<=0) reasons.push("PROJECTED_LOSS_INVALID");
      if(projectedEquity!==null&&projectedEquity<=floor) reasons.push("PROJECTED_STOP_BREACHES_MAX_LOSS");
      if(projectedLoss>remaining) reasons.push("INTENT_EXCEEDS_REMAINING_LOSS_BUDGET");
    }
    const unique=[...new Set(reasons)];
    const achieved=Math.max(0,balance-initial);
    const targetDistance=target-initial;
    const progress=Math.min(1,targetDistance>0?achieved/targetDistance:1);
    const decision=unique.length===0?"ALLOWED":"BLOCKED";

    await sql`
      insert into ai_trade.prop_guard_events(
        provider,balance,equity,projected_loss_at_stop,visible_stop,
        decision,reasons,details
      ) values(
        'THE5ERS',${balance},${equity},${projectedLoss},${visibleStop},
        ${decision},${JSON.stringify(unique)}::jsonb,
        ${JSON.stringify({
          phase:Number(cfg.phase),targetBalance:target,lossFloor:floor,
          remainingLossBudget:remaining,progressToTarget:progress,
          accountIsDemo,automationApprovalVerified:Boolean(cfg.automation_approval_verified),
          executionEnabled:Boolean(cfg.enabled)
        })}::jsonb
      )
    `;

    return json({
      ok:true,
      provider:"THE5ERS",
      program:"BOOTCAMP",
      phase:Number(cfg.phase),
      decision,
      reasons:unique,
      initialBalance:initial,
      targetBalance:target,
      lossFloor:floor,
      remainingLossBudget:remaining,
      progressToTarget:progress,
      projectedEquityAtStop:projectedEquity,
      automationApprovalVerified:Boolean(cfg.automation_approval_verified),
      executionEnabled:Boolean(cfg.enabled),
      liveMoneyLocked:true
    });
  }catch(error){
    return json({ok:false,status:"ERROR",message:error instanceof Error?error.message:String(error)},500);
  }
});