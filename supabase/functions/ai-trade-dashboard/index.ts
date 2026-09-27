import postgres from "npm:postgres@3.4.9";

const sql=postgres(Deno.env.get("SUPABASE_DB_URL")!,{
  prepare:false,max:1,connect_timeout:10,idle_timeout:20
});

function esc(v:unknown){
  return String(v??"")
    .replaceAll("&","&amp;")
    .replaceAll("<","&lt;")
    .replaceAll(">","&gt;")
    .replaceAll('"',"&quot;");
}

function pct(value:number,target:number){
  if(target<=0)return 0;
  return Math.max(0,Math.min(100,Math.round(value/target*100)));
}

function fmtR(v:unknown){
  const n=Number(v??0);
  if(!Number.isFinite(n))return "—";
  return (n>0?"+":"")+n.toFixed(2)+"R";
}

function badgeClass(kind:string){
  if(["ACTIVE","PASS","CONNECTED","COLLECTING"].includes(kind))return "good";
  if(["BLOCKED_APPROVAL","LOCKED","WAITING"].includes(kind))return "warn";
  if(["FAIL","ERROR","FORWARD_REJECT"].includes(kind))return "bad";
  return "muted";
}

async function validToken(token:string){
  if(!token)return false;
  const rows=await sql`
    select id
    from ai_trade.dashboard_access_tokens
    where token_hash=encode(digest(${token},'sha256'),'hex')
      and revoked_at is null
      and expires_at>now()
    limit 1
  `;
  return Boolean(rows[0]?.id);
}

