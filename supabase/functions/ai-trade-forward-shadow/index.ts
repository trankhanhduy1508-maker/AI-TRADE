import postgres from "npm:postgres@3.4.9";

type Direction="UP"|"DOWN";
type AssetClass="FX"|"COMMODITY"|"CRYPTO"|"INDEX";
type Bar={timestamp:number;open:number;high:number;low:number;close:number};
type Instrument={key:string;yahooSymbol:string;assetClass:AssetClass;coinbaseProduct?:string};
type Position={direction:Direction;entryTs:number;entryPrice:number;stop:number;initialStop:number;riskPrice:number};

const STRATEGY_ID="TF-013A-FORWARD-DIVERSIFIED-TREND";
const sql=postgres(Deno.env.get("SUPABASE_DB_URL")!,{prepare:false,max:1,connect_timeout:10,idle_timeout:20});
const json=(b:unknown,s=200)=>new Response(JSON.stringify(b),{status:s,headers:{"content-type":"application/json; charset=utf-8"}});

const UNIVERSE:Instrument[]=[
 {key:"EURUSD",yahooSymbol:"EURUSD=X",assetClass:"FX"},
 {key:"GBPUSD",yahooSymbol:"GBPUSD=X",assetClass:"FX"},
 {key:"USDJPY",yahooSymbol:"USDJPY=X",assetClass:"FX"},
 {key:"AUDUSD",yahooSymbol:"AUDUSD=X",assetClass:"FX"},
 {key:"USDCAD",yahooSymbol:"CAD=X",assetClass:"FX"},
 {key:"USDCHF",yahooSymbol:"CHF=X",assetClass:"FX"},
 {key:"NZDUSD",yahooSymbol:"NZDUSD=X",assetClass:"FX"},
 {key:"XAUUSD",yahooSymbol:"GC=F",assetClass:"COMMODITY"},
 {key:"USOIL",yahooSymbol:"CL=F",assetClass:"COMMODITY"},
 {key:"BTCUSD",yahooSymbol:"BTC-USD",assetClass:"CRYPTO"},
 {key:"ETHUSD",yahooSymbol:"ETH-USD",assetClass:"CRYPTO",coinbaseProduct:"ETH-USD"},
 {key:"US30",yahooSymbol:"^DJI",assetClass:"INDEX"},
 {key:"NAS100",yahooSymbol:"^NDX",assetClass:"INDEX"},
 {key:"US500",yahooSymbol:"^GSPC",assetClass:"INDEX"},
];

async function authorized(req:Request){
 const rows=await sql`select secret from ai_trade.cron_auth where id=1`;
 const expected=String(rows[0]?.secret??"");
 return Boolean(expected)&&(req.headers.get("x-ai-trade-cron")??"")===expected;
}
async function event(type:string,result:string,details:Record<string,unknown>={}){
 await sql`insert into ai_trade.events(event_type,result,details)
 values(${type},${result},${JSON.stringify({...details,strategyId:STRATEGY_ID})}::jsonb)`;
}
function n(x:unknown){const v=Number(x);return Number.isFinite(v)?v:null;}
function round(v:number,d=8){const p=10**d;return Math.round(v*p)/p;}
function monthKey(ts:number){return new Date(ts*1000).toISOString().slice(0,7);}

