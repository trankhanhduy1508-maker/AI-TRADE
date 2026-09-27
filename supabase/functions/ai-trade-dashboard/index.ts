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

const DASH_STRATEGY="TF-013A-FORWARD-DIVERSIFIED-TREND";
const YAHOO_SYMBOLS:Record<string,string>={
  EURUSD:"EURUSD=X",GBPUSD:"GBPUSD=X",USDJPY:"USDJPY=X",AUDUSD:"AUDUSD=X",
  USDCAD:"CAD=X",USDCHF:"CHF=X",NZDUSD:"NZDUSD=X",XAUUSD:"GC=F",USOIL:"CL=F",
  BTCUSD:"BTC-USD",ETHUSD:"ETH-USD",US30:"^DJI",NAS100:"^NDX",US500:"^GSPC"
};

async function yahooCandles(symbol:string,timeframe:string,limit:number){
  const yahoo=YAHOO_SYMBOLS[symbol]??YAHOO_SYMBOLS.EURUSD;
  const tf=String(timeframe||"1h").toLowerCase();
  const spec:Record<string,{interval:string,lookbackDays:number,aggregateHours?:number}>={
    "15m":{interval:"15m",lookbackDays:55},
    "30m":{interval:"30m",lookbackDays:55},
    "1h":{interval:"60m",lookbackDays:300},
    "4h":{interval:"60m",lookbackDays:300,aggregateHours:4},
    "1d":{interval:"1d",lookbackDays:1200}
  };
  const selected=spec[tf]??spec["1h"];
  const now=Math.floor(Date.now()/1000);
  const start=now-selected.lookbackDays*86400;
  const url="https://query1.finance.yahoo.com/v8/finance/chart/"+encodeURIComponent(yahoo)+
    "?period1="+start+"&period2="+now+"&interval="+selected.interval+
    "&events=history&includeAdjustedClose=true";
  const res=await fetch(url,{headers:{"user-agent":"AI-TRADE-dashboard/1.0"}});
  if(!res.ok)return [];
  const payload=await res.json();
  const result=payload?.chart?.result?.[0];
  const q=result?.indicators?.quote?.[0];
  const ts:number[]=result?.timestamp??[];
  if(!q)return [];
  const raw:any[]=[];
  for(let i=0;i<ts.length;i++){
    const open=Number(q.open?.[i]),high=Number(q.high?.[i]),low=Number(q.low?.[i]),close=Number(q.close?.[i]);
    if(![open,high,low,close].every(Number.isFinite)||[open,high,low,close].some(v=>v<=0))continue;
    raw.push({time:Number(ts[i]),open,high,low,close});
  }
  let out=raw;
  if(selected.aggregateHours){
    const bucketSec=selected.aggregateHours*3600;
    const grouped=new Map<number,any>();
    for(const b of raw){
      const bucket=Math.floor(Number(b.time)/bucketSec)*bucketSec;
      const prev=grouped.get(bucket);
      if(!prev)grouped.set(bucket,{time:bucket,open:b.open,high:b.high,low:b.low,close:b.close});
      else{
        prev.high=Math.max(prev.high,b.high);
        prev.low=Math.min(prev.low,b.low);
        prev.close=b.close;
      }
    }
    out=[...grouped.values()].sort((a,b)=>a.time-b.time);
  }
  return out.slice(-Math.max(20,Math.min(limit,300)));
}

function badgeClass(kind:string){
  if(["ACTIVE","PASS","CONNECTED","COLLECTING"].includes(kind))return "good";
  if(["BLOCKED_APPROVAL","LOCKED","WAITING"].includes(kind))return "warn";
  if(["FAIL","ERROR","FORWARD_REJECT"].includes(kind))return "bad";
  return "muted";
}

