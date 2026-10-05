import postgres from "npm:postgres@3.4.9";

type Direction="UP"|"DOWN";
type Bar={timestamp:number;open:number;high:number;low:number;close:number};
type Instrument={key:string;label:string;yahooSymbol:string;coinbaseProduct?:string};

type Trade={r:number;entryIndex:number;exitIndex:number;direction:Direction};
type Metrics={trades:number;netR:number;medianR:number;maxDrawdownR:number;positive:boolean};
type CandidateId="TF-005A-TSMOM-12M"|"TF-006A-DONCHIAN-55-20"|"TF-007A-MA-50-200";

const sql=postgres(Deno.env.get("SUPABASE_DB_URL")!,{
  prepare:false,max:1,connect_timeout:10,idle_timeout:20
});

const UNIVERSE:Instrument[]=[
  {key:"EURUSD",label:"EUR/USD",yahooSymbol:"EURUSD=X"},
  {key:"GBPUSD",label:"GBP/USD",yahooSymbol:"GBPUSD=X"},
  {key:"USDJPY",label:"USD/JPY",yahooSymbol:"USDJPY=X"},
  {key:"AUDUSD",label:"AUD/USD",yahooSymbol:"AUDUSD=X"},
  {key:"USDCAD",label:"USD/CAD",yahooSymbol:"CAD=X"},
  {key:"USDCHF",label:"USD/CHF",yahooSymbol:"CHF=X"},
  {key:"NZDUSD",label:"NZD/USD",yahooSymbol:"NZDUSD=X"},
  {key:"XAUUSD",label:"Gold",yahooSymbol:"GC=F"},
  {key:"USOIL",label:"WTI Oil",yahooSymbol:"CL=F"},
  {key:"BTCUSD",label:"Bitcoin",yahooSymbol:"BTC-USD",coinbaseProduct:"BTC-USD"},
  {key:"ETHUSD",label:"Ethereum",yahooSymbol:"ETH-USD",coinbaseProduct:"ETH-USD"},
  {key:"US30",label:"Dow Jones",yahooSymbol:"^DJI"},
  {key:"NAS100",label:"Nasdaq 100",yahooSymbol:"^NDX"},
  {key:"US500",label:"S&P 500",yahooSymbol:"^GSPC"},
];

const CANDIDATES:CandidateId[]=[
  "TF-005A-TSMOM-12M",
  "TF-006A-DONCHIAN-55-20",
  "TF-007A-MA-50-200",
];

const json=(body:unknown,status=200)=>new Response(JSON.stringify(body),{
  status,headers:{"content-type":"application/json; charset=utf-8"}
});

async function authorized(req:Request){
  const rows=await sql`select secret from ai_trade.cron_auth where id=1`;
  const expected=String(rows[0]?.secret??"");
  return Boolean(expected)&&(req.headers.get("x-ai-trade-cron")??"")===expected;
}

function num(x:unknown){
  const v=Number(x);
  return Number.isFinite(v)?v:null;
}
function round(v:number,d=6){
  const p=10**d; return Math.round(v*p)/p;
}
function median(values:number[]){
  if(!values.length) return 0;
  const a=[...values].sort((x,y)=>x-y);
  const m=Math.floor(a.length/2);
  return a.length%2?a[m]:(a[m-1]+a[m])/2;
}
function summarize(trades:Trade[]):Metrics{
  const rs=trades.map(t=>t.r);
  let eq=0,peak=0,dd=0;
  for(const r of rs){
    eq+=r; peak=Math.max(peak,eq); dd=Math.max(dd,peak-eq);
  }
  const net=rs.reduce((a,b)=>a+b,0);
  return {
    trades:trades.length,
    netR:round(net),
    medianR:round(median(rs)),
    maxDrawdownR:round(dd),
    positive:net>0,
  };
}

