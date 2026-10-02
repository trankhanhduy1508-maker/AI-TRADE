import postgres from "npm:postgres@3.4.9";

type Direction="UP"|"DOWN";
type Bar={timestamp:number;open:number;high:number;low:number;close:number};
type Instrument={key:string;label:string;yahooSymbol:string;category:"FX"|"COMMODITY"|"CRYPTO"|"INDEX"};
type CandidateId="TF-008A-MULTI-HORIZON-TSMOM"|"TF-009A-DIVERSIFIED-TREND-ENSEMBLE"|"TF-010A-TSMOM-6M";
type Trade={r:number;exitTs:number;symbol:string};
type Metrics={trades:number;netR:number;maxDrawdownR:number;tradeEvents:Trade[]};

const sql=postgres(Deno.env.get("SUPABASE_DB_URL")!,{prepare:false,max:1,connect_timeout:10,idle_timeout:20});
const json=(b:unknown,s=200)=>new Response(JSON.stringify(b),{status:s,headers:{"content-type":"application/json; charset=utf-8"}});

const UNIVERSE:Instrument[]=[
 {key:"EURUSD",label:"EUR/USD",yahooSymbol:"EURUSD=X",category:"FX"},
 {key:"GBPUSD",label:"GBP/USD",yahooSymbol:"GBPUSD=X",category:"FX"},
 {key:"USDJPY",label:"USD/JPY",yahooSymbol:"USDJPY=X",category:"FX"},
 {key:"AUDUSD",label:"AUD/USD",yahooSymbol:"AUDUSD=X",category:"FX"},
 {key:"USDCAD",label:"USD/CAD",yahooSymbol:"CAD=X",category:"FX"},
 {key:"USDCHF",label:"USD/CHF",yahooSymbol:"CHF=X",category:"FX"},
 {key:"NZDUSD",label:"NZD/USD",yahooSymbol:"NZDUSD=X",category:"FX"},
 {key:"XAUUSD",label:"Gold",yahooSymbol:"GC=F",category:"COMMODITY"},
 {key:"USOIL",label:"WTI Oil",yahooSymbol:"CL=F",category:"COMMODITY"},
 {key:"BTCUSD",label:"Bitcoin",yahooSymbol:"BTC-USD",category:"CRYPTO"},
 {key:"ETHUSD",label:"Ethereum",yahooSymbol:"ETH-USD",category:"CRYPTO"},
 {key:"US30",label:"Dow Jones",yahooSymbol:"^DJI",category:"INDEX"},
 {key:"NAS100",label:"Nasdaq 100",yahooSymbol:"^NDX",category:"INDEX"},
 {key:"US500",label:"S&P 500",yahooSymbol:"^GSPC",category:"INDEX"},
];
const CANDIDATES:CandidateId[]=[
 "TF-008A-MULTI-HORIZON-TSMOM",
 "TF-009A-DIVERSIFIED-TREND-ENSEMBLE",
 "TF-010A-TSMOM-6M",
];

async function authorized(req:Request){
 const rows=await sql`select secret from ai_trade.cron_auth where id=1`;
 const expected=String(rows[0]?.secret??"");
 return Boolean(expected)&&(req.headers.get("x-ai-trade-cron")??"")===expected;
}
function finite(x:unknown){const n=Number(x);return Number.isFinite(n)?n:null;}
function round(v:number,d=6){const p=10**d;return Math.round(v*p)/p;}

