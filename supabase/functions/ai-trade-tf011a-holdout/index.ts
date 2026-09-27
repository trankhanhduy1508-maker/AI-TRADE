import postgres from "npm:postgres@3.4.9";

type Direction="UP"|"DOWN";
type Category="FX"|"COMMODITY"|"CRYPTO"|"INDEX";
type Bar={timestamp:number;open:number;high:number;low:number;close:number};
type Instrument={key:string;yahooSymbol:string;category:Category};
type Trade={r:number;exitTs:number;symbol:string};
type Metrics={trades:number;netR:number;maxDrawdownR:number;tradeEvents:Trade[]};

const sql=postgres(Deno.env.get("SUPABASE_DB_URL")!,{prepare:false,max:1,connect_timeout:10,idle_timeout:20});
const json=(b:unknown,s=200)=>new Response(JSON.stringify(b),{status:s,headers:{"content-type":"application/json; charset=utf-8"}});

const SELECTED:Instrument[]=[
 {key:"GBPUSD",yahooSymbol:"GBPUSD=X",category:"FX"},
 {key:"USDJPY",yahooSymbol:"USDJPY=X",category:"FX"},
 {key:"XAUUSD",yahooSymbol:"GC=F",category:"COMMODITY"},
 {key:"USOIL",yahooSymbol:"CL=F",category:"COMMODITY"},
 {key:"BTCUSD",yahooSymbol:"BTC-USD",category:"CRYPTO"},
 {key:"ETHUSD",yahooSymbol:"ETH-USD",category:"CRYPTO"},
 {key:"US30",yahooSymbol:"^DJI",category:"INDEX"},
 {key:"NAS100",yahooSymbol:"^NDX",category:"INDEX"},
 {key:"US500",yahooSymbol:"^GSPC",category:"INDEX"},
];
const CLASS_WEIGHT:Record<Category,number>={FX:.25,COMMODITY:.25,CRYPTO:.25,INDEX:.25};

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
 const res=await fetch(url,{headers:{"user-agent":"AI-TRADE-TF011A/1.0"}});
 if(!res.ok) throw new Error("YAHOO_HTTP_"+res.status);
 const payload=await res.json(),result=payload?.chart?.result?.[0],q=result?.indicators?.quote?.[0],ts:number[]=result?.timestamp??[];
 if(!q) throw new Error("YAHOO_NO_DATA");
 const out:Bar[]=[];
 for(let i=0;i<ts.length;i++){
  const open=finite(q.open?.[i]),high=finite(q.high?.[i]),low=finite(q.low?.[i]),close=finite(q.close?.[i]);
  if(open===null||high===null||low===null||close===null||open<=0||high<=0||low<=0||close<=0) continue;
  if(high<Math.max(open,close)||low>Math.min(open,close)) continue;
  out.push({timestamp:Number(ts[i]),open,high,low,close});
 }
 out.sort((a,b)=>a.timestamp-b.timestamp);
 if(out.length<500) throw new Error("INSUFFICIENT_BARS");
 return out;
}
async function coinbaseBars(product:string,start:string,endExclusive:string):Promise<Bar[]>{
 const startMs=new Date(start+"T00:00:00Z").getTime(),endMs=new Date(endExclusive+"T00:00:00Z").getTime();
 const map=new Map<number,Bar>(),chunk=280*86400*1000;
 for(let s=startMs;s<endMs;s+=chunk){
  const e=Math.min(endMs,s+chunk);
  const url="https://api.exchange.coinbase.com/products/"+encodeURIComponent(product)+
   "/candles?granularity=86400&start="+encodeURIComponent(new Date(s).toISOString())+
   "&end="+encodeURIComponent(new Date(e).toISOString());
  const res=await fetch(url,{headers:{"user-agent":"AI-TRADE-TF011A/1.0","accept":"application/json"}});
  if(!res.ok) throw new Error("COINBASE_HTTP_"+res.status);
  const rows=await res.json();if(!Array.isArray(rows)) throw new Error("COINBASE_BAD_RESPONSE");
  for(const row of rows){
   if(!Array.isArray(row)||row.length<5) continue;
   const timestamp=Number(row[0]),low=finite(row[1]),high=finite(row[2]),open=finite(row[3]),close=finite(row[4]);
   if(open===null||high===null||low===null||close===null||open<=0||high<=0||low<=0||close<=0) continue;
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
 let s=0;for(let i=1;i<=period;i++)s+=tr[i];atr[period]=s/period;
 for(let i=period+1;i<bars.length;i++)atr[i]=(atr[i-1]*(period-1)+tr[i])/period;
 return atr;
}
function sma(bars:Bar[],idx:number,p:number){
 if(idx+1<p) return null;let s=0;for(let i=idx-p+1;i<=idx;i++)s+=bars[i].close;return s/p;
}
function signal(bars:Bar[],idx:number):Direction|null{
 if(idx<252) return null;
 const f=sma(bars,idx,10),s=sma(bars,idx,200);if(f===null||s===null) return null;
 const parts=[bars[idx].close-bars[idx-21].close,bars[idx].close-bars[idx-252].close,f-s]
  .map(x=>x>0?1:x<0?-1:0);
 const score=parts.reduce((a,b)=>a+b,0);
 return score>0?"UP":score<0?"DOWN":null;
}
function simulate(bars:Bar[],symbol:string,start:number,bps:number):Metrics{
 const atr=atrSeries(bars,20),end=bars.length;
 let pos:null|{direction:Direction;entry:number;stop:number;risk:number}=null;
 let pending:null|{direction:Direction;atr:number}=null;
 const events:Trade[]=[];
 const close=(price:number,idx:number)=>{
  if(!pos)return;
  const gross=pos.direction==="UP"?price-pos.entry:pos.entry-price;
  const friction=pos.entry*(bps/10000);
  events.push({r:round((gross-friction)/pos.risk,8),exitTs:bars[idx].timestamp,symbol});
  pos=null;
 };
 const enter=(direction:Direction,entry:number,av:number)=>{
  const risk=4*av;if(!(risk>0&&Number.isFinite(risk)))return;
  pos={direction,entry,stop:direction==="UP"?entry-risk:entry+risk,risk};
 };
 for(let idx=1;idx<end;idx++){
  const bar=bars[idx],prev=idx-1;
  if(pos){
   const hit=pos.direction==="UP"?bar.low<=pos.stop:bar.high>=pos.stop;
   if(hit){
    const exit=pos.direction==="UP"?Math.min(pos.stop,bar.open):Math.max(pos.stop,bar.open);
    close(exit,idx);pending=null;
   }
  }
  if(pending&&idx>=start){
   if(pos&&pos.direction!==pending.direction){const d=pending.direction,av=pending.atr;close(bar.open,idx);enter(d,bar.open,av);}
   else if(!pos)enter(pending.direction,bar.open,pending.atr);
   pending=null;
  }
  if(prev<start-1||prev<252||((prev-252)%21)!==0)continue;
  const av=atr[prev];if(!(av>0&&Number.isFinite(av)))continue;
  const sig=signal(bars,prev);if(!sig)continue;
  if(!pos||pos.direction!==sig)pending={direction:sig,atr:av};
 }
 if(pos)close(bars[end-1].close,end-1);
 let eq=0,peak=0,dd=0;for(const e of events){eq+=e.r;peak=Math.max(peak,eq);dd=Math.max(dd,peak-eq);}
 return {trades:events.length,netR:round(eq),maxDrawdownR:round(dd),tradeEvents:events};
}
function weightFor(i:Instrument){
 const count=SELECTED.filter(x=>x.category===i.category).length;
 return CLASS_WEIGHT[i.category]/count;
}
function weightedPortfolio(rows:{instrument:Instrument;metrics:Metrics}[]){
 const byTs=new Map<number,number>();
 for(const row of rows){
  const w=weightFor(row.instrument);
  for(const e of row.metrics.tradeEvents)byTs.set(e.exitTs,(byTs.get(e.exitTs)??0)+e.r*w);
 }
 const ordered=[...byTs.entries()].sort((a,b)=>a[0]-b[0]);
 let eq=0,peak=0,dd=0;for(const [,r] of ordered){eq+=r;peak=Math.max(peak,eq);dd=Math.max(dd,peak-eq);}
 return {netR:round(eq),maxDrawdownR:round(dd),returnToDrawdown:dd>0?round(eq/dd):eq>0?999:0};
}
function contributions(rows:{instrument:Instrument;metrics:Metrics}[]){
 const market=rows.map(r=>({symbol:r.instrument.key,category:r.instrument.category,weight:weightFor(r.instrument),weightedNetR:round(r.metrics.netR*weightFor(r.instrument))}));
 const positives=market.filter(x=>x.weightedNetR>0);
 const positiveTotal=positives.reduce((a,b)=>a+b.weightedNetR,0);
 const marketDominance=positiveTotal>0?Math.max(...positives.map(x=>x.weightedNetR))/positiveTotal:1;
 const classMap=new Map<Category,number>();
 for(const x of market)classMap.set(x.category,(classMap.get(x.category)??0)+x.weightedNetR);
 const positiveClasses=[...classMap.entries()].filter(([,v])=>v>0);
 const classPositiveTotal=positiveClasses.reduce((a,[,v])=>a+v,0);
 const classDominance=classPositiveTotal>0?Math.max(...positiveClasses.map(([,v])=>v))/classPositiveTotal:1;
 return {
  market,
  classNetR:Object.fromEntries(classMap),
  marketDominance:round(marketDominance,4),
  classDominance:round(classDominance,4),
  positiveClassCount:positiveClasses.length,
 };
}

Deno.serve(async(req)=>{
 try{
  if(!(await authorized(req)))return json({ok:false,status:"UNAUTHORIZED"},401);
  const today=new Date(),endExclusive=new Date(Date.UTC(today.getUTCFullYear(),today.getUTCMonth(),today.getUTCDate()+1)).toISOString().slice(0,10);
  const loaded:{instrument:Instrument;bars:Bar[]}[]=[];
  for(const instrument of SELECTED){loaded.push({instrument,bars:await longestBars(instrument,endExclusive)});await new Promise(r=>setTimeout(r,80));}
  const rows10:any[]=[],rows20:any[]=[];
  for(const {instrument,bars} of loaded){
   const start=Math.floor(bars.length*.80);
   rows10.push({instrument,holdoutStart:new Date(bars[start].timestamp*1000).toISOString().slice(0,10),metrics:simulate(bars,instrument.key,start,10)});
   rows20.push({instrument,metrics:simulate(bars,instrument.key,start,20)});
  }
  const p10=weightedPortfolio(rows10),p20=weightedPortfolio(rows20),c10=contributions(rows10);
  const positiveMarkets=rows10.filter(x=>x.metrics.netR>0).length;
  const pass=
   p10.netR>0&&p20.netR>0&&p10.returnToDrawdown>0.5&&
   positiveMarkets>=6&&c10.positiveClassCount>=3&&
   c10.marketDominance<=0.30&&c10.classDominance<=0.50;

  const result={
   ok:true,status:pass?"HOLDOUT_PASS":"HOLDOUT_FAIL",mode:"RESEARCH_ONLY",brokerOrders:false,liveMoneyLocked:true,
   strategyId:"TF-011A-CLASS-BALANCED-TREND",
   preregistration:"research/TF_011A_CLASS_BALANCED_HOLDOUT_PROTOCOL_2026-09-27.md",
   holdout:{
    pass,
    portfolio10bps:p10,
    portfolio20bps:p20,
    positiveMarkets,
    positiveClassCount:c10.positiveClassCount,
    marketDominance:c10.marketDominance,
    classDominance:c10.classDominance,
    classNetR10bps:c10.classNetR,
    markets10bps:rows10.map(x=>({symbol:x.instrument.key,category:x.instrument.category,weight:weightFor(x.instrument),holdoutStart:x.holdoutStart,trades:x.metrics.trades,netR:x.metrics.netR,maxDrawdownR:x.metrics.maxDrawdownR})),
    markets20bps:rows20.map(x=>({symbol:x.instrument.key,netR:x.metrics.netR}))
   }
  };
  await sql`
   insert into ai_trade.robustness_runs(run_key,strategy_id,result)
   values('TF011A_CLASS_BALANCED_FINAL_HOLDOUT_20260927','TF-011A-CLASS-BALANCED-TREND',${sql.json(result)})
   on conflict (run_key) do nothing
  `;
  return json(result);
 }catch(error){
  return json({ok:false,status:"ERROR",brokerOrders:false,liveMoneyLocked:true,message:error instanceof Error?error.message:String(error)},500);
 }
});