async function yahooBars(symbol:string):Promise<Bar[]>{
 const now=new Date();
 const p2=Math.floor(Date.UTC(now.getUTCFullYear(),now.getUTCMonth(),now.getUTCDate())/1000);
 const p1=p2-550*86400;
 const url="https://query1.finance.yahoo.com/v8/finance/chart/"+encodeURIComponent(symbol)+
  "?period1="+p1+"&period2="+p2+"&interval=1d&events=history&includeAdjustedClose=true";
 const res=await fetch(url,{headers:{"user-agent":"AI-TRADE-forward-shadow/1.0"}});
 if(!res.ok)throw new Error("YAHOO_HTTP_"+res.status);
 const payload=await res.json(),result=payload?.chart?.result?.[0],q=result?.indicators?.quote?.[0],ts:number[]=result?.timestamp??[];
 if(!q)throw new Error("YAHOO_NO_DATA");
 const out:Bar[]=[];
 for(let i=0;i<ts.length;i++){
  const open=n(q.open?.[i]),high=n(q.high?.[i]),low=n(q.low?.[i]),close=n(q.close?.[i]);
  if(open===null||high===null||low===null||close===null)continue;
  if(ts[i]>=p2||open<=0||high<=0||low<=0||close<=0)continue;
  if(high<Math.max(open,close)||low>Math.min(open,close))continue;
  out.push({timestamp:Number(ts[i]),open,high,low,close});
 }
 out.sort((a,b)=>a.timestamp-b.timestamp);
 if(out.length<300)throw new Error("INSUFFICIENT_BARS");
 return out;
}
async function coinbaseBars(product:string):Promise<Bar[]>{
 const now=new Date();
 const endMs=Date.UTC(now.getUTCFullYear(),now.getUTCMonth(),now.getUTCDate());
 const startMs=endMs-550*86400*1000,chunk=280*86400*1000,map=new Map<number,Bar>();
 for(let s=startMs;s<endMs;s+=chunk){
  const e=Math.min(endMs,s+chunk);
  const url="https://api.exchange.coinbase.com/products/"+encodeURIComponent(product)+
   "/candles?granularity=86400&start="+encodeURIComponent(new Date(s).toISOString())+
   "&end="+encodeURIComponent(new Date(e).toISOString());
  const res=await fetch(url,{headers:{"user-agent":"AI-TRADE-forward-shadow/1.0","accept":"application/json"}});
  if(!res.ok)throw new Error("COINBASE_HTTP_"+res.status);
  const rows=await res.json();if(!Array.isArray(rows))throw new Error("COINBASE_BAD_RESPONSE");
  for(const row of rows){
   if(!Array.isArray(row)||row.length<5)continue;
   const timestamp=Number(row[0]),low=n(row[1]),high=n(row[2]),open=n(row[3]),close=n(row[4]);
   if(open===null||high===null||low===null||close===null)continue;
   if(timestamp*1000>=endMs||open<=0||high<=0||low<=0||close<=0)continue;
   map.set(timestamp,{timestamp,open,high,low,close});
  }
  await new Promise(r=>setTimeout(r,120));
 }
 const out=[...map.values()].sort((a,b)=>a.timestamp-b.timestamp);
 if(out.length<300)throw new Error("INSUFFICIENT_COINBASE_BARS");
 return out;
}
async function barsFor(i:Instrument){return i.coinbaseProduct?coinbaseBars(i.coinbaseProduct):yahooBars(i.yahooSymbol);}