async function yahooBars(symbol:string,start:string,endExclusive:string):Promise<Bar[]>{
 const p1=Math.floor(new Date(start+"T00:00:00Z").getTime()/1000);
 const p2=Math.floor(new Date(endExclusive+"T00:00:00Z").getTime()/1000);
 const url="https://query1.finance.yahoo.com/v8/finance/chart/"+encodeURIComponent(symbol)+
   "?period1="+p1+"&period2="+p2+"&interval=1d&events=history&includeAdjustedClose=true";
 const res=await fetch(url,{headers:{"user-agent":"AI-TRADE-portfolio-research/1.0"}});
 if(!res.ok) throw new Error("YAHOO_HTTP_"+res.status);
 const payload=await res.json();
 if(payload?.chart?.error) throw new Error("YAHOO_CHART_ERROR");
 const result=payload?.chart?.result?.[0],q=result?.indicators?.quote?.[0],ts:number[]=result?.timestamp??[];
 if(!q) throw new Error("YAHOO_NO_DATA");
 const out:Bar[]=[];
 for(let i=0;i<ts.length;i++){
  const open=finite(q.open?.[i]),high=finite(q.high?.[i]),low=finite(q.low?.[i]),close=finite(q.close?.[i]);
  if(open===null||high===null||low===null||close===null) continue;
  if(open<=0||high<=0||low<=0||close<=0) continue;
  if(high<Math.max(open,close)||low>Math.min(open,close)) continue;
  out.push({timestamp:Number(ts[i]),open,high,low,close});
 }
 out.sort((a,b)=>a.timestamp-b.timestamp);
 if(out.length<500) throw new Error("INSUFFICIENT_BARS");
 return out;
}
async function coinbaseBars(product:string,start:string,endExclusive:string):Promise<Bar[]>{
 const startMs=new Date(start+"T00:00:00Z").getTime(), endMs=new Date(endExclusive+"T00:00:00Z").getTime();
 const chunkMs=280*86400*1000, map=new Map<number,Bar>();
 for(let s=startMs;s<endMs;s+=chunkMs){
  const e=Math.min(endMs,s+chunkMs);
  const url="https://api.exchange.coinbase.com/products/"+encodeURIComponent(product)+
    "/candles?granularity=86400&start="+encodeURIComponent(new Date(s).toISOString())+
    "&end="+encodeURIComponent(new Date(e).toISOString());
  const res=await fetch(url,{headers:{"user-agent":"AI-TRADE-portfolio-research/1.0","accept":"application/json"}});
  if(!res.ok) throw new Error("COINBASE_HTTP_"+res.status);
  const rows=await res.json();
  if(!Array.isArray(rows)) throw new Error("COINBASE_BAD_RESPONSE");
  for(const row of rows){
   if(!Array.isArray(row)||row.length<5) continue;
   const timestamp=Number(row[0]),low=finite(row[1]),high=finite(row[2]),open=finite(row[3]),close=finite(row[4]);
   if(open===null||high===null||low===null||close===null) continue;
   if(open<=0||high<=0||low<=0||close<=0) continue;
   map.set(timestamp,{timestamp,open,high,low,close});
  }
  await new Promise(r=>setTimeout(r,220));
 }
 const out=[...map.values()].sort((a,b)=>a.timestamp-b.timestamp);
 if(out.length<500) throw new Error("INSUFFICIENT_COINBASE_BARS");
 return out;
}
async function longestBars(i:Instrument,endExclusive:string){
 if(i.key==="ETHUSD") return coinbaseBars("ETH-USD","2015-01-01",endExclusive);
 if(i.key==="BTCUSD") return yahooBars(i.yahooSymbol,"2014-01-01",endExclusive);
 try{return await yahooBars(i.yahooSymbol,"1900-01-01",endExclusive);}
 catch(_){return yahooBars(i.yahooSymbol,"1970-01-01",endExclusive);}
}
function atrSeries(bars:Bar[],period=20){
 const tr:number[]=[],atr=Array(bars.length).fill(NaN);
 for(let i=0;i<bars.length;i++){
  if(i===0) tr.push(bars[i].high-bars[i].low);
  else tr.push(Math.max(bars[i].high-bars[i].low,Math.abs(bars[i].high-bars[i-1].close),Math.abs(bars[i].low-bars[i-1].close)));
 }
 if(bars.length<=period) return atr;
 let s=0;for(let i=1;i<=period;i++) s+=tr[i];
 atr[period]=s/period;
 for(let i=period+1;i<bars.length;i++) atr[i]=(atr[i-1]*(period-1)+tr[i])/period;
 return atr;
}
function sma(bars:Bar[],idx:number,p:number){
 if(idx+1<p) return null;let s=0;for(let i=idx-p+1;i<=idx;i++)s+=bars[i].close;return s/p;
}
function signalFor(candidate:CandidateId,bars:Bar[],idx:number):Direction|null{
 if(candidate==="TF-008A-MULTI-HORIZON-TSMOM"){
  if(idx<252) return null;
  const signs=[63,126,252].map(p=>bars[idx].close-bars[idx-p].close).map(x=>x>0?1:x<0?-1:0);
  const score=signs.reduce((a,b)=>a+b,0);
  return score>0?"UP":score<0?"DOWN":null;
 }
 if(candidate==="TF-009A-DIVERSIFIED-TREND-ENSEMBLE"){
  if(idx<252) return null;
  const f=sma(bars,idx,10),s=sma(bars,idx,200);
  if(f===null||s===null) return null;
  const signs=[
    bars[idx].close-bars[idx-21].close,
    bars[idx].close-bars[idx-252].close,
    f-s
  ].map(x=>x>0?1:x<0?-1:0);
  const score=signs.reduce((a,b)=>a+b,0);
  return score>0?"UP":score<0?"DOWN":null;
 }
 if(idx<126) return null;
 const d=bars[idx].close-bars[idx-126].close;
 return d>0?"UP":d<0?"DOWN":null;
}
function maxLookback(candidate:CandidateId){return candidate==="TF-010A-TSMOM-6M"?126:252;}