async function yahooBars(symbol:string,start:string,endExclusive:string):Promise<Bar[]>{
  const p1=Math.floor(new Date(start+"T00:00:00Z").getTime()/1000);
  const p2=Math.floor(new Date(endExclusive+"T00:00:00Z").getTime()/1000);
  const url="https://query1.finance.yahoo.com/v8/finance/chart/"+
    encodeURIComponent(symbol)+
    "?period1="+p1+"&period2="+p2+
    "&interval=1d&events=history&includeAdjustedClose=true";
  const response=await fetch(url,{headers:{"user-agent":"AI-TRADE-preregistered/1.0"}});
  if(!response.ok) throw new Error("YAHOO_HTTP_"+response.status);
  const payload=await response.json();
  if(payload?.chart?.error) throw new Error("YAHOO_CHART_ERROR");
  const result=payload?.chart?.result?.[0];
  const quote=result?.indicators?.quote?.[0];
  const ts:number[]=result?.timestamp??[];
  if(!quote) throw new Error("YAHOO_NO_DATA");
  const bars:Bar[]=[];
  for(let i=0;i<ts.length;i++){
    const open=num(quote.open?.[i]),high=num(quote.high?.[i]);
    const low=num(quote.low?.[i]),close=num(quote.close?.[i]);
    if(open===null||high===null||low===null||close===null) continue;
    if(open<=0||high<=0||low<=0||close<=0) continue;
    if(high<Math.max(open,close)||low>Math.min(open,close)) continue;
    bars.push({timestamp:Number(ts[i]),open,high,low,close});
  }
  bars.sort((a,b)=>a.timestamp-b.timestamp);
  if(bars.length<500) throw new Error("INSUFFICIENT_DAILY_BARS");
  return bars;
}

async function coinbaseBars(product:string,start:string,endExclusive:string):Promise<Bar[]>{
  const startMs=new Date(start+"T00:00:00Z").getTime();
  const endMs=new Date(endExclusive+"T00:00:00Z").getTime();
  const chunkMs=280*86400*1000;
  const byTs=new Map<number,Bar>();
  for(let s=startMs;s<endMs;s+=chunkMs){
    const e=Math.min(endMs,s+chunkMs);
    const url="https://api.exchange.coinbase.com/products/"+
      encodeURIComponent(product)+"/candles?granularity=86400"+
      "&start="+encodeURIComponent(new Date(s).toISOString())+
      "&end="+encodeURIComponent(new Date(e).toISOString());
    const response=await fetch(url,{headers:{
      "user-agent":"AI-TRADE-preregistered/1.0","accept":"application/json"
    }});
    if(!response.ok) throw new Error("COINBASE_HTTP_"+response.status);
    const rows=await response.json();
    if(!Array.isArray(rows)) throw new Error("COINBASE_BAD_RESPONSE");
    for(const row of rows){
      if(!Array.isArray(row)||row.length<5) continue;
      const timestamp=Number(row[0]);
      const low=num(row[1]),high=num(row[2]),open=num(row[3]),close=num(row[4]);
      if(open===null||high===null||low===null||close===null) continue;
      if(open<=0||high<=0||low<=0||close<=0) continue;
      byTs.set(timestamp,{timestamp,open,high,low,close});
    }
    await new Promise(r=>setTimeout(r,250));
  }
  const bars=[...byTs.values()].sort((a,b)=>a.timestamp-b.timestamp);
  if(bars.length<500) throw new Error("INSUFFICIENT_COINBASE_BARS");
  return bars;
}

async function longestBars(i:Instrument,endExclusive:string){
  if(i.key==="ETHUSD") return coinbaseBars("ETH-USD","2015-01-01",endExclusive);
  if(i.key==="BTCUSD") return yahooBars(i.yahooSymbol,"2014-01-01",endExclusive);
  try{return await yahooBars(i.yahooSymbol,"1900-01-01",endExclusive);}
  catch(_){return yahooBars(i.yahooSymbol,"1970-01-01",endExclusive);}
}