Deno.serve(async(req)=>{
  const url=new URL(req.url);
  const token=url.searchParams.get("t")??"";
  if(!(await validToken(token))){
    return new Response("<h1>Liên kết dashboard không hợp lệ hoặc đã hết hạn.</h1>",{
      status:403,
      headers:{
        "content-type":"text/html; charset=utf-8",
        "cache-control":"no-store",
        "referrer-policy":"no-referrer"
      }
    });
  }

  const [readiness]=await sql`
    select *
    from ai_trade.forward_validation_readiness
    where strategy_id='TF-013A-FORWARD-DIVERSIFIED-TREND'
    limit 1
  `;

  const crons=await sql`
    select jobname,schedule,active
    from cron.job
    where jobname in (
      'ai-trade-forward-shadow-daily',
      'ai-trade-shadow-broker-reconcile-daily',
      'ai-trade-forward-evaluate-daily'
    )
    order by schedule
  `;

  const [counts]=await sql`
    select
      (select count(*) from ai_trade.forward_shadow_state
        where strategy_id='TF-013A-FORWARD-DIVERSIFIED-TREND')::int as forward_states,
      (select count(*) from ai_trade.forward_shadow_trades
        where strategy_id='TF-013A-FORWARD-DIVERSIFIED-TREND')::int as forward_trades,
      (select count(*) from ai_trade.shadow_broker_orders
        where strategy_id='TF-013A-FORWARD-DIVERSIFIED-TREND')::int as shadow_orders,
      (select count(*) from ai_trade.shadow_broker_positions
        where strategy_id='TF-013A-FORWARD-DIVERSIFIED-TREND')::int as shadow_positions,
      (select count(*) from ai_trade.shadow_broker_runs
        where strategy_id='TF-013A-FORWARD-DIVERSIFIED-TREND')::int as shadow_runs
  `;

  const [demo]=await sql`
    select server,account_type,is_active,last_verified_at,source
    from ai_trade.mt5_demo_accounts
    where account_type='DEMO' and is_active=true
    order by last_verified_at desc nulls last
    limit 1
  `;

  const [gates]=await sql`
    select
      (select readiness from ai_trade.bootcamp_readiness where provider='THE5ERS') as the5ers_readiness,
      (select risk_profile_approved from ai_trade.runtime_config where id=1) as risk_profile_approved,
      (select demo_send_enabled from ai_trade.runtime_config where id=1) as demo_send_enabled,
      (select automation_approval_verified from ai_trade.prop_program_config where provider='THE5ERS') as automation_approval_verified
  `;

  if(url.searchParams.get("format")==="json"){
    const payload={
      ok:true,
      evaluation:{
        state:String(readiness?.evaluation_state??"COLLECTING"),
        closedTrades:Number(readiness?.closed_trades??0),
        elapsedDays:Number(readiness?.elapsed_days??0),
        marketsWithTrades:Number(readiness?.markets_with_trades??0),
        positiveMarkets:Number(readiness?.positive_markets??0),
        netR10bps:Number(readiness?.net_r_10bps??0),
        expectancyR10bps:Number(readiness?.expectancy_r_10bps??0),
        profitFactorR10bps:readiness?.profit_factor_r_10bps==null?null:Number(readiness.profit_factor_r_10bps),
        maxDrawdownR10bps:Number(readiness?.max_drawdown_r_10bps??0),
        netR20bps:Number(readiness?.net_r_20bps??0),
        flaggedBars:Number(readiness?.flagged_bars??0),
        entryWithoutVisibleStop:Number(readiness?.entry_without_visible_stop??0)
      },
      counts:{
        forwardStates:Number(counts?.forward_states??0),
        forwardTrades:Number(counts?.forward_trades??0),
        shadowOrders:Number(counts?.shadow_orders??0),
        shadowPositions:Number(counts?.shadow_positions??0),
        shadowRuns:Number(counts?.shadow_runs??0)
      },
      crons:crons.map((c:any)=>({
        jobname:String(c.jobname),
        schedule:String(c.schedule),
        active:Boolean(c.active)
      })),
      mt5:{
        connected:Boolean(demo?.is_active),
        server:String(demo?.server??""),
        accountType:String(demo?.account_type??""),
        lastVerifiedAt:demo?.last_verified_at?new Date(demo.last_verified_at).toISOString():null
      },
      gates:{
        the5ersReadiness:String(gates?.the5ers_readiness??""),
        automationApprovalVerified:Boolean(gates?.automation_approval_verified),
        riskProfileApproved:Boolean(gates?.risk_profile_approved),
        demoSendEnabled:Boolean(gates?.demo_send_enabled),
        liveMoneyLocked:true
      },
      updatedAt:new Date().toISOString()
    };
    return new Response(JSON.stringify(payload),{
      status:200,
      headers:{
        "content-type":"application/json; charset=utf-8",
        "cache-control":"no-store, max-age=0",
        "access-control-allow-origin":"*",
        "referrer-policy":"no-referrer"
      }
    });
  }

  const closed=Number(readiness?.closed_trades??0);
  const days=Number(readiness?.elapsed_days??0);
  const markets=Number(readiness?.markets_with_trades??0);
  const evalState=String(readiness?.evaluation_state??"COLLECTING");
  const updated=new Date().toLocaleString("vi-VN",{timeZone:"Asia/Ho_Chi_Minh",hour12:false});

  const cronCards=crons.map((c:any)=>{
    const label=
      c.jobname==="ai-trade-forward-shadow-daily"?"1. Tín hiệu forward":
      c.jobname==="ai-trade-shadow-broker-reconcile-daily"?"2. Shadow Broker":
      "3. Chấm điểm";
    const time=c.schedule.startsWith("15 3")?"10:15 VN":
      c.schedule.startsWith("20 3")?"10:20 VN":
      c.schedule.startsWith("25 3")?"10:25 VN":c.schedule;
    return `<div class="step">
      <div><strong>${esc(label)}</strong><span>${esc(time)}</span></div>
      <b class="pill ${c.active?"good":"bad"}">${c.active?"ACTIVE":"OFF"}</b>
    </div>`;
  }).join("");

  const html=`<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta http-equiv="refresh" content="30">
<meta name="theme-color" content="#0b0d12">
<title>AI-TRADE Forward Monitor</title>
<style>
:root{color-scheme:dark;--bg:#0b0d12;--card:#151922;--line:#262d3a;--text:#f4f6fb;--sub:#939cad;--green:#53d18b;--yellow:#f1c75b;--red:#ff6b6b;--blue:#71a7ff}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:860px;margin:auto;padding:20px 14px 60px}.top{display:flex;align-items:flex-start;justify-content:space-between;gap:14px;margin:8px 2px 20px}
h1{font-size:24px;line-height:1.1;margin:0 0 7px}.sub{color:var(--sub);font-size:13px}.live{display:flex;align-items:center;gap:8px;font-size:12px;color:var(--green);white-space:nowrap}.dot{width:9px;height:9px;border-radius:50%;background:var(--green);box-shadow:0 0 12px var(--green)}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:15px}
.metric strong{display:block;font-size:24px;margin:4px 0}.metric small{color:var(--sub)}.bar{height:9px;border-radius:99px;background:#252b36;overflow:hidden;margin-top:12px}.fill{height:100%;border-radius:99px;background:linear-gradient(90deg,#547cff,#7ca9ff)}
.section{margin-top:16px}.section h2{font-size:15px;margin:0 0 10px;color:#dfe5f0}.step{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:13px 14px;display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}.step div{display:flex;flex-direction:column;gap:3px}.step span{font-size:12px;color:var(--sub)}
.pill{padding:5px 9px;border-radius:99px;font-size:11px;letter-spacing:.02em}.good{background:rgba(83,209,139,.12);color:var(--green)}.warn{background:rgba(241,199,91,.12);color:var(--yellow)}.bad{background:rgba(255,107,107,.12);color:var(--red)}.muted{background:#242a34;color:#aab2c0}
.two{display:grid;grid-template-columns:1fr 1fr;gap:10px}.row{display:flex;justify-content:space-between;gap:12px;padding:9px 0;border-bottom:1px solid var(--line)}.row:last-child{border:0}.row span{color:var(--sub)}.row b{text-align:right}
.hero{display:flex;align-items:center;justify-content:space-between;gap:10px}.hero strong{font-size:18px}.footer{margin-top:18px;color:var(--sub);font-size:12px;line-height:1.5}.refresh{display:inline-block;margin-top:10px;color:#c7d7ff;text-decoration:none;border:1px solid var(--line);padding:8px 11px;border-radius:10px}
@media(max-width:640px){main{padding-top:14px}.grid{grid-template-columns:1fr}.two{grid-template-columns:1fr}.top{align-items:center}h1{font-size:22px}.metric{display:grid;grid-template-columns:1fr auto;align-items:end}.metric .bar{grid-column:1/-1}}
</style>
</head>
<body><main>
  <div class="top">
    <div><h1>AI-TRADE Forward Monitor</h1><div class="sub">TF-013A · tự cập nhật mỗi 30 giây</div></div>
    <div class="live"><i class="dot"></i> LIVE</div>
  </div>

  <div class="card hero">
    <div><div class="sub">Trạng thái kiểm chứng</div><strong>${esc(evalState)}</strong></div>
    <b class="pill ${badgeClass(evalState)}">${esc(evalState)}</b>
  </div>

  <div class="section"><h2>Tiến độ đủ mẫu</h2>
    <div class="grid">
      <div class="card metric"><small>Closed trades</small><strong>${closed}/50</strong><div class="bar"><div class="fill" style="width:${pct(closed,50)}%"></div></div></div>
      <div class="card metric"><small>Số ngày</small><strong>${days}/120</strong><div class="bar"><div class="fill" style="width:${pct(days,120)}%"></div></div></div>
      <div class="card metric"><small>Market có trade</small><strong>${markets}/8</strong><div class="bar"><div class="fill" style="width:${pct(markets,8)}%"></div></div></div>
    </div>
  </div>

  <div class="section"><h2>Pipeline tự động mỗi ngày</h2>${cronCards}</div>

  <div class="section two">
    <div class="card">
      <h2>Forward performance</h2>
      <div class="row"><span>Net R @ 10bps</span><b>${fmtR(readiness?.net_r_10bps)}</b></div>
      <div class="row"><span>Expectancy</span><b>${fmtR(readiness?.expectancy_r_10bps)}</b></div>
      <div class="row"><span>Profit factor</span><b>${readiness?.profit_factor_r_10bps==null?"—":Number(readiness.profit_factor_r_10bps).toFixed(2)}</b></div>
      <div class="row"><span>Max drawdown</span><b>${fmtR(readiness?.max_drawdown_r_10bps)}</b></div>
      <div class="row"><span>Net R @ 20bps</span><b>${fmtR(readiness?.net_r_20bps)}</b></div>
    </div>

    <div class="card">
      <h2>Execution</h2>
      <div class="row"><span>Forward states</span><b>${Number(counts?.forward_states??0)}</b></div>
      <div class="row"><span>Closed forward trades</span><b>${Number(counts?.forward_trades??0)}</b></div>
      <div class="row"><span>Shadow orders</span><b>${Number(counts?.shadow_orders??0)}</b></div>
      <div class="row"><span>Open shadow positions</span><b>${Number(counts?.shadow_positions??0)}</b></div>
      <div class="row"><span>Flagged bars</span><b>${Number(readiness?.flagged_bars??0)}</b></div>
    </div>
  </div>

  <div class="section two">
    <div class="card">
      <h2>MT5 DEMO</h2>
      <div class="row"><span>Kết nối</span><b class="pill ${demo?.is_active?"good":"bad"}">${demo?.is_active?"CONNECTED":"OFF"}</b></div>
      <div class="row"><span>Server</span><b>${esc(demo?.server??"—")}</b></div>
      <div class="row"><span>Loại tài khoản</span><b>${esc(demo?.account_type??"—")}</b></div>
      <div class="row"><span>Verify gần nhất</span><b>${demo?.last_verified_at?esc(new Date(demo.last_verified_at).toLocaleString("vi-VN",{timeZone:"Asia/Ho_Chi_Minh",hour12:false})):"—"}</b></div>
    </div>

    <div class="card">
      <h2>Safety gates</h2>
      <div class="row"><span>The5ers</span><b class="pill ${badgeClass(String(gates?.the5ers_readiness??""))}">${esc(gates?.the5ers_readiness??"—")}</b></div>
      <div class="row"><span>Written approval</span><b>${gates?.automation_approval_verified?"VERIFIED":"CHƯA CÓ"}</b></div>
      <div class="row"><span>Risk profile</span><b>${gates?.risk_profile_approved?"APPROVED":"CHƯA DUYỆT"}</b></div>
      <div class="row"><span>DEMO send</span><b>${gates?.demo_send_enabled?"ON":"OFF"}</b></div>
      <div class="row"><span>Live money</span><b class="pill warn">LOCKED</b></div>
    </div>
  </div>

  <div class="footer">
    Cập nhật lúc ${esc(updated)} · Dashboard chỉ đọc dữ liệu tổng hợp, không hiển thị credential MT5.<br>
    <a class="refresh" href="?t=${encodeURIComponent(token)}">Làm mới ngay</a>
  </div>
</main></body></html>`;

  return new Response(html,{
    status:200,
    headers:{
      "content-type":"text/html; charset=utf-8",
      "cache-control":"no-store, max-age=0",
      "referrer-policy":"no-referrer",
      "x-frame-options":"DENY",
      "content-security-policy":"default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
    }
  });
});