function atrSeries(bars:Bar[],p=20){
 const tr:number[]=[],atr=Array(bars.length).fill(NaN);
 for(let i=0;i<bars.length;i++){
  if(i===0)tr.push(bars[i].high-bars[i].low);
  else tr.push(Math.max(bars[i].high-bars[i].low,Math.abs(bars[i].high-bars[i-1].close),Math.abs(bars[i].low-bars[i-1].close)));
 }
 if(bars.length<=p)return atr;
 let s=0;for(let i=1;i<=p;i++)s+=tr[i];atr[p]=s/p;
 for(let i=p+1;i<bars.length;i++)atr[i]=(atr[i-1]*(p-1)+tr[i])/p;
 return atr;
}
function sma(bars:Bar[],idx:number,p:number){
 if(idx+1<p)return null;let s=0;for(let i=idx-p+1;i<=idx;i++)s+=bars[i].close;return s/p;
}
function signal(bars:Bar[],idx:number):Direction|null{
 if(idx<252)return null;
 const fast=sma(bars,idx,10),slow=sma(bars,idx,200);if(fast===null||slow===null)return null;
 const votes=[bars[idx].close-bars[idx-21].close,bars[idx].close-bars[idx-252].close,fast-slow].map(x=>x>0?1:x<0?-1:0);
 const score=votes.reduce((a,b)=>a+b,0);
 return score>0?"UP":score<0?"DOWN":null;
}
async function recordTrade(i:Instrument,pos:Position,exitTs:number,exitPrice:number,reason:string){
 const gross=pos.direction==="UP"?exitPrice-pos.entryPrice:pos.entryPrice-exitPrice;
 const grossR=gross/pos.riskPrice;
 const r10=(gross-pos.entryPrice*.001)/pos.riskPrice;
 const r20=(gross-pos.entryPrice*.002)/pos.riskPrice;
 await sql`insert into ai_trade.forward_shadow_trades(
   strategy_id,symbol,asset_class,direction,entry_ts,exit_ts,
   entry_price,exit_price,initial_stop,risk_price,gross_r,r_10bps,r_20bps,exit_reason
 ) values(
   ${STRATEGY_ID},${i.key},${i.assetClass},${pos.direction},
   to_timestamp(${pos.entryTs}),to_timestamp(${exitTs}),
   ${pos.entryPrice},${exitPrice},${pos.initialStop},${pos.riskPrice},
   ${grossR},${r10},${r20},${reason}
 ) on conflict(strategy_id,symbol,entry_ts,exit_ts) do nothing`;
 await event("forward_shadow_exit","CLOSED",{symbol:i.key,direction:pos.direction,grossR:round(grossR),r10bps:round(r10),r20bps:round(r20),reason});
}

async function processInstrument(i:Instrument){
 const bars=await barsFor(i),atr=atrSeries(bars,20),latest=bars[bars.length-1];
 const rows=await sql`select extract(epoch from last_processed)::bigint as last_epoch,last_review_month,pending_direction,position
   from ai_trade.forward_shadow_state where strategy_id=${STRATEGY_ID} and symbol=${i.key}`;
 if(!rows[0]){
  await sql`insert into ai_trade.forward_shadow_state(
   strategy_id,symbol,asset_class,last_processed,last_review_month,pending_direction,position
  ) values(${STRATEGY_ID},${i.key},${i.assetClass},to_timestamp(${latest.timestamp}),${monthKey(latest.timestamp)},null,null)`;
  await event("forward_shadow_warm","WARMED",{symbol:i.key,lastProcessed:latest.timestamp,detail:"No historical trade backfill"});
  return {symbol:i.key,status:"WARMED",lastProcessed:latest.timestamp,position:null,pending:null};
 }
 const state=rows[0],last=Number(state.last_epoch);
 if(last<bars[0].timestamp)return {symbol:i.key,status:"GAP_BLOCKED",lastProcessed:last,firstAvailable:bars[0].timestamp};

 let position:Position|null=state.position?{
  direction:String(state.position.direction) as Direction,
  entryTs:Number(state.position.entryTs),entryPrice:Number(state.position.entryPrice),
  stop:Number(state.position.stop),initialStop:Number(state.position.initialStop),riskPrice:Number(state.position.riskPrice)
 }:null;
 let pending:Direction|null=state.pending_direction?String(state.pending_direction) as Direction:null;
 let reviewMonth=String(state.last_review_month);
 const indexes=bars.map((b,index)=>({b,index})).filter(x=>x.b.timestamp>last).map(x=>x.index);
 if(!indexes.length)return {symbol:i.key,status:"NO_NEW_CLOSED_BAR",lastProcessed:last,position:position?.direction??null,pending};

 let checkpoint=last,entries=0,exits=0,reviews=0;
 for(const idx of indexes){
  const bar=bars[idx];

  if(pending){
   if(position&&position.direction!==pending){
    await recordTrade(i,position,bar.timestamp,bar.open,"MONTHLY_REVERSAL");
    position=null;exits++;
   }
   if(!position){
    const av=atr[idx-1];
    if(!(av>0&&Number.isFinite(av)))throw new Error("ATR_UNAVAILABLE");
    const risk=4*av;
    position={direction:pending,entryTs:bar.timestamp,entryPrice:bar.open,stop:pending==="UP"?bar.open-risk:bar.open+risk,initialStop:pending==="UP"?bar.open-risk:bar.open+risk,riskPrice:risk};
    entries++;
    await event("forward_shadow_entry","OPEN",{symbol:i.key,direction:pending,entryPrice:bar.open,stop:position.stop,riskPrice:risk});
   }
   pending=null;
  }

  if(position){
   const hit=position.direction==="UP"?bar.low<=position.stop:bar.high>=position.stop;
   if(hit){
    const exit=position.direction==="UP"?Math.min(position.stop,bar.open):Math.max(position.stop,bar.open);
    await recordTrade(i,position,bar.timestamp,exit,"EMERGENCY_STOP");
    position=null;exits++;
   }
  }

  const mk=monthKey(bar.timestamp);
  if(mk!==reviewMonth){
   const sig=signal(bars,idx);
   reviewMonth=mk;reviews++;
   if(sig&&(!position||position.direction!==sig))pending=sig;
   await event("forward_shadow_review","REVIEWED",{symbol:i.key,month:mk,signal:sig,pendingDirection:pending,position:position?.direction??null});
  }
  checkpoint=bar.timestamp;
 }

 await sql`update ai_trade.forward_shadow_state set
  last_processed=to_timestamp(${checkpoint}),
  last_review_month=${reviewMonth},
  pending_direction=${pending},
  position=${position?JSON.stringify(position):null}::jsonb,
  updated_at=now()
 where strategy_id=${STRATEGY_ID} and symbol=${i.key}`;

 return {symbol:i.key,status:"PROCESSED",processedBars:indexes.length,entries,exits,reviews,lastProcessed:checkpoint,position:position?.direction??null,pending};
}