function atrSeries(bars:Bar[],period=20){
  const tr:number[]=[];
  for(let i=0;i<bars.length;i++){
    if(i===0) tr.push(bars[i].high-bars[i].low);
    else tr.push(Math.max(
      bars[i].high-bars[i].low,
      Math.abs(bars[i].high-bars[i-1].close),
      Math.abs(bars[i].low-bars[i-1].close)
    ));
  }
  const atr=Array(bars.length).fill(NaN);
  if(bars.length<=period) return atr;
  let initial=0;
  for(let i=1;i<=period;i++) initial+=tr[i];
  atr[period]=initial/period;
  for(let i=period+1;i<bars.length;i++){
    atr[i]=(atr[i-1]*(period-1)+tr[i])/period;
  }
  return atr;
}
function sma(bars:Bar[],index:number,period:number){
  if(index+1<period) return null;
  let s=0;
  for(let i=index-period+1;i<=index;i++) s+=bars[i].close;
  return s/period;
}
function priorHigh(bars:Bar[],index:number,period:number){
  if(index<period) return null;
  let v=-Infinity;
  for(let i=index-period;i<index;i++) v=Math.max(v,bars[i].high);
  return v;
}
function priorLow(bars:Bar[],index:number,period:number){
  if(index<period) return null;
  let v=Infinity;
  for(let i=index-period;i<index;i++) v=Math.min(v,bars[i].low);
  return v;
}

type Position={
  direction:Direction;
  entry:number;
  stop:number;
  risk:number;
  entryIndex:number;
};
type Pending={
  kind:"ENTER"|"EXIT"|"REVERSE";
  direction?:Direction;
  atrAtSignal?:number;
};

function simulate(
  bars:Bar[],
  candidate:CandidateId,
  startIndex:number,
  endIndex:number,
  frictionBpsRoundTrip:number,
):Metrics{
  const atr=atrSeries(bars,20);
  let pos:Position|null=null;
  let pending:Pending|null=null;
  let lastMaRegime:Direction|null=null;
  const trades:Trade[]=[];

  const closePosition=(exit:number,index:number)=>{
    if(!pos) return;
    const gross=pos.direction==="UP"?exit-pos.entry:pos.entry-exit;
    const friction=pos.entry*(frictionBpsRoundTrip/10000);
    const pnl=gross-friction;
    trades.push({
      r:round(pnl/pos.risk,8),
      entryIndex:pos.entryIndex,
      exitIndex:index,
      direction:pos.direction,
    });
    pos=null;
  };

  const enter=(direction:Direction,entry:number,atrValue:number,index:number)=>{
    const mult=candidate==="TF-005A-TSMOM-12M"?4:
      candidate==="TF-006A-DONCHIAN-55-20"?2:3;
    const risk=atrValue*mult;
    if(!(risk>0&&Number.isFinite(risk))) return;
    const stop=direction==="UP"?entry-risk:entry+risk;
    pos={direction,entry,stop,risk,entryIndex:index};
  };

  for(let index=1;index<bars.length;index++){
    const bar=bars[index];
    const priorIndex=index-1;

    if(pos){
      const stopHit=pos.direction==="UP"?bar.low<=pos.stop:bar.high>=pos.stop;
      if(stopHit){
        const rawExit=pos.direction==="UP"
          ? Math.min(pos.stop,bar.open)
          : Math.max(pos.stop,bar.open);
        closePosition(rawExit,index);
        pending=null;
      }
    }

    if(!pos&&pending&&index>=startIndex&&index<endIndex){
      if(pending.kind==="ENTER"||pending.kind==="REVERSE"){
        if(pending.direction&&pending.atrAtSignal){
          enter(pending.direction,bar.open,pending.atrAtSignal,index);
        }
      }
      pending=null;
    }else if(pos&&pending&&index>=startIndex&&index<endIndex){
      if(pending.kind==="EXIT"){
        closePosition(bar.open,index);
        pending=null;
      }else if(pending.kind==="REVERSE"&&pending.direction&&pending.atrAtSignal){
        const dir=pending.direction, av=pending.atrAtSignal;
        closePosition(bar.open,index);
        enter(dir,bar.open,av,index);
        pending=null;
      }
    }

    if(index>=endIndex) break;
    if(index<startIndex-1) continue;

    const atrValue=atr[priorIndex];
    if(!(atrValue>0&&Number.isFinite(atrValue))) continue;

    if(candidate==="TF-005A-TSMOM-12M"){
      if(priorIndex<252) continue;
      if((priorIndex-252)%21!==0) continue;
      const ret=bars[priorIndex].close/bars[priorIndex-252].close-1;
      if(ret===0) continue;
      const dir:Direction=ret>0?"UP":"DOWN";
      if(!pos) pending={kind:"ENTER",direction:dir,atrAtSignal:atrValue};
      else if(pos.direction!==dir){
        pending={kind:"REVERSE",direction:dir,atrAtSignal:atrValue};
      }
    }

    if(candidate==="TF-006A-DONCHIAN-55-20"){
      if(pos){
        const exitLow=priorLow(bars,priorIndex,20);
        const exitHigh=priorHigh(bars,priorIndex,20);
        if(pos.direction==="UP"&&exitLow!==null&&bars[priorIndex].close<exitLow){
          pending={kind:"EXIT"};
        }else if(pos.direction==="DOWN"&&exitHigh!==null&&bars[priorIndex].close>exitHigh){
          pending={kind:"EXIT"};
        }
      }else{
        const high55=priorHigh(bars,priorIndex,55);
        const low55=priorLow(bars,priorIndex,55);
        if(high55!==null&&bars[priorIndex].close>high55){
          pending={kind:"ENTER",direction:"UP",atrAtSignal:atrValue};
        }else if(low55!==null&&bars[priorIndex].close<low55){
          pending={kind:"ENTER",direction:"DOWN",atrAtSignal:atrValue};
        }
      }
    }

    if(candidate==="TF-007A-MA-50-200"){
      const fast=sma(bars,priorIndex,50);
      const slow=sma(bars,priorIndex,200);
      if(fast===null||slow===null||fast===slow) continue;
      const regime:Direction=fast>slow?"UP":"DOWN";
      const changed=lastMaRegime!==null&&regime!==lastMaRegime;
      const first=lastMaRegime===null;
      lastMaRegime=regime;
      if(first){
        if(!pos) pending={kind:"ENTER",direction:regime,atrAtSignal:atrValue};
      }else if(changed){
        if(pos) pending={kind:"REVERSE",direction:regime,atrAtSignal:atrValue};
        else pending={kind:"ENTER",direction:regime,atrAtSignal:atrValue};
      }
    }
  }

  if(pos){
    const last=Math.min(endIndex-1,bars.length-1);
    if(last>=startIndex) closePosition(bars[last].close,last);
  }
  return summarize(trades);
}

