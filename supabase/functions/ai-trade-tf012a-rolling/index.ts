import postgres from "npm:postgres@3.4.9";

type Direction="UP"|"DOWN";
type Category="FX"|"COMMODITY"|"CRYPTO"|"INDEX";
type Bar={timestamp:number;open:number;high:number;low:number;close:number};
type Instrument={key:string;yahooSymbol:string;category:Category};
type Trade={r:number;exitTs:number;symbol:string};
type Metrics={trades:number;netR:number;maxDrawdownR:number;ratio:number;events:Trade[]};

const sql=postgres(Deno.env.get("SUPABASE_DB_URL")!,{prepare:false,max:1,connect_timeout:10,idle_timeout:20});
const json=(b:unknown,s=200)=>new Response(JSON.stringify(b),{status:s,headers:{"content-type":"application/json; charset=utf-8"}});

const UNIVERSE:Instrument[]=[
 {key:"EURUSD",yahooSymbol:"EURUSD=X",category:"FX"},
 {key:"GBPUSD",yahooSymbol:"GBPUSD=X",category:"FX"},
 {key:"USDJPY",yahooSymbol:"USDJPY=X",category:"FX"},
 {key:"AUDUSD",yahooSymbol:"AUDUSD=X",category:"FX"},
 {key:"USDCAD",yahooSymbol:"CAD=X",category:"FX"},
 {key:"USDCHF",yahooSymbol:"CHF=X",category:"FX"},
 {key:"NZDUSD",yahooSymbol:"NZDUSD=X",category:"FX"},
 {key:"XAUUSD",yahooSymbol:"GC=F",category:"COMMODITY"},
 {key:"USOIL",yahooSymbol:"CL=F",category:"COMMODITY"},
 {key:"BTCUSD",yahooSymbol:"BTC-USD",category:"CRYPTO"},
 {key:"ETHUSD",yahooSymbol:"ETH-USD",category:"CRYPTO"},
 {key:"US30",yahooSymbol:"^DJI",category:"INDEX"},
 {key:"NAS100",yahooSymbol:"^NDX",category:"INDEX"},
 {key:"US500",yahooSymbol:"^GSPC",category:"INDEX"},
];
const CLASS_WEIGHT:Record<Category,number>={FX:.25,COMMODITY:.25,CRYPTO:.25,INDEX:.25};
const MAX_MARKET_WEIGHT=.125;

async function authorized(req:Request){
 const rows=await sql`select secret from ai_trade.cron_auth where id=1`;
 const expected=String(rows[0]?.secret??"");
 return Boolean(expected)&&(req.headers.get("x-ai-trade-cron")??"")===expected;
}
function finite(x:unknown){const n=Number(x);return Number.isFinite(n)?n:null;}
function round(v:number,d=6){const p=10**d;return Math.round(v*p)/p;}