async function accessContext(token:string){
  if(!token)return null;
  const rows=await sql`
    select id,access_role,entitlement_state,subject_label,tester_expires_at,expires_at
    from ai_trade.dashboard_access_tokens
    where token_hash=encode(digest(${token},'sha256'),'hex')
      and revoked_at is null
      and expires_at>now()
    limit 1
  `;
  const row=rows[0];
  if(!row)return null;
  if(row.entitlement_state==="ACTIVE_TESTER" && row.tester_expires_at && new Date(row.tester_expires_at)<=new Date()){
    await sql.begin(async(tx)=>{
      await tx`update ai_trade.dashboard_access_tokens
        set entitlement_state='CUSTOMER_FREE',access_role='CUSTOMER',updated_at=now()
        where id=${row.id} and entitlement_state='ACTIVE_TESTER'`;
      await tx`insert into ai_trade.account_entitlement_audit
        (token_id,actor_token_id,old_state,new_state,action,reason)
        values(${row.id},null,'ACTIVE_TESTER','CUSTOMER_FREE','AUTO_EXPIRE','Tester expiry reached')`;
    });
    row.entitlement_state="CUSTOMER_FREE";
    row.access_role="CUSTOMER";
  }
  return row;
}

Deno.serve(async(req)=>{
  const url=new URL(req.url);
  if(url.searchParams.get("admin_preview")==="1"){
    const target="https://raw.githack.com/trankhanhduy1508-maker/AI-TRADE/e55956eed27c618d33f741a75e5985b788bfb650/dashboard/index.html?mode=admin-preview";
    return new Response(null,{status:302,headers:{
      "location":target,
      "cache-control":"no-store, max-age=0",
      "referrer-policy":"no-referrer"
    }});
  }
  const publicFormat=url.searchParams.get("format");
  if(publicFormat==="preview-candles"){
    const symbol=String(url.searchParams.get("symbol")??"EURUSD").toUpperCase();
    const timeframe=String(url.searchParams.get("timeframe")??"1h").toLowerCase();
    if(!YAHOO_SYMBOLS[symbol]||!["15m","30m","1h","4h","1d"].includes(timeframe)){
      return new Response(JSON.stringify({ok:false,error:"UNSUPPORTED_MARKET_OR_TIMEFRAME"}),{status:400,headers:{"content-type":"application/json","cache-control":"no-store"}});
    }
    const candles=await yahooCandles(symbol,timeframe,220);
    return new Response(JSON.stringify({ok:true,symbol,timeframe,candles,publicMarketData:true}),{status:200,headers:{
      "content-type":"application/json; charset=utf-8",
      "cache-control":"public, max-age=30",
      "access-control-allow-origin":"*",
      "referrer-policy":"no-referrer"
    }});
  }
  const token=url.searchParams.get("t")??"";
  const access=await accessContext(token);
  if(!access || ["SUSPENDED","REVOKED"].includes(String(access.entitlement_state))){
    return new Response("<h1>Tài khoản không còn quyền truy cập CWS AI Trade.</h1>",{
      status:403,
      headers:{
        "content-type":"text/html; charset=utf-8",
        "cache-control":"no-store",
        "referrer-policy":"no-referrer"
      }
    });
  }

  const format=publicFormat;
  const isFounder=String(access.access_role)==="FOUNDER";

  if(format==="admin-testers"){
    if(!isFounder)return new Response(JSON.stringify({ok:false,error:"FOUNDER_ONLY"}),{status:403,headers:{"content-type":"application/json"}});
    if(req.method==="POST"){
      const body=await req.json().catch(()=>({}));
      const targetId=Number(body?.tokenId??0);
      const action=String(body?.action??"");
      const map:Record<string,{role:string,state:string}>={
        TO_CUSTOMER_FREE:{role:"CUSTOMER",state:"CUSTOMER_FREE"},
        TO_CUSTOMER_PAID:{role:"CUSTOMER",state:"CUSTOMER_PAID"},
        SUSPEND:{role:"CUSTOMER",state:"SUSPENDED"},
        REVOKE:{role:"CUSTOMER",state:"REVOKED"},
        RESTORE_TESTER:{role:"TESTER",state:"ACTIVE_TESTER"}
      };
      const next=map[action];
      if(!targetId||!next)return new Response(JSON.stringify({ok:false,error:"INVALID_ACTION"}),{status:400,headers:{"content-type":"application/json"}});
      const [old]=await sql`select id,entitlement_state from ai_trade.dashboard_access_tokens where id=${targetId} and access_role<>'FOUNDER' limit 1`;
      if(!old)return new Response(JSON.stringify({ok:false,error:"TARGET_NOT_FOUND"}),{status:404,headers:{"content-type":"application/json"}});
      await sql.begin(async(tx)=>{
        await tx`update ai_trade.dashboard_access_tokens
          set access_role=${next.role},entitlement_state=${next.state},
              tester_expires_at=case when ${action}='RESTORE_TESTER' then now()+interval '30 days' else tester_expires_at end,
              updated_at=now()
          where id=${targetId}`;
        await tx`insert into ai_trade.account_entitlement_audit
          (token_id,actor_token_id,old_state,new_state,action,reason)
          values(${targetId},${access.id},${String(old.entitlement_state)},${next.state},${action},'Founder dashboard action')`;
      });
      return new Response(JSON.stringify({ok:true,tokenId:targetId,state:next.state}),{status:200,headers:{"content-type":"application/json","cache-control":"no-store"}});
    }
    const testers=await sql`select id,label,subject_label,access_role,entitlement_state,tester_expires_at,expires_at,updated_at
      from ai_trade.dashboard_access_tokens where id<>${access.id} order by id`;
    return new Response(JSON.stringify({ok:true,testers}),{status:200,headers:{"content-type":"application/json","cache-control":"no-store","access-control-allow-origin":"*"}});
  }

  if(format==="symbol-spec"){
    const symbol=String(url.searchParams.get("symbol")??"").toUpperCase();
    if(!YAHOO_SYMBOLS[symbol]){
      return new Response(JSON.stringify({ok:false,error:"UNSUPPORTED_MARKET"}),{status:400,headers:{"content-type":"application/json","cache-control":"no-store"}});
    }
    const [row]=await sql`
      select market,broker_symbol,supported,description,digits,
             contract_size::float8 as contract_size,
             tick_size::float8 as tick_size,
             tick_value::float8 as tick_value,
             currency_base,currency_profit,currency_margin,calc_mode,
             source,observed_at,details
      from ai_trade.dashboard_symbol_specs
      where market=${symbol}
      limit 1
    `;
    const accountCurrency=String(row?.details?.accountCurrency??"");
    const spec=row?.supported?{
      market:String(row.market),
      brokerSymbol:String(row.broker_symbol??row.market),
      description:String(row.description??""),
      digits:row.digits==null?null:Number(row.digits),
      contractSize:row.contract_size==null?null:Number(row.contract_size),
      tickSize:row.tick_size==null?null:Number(row.tick_size),
      tickValue:row.tick_value==null?null:Number(row.tick_value),
      currencyBase:String(row.currency_base??""),
      currencyProfit:String(row.currency_profit??""),
      currencyMargin:String(row.currency_margin??""),
      accountCurrency:accountCurrency||null,
      calcMode:row.calc_mode==null?null:Number(row.calc_mode),
      source:String(row.source??""),
      observedAt:row.observed_at?new Date(row.observed_at).toISOString():null
    }:null;
    return new Response(JSON.stringify({
      ok:true,symbol,supported:Boolean(row?.supported),spec,
      unavailableReason:row?.supported?null:String(row?.details?.reason??"SPEC_UNAVAILABLE"),
      brokerOrders:false,liveMoneyLocked:true
    }),{status:200,headers:{
      "content-type":"application/json; charset=utf-8",
      "cache-control":"private, max-age=60",
      "access-control-allow-origin":"*","referrer-policy":"no-referrer"
    }});
  }

  if(!format){
    const target="https://raw.githack.com/trankhanhduy1508-maker/AI-TRADE/c87c08174b3adfa9b80641d1afdf19a2718e38f1/dashboard/index.html?t="+encodeURIComponent(token);
    return new Response(null,{
      status:302,
      headers:{
        "location":target,
        "cache-control":"no-store, max-age=0",
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
    select account_login,server,account_type,connection_state,last_verified_at
    from ai_trade.account_mt5_bindings
    where access_token_id=${access.id}
      and connection_state<>'REVOKED'
    limit 1
  `;

  const [gates]=await sql`
    select
      (select readiness from ai_trade.bootcamp_readiness where provider='THE5ERS') as the5ers_readiness,
      (select risk_profile_approved from ai_trade.runtime_config where id=1) as risk_profile_approved,
      (select demo_send_enabled from ai_trade.runtime_config where id=1) as demo_send_enabled,
      (select automation_approval_verified from ai_trade.prop_program_config where provider='THE5ERS') as automation_approval_verified
  `;

  if(format==="arena"){
    const positions=await sql`
      select symbol,asset_class,direction,entry_ts,entry_price::float8 as entry_price,
             stop_price::float8 as stop_price,risk_price::float8 as risk_price,
             last_mark_ts,last_mark_price::float8 as last_mark_price,
             unrealized_r::float8 as unrealized_r,opened_reason,updated_at
      from ai_trade.training_arena_positions
      where strategy_id='TF-013A-ARENA-ALL-MARKETS'
      order by asset_class,symbol
    `;
    const trades=await sql`
      select id,symbol,asset_class,direction,entry_ts,exit_ts,
             entry_price::float8 as entry_price,exit_price::float8 as exit_price,
             initial_stop::float8 as initial_stop,r_10bps::float8 as r_10bps,
             r_20bps::float8 as r_20bps,exit_reason
      from ai_trade.training_arena_trades
      where strategy_id='TF-013A-ARENA-ALL-MARKETS'
      order by exit_ts desc,id desc
      limit 40
    `;
    const journal=await sql`
      select id,symbol,event_type,event_ts,direction,price::float8 as price,
             stop_price::float8 as stop_price,realized_r::float8 as realized_r,
             unrealized_r::float8 as unrealized_r,setup,reason,lesson,metadata
      from ai_trade.training_arena_journal
      where strategy_id='TF-013A-ARENA-ALL-MARKETS'
      order by event_ts desc,id desc
      limit 80
    `;
    return new Response(JSON.stringify({
      ok:true,
      mode:"PAPER_TRAINING_ARENA",
      brokerOrders:false,liveMoneyLocked:true,contaminatesForward:false,
      positions:positions.map((p:any)=>({
        symbol:String(p.symbol),assetClass:String(p.asset_class),direction:String(p.direction),
        side:String(p.direction)==="UP"?"BUY":"SELL",
        entryTs:new Date(p.entry_ts).toISOString(),entryPrice:Number(p.entry_price),
        stopPrice:Number(p.stop_price),riskPrice:Number(p.risk_price),
        lastMarkTs:new Date(p.last_mark_ts).toISOString(),
        lastMarkPrice:Number(p.last_mark_price),unrealizedR:Number(p.unrealized_r),
        openedReason:String(p.opened_reason)
      })),
      trades:trades.map((t:any)=>({
        id:Number(t.id),symbol:String(t.symbol),assetClass:String(t.asset_class),
        direction:String(t.direction),side:String(t.direction)==="UP"?"BUY":"SELL",
        entryTs:new Date(t.entry_ts).toISOString(),exitTs:new Date(t.exit_ts).toISOString(),
        entryPrice:Number(t.entry_price),exitPrice:Number(t.exit_price),
        stopPrice:Number(t.initial_stop),r10bps:Number(t.r_10bps),
        r20bps:Number(t.r_20bps),exitReason:String(t.exit_reason)
      })),
      journal:isFounder?journal.map((j:any)=>({
        id:Number(j.id),symbol:String(j.symbol),eventType:String(j.event_type),
        eventTs:new Date(j.event_ts).toISOString(),direction:j.direction?String(j.direction):null,
        side:String(j.direction)==="UP"?"BUY":String(j.direction)==="DOWN"?"SELL":null,
        price:j.price==null?null:Number(j.price),stopPrice:j.stop_price==null?null:Number(j.stop_price),
        realizedR:j.realized_r==null?null:Number(j.realized_r),
        unrealizedR:j.unrealized_r==null?null:Number(j.unrealized_r),
        setup:String(j.setup),reason:String(j.reason),lesson:String(j.lesson),metadata:j.metadata??{}
      })): []
    }),{status:200,headers:{
      "content-type":"application/json; charset=utf-8","cache-control":"no-store",
      "access-control-allow-origin":"*","referrer-policy":"no-referrer"
    }});
  }

  if(format==="current"){
    const positions=await sql`
      select symbol,direction,entry_ts,entry_price::float8 as entry_price,
             stop_price::float8 as stop_price,synthetic_volume::float8 as synthetic_volume,
             updated_at
      from ai_trade.shadow_broker_positions
      where strategy_id=${DASH_STRATEGY}
      order by updated_at desc
    `;
    let currentTrade=null;
    if(positions[0]){
      const p=positions[0];
      const candles=await yahooCandles(String(p.symbol),"1h",20);
      const latest=candles.at(-1);
      const entryPrice=Number(p.entry_price);
      const currentPrice=latest?Number(latest.close):entryPrice;
      const stopPrice=Number(p.stop_price);
      const riskPrice=Math.abs(entryPrice-stopPrice);
      const floatingR=riskPrice>0
        ? (String(p.direction)==="UP"?(currentPrice-entryPrice):(entryPrice-currentPrice))/riskPrice
        : null;
      currentTrade={
        symbol:String(p.symbol),
        direction:String(p.direction),
        side:String(p.direction)==="UP"?"BUY":"SELL",
        entryTs:new Date(p.entry_ts).toISOString(),
        entryPrice,currentPrice,stopPrice,
        takeProfit:null,
        floatingPL:null,
        floatingR,
        riskReward:null,
        volumeLabel:"Shadow "+Number(p.synthetic_volume).toFixed(1),
        mode:"SHADOW_ONLY",
        mt5Login:demo?.account_login?String(demo.account_login):null
      };
    }
    return new Response(JSON.stringify({
      ok:true,currentTrade,
      openPositions:positions.map((p:any)=>({
        symbol:String(p.symbol),direction:String(p.direction),
        entryTs:new Date(p.entry_ts).toISOString(),
        entryPrice:Number(p.entry_price),stopPrice:Number(p.stop_price),
        syntheticVolume:Number(p.synthetic_volume)
      })),
      brokerOrders:false,liveMoneyLocked:true
    }),{status:200,headers:{
      "content-type":"application/json; charset=utf-8",
      "cache-control":"no-store","access-control-allow-origin":"*","referrer-policy":"no-referrer"
    }});
  }

  if(format==="trades"){
    const requested=Math.max(1,Math.min(Number(url.searchParams.get("limit")??12)||12,50));
    const trades=await sql`
      select id,symbol,direction,entry_ts,exit_ts,
             entry_price::float8 as entry_price,exit_price::float8 as exit_price,
             initial_stop::float8 as initial_stop,
             r_10bps::float8 as r_10bps,r_20bps::float8 as r_20bps,
             exit_reason
      from ai_trade.forward_shadow_trades
      where strategy_id=${DASH_STRATEGY}
      order by exit_ts desc,id desc
      limit ${requested}
    `;
    return new Response(JSON.stringify({
      ok:true,trades:trades.map((t:any)=>({
        id:Number(t.id),symbol:String(t.symbol),direction:String(t.direction),
        side:String(t.direction)==="UP"?"BUY":"SELL",status:"CLOSED",
        entryTs:new Date(t.entry_ts).toISOString(),exitTs:new Date(t.exit_ts).toISOString(),
        entryPrice:Number(t.entry_price),exitPrice:Number(t.exit_price),
        stopPrice:Number(t.initial_stop),r10bps:Number(t.r_10bps),
        r20bps:Number(t.r_20bps),exitReason:String(t.exit_reason??"")
      }))
    }),{status:200,headers:{
      "content-type":"application/json; charset=utf-8",
      "cache-control":"no-store","access-control-allow-origin":"*","referrer-policy":"no-referrer"
    }});
  }

  if(format==="journal"){
    if(!isFounder){
      return new Response(JSON.stringify({ok:true,journal:[],restricted:true}),{status:200,headers:{
        "content-type":"application/json; charset=utf-8","cache-control":"no-store","access-control-allow-origin":"*","referrer-policy":"no-referrer"
      }});
    }
    const requested=Math.max(1,Math.min(Number(url.searchParams.get("limit")??12)||12,50));
    const rows=await sql`
      select id,trade_id,symbol,direction,entry_ts,exit_ts,
             r_10bps::float8 as r_10bps,result_label,setup,
             entry_reason,exit_reason,lesson,chart_timeframe,tags
      from ai_trade.forward_trade_journal
      where strategy_id=${DASH_STRATEGY}
      order by exit_ts desc,id desc
      limit ${requested}
    `;
    return new Response(JSON.stringify({
      ok:true,journal:rows.map((j:any)=>({
        id:Number(j.id),tradeId:String(j.trade_id),symbol:String(j.symbol),
        direction:String(j.direction),entryTs:new Date(j.entry_ts).toISOString(),
        exitTs:new Date(j.exit_ts).toISOString(),r10bps:Number(j.r_10bps),
        resultLabel:String(j.result_label),setup:String(j.setup),
        entryReason:String(j.entry_reason),exitReason:String(j.exit_reason),
        lesson:String(j.lesson),chartTimeframe:String(j.chart_timeframe),tags:j.tags??[]
      }))
    }),{status:200,headers:{
      "content-type":"application/json; charset=utf-8",
      "cache-control":"no-store","access-control-allow-origin":"*","referrer-policy":"no-referrer"
    }});
  }

  if(format==="candles"){
    const symbol=String(url.searchParams.get("symbol")??"EURUSD").toUpperCase();
    const requestedTf=String(url.searchParams.get("timeframe")??"1h").toLowerCase();
    const allowed=new Set(["15m","30m","1h","4h","1d"]);
    const timeframe=allowed.has(requestedTf)?requestedTf:"1h";
    const limit=Math.max(20,Math.min(Number(url.searchParams.get("limit")??160)||160,300));
    const candles=await yahooCandles(symbol,timeframe,limit);
    return new Response(JSON.stringify({
      ok:true,symbol,timeframe,candles
    }),{status:200,headers:{
      "content-type":"application/json; charset=utf-8",
      "cache-control":"no-store","access-control-allow-origin":"*","referrer-policy":"no-referrer"
    }});
  }

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
      viewer:{
        role:String(access.access_role),
        entitlementState:String(access.entitlement_state),
        subjectLabel:String(access.subject_label??""),
        testerExpiresAt:access.tester_expires_at?new Date(access.tester_expires_at).toISOString():null,
        founder:isFounder
      },
      crons:isFounder?crons.map((c:any)=>({
        jobname:String(c.jobname),
        schedule:String(c.schedule),
        active:Boolean(c.active)
      })):[],
      mt5:{
        connected:String(demo?.connection_state??"")==="CONNECTED",
        login:demo?.account_login?String(demo.account_login):null,
        server:String(demo?.server??""),
        accountType:String(demo?.account_type??""),
        lastVerifiedAt:demo?.last_verified_at?new Date(demo.last_verified_at).toISOString():null
      },
      gates:isFounder?{
        the5ersReadiness:String(gates?.the5ers_readiness??""),
        automationApprovalVerified:Boolean(gates?.automation_approval_verified),
        riskProfileApproved:Boolean(gates?.risk_profile_approved),
        demoSendEnabled:Boolean(gates?.demo_send_enabled),
        liveMoneyLocked:true
      }:{liveMoneyLocked:true,demoOnly:true},
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

  if(url.searchParams.get("format")==="svg"){
    const W=420,H=1180;
    const barWidth=332;
    const p1=Math.round(barWidth*pct(closed,50)/100);
    const p2=Math.round(barWidth*pct(days,120)/100);
    const p3=Math.round(barWidth*pct(markets,8)/100);
    const stateColor=evalState==="FORWARD_CANDIDATE"?"#53d18b":evalState==="FORWARD_REJECT"?"#ff6b6b":"#f1c75b";
    const cronRows=crons.map((c:any,i:number)=>{
      const label=c.jobname==="ai-trade-forward-shadow-daily"?"1. Tín hiệu forward":c.jobname==="ai-trade-shadow-broker-reconcile-daily"?"2. Shadow Broker":"3. Chấm điểm";
      const time=c.schedule.startsWith("15 3")?"10:15 VN":c.schedule.startsWith("20 3")?"10:20 VN":c.schedule.startsWith("25 3")?"10:25 VN":String(c.schedule);
      const y=430+i*66;
      return `<rect x="24" y="${y}" width="372" height="54" rx="14" fill="#151922" stroke="#262d3a"/>
        <text x="40" y="${y+23}" class="label">${esc(label)}</text>
        <text x="40" y="${y+42}" class="sub">${esc(time)}</text>
        <rect x="315" y="${y+14}" width="64" height="26" rx="13" fill="${c.active?"#173529":"#3a1d21"}"/>
        <text x="347" y="${y+32}" text-anchor="middle" class="${c.active?"good":"bad"}">${c.active?"ACTIVE":"OFF"}</text>`;
    }).join("");

    const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 ${W} ${H}" role="img" aria-label="AI-TRADE Forward Monitor">
      <style>
        text{font-family:Inter,Arial,sans-serif;fill:#f4f6fb}
        .title{font-size:24px;font-weight:700}.sub{font-size:12px;fill:#939cad}.label{font-size:14px;font-weight:600}
        .value{font-size:24px;font-weight:700}.good{font-size:11px;font-weight:700;fill:#53d18b}.warn{font-size:11px;font-weight:700;fill:#f1c75b}.bad{font-size:11px;font-weight:700;fill:#ff6b6b}
        .small{font-size:12px}.metric{font-size:13px;fill:#939cad}.metricv{font-size:15px;font-weight:700}
      </style>
      <rect width="420" height="1180" fill="#0b0d12"/>
      <text x="24" y="42" class="title">AI-TRADE Forward Monitor</text>
      <text x="24" y="64" class="sub">TF-013A · live từ Supabase · refresh 30 giây</text>
      <circle cx="377" cy="36" r="5" fill="#53d18b"/><text x="367" y="58" text-anchor="middle" class="good">LIVE</text>

      <rect x="24" y="86" width="372" height="76" rx="16" fill="#151922" stroke="#262d3a"/>
      <text x="40" y="113" class="sub">Trạng thái kiểm chứng</text>
      <text x="40" y="143" font-size="20" font-weight="700">${esc(evalState)}</text>
      <rect x="284" y="105" width="96" height="34" rx="17" fill="#222832"/>
      <text x="332" y="127" text-anchor="middle" font-size="11" font-weight="700" fill="${stateColor}">${esc(evalState)}</text>

      <text x="24" y="194" class="label">Tiến độ đủ mẫu</text>

      <rect x="24" y="210" width="372" height="72" rx="14" fill="#151922" stroke="#262d3a"/>
      <text x="40" y="236" class="sub">Closed trades</text><text x="380" y="238" text-anchor="end" class="value">${closed}/50</text>
      <rect x="40" y="254" width="${barWidth}" height="8" rx="4" fill="#252b36"/><rect x="40" y="254" width="${p1}" height="8" rx="4" fill="#71a7ff"/>

      <rect x="24" y="292" width="372" height="72" rx="14" fill="#151922" stroke="#262d3a"/>
      <text x="40" y="318" class="sub">Số ngày</text><text x="380" y="320" text-anchor="end" class="value">${days}/120</text>
      <rect x="40" y="336" width="${barWidth}" height="8" rx="4" fill="#252b36"/><rect x="40" y="336" width="${p2}" height="8" rx="4" fill="#71a7ff"/>

      <rect x="24" y="374" width="372" height="72" rx="14" fill="#151922" stroke="#262d3a"/>
      <text x="40" y="400" class="sub">Market có trade</text><text x="380" y="402" text-anchor="end" class="value">${markets}/8</text>
      <rect x="40" y="418" width="${barWidth}" height="8" rx="4" fill="#252b36"/><rect x="40" y="418" width="${p3}" height="8" rx="4" fill="#71a7ff"/>

      <text x="24" y="474" class="label">Pipeline tự động mỗi ngày</text>
      ${cronRows}

      <rect x="24" y="640" width="372" height="186" rx="16" fill="#151922" stroke="#262d3a"/>
      <text x="40" y="668" class="label">Forward performance</text>
      <text x="40" y="697" class="metric">Net R @ 10bps</text><text x="380" y="697" text-anchor="end" class="metricv">${esc(fmtR(readiness?.net_r_10bps))}</text>
      <text x="40" y="725" class="metric">Expectancy</text><text x="380" y="725" text-anchor="end" class="metricv">${esc(fmtR(readiness?.expectancy_r_10bps))}</text>
      <text x="40" y="753" class="metric">Profit factor</text><text x="380" y="753" text-anchor="end" class="metricv">${readiness?.profit_factor_r_10bps==null?"—":Number(readiness.profit_factor_r_10bps).toFixed(2)}</text>
      <text x="40" y="781" class="metric">Max drawdown</text><text x="380" y="781" text-anchor="end" class="metricv">${esc(fmtR(readiness?.max_drawdown_r_10bps))}</text>
      <text x="40" y="809" class="metric">Net R @ 20bps</text><text x="380" y="809" text-anchor="end" class="metricv">${esc(fmtR(readiness?.net_r_20bps))}</text>

      <rect x="24" y="840" width="180" height="190" rx="16" fill="#151922" stroke="#262d3a"/>
      <text x="40" y="868" class="label">Execution</text>
      <text x="40" y="898" class="metric">Forward states</text><text x="188" y="898" text-anchor="end" class="metricv">${Number(counts?.forward_states??0)}</text>
      <text x="40" y="926" class="metric">Closed trades</text><text x="188" y="926" text-anchor="end" class="metricv">${Number(counts?.forward_trades??0)}</text>
      <text x="40" y="954" class="metric">Shadow orders</text><text x="188" y="954" text-anchor="end" class="metricv">${Number(counts?.shadow_orders??0)}</text>
      <text x="40" y="982" class="metric">Open positions</text><text x="188" y="982" text-anchor="end" class="metricv">${Number(counts?.shadow_positions??0)}</text>
      <text x="40" y="1010" class="metric">Flagged bars</text><text x="188" y="1010" text-anchor="end" class="metricv">${Number(readiness?.flagged_bars??0)}</text>

      <rect x="216" y="840" width="180" height="190" rx="16" fill="#151922" stroke="#262d3a"/>
      <text x="232" y="868" class="label">MT5 DEMO</text>
      <text x="232" y="898" class="metric">Kết nối</text><text x="380" y="898" text-anchor="end" class="${demo?.is_active?"good":"bad"}">${demo?.is_active?"CONNECTED":"OFF"}</text>
      <text x="232" y="926" class="metric">Server</text><text x="380" y="926" text-anchor="end" class="small">${esc(demo?.server??"—")}</text>
      <text x="232" y="954" class="metric">Loại</text><text x="380" y="954" text-anchor="end" class="metricv">${esc(demo?.account_type??"—")}</text>
      <text x="232" y="982" class="metric">The5ers</text><text x="380" y="982" text-anchor="end" class="warn">${esc(gates?.the5ers_readiness??"—")}</text>
      <text x="232" y="1010" class="metric">Live money</text><text x="380" y="1010" text-anchor="end" class="warn">LOCKED</text>

      <rect x="24" y="1046" width="372" height="80" rx="16" fill="#151922" stroke="#262d3a"/>
      <text x="40" y="1074" class="label">Safety gates</text>
      <text x="40" y="1100" class="metric">Approval: ${gates?.automation_approval_verified?"VERIFIED":"CHƯA CÓ"} · Risk: ${gates?.risk_profile_approved?"APPROVED":"CHƯA DUYỆT"} · DEMO send: ${gates?.demo_send_enabled?"ON":"OFF"}</text>
      <text x="40" y="1148" class="sub">Cập nhật ${esc(updated)} · Không hiển thị credential MT5</text>
    </svg>`;

    return new Response(svg,{
      status:200,
      headers:{
        "content-type":"image/svg+xml; charset=utf-8",
        "cache-control":"no-store, max-age=0",
        "refresh":"30",
        "referrer-policy":"no-referrer",
        "access-control-allow-origin":"*"
      }
    });
  }

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