function simulateMarket(bars:Bar[],symbol:string,candidate:CandidateId,start:number,end:number,bps:number):Metrics{
 const atr=atrSeries(bars,20);
 let pos:null|{direction:Direction;entry:number;stop:number;risk:number;entryIndex:number}=null;
 let pending:null|{direction:Direction;atr:number}=null;
 const events:Trade[]=[];
 const close=(price:number,idx:number)=>{
  if(!pos) return;
  const gross=pos.direction==="UP"?price-pos.entry:pos.entry-price;
  const friction=pos.entry*(bps/10000);
  events.push({r:round((gross-friction)/pos.risk,8),exitTs:bars[idx].timestamp,symbol});
  pos=null;
 };
 const enter=(direction:Direction,entry:number,av:number,idx:number)=>{
  const risk=4*av;if(!(risk>0&&Number.isFinite(risk))) return;
  pos={direction,entry,stop:direction==="UP"?entry-risk:entry+risk,risk,entryIndex:idx};
 };

 const anchor=maxLookback(candidate);
 for(let idx=1;idx<bars.length;idx++){
  const bar=bars[idx],prev=idx-1;

  if(pos){
   const hit=pos.direction==="UP"?bar.low<=pos.stop:bar.high>=pos.stop;
   if(hit){
    const exit=pos.direction==="UP"?Math.min(pos.stop,bar.open):Math.max(pos.stop,bar.open);
    close(exit,idx);pending=null;
   }
  }

  if(pending&&idx>=start&&idx<end){
   if(pos&&pos.direction!==pending.direction){const d=pending.direction,av=pending.atr;close(bar.open,idx);enter(d,bar.open,av,idx);}
   else if(!pos) enter(pending.direction,bar.open,pending.atr,idx);
   pending=null;
  }

  if(idx>=end) break;
  if(prev<start-1) continue;
  if(prev<anchor||((prev-anchor)%21)!==0) continue;
  const av=atr[prev];if(!(av>0&&Number.isFinite(av))) continue;
  const sig=signalFor(candidate,bars,prev);if(!sig) continue;
  if(!pos||pos.direction!==sig) pending={direction:sig,atr:av};
 }
 if(pos){
  const last=Math.min(end-1,bars.length-1);
  if(last>=start) close(bars[last].close,last);
 }
 let eq=0,peak=0,dd=0;
 for(const e of events){eq+=e.r;peak=Math.max(peak,eq);dd=Math.max(dd,peak-eq);}
 return {trades:events.length,netR:round(eq),maxDrawdownR:round(dd),tradeEvents:events};
}