async function yahooBars(symbol:string,start:string,endExclusive:string):Promise<Bar[]>{
 const p1=Math.floor(new Date(start+"T00:00:00Z").getTime()/1000),p2=Math.floor(new Date(endExclusive+"T00:00:00Z").getTime()/1000);
 const url="https://query1.finance.yahoo.com/v8/finance/chart/"+encodeURIComponent(symbol)+
  "?period1="+p1+"&period2="+p2+"&interval=1d&events=history&includeAdjustedClose=true";
 const res=await fetch(url,{headers:{"user-agent":"AI-TRADE-TF012A/1.0"}});
 if(!res.ok)throw new Error("YAHOO_HTTP_"+res.status);
 const payload=await res.json(),result=payload?.chart?.result?.[0],q=result?.indicators?.quote?.[0],ts:number[]=result?.timestamp??[];
 if(!q)throw new Error("YAHOO_NO_DATA");
 const out:Bar[]=[];
 for(let i=0;i<ts.length;i++){
  const open=finite(q.open?.[i]),high=finite(q.high?.[i]),low=finite(q.low?.[i]),close=finite(q.close?.[i]);
  if(open===null||high===null||low===null||close===null||open<=0||high<=0||low<=0||close<=0)continue;
  if(high<Math.max(open,close)||low>Math.min(open,close))continue;
  out.push({timestamp:Number(ts[i]),open,high,low,close});
 }
 out.sort((a,b)=>a.timestamp-b.timestamp);
 if(out.length<500)throw new Error("INSUFFICIENT_BARS");
 return out;
}
async function coinbaseBars(product:string,start:string,endExclusive:string):Promise<Bar[]>{
 const startMs=new Date(start+"T00:00:00Z").getTime(),endMs=new Date(endExclusive+"T00:00:00Z").getTime(),chunk=280*86400*1000;
 const map=new Map<number,Bar>();
 for(let s=startMs;s<endMs;s+=chunk){
  const e=Math.min(endMs,s+chunk);
  const url="https://api.exchange.coinbase.com/products/"+encodeURIComponent(product)+
   "/candles?granularity=86400&start="+encodeURIComponent(new Date(s).toISOString())+
   "&end="+encodeURIComponent(new Date(e).toISOString());
  const res=await fetch(url,{headers:{"user-agent":"AI-TRADE-TF012A/1.0","accept":"application/json"}});
  if(!res.ok)throw new Error("COINBASE_HTTP_"+res.status);
  const rows=await res.json();if(!Array.isArray(rows))throw new Error("COINBASE_BAD_RESPONSE");
  for(const row of rows){
   if(!Array.isArray(row)||row.length<5)continue;
   const timestamp=Number(row[0]),low=finite(row[1]),high=finite(row[2]),open=finite(row[3]),close=finite(row[4]);
   if(open===null||high===null||low===null||close===null||open<=0||high<=0||low<=0||close<=0)continue;
   map.set(timestamp,{timestamp,open,high,low,close});
  }
  await new Promise(r=>setTimeout(r,220));
 }
 const out=[...map.values()].sort((a,b)=>a.timestamp-b.timestamp);
 if(out.length<500)throw new Error("INSUFFICIENT_COINBASE_BARS");
 return out;
}
async function longestBars(i:Instrument,endExclusive:string){
 if(i.key==="ETHUSD")return coinbaseBars("ETH-USD","2015-01-01",endExclusive);
 if(i.key==="BTCUSD")return yahooBars(i.yahooSymbol,"2014-01-01",endExclusive);
 try{return await yahooBars(i.yahooSymbol,"1900-01-01",endExclusive);}
 catch(_){return yahooBars(i.yahooSymbol,"1970-01-01",endExclusive);}
}
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
 const v=[bars[idx].close-bars[idx-21].close,bars[idx].close-bars[idx-252].close,fast-slow].map(x=>x>0?1:x<0?-1:0);
 const score=v.reduce((a,b)=>a+b,0);return score>0?"UP":score<0?"DOWN":null;
}
function lowerBound(bars:Bar[],ts:number){
 let lo=0,hi=bars.length;
 while(lo<hi){const m=(lo+hi)>>1;if(bars[m].timestamp<ts)lo=m+1;else hi=m;}
 return lo;
}
function simulate(bars:Bar[],symbol:string,startTs:number,endTs:number,bps:number):Metrics{
 const start=lowerBound(bars,startTs),end=Math.min(lowerBound(bars,endTs),bars.length);
 if(end-start<5)return {trades:0,netR:0,maxDrawdownR:0,ratio:0,events:[]};
 const atr=atrSeries(bars,20);
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
 const enter=(direction:Direction,price:number,av:number)=>{
  const risk=4*av;if(!(risk>0&&Number.isFinite(risk)))return;
  pos={direction,entry:price,stop:direction==="UP"?price-risk:price+risk,risk};
 };
 for(let idx=1;idx<bars.length;idx++){
  const bar=bars[idx],prev=idx-1;
  if(pos){
   const hit=pos.direction==="UP"?bar.low<=pos.stop:bar.high>=pos.stop;
   if(hit){const exit=pos.direction==="UP"?Math.min(pos.stop,bar.open):Math.max(pos.stop,bar.open);close(exit,idx);pending=null;}
  }
  if(pending&&idx>=start&&idx<end){
   if(pos&&pos.direction!==pending.direction){const d=pending.direction,av=pending.atr;close(bar.open,idx);enter(d,bar.open,av);}
   else if(!pos)enter(pending.direction,bar.open,pending.atr);
   pending=null;
  }
  if(idx>=end)break;
  if(prev<start-1||prev<252||((prev-252)%21)!==0)continue;
  const av=atr[prev];if(!(av>0&&Number.isFinite(av)))continue;
  const sig=signal(bars,prev);if(sig&&(!pos||pos.direction!==sig))pending={direction:sig,atr:av};
 }
 if(pos)close(bars[end-1].close,end-1);
 let eq=0,peak=0,dd=0;for(const e of events){eq+=e.r;peak=Math.max(peak,eq);dd=Math.max(dd,peak-eq);}
 return {trades:events.length,netR:round(eq),maxDrawdownR:round(dd),ratio:dd>0?round(eq/dd):eq>0?999:0,events};
}
function marketWeight(category:Category,count:number){
 if(count<=0)return 0;return Math.min(MAX_MARKET_WEIGHT,CLASS_WEIGHT[category]/count);
}
function overallMetrics(events:{ts:number;r:number}[]){
 const ordered=[...events].sort((a,b)=>a.ts-b.ts);let eq=0,peak=0,dd=0;
 for(const e of ordered){eq+=e.r;peak=Math.max(peak,eq);dd=Math.max(dd,peak-eq);}
 return {netR:round(eq),maxDrawdownR:round(dd),returnToDrawdown:dd>0?round(eq/dd):eq>0?999:0};
}