async function metrics(){
 const rows=await sql`
 select s.symbol,s.asset_class,s.last_processed,s.last_review_month,s.pending_direction,s.position,
        count(t.id)::int as closed_trades,
        coalesce(sum(t.gross_r),0)::float8 as gross_r,
        coalesce(sum(t.r_10bps),0)::float8 as r_10bps,
        coalesce(sum(t.r_20bps),0)::float8 as r_20bps
 from ai_trade.forward_shadow_state s
 left join ai_trade.forward_shadow_trades t
   on t.strategy_id=s.strategy_id and t.symbol=s.symbol
 where s.strategy_id=${STRATEGY_ID}
 group by s.symbol,s.asset_class,s.last_processed,s.last_review_month,s.pending_direction,s.position
 order by s.asset_class,s.symbol`;
 return rows;
}

Deno.serve(async(req)=>{
 try{
  if(!(await authorized(req)))return json({ok:false,status:"UNAUTHORIZED"},401);
  const runId=crypto.randomUUID(),results=[];
  for(const i of UNIVERSE){
   try{results.push(await processInstrument(i));}
   catch(error){
    const message=error instanceof Error?error.message:String(error);
    results.push({symbol:i.key,status:"ERROR",error:message});
    await event("forward_shadow_error","ERROR",{symbol:i.key,message});
   }
   await new Promise(r=>setTimeout(r,75));
  }
  const result={
   ok:true,status:"FORWARD_SHADOW",mode:"PAPER_ONLY",
   strategyId:STRATEGY_ID,forwardStartUtc:"2026-09-27",
   universeSize:UNIVERSE.length,brokerOrders:false,liveMoneyLocked:true,
   historicalTradeBackfill:false,results,metrics:await metrics()
  };
  await sql`insert into ai_trade.forward_shadow_runs(strategy_id,request_id,status,result)
   values(${STRATEGY_ID},${runId},'FORWARD_SHADOW',${JSON.stringify(result)}::jsonb)`;
  return json(result);
 }catch(error){
  return json({ok:false,status:"ERROR",brokerOrders:false,liveMoneyLocked:true,message:error instanceof Error?error.message:String(error)},500);
 }
});