function portfolioMetrics(rows:{symbol:string;metrics:Metrics}[]){
 const n=rows.length;if(!n) return {netR:0,maxDrawdownR:0,ratio:0,events:[] as any[]};
 const byTs=new Map<number,number>();
 for(const row of rows) for(const e of row.metrics.tradeEvents){
  byTs.set(e.exitTs,(byTs.get(e.exitTs)??0)+e.r/n);
 }
 const ordered=[...byTs.entries()].sort((a,b)=>a[0]-b[0]).map(([ts,r])=>({ts,r}));
 let eq=0,peak=0,dd=0;
 for(const e of ordered){eq+=e.r;peak=Math.max(peak,eq);dd=Math.max(dd,peak-eq);}
 return {netR:round(eq),maxDrawdownR:round(dd),ratio:dd>0?round(eq/dd):eq>0?999:0,events:ordered};
}
function concentration(rows:{symbol:string;metrics:Metrics}[]){
 const positives=rows.filter(x=>x.metrics.netR>0).map(x=>x.metrics.netR);
 const total=positives.reduce((a,b)=>a+b,0);
 return total>0?round(Math.max(...positives)/total,4):1;
}

Deno.serve(async(req)=>{
 try{
  if(!(await authorized(req))) return json({ok:false,status:"UNAUTHORIZED"},401);
  const today=new Date(),endExclusive=new Date(Date.UTC(today.getUTCFullYear(),today.getUTCMonth(),today.getUTCDate()+1)).toISOString().slice(0,10);
  const loaded:{instrument:Instrument;bars:Bar[]}[]=[];
  for(const instrument of UNIVERSE){
   loaded.push({instrument,bars:await longestBars(instrument,endExclusive)});
   await new Promise(r=>setTimeout(r,80));
  }

  const validation:any={};
  for(const candidate of CANDIDATES){
   const all10:any[]=[],all20:any[]=[];
   for(const {instrument,bars} of loaded){
    const start=Math.floor(bars.length*.60),end=Math.floor(bars.length*.80);
    all10.push({instrument,symbol:instrument.key,metrics:simulateMarket(bars,instrument.key,candidate,start,end,10)});
    all20.push({instrument,symbol:instrument.key,metrics:simulateMarket(bars,instrument.key,candidate,start,end,20)});
   }
   const selected10=all10.filter((x:any)=>{
    const m20=all20.find((y:any)=>y.symbol===x.symbol)?.metrics;
    return x.metrics.trades>=3&&x.metrics.netR>0&&m20&&m20.netR>0;
   });
   const selectedSymbols=new Set(selected10.map((x:any)=>x.symbol));
   const selected20=all20.filter((x:any)=>selectedSymbols.has(x.symbol));
   const categories=new Set(selected10.map((x:any)=>x.instrument.category));
   const fxCount=selected10.filter((x:any)=>x.instrument.category==="FX").length;
   const commodityCount=selected10.filter((x:any)=>x.instrument.category==="COMMODITY").length;
   const cryptoCount=selected10.filter((x:any)=>x.instrument.category==="CRYPTO").length;
   const indexCount=selected10.filter((x:any)=>x.instrument.category==="INDEX").length;
   const p10=portfolioMetrics(selected10),p20=portfolioMetrics(selected20);
   const dom=concentration(selected10);
   const eligible=
    selected10.length>=6&&fxCount>=2&&commodityCount>=1&&cryptoCount>=1&&indexCount>=1&&
    p10.netR>0&&p20.netR>0&&p10.ratio>0.5&&dom<=0.40;
   validation[candidate]={
    eligible,
    selectedMarkets:[...selectedSymbols],
    breadth:{total:selected10.length,fx:fxCount,commodity:commodityCount,crypto:cryptoCount,index:indexCount,categories:[...categories]},
    portfolio10bps:{netR:p10.netR,maxDrawdownR:p10.maxDrawdownR,returnToDrawdown:p10.ratio},
    portfolio20bps:{netR:p20.netR,maxDrawdownR:p20.maxDrawdownR,returnToDrawdown:p20.ratio},
    positiveContributionDominance:dom,
    markets10bps:all10.map((x:any)=>({symbol:x.symbol,category:x.instrument.category,trades:x.metrics.trades,netR:x.metrics.netR,maxDrawdownR:x.metrics.maxDrawdownR})),
    markets20bps:all20.map((x:any)=>({symbol:x.symbol,trades:x.metrics.trades,netR:x.metrics.netR}))
   };
  }

  const eligible=CANDIDATES.filter(c=>validation[c].eligible).sort((a,b)=>{
   const A=validation[a],B=validation[b];
   return B.portfolio10bps.returnToDrawdown-A.portfolio10bps.returnToDrawdown ||
     B.breadth.total-A.breadth.total ||
     A.positiveContributionDominance-B.positiveContributionDominance;
  });
  const selected:CandidateId|null=eligible[0]??null;
  let holdout:any=null;

  if(selected){
   const frozen=new Set<string>(validation[selected].selectedMarkets);
   const rows10:any[]=[],rows20:any[]=[];
   for(const {instrument,bars} of loaded){
    if(!frozen.has(instrument.key)) continue;
    const start=Math.floor(bars.length*.80),end=bars.length;
    rows10.push({instrument,symbol:instrument.key,metrics:simulateMarket(bars,instrument.key,selected,start,end,10)});
    rows20.push({instrument,symbol:instrument.key,metrics:simulateMarket(bars,instrument.key,selected,start,end,20)});
   }
   const p10=portfolioMetrics(rows10),p20=portfolioMetrics(rows20);
   const positive10=rows10.filter((x:any)=>x.metrics.netR>0);
   const positiveCats=new Set(positive10.map((x:any)=>x.instrument.category));
   const dom=concentration(rows10);
   const positiveFraction=rows10.length?positive10.length/rows10.length:0;
   const pass=
    p10.netR>0&&p20.netR>0&&positiveFraction>=0.60&&
    positiveCats.has("FX")&&positiveCats.has("COMMODITY")&&positiveCats.has("CRYPTO")&&positiveCats.has("INDEX")&&
    p10.ratio>0.5&&dom<=0.40;
   holdout={
    selectedCandidate:selected,
    frozenMarkets:[...frozen],
    pass,
    positiveFraction:round(positiveFraction,4),
    positiveCategories:[...positiveCats],
    portfolio10bps:{netR:p10.netR,maxDrawdownR:p10.maxDrawdownR,returnToDrawdown:p10.ratio},
    portfolio20bps:{netR:p20.netR,maxDrawdownR:p20.maxDrawdownR,returnToDrawdown:p20.ratio},
    positiveContributionDominance:dom,
    markets10bps:rows10.map((x:any)=>({symbol:x.symbol,category:x.instrument.category,trades:x.metrics.trades,netR:x.metrics.netR,maxDrawdownR:x.metrics.maxDrawdownR})),
    markets20bps:rows20.map((x:any)=>({symbol:x.symbol,netR:x.metrics.netR}))
   };
  }

  const result={
   ok:true,status:selected?(holdout?.pass?"HOLDOUT_PASS":"HOLDOUT_FAIL"):"NO_VALIDATION_CANDIDATE",
   mode:"RESEARCH_ONLY",brokerOrders:false,liveMoneyLocked:true,
   preregistration:"research/PREREGISTERED_PORTFOLIO_TREND_SUITE_2026-09-27.md",
   validation,selectedCandidate:selected,holdout
  };
  await sql`
   insert into ai_trade.robustness_runs(run_key,strategy_id,result)
   values('PREREG_PORTFOLIO_TREND_SUITE_20260927_V1','PREREGISTERED_PORTFOLIO_TREND_SUITE',${sql.json(result)})
   on conflict (run_key) do nothing
  `;
  return json(result);
 }catch(error){
  return json({ok:false,status:"ERROR",brokerOrders:false,liveMoneyLocked:true,message:error instanceof Error?error.message:String(error)},500);
 }
});