Deno.serve(async(req)=>{
 try{
  if(!(await authorized(req)))return json({ok:false,status:"UNAUTHORIZED"},401);
  const now=new Date(),lastYear=now.getUTCFullYear();
  const endExclusive=new Date(Date.UTC(lastYear,now.getUTCMonth(),now.getUTCDate()+1)).toISOString().slice(0,10);
  const loaded=new Map<string,{instrument:Instrument;bars:Bar[]}>();
  for(const i of UNIVERSE){loaded.set(i.key,{instrument:i,bars:await longestBars(i,endExclusive)});await new Promise(r=>setTimeout(r,80));}

  const yearly:any[]=[];
  const allEvents10:{ts:number;r:number}[]=[],allEvents20:{ts:number;r:number}[]=[];
  const marketContribution=new Map<string,number>(),classContribution=new Map<Category,number>();
  let completedYears=0;

  for(let year=2010;year<=lastYear;year++){
   const trainStart=Date.UTC(year-5,0,1)/1000,trainEnd=Date.UTC(year,0,1)/1000;
   const testStart=trainEnd;
   const testEnd=year===lastYear
    ? Math.floor(new Date(endExclusive+"T00:00:00Z").getTime()/1000)
    : Date.UTC(year+1,0,1)/1000;
   if(testEnd<=testStart)continue;

   const eligibility:any[]=[];
   for(const i of UNIVERSE){
    const data=loaded.get(i.key)!;
    const tm=simulate(data.bars,i.key,trainStart,trainEnd,10);
    const enoughCalendarHistory=data.bars.length>0&&data.bars[0].timestamp<=trainStart+31*86400;
    const eligible=enoughCalendarHistory&&tm.trades>=5&&tm.netR>0&&tm.ratio>0.5;
    eligibility.push({instrument:i,eligible,training:{trades:tm.trades,netR:tm.netR,maxDrawdownR:tm.maxDrawdownR,ratio:tm.ratio}});
   }

   const eligible=eligibility.filter(x=>x.eligible);
   const counts:Record<Category,number>={FX:0,COMMODITY:0,CRYPTO:0,INDEX:0};
   for(const x of eligible)counts[x.instrument.category]++;

   const rows10:any[]=[],rows20:any[]=[];
   for(const x of eligible){
    const i=x.instrument as Instrument,w=marketWeight(i.category,counts[i.category]);
    if(w<=0)continue;
    const data=loaded.get(i.key)!;
    const m10=simulate(data.bars,i.key,testStart,testEnd,10),m20=simulate(data.bars,i.key,testStart,testEnd,20);
    rows10.push({instrument:i,weight:w,metrics:m10});
    rows20.push({instrument:i,weight:w,metrics:m20});
    const weighted=m10.netR*w;
    marketContribution.set(i.key,(marketContribution.get(i.key)??0)+weighted);
    classContribution.set(i.category,(classContribution.get(i.category)??0)+weighted);
    for(const e of m10.events)allEvents10.push({ts:e.exitTs,r:e.r*w});
    for(const e of m20.events)allEvents20.push({ts:e.exitTs,r:e.r*w});
   }

   const yearNet10=round(rows10.reduce((s,x)=>s+x.metrics.netR*x.weight,0));
   const yearNet20=round(rows20.reduce((s,x)=>s+x.metrics.netR*x.weight,0));
   yearly.push({
    year,
    selected:eligible.map(x=>({symbol:x.instrument.key,category:x.instrument.category,training:x.training,weight:marketWeight(x.instrument.category,counts[x.instrument.category])})),
    selectedCount:eligible.length,
    activeClassCount:Object.values(counts).filter(x=>x>0).length,
    netR10bps:yearNet10,
    netR20bps:yearNet20,
   });
   completedYears++;
  }

  const p10=overallMetrics(allEvents10),p20=overallMetrics(allEvents20);
  const positiveYears=yearly.filter(y=>y.netR10bps>0).length;
  const positiveYearFraction=yearly.length?positiveYears/yearly.length:0;
  const last5=yearly.slice(-5);
  const last5NetR=round(last5.reduce((s,y)=>s+y.netR10bps,0));
  const positiveClasses=[...classContribution.entries()].filter(([,v])=>v>0);
  const posClassTotal=positiveClasses.reduce((s,[,v])=>s+v,0);
  const classDominance=posClassTotal>0?Math.max(...positiveClasses.map(([,v])=>v))/posClassTotal:1;
  const positiveMarkets=[...marketContribution.entries()].filter(([,v])=>v>0);
  const posMarketTotal=positiveMarkets.reduce((s,[,v])=>s+v,0);
  const marketDominance=posMarketTotal>0?Math.max(...positiveMarkets.map(([,v])=>v))/posMarketTotal:1;

  const pass=
   completedYears>=12&&p10.netR>0&&p20.netR>0&&p10.returnToDrawdown>1&&
   positiveYearFraction>=.60&&last5NetR>0&&positiveClasses.length>=3&&
   marketDominance<=.30&&classDominance<=.50;

  const result={
   ok:true,status:pass?"ROLLING_OOS_PASS":"ROLLING_OOS_FAIL",mode:"RESEARCH_ONLY",brokerOrders:false,liveMoneyLocked:true,
   strategyId:"TF-012A-ROLLING-CAUSAL-TREND",
   preregistration:"research/TF_012A_ROLLING_CAUSAL_PORTFOLIO_PROTOCOL_2026-09-27.md",
   summary:{
    pass,completedYears,portfolio10bps:p10,portfolio20bps:p20,
    positiveYears,positiveYearFraction:round(positiveYearFraction,4),
    last5Years:last5.map(x=>x.year),last5NetR,
    positiveClassCount:positiveClasses.length,
    classContribution:Object.fromEntries(classContribution),
    classDominance:round(classDominance,4),
    marketContribution:Object.fromEntries(marketContribution),
    marketDominance:round(marketDominance,4),
   },
   yearly
  };

  await sql`
   insert into ai_trade.robustness_runs(run_key,strategy_id,result)
   values('TF012A_ROLLING_CAUSAL_20260927_V1','TF-012A-ROLLING-CAUSAL-TREND',${sql.json(result)})
   on conflict(run_key)do nothing
  `;
  return json(result);
 }catch(error){
  return json({ok:false,status:"ERROR",brokerOrders:false,liveMoneyLocked:true,message:error instanceof Error?error.message:String(error)},500);
 }
});