function dominance(netRs:number[]){
  const positives=netRs.filter(x=>x>0);
  const total=positives.reduce((a,b)=>a+b,0);
  return total>0?Math.max(...positives)/total:1;
}

Deno.serve(async(req)=>{
  try{
    if(!(await authorized(req))) return json({ok:false,status:"UNAUTHORIZED"},401);

    const today=new Date();
    const endExclusive=new Date(Date.UTC(
      today.getUTCFullYear(),today.getUTCMonth(),today.getUTCDate()+1
    )).toISOString().slice(0,10);

    const loaded:{instrument:Instrument;bars:Bar[]}[]=[];
    for(const instrument of UNIVERSE){
      loaded.push({instrument,bars:await longestBars(instrument,endExclusive)});
      await new Promise(r=>setTimeout(r,100));
    }

    const validation:any={};
    for(const candidate of CANDIDATES){
      const marketRows=[];
      for(const {instrument,bars} of loaded){
        const n=bars.length;
        const valStart=Math.floor(n*0.60);
        const valEnd=Math.floor(n*0.80);
        const m10=simulate(bars,candidate,valStart,valEnd,10);
        const stresses=[0,5,10,20].map(bps=>({
          bps,
          ...simulate(bars,candidate,valStart,valEnd,bps),
        }));
        marketRows.push({
          symbol:instrument.key,
          firstDate:new Date(bars[0].timestamp*1000).toISOString().slice(0,10),
          validationStart:new Date(bars[valStart].timestamp*1000).toISOString().slice(0,10),
          validationEnd:new Date(bars[valEnd-1].timestamp*1000).toISOString().slice(0,10),
          at10bps:m10,
          frictionStress:stresses,
        });
      }
      const netRs=marketRows.map((x:any)=>Number(x.at10bps.netR));
      const fx=marketRows.slice(0,7);
      const cross=marketRows.slice(7);
      const summary={
        positiveMarkets:marketRows.filter((x:any)=>x.at10bps.netR>0).length,
        positiveFx:fx.filter((x:any)=>x.at10bps.netR>0).length,
        positiveCrossAsset:cross.filter((x:any)=>x.at10bps.netR>0).length,
        medianNetR:round(median(netRs)),
        medianDrawdownR:round(median(marketRows.map((x:any)=>Number(x.at10bps.maxDrawdownR)))),
        positiveRDominance:round(dominance(netRs),4),
      };
      const eligible=
        summary.medianNetR>0 &&
        summary.positiveMarkets>=9 &&
        summary.positiveFx>=4 &&
        summary.positiveCrossAsset>=4 &&
        summary.positiveRDominance<=0.40;
      validation[candidate]={eligible,summary,markets:marketRows};
    }

    const eligible=CANDIDATES
      .filter(c=>validation[c].eligible)
      .sort((a,b)=>{
        const A=validation[a].summary,B=validation[b].summary;
        return (
          B.positiveMarkets-A.positiveMarkets ||
          B.medianNetR-A.medianNetR ||
          A.medianDrawdownR-B.medianDrawdownR
        );
      });

    const selected:CandidateId|null=eligible[0]??null;
    let holdout:any=null;

    if(selected){
      const rows=[];
      for(const {instrument,bars} of loaded){
        const n=bars.length;
        const start=Math.floor(n*0.80);
        const m10=simulate(bars,selected,start,n,10);
        const m20=simulate(bars,selected,start,n,20);
        rows.push({
          symbol:instrument.key,
          holdoutStart:new Date(bars[start].timestamp*1000).toISOString().slice(0,10),
          endDate:new Date(bars[n-1].timestamp*1000).toISOString().slice(0,10),
          at10bps:m10,
          at20bps:m20,
        });
      }
      const r10=rows.map((x:any)=>Number(x.at10bps.netR));
      const r20=rows.map((x:any)=>Number(x.at20bps.netR));
      const fx=rows.slice(0,7),cross=rows.slice(7);
      const summary={
        positiveMarkets10bps:rows.filter((x:any)=>x.at10bps.netR>0).length,
        positiveFx10bps:fx.filter((x:any)=>x.at10bps.netR>0).length,
        positiveCrossAsset10bps:cross.filter((x:any)=>x.at10bps.netR>0).length,
        medianNetR10bps:round(median(r10)),
        aggregateNetR10bps:round(r10.reduce((a,b)=>a+b,0)),
        aggregateNetR20bps:round(r20.reduce((a,b)=>a+b,0)),
        positiveRDominance10bps:round(dominance(r10),4),
      };
      const pass=
        summary.medianNetR10bps>0 &&
        summary.positiveMarkets10bps>=9 &&
        summary.positiveFx10bps>=4 &&
        summary.positiveCrossAsset10bps>=4 &&
        summary.aggregateNetR10bps>0 &&
        summary.aggregateNetR20bps>0 &&
        summary.positiveRDominance10bps<=0.40;
      holdout={selected,pass,summary,markets:rows};
    }

    const result={
      ok:true,
      status:selected?(holdout?.pass?"HOLDOUT_PASS":"HOLDOUT_FAIL"):"NO_VALIDATION_CANDIDATE",
      mode:"RESEARCH_ONLY",
      brokerOrders:false,
      preregistration:"research/PREREGISTERED_STRATEGY_SUITE_2026-09-27.md",
      universe:UNIVERSE.map(x=>x.key),
      candidates:CANDIDATES,
      validation,
      selectedCandidate:selected,
      holdout,
      liveMoneyLocked:true,
      warnings:[
        "Universal friction is synthetic stress, not broker-specific cost.",
        "Selection uses only the middle 20% validation slice.",
        "The final 20% is computed only for the selected candidate.",
        "A holdout pass would not approve account risk or broker execution."
      ]
    };

    await sql`
      insert into ai_trade.robustness_runs(run_key,strategy_id,result)
      values(
        'PREREG_SUITE_20260927_V1',
        'PREREGISTERED_STRATEGY_SUITE',
        ${sql.json(result)}
      )
      on conflict (run_key) do nothing
    `;

    return json(result);
  }catch(error){
    return json({
      ok:false,status:"ERROR",brokerOrders:false,liveMoneyLocked:true,
      message:error instanceof Error?error.message:String(error)
    },500);
  }
});
