import postgres from "npm:postgres@3.4.9";

type Row = Record<string, unknown>;
type Direction = "UP" | "DOWN";
type CostMode = "RESEARCH_PROXY" | "GROSS_ONLY";

type Cost = {
  spread: number;
  commission: number;
  slippage: number;
  swapPerBar: number;
};

type Instrument = {
  key: string;
  label: string;
  yahooSymbol: string;
  costMode: CostMode;
  cost: Cost;
};

type Bar = {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
};

type Position = {
  direction: Direction;
  entryPrice: number;
  stop: number;
  initialStop: number;
  holdingBars: number;
};

type Metrics = {
  trades: number;
  netR: number;
  expectancyR: number;
  profitFactorR: number | null;
  maxDrawdownR: number;
  maxLossStreak: number;
};

const ZERO_COST: Cost = {
  spread: 0,
  commission: 0,
  slippage: 0,
  swapPerBar: 0,
};

const UNIVERSE: Instrument[] = [
  {
    key:"EURUSD", label:"EUR/USD", yahooSymbol:"EURUSD=X",
    costMode:"RESEARCH_PROXY",
    cost:{spread:0.0002,commission:0.00002,slippage:0.00005,swapPerBar:0.00001},
  },
  {
    key:"GBPUSD", label:"GBP/USD", yahooSymbol:"GBPUSD=X",
    costMode:"RESEARCH_PROXY",
    cost:{spread:0.0002,commission:0.00002,slippage:0.00005,swapPerBar:0.00001},
  },
  {
    key:"USDJPY", label:"USD/JPY", yahooSymbol:"USDJPY=X",
    costMode:"RESEARCH_PROXY",
    cost:{spread:0.02,commission:0.002,slippage:0.005,swapPerBar:0.001},
  },
  {
    key:"AUDUSD", label:"AUD/USD", yahooSymbol:"AUDUSD=X",
    costMode:"RESEARCH_PROXY",
    cost:{spread:0.00025,commission:0.000025,slippage:0.00006,swapPerBar:0.000012},
  },
  {
    key:"USDCAD", label:"USD/CAD", yahooSymbol:"CAD=X",
    costMode:"GROSS_ONLY", cost:ZERO_COST,
  },
  {
    key:"USDCHF", label:"USD/CHF", yahooSymbol:"CHF=X",
    costMode:"GROSS_ONLY", cost:ZERO_COST,
  },
  {
    key:"NZDUSD", label:"NZD/USD", yahooSymbol:"NZDUSD=X",
    costMode:"GROSS_ONLY", cost:ZERO_COST,
  },
  {
    key:"XAUUSD", label:"Gold", yahooSymbol:"GC=F",
    costMode:"RESEARCH_PROXY",
    cost:{spread:0.5,commission:0.1,slippage:0.25,swapPerBar:0.05},
  },
  {
    key:"BTCUSD", label:"Bitcoin", yahooSymbol:"BTC-USD",
    costMode:"RESEARCH_PROXY",
    cost:{spread:50,commission:20,slippage:25,swapPerBar:0},
  },
  {
    key:"ETHUSD", label:"Ethereum", yahooSymbol:"ETH-USD",
    costMode:"GROSS_ONLY", cost:ZERO_COST,
  },
  {
    key:"USOIL", label:"WTI Oil", yahooSymbol:"CL=F",
    costMode:"RESEARCH_PROXY",
    cost:{spread:0.05,commission:0.02,slippage:0.03,swapPerBar:0.02},
  },
  {
    key:"US30", label:"Dow Jones / US30", yahooSymbol:"^DJI",
    costMode:"GROSS_ONLY", cost:ZERO_COST,
  },
  {
    key:"NAS100", label:"Nasdaq 100", yahooSymbol:"^NDX",
    costMode:"GROSS_ONLY", cost:ZERO_COST,
  },
  {
    key:"US500", label:"S&P 500", yahooSymbol:"^GSPC",
    costMode:"GROSS_ONLY", cost:ZERO_COST,
  },
];

const REQUESTED_START = "2016-01-01";
const STRATEGY_ID = "TF-004-TIME-SERIES-CHANNEL";
const LOOKBACK = 20;
const STOP_LOOKBACK = 5;
const TRAILING_LOOKBACK = 20;

const sql = postgres(Deno.env.get("SUPABASE_DB_URL")!, {
  prepare:false,
  max:1,
  connect_timeout:10,
  idle_timeout:20,
});

const json=(body:unknown,status=200)=>new Response(JSON.stringify(body),{
  status,
  headers:{"content-type":"application/json; charset=utf-8"},
});

async function authorized(req:Request){
  const rows=await sql`select secret from ai_trade.cron_auth where id=1`;
  const expected=String(rows[0]?.secret??"");
  return Boolean(expected)&&(req.headers.get("x-ai-trade-cron")??"")===expected;
}

function finite(n:unknown){
  const v=Number(n);
  return Number.isFinite(v)?v:null;
}

function round(v:number,d=6){
  const p=10**d;
  return Math.round(v*p)/p;
}

async function yahooBars(symbol:string,start:string,endExclusive:string):Promise<Bar[]>{
  const p1=Math.floor(new Date(start+"T00:00:00Z").getTime()/1000);
  const p2=Math.floor(new Date(endExclusive+"T00:00:00Z").getTime()/1000);
  const url=
    "https://query1.finance.yahoo.com/v8/finance/chart/"+
    encodeURIComponent(symbol)+
    "?period1="+p1+
    "&period2="+p2+
    "&interval=1d&events=history&includeAdjustedClose=true";
  const response=await fetch(url,{
    headers:{"user-agent":"AI-TRADE-research/0.4"},
  });
  if(!response.ok) throw new Error("YAHOO_HTTP_"+response.status);
  const payload=await response.json();
  if(payload?.chart?.error) throw new Error("YAHOO_CHART_ERROR");
  const result=payload?.chart?.result?.[0];
  const timestamps:number[]=result?.timestamp??[];
  const quote=result?.indicators?.quote?.[0];
  if(!quote) throw new Error("YAHOO_NO_DATA");

  const bars:Bar[]=[];
  for(let i=0;i<timestamps.length;i++){
    const open=finite(quote.open?.[i]);
    const high=finite(quote.high?.[i]);
    const low=finite(quote.low?.[i]);
    const close=finite(quote.close?.[i]);
    if(open===null||high===null||low===null||close===null) continue;
    if(!(high>=Math.max(open,close)&&low<=Math.min(open,close))) continue;
    bars.push({timestamp:timestamps[i],open,high,low,close});
  }
  bars.sort((a,b)=>a.timestamp-b.timestamp);
  if(bars.length<80) throw new Error("INSUFFICIENT_BARS");
  return bars;
}

async function cryptoCompareBars(
  fsym:string,
  tsym:string,
  start:string,
  endExclusive:string,
):Promise<Bar[]>{
  const startTs=Math.floor(new Date(start+"T00:00:00Z").getTime()/1000);
  let toTs=Math.floor(new Date(endExclusive+"T00:00:00Z").getTime()/1000)-1;
  const byTs=new Map<number,Bar>();

  for(let page=0;page<4;page++){
    const url=
      "https://min-api.cryptocompare.com/data/v2/histoday"+
      "?fsym="+encodeURIComponent(fsym)+
      "&tsym="+encodeURIComponent(tsym)+
      "&limit=2000&aggregate=1&toTs="+toTs+
      "&e=CCCAGG&tryConversion=true";
    const response=await fetch(url,{
      headers:{"user-agent":"AI-TRADE-research/0.5"},
    });
    if(!response.ok) throw new Error("CRYPTOCOMPARE_HTTP_"+response.status);
    const payload=await response.json();
    if(String(payload?.Response??"").toLowerCase()==="error"){
      throw new Error("CRYPTOCOMPARE_"+String(payload?.Message??"ERROR"));
    }
    const rows=payload?.Data?.Data??[];
    if(!Array.isArray(rows)||rows.length===0) break;

    let earliest=Number.POSITIVE_INFINITY;
    for(const row of rows){
      const timestamp=Number(row.time);
      earliest=Math.min(earliest,timestamp);
      if(timestamp<startTs||timestamp>=Math.floor(new Date(endExclusive+"T00:00:00Z").getTime()/1000)) continue;
      const open=finite(row.open);
      const high=finite(row.high);
      const low=finite(row.low);
      const close=finite(row.close);
      if(open===null||high===null||low===null||close===null) continue;
      if(open<=0||high<=0||low<=0||close<=0) continue;
      if(!(high>=Math.max(open,close)&&low<=Math.min(open,close))) continue;
      byTs.set(timestamp,{timestamp,open,high,low,close});
    }
    if(!Number.isFinite(earliest)||earliest<=startTs) break;
    toTs=earliest-1;
    await new Promise(resolve=>setTimeout(resolve,150));
  }

  const bars=[...byTs.values()].sort((a,b)=>a.timestamp-b.timestamp);
  if(bars.length<80) throw new Error("INSUFFICIENT_CRYPTOCOMPARE_BARS");
  return bars;
}

async function coinbaseBars(
  product:string,
  start:string,
  endExclusive:string,
):Promise<Bar[]>{
  const startMs=new Date(start+"T00:00:00Z").getTime();
  const endMs=new Date(endExclusive+"T00:00:00Z").getTime();
  const chunkMs=280*86400*1000;
  const byTs=new Map<number,Bar>();

  for(let chunkStart=startMs;chunkStart<endMs;chunkStart+=chunkMs){
    const chunkEnd=Math.min(endMs,chunkStart+chunkMs);
    const url=
      "https://api.exchange.coinbase.com/products/"+
      encodeURIComponent(product)+
      "/candles?granularity=86400"+
      "&start="+encodeURIComponent(new Date(chunkStart).toISOString())+
      "&end="+encodeURIComponent(new Date(chunkEnd).toISOString());
    const response=await fetch(url,{
      headers:{
        "user-agent":"AI-TRADE-research/0.6",
        "accept":"application/json",
      },
    });
    if(!response.ok) throw new Error("COINBASE_HTTP_"+response.status);
    const rows=await response.json();
    if(!Array.isArray(rows)) throw new Error("COINBASE_BAD_RESPONSE");

    for(const row of rows){
      if(!Array.isArray(row)||row.length<5) continue;
      const timestamp=Number(row[0]);
      const low=finite(row[1]);
      const high=finite(row[2]);
      const open=finite(row[3]);
      const close=finite(row[4]);
      if(open===null||high===null||low===null||close===null) continue;
      if(open<=0||high<=0||low<=0||close<=0) continue;
      if(!(high>=Math.max(open,close)&&low<=Math.min(open,close))) continue;
      byTs.set(timestamp,{timestamp,open,high,low,close});
    }
    await new Promise(resolve=>setTimeout(resolve,360));
  }

  const bars=[...byTs.values()].sort((a,b)=>a.timestamp-b.timestamp);
  if(bars.length<80) throw new Error("INSUFFICIENT_COINBASE_BARS");
  return bars;
}

function summarize(rs:number[]):Metrics{
  if(rs.length===0){
    return {
      trades:0,netR:0,expectancyR:0,profitFactorR:null,
      maxDrawdownR:0,maxLossStreak:0,
    };
  }
  let equity=0;
  let peak=0;
  let maxDd=0;
  let losses=0;
  let maxLosses=0;
  let grossProfit=0;
  let grossLoss=0;

  for(const r of rs){
    equity+=r;
    peak=Math.max(peak,equity);
    maxDd=Math.max(maxDd,peak-equity);
    if(r>0){
      grossProfit+=r;
      losses=0;
    }else if(r<0){
      grossLoss+=Math.abs(r);
      losses+=1;
      maxLosses=Math.max(maxLosses,losses);
    }else{
      losses=0;
    }
  }
  return {
    trades:rs.length,
    netR:round(rs.reduce((a,b)=>a+b,0)),
    expectancyR:round(rs.reduce((a,b)=>a+b,0)/rs.length),
    profitFactorR:grossLoss>0?round(grossProfit/grossLoss):null,
    maxDrawdownR:round(maxDd),
    maxLossStreak:maxLosses,
  };
}

function simulate(
  bars:Bar[],
  entryStartIndex:number,
  entryEndIndex:number,
  cost:Cost,
  multiplier:number,
):Metrics{
  let position:Position|null=null;
  const rs:number[]=[];
  const scaled:Cost={
    spread:cost.spread*multiplier,
    commission:cost.commission*multiplier,
    slippage:cost.slippage*multiplier,
    swapPerBar:cost.swapPerBar*multiplier,
  };

  for(let index=Math.max(LOOKBACK+1,STOP_LOOKBACK+1);index<bars.length;index++){
    const bar=bars[index];
    let exited=false;

    if(position){
      position.holdingBars+=1;
      const priorChannel=bars.slice(index-TRAILING_LOOKBACK,index);
      if(priorChannel.length===TRAILING_LOOKBACK){
        const channelStop=position.direction==="UP"
          ? Math.min(...priorChannel.map(x=>x.low))
          : Math.max(...priorChannel.map(x=>x.high));
        position.stop=position.direction==="UP"
          ? Math.max(position.stop,channelStop)
          : Math.min(position.stop,channelStop);
      }

      const stopHit=position.direction==="UP"
        ? bar.low<=position.stop
        : bar.high>=position.stop;

      if(stopHit){
        const exitPrice=position.direction==="UP"
          ? position.stop-scaled.slippage
          : position.stop+scaled.slippage;
        const executed=position.direction==="UP"
          ? exitPrice-position.entryPrice
          : position.entryPrice-exitPrice;
        const pnl=
          executed-scaled.spread-scaled.commission-
          scaled.swapPerBar*position.holdingBars;
        const initialRisk=Math.abs(position.entryPrice-position.initialStop);
        if(initialRisk>0&&Number.isFinite(initialRisk)){
          rs.push(pnl/initialRisk);
        }
        position=null;
        exited=true;
      }
    }

    if(
      !position &&
      !exited &&
      index>=entryStartIndex &&
      index<entryEndIndex &&
      index>LOOKBACK &&
      index>STOP_LOOKBACK
    ){
      const reference=bars[index-LOOKBACK-1].close;
      if(reference===bar.close) continue;
      const direction:Direction=bar.close>reference?"UP":"DOWN";
      const prior=bars.slice(index-STOP_LOOKBACK,index);
      const stop=direction==="UP"
        ? Math.min(...prior.map(x=>x.low))
        : Math.max(...prior.map(x=>x.high));
      const valid=direction==="UP"?stop<bar.close:stop>bar.close;
      if(!valid) continue;
      const entryPrice=direction==="UP"
        ? bar.close+scaled.slippage
        : bar.close-scaled.slippage;
      position={
        direction,
        entryPrice,
        stop,
        initialStop:stop,
        holdingBars:0,
      };
    }

    if(index>=entryEndIndex&&position===null) break;
  }

  return summarize(rs);
}


type CustomSimulation = { metrics: Metrics; rs: number[] };

function simulateCustom(
  bars:Bar[],
  entryStartIndex:number,
  entryEndIndex:number,
  cost:Cost,
  multiplier:number,
  lookback:number,
  stopLookback:number,
  trailLookback:number,
):CustomSimulation{
  let position:Position|null=null;
  const rs:number[]=[];
  const scaled:Cost={
    spread:cost.spread*multiplier,
    commission:cost.commission*multiplier,
    slippage:cost.slippage*multiplier,
    swapPerBar:cost.swapPerBar*multiplier,
  };
  const warmup=Math.max(lookback+1,stopLookback+1,trailLookback);

  for(let index=warmup;index<bars.length;index++){
    const bar=bars[index];
    let exited=false;

    if(position){
      position.holdingBars+=1;
      const priorChannel=bars.slice(index-trailLookback,index);
      if(priorChannel.length===trailLookback){
        const channelStop=position.direction==="UP"
          ? Math.min(...priorChannel.map(x=>x.low))
          : Math.max(...priorChannel.map(x=>x.high));
        position.stop=position.direction==="UP"
          ? Math.max(position.stop,channelStop)
          : Math.min(position.stop,channelStop);
      }

      const stopHit=position.direction==="UP"
        ? bar.low<=position.stop
        : bar.high>=position.stop;
      if(stopHit){
        const exitPrice=position.direction==="UP"
          ? position.stop-scaled.slippage
          : position.stop+scaled.slippage;
        const executed=position.direction==="UP"
          ? exitPrice-position.entryPrice
          : position.entryPrice-exitPrice;
        const pnl=
          executed-scaled.spread-scaled.commission-
          scaled.swapPerBar*position.holdingBars;
        const initialRisk=Math.abs(position.entryPrice-position.initialStop);
        if(initialRisk>0&&Number.isFinite(initialRisk)) rs.push(pnl/initialRisk);
        position=null;
        exited=true;
      }
    }

    if(
      !position && !exited &&
      index>=entryStartIndex && index<entryEndIndex &&
      index>lookback && index>stopLookback
    ){
      const reference=bars[index-lookback-1].close;
      if(reference===bar.close) continue;
      const direction:Direction=bar.close>reference?"UP":"DOWN";
      const prior=bars.slice(index-stopLookback,index);
      const stop=direction==="UP"
        ? Math.min(...prior.map(x=>x.low))
        : Math.max(...prior.map(x=>x.high));
      const valid=direction==="UP"?stop<bar.close:stop>bar.close;
      if(!valid) continue;
      const entryPrice=direction==="UP"
        ? bar.close+scaled.slippage
        : bar.close-scaled.slippage;
      position={direction,entryPrice,stop,initialStop:stop,holdingBars:0};
    }

    if(index>=entryEndIndex&&position===null) break;
  }
  return {metrics:summarize(rs),rs};
}

function walkForwardCustom(
  bars:Bar[],
  cost:Cost,
  multiplier:number,
  lookback:number,
  stopLookback:number,
  trailLookback:number,
){
  const n=bars.length;
  const warmup=Math.max(lookback+1,stopLookback+1,trailLookback);
  const train=Math.max(warmup+5,Math.floor(n*0.5));
  const test=Math.max(1,Math.floor(n*0.1));
  const folds=[];
  for(let start=train;start<n;start+=test){
    const end=Math.min(n,start+test);
    if(end-start<Math.max(5,Math.floor(test*0.1))) break;
    const metrics=simulateCustom(
      bars,start,end,cost,multiplier,lookback,stopLookback,trailLookback
    ).metrics;
    folds.push({
      startDate:new Date(bars[start].timestamp*1000).toISOString().slice(0,10),
      endDate:new Date(bars[end-1].timestamp*1000).toISOString().slice(0,10),
      ...metrics,
    });
  }
  return {
    folds,
    positiveFolds:folds.filter(x=>x.netR>0).length,
    netRSum:round(folds.reduce((s,x)=>s+x.netR,0)),
    worstDrawdownR:round(Math.max(0,...folds.map(x=>x.maxDrawdownR))),
  };
}

function median(values:number[]){
  if(values.length===0) return 0;
  const a=[...values].sort((x,y)=>x-y);
  const m=Math.floor(a.length/2);
  return a.length%2?a[m]:(a[m-1]+a[m])/2;
}

function quantile(values:number[],q:number){
  if(values.length===0) return 0;
  const a=[...values].sort((x,y)=>x-y);
  const pos=(a.length-1)*q;
  const lo=Math.floor(pos);
  const hi=Math.ceil(pos);
  if(lo===hi) return a[lo];
  return a[lo]+(a[hi]-a[lo])*(pos-lo);
}

function lcg(seed:number){
  let state=seed>>>0;
  return ()=>{
    state=(1664525*state+1013904223)>>>0;
    return state/4294967296;
  };
}

function seedFrom(text:string){
  let h=2166136261>>>0;
  for(let i=0;i<text.length;i++){
    h^=text.charCodeAt(i);
    h=Math.imul(h,16777619)>>>0;
  }
  return h>>>0;
}

function monteCarlo(rs:number[],seedText:string,iterations=2000){
  if(rs.length===0){
    return {
      iterations:0,
      probabilityNegativeNetR:null,
      netR:{p05:null,p50:null,p95:null},
      maxDrawdownR:{p50:null,p95:null,p99:null},
    };
  }
  const random=lcg(seedFrom(seedText));
  const totals:number[]=[];
  const dds:number[]=[];
  let negative=0;
  for(let i=0;i<iterations;i++){
    const sample:number[]=[];
    for(let j=0;j<rs.length;j++){
      sample.push(rs[Math.floor(random()*rs.length)]);
    }
    const m=summarize(sample);
    totals.push(m.netR);
    dds.push(m.maxDrawdownR);
    if(m.netR<0) negative+=1;
  }
  return {
    iterations,
    probabilityNegativeNetR:round(negative/iterations,4),
    netR:{
      p05:round(quantile(totals,0.05)),
      p50:round(quantile(totals,0.50)),
      p95:round(quantile(totals,0.95)),
    },
    maxDrawdownR:{
      p50:round(quantile(dds,0.50)),
      p95:round(quantile(dds,0.95)),
      p99:round(quantile(dds,0.99)),
    },
  };
}

function aggregateBars(bars:Bar[],group:number):Bar[]{
  if(group<=1) return bars;
  const out:Bar[]=[];
  for(let i=0;i<bars.length;i+=group){
    const chunk=bars.slice(i,i+group);
    if(chunk.length<group) break;
    out.push({
      timestamp:chunk[chunk.length-1].timestamp,
      open:chunk[0].open,
      high:Math.max(...chunk.map(x=>x.high)),
      low:Math.min(...chunk.map(x=>x.low)),
      close:chunk[chunk.length-1].close,
    });
  }
  return out;
}

async function longestBars(instrument:Instrument,endExclusive:string){
  if(instrument.key==="ETHUSD"){
    return {
      source:"COINBASE_EXCHANGE_PUBLIC",
      bars:await coinbaseBars("ETH-USD","2015-01-01",endExclusive),
    };
  }
  if(instrument.key==="BTCUSD"){
    return {
      source:"YAHOO_RESEARCH_PROXY",
      bars:await yahooBars(instrument.yahooSymbol,"2014-01-01",endExclusive),
    };
  }
  try{
    return {
      source:"YAHOO_RESEARCH_PROXY",
      bars:await yahooBars(instrument.yahooSymbol,"1900-01-01",endExclusive),
    };
  }catch(_){
    return {
      source:"YAHOO_RESEARCH_PROXY",
      bars:await yahooBars(instrument.yahooSymbol,"1970-01-01",endExclusive),
    };
  }
}

function robustnessAnalyze(instrument:Instrument,bars:Bar[]){
  const n=bars.length;
  const split=Math.floor(n*0.7);
  const firstDate=new Date(bars[0].timestamp*1000).toISOString().slice(0,10);
  const lastDate=new Date(bars[n-1].timestamp*1000).toISOString().slice(0,10);
  const coverageYears=round(
    (bars[n-1].timestamp-bars[0].timestamp)/(365.2425*86400),2
  );

  const baselineFull=simulateCustom(
    bars,LOOKBACK+1,n,instrument.cost,1,20,5,20
  );
  const baselineOos=simulateCustom(
    bars,split,n,instrument.cost,1,20,5,20
  ).metrics;
  const baselineWf=walkForwardCustom(
    bars,instrument.cost,1,20,5,20
  );

  const parameterRows=[];
  for(const lookback of [10,20,40]){
    for(const stopLookback of [3,5,10]){
      for(const trailLookback of [10,20,40]){
        const oos=simulateCustom(
          bars,split,n,instrument.cost,1,
          lookback,stopLookback,trailLookback
        ).metrics;
        const wf=walkForwardCustom(
          bars,instrument.cost,1,
          lookback,stopLookback,trailLookback
        );
        parameterRows.push({
          lookback,stopLookback,trailLookback,
          oosNetR:oos.netR,
          wfNetR:wf.netRSum,
          wfPositiveFolds:wf.positiveFolds,
          wfFoldCount:wf.folds.length,
        });
      }
    }
  }

  const parameterSensitivity={
    combinations:parameterRows.length,
    oosPositiveCount:parameterRows.filter(x=>x.oosNetR>0).length,
    wfPositiveCount:parameterRows.filter(x=>x.wfNetR>0).length,
    bothPositiveCount:parameterRows.filter(x=>x.oosNetR>0&&x.wfNetR>0).length,
    medianOosNetR:round(median(parameterRows.map(x=>x.oosNetR))),
    medianWfNetR:round(median(parameterRows.map(x=>x.wfNetR))),
    minOosNetR:round(Math.min(...parameterRows.map(x=>x.oosNetR))),
    maxOosNetR:round(Math.max(...parameterRows.map(x=>x.oosNetR))),
    minWfNetR:round(Math.min(...parameterRows.map(x=>x.wfNetR))),
    maxWfNetR:round(Math.max(...parameterRows.map(x=>x.wfNetR))),
    baseline:{
      lookback:20,stopLookback:5,trailLookback:20,
      oosNetR:baselineOos.netR,
      wfNetR:baselineWf.netRSum,
    },
  };

  const costStress=[0,0.5,1,1.5,2,3,5].map(multiplier=>{
    const oos=simulateCustom(
      bars,split,n,instrument.cost,multiplier,20,5,20
    ).metrics;
    const wf=walkForwardCustom(
      bars,instrument.cost,multiplier,20,5,20
    );
    return {
      multiplier,
      oosNetR:oos.netR,
      oosDrawdownR:oos.maxDrawdownR,
      wfNetR:wf.netRSum,
      wfPositiveFolds:wf.positiveFolds,
      wfFoldCount:wf.folds.length,
    };
  });

  const regimeCount=6;
  const regimeSize=Math.floor(n/regimeCount);
  const regimes=[];
  for(let i=0;i<regimeCount;i++){
    const start=i*regimeSize;
    const end=i===regimeCount-1?n:(i+1)*regimeSize;
    if(end-start<50) continue;
    const m=simulateCustom(
      bars,start,end,instrument.cost,1,20,5,20
    ).metrics;
    regimes.push({
      startDate:new Date(bars[start].timestamp*1000).toISOString().slice(0,10),
      endDate:new Date(bars[end-1].timestamp*1000).toISOString().slice(0,10),
      ...m,
    });
  }

  const firstTs=bars[0].timestamp;
  const startSensitivity=[];
  for(const offsetYears of [0,2,5,10]){
    const target=firstTs+offsetYears*365.2425*86400;
    const idx=Math.max(0,bars.findIndex(x=>x.timestamp>=target));
    if(idx<0||n-idx<100) continue;
    const m=simulateCustom(
      bars,idx,n,instrument.cost,1,20,5,20
    ).metrics;
    startSensitivity.push({
      offsetYears,
      startDate:new Date(bars[idx].timestamp*1000).toISOString().slice(0,10),
      ...m,
    });
  }

  const timeScale=[1,3,5].map(group=>{
    const scaledBars=aggregateBars(bars,group);
    const scaledCost:Cost={
      ...instrument.cost,
      swapPerBar:instrument.cost.swapPerBar*group,
    };
    const splitScaled=Math.floor(scaledBars.length*0.7);
    const oos=simulateCustom(
      scaledBars,splitScaled,scaledBars.length,scaledCost,1,20,5,20
    ).metrics;
    const wf=walkForwardCustom(
      scaledBars,scaledCost,1,20,5,20
    );
    return {
      aggregation:group===1?"1D":group+"D",
      bars:scaledBars.length,
      oosNetR:oos.netR,
      oosDrawdownR:oos.maxDrawdownR,
      wfNetR:wf.netRSum,
      wfPositiveFolds:wf.positiveFolds,
      wfFoldCount:wf.folds.length,
    };
  });

  return {
    symbol:instrument.key,
    label:instrument.label,
    costMode:instrument.costMode,
    firstDate,lastDate,coverageYears,bars:n,
    baseline:{
      fullSample:baselineFull.metrics,
      oos70_30:baselineOos,
      walkForward:{
        positiveFolds:baselineWf.positiveFolds,
        foldCount:baselineWf.folds.length,
        netRSum:baselineWf.netRSum,
        worstDrawdownR:baselineWf.worstDrawdownR,
      },
    },
    parameterSensitivity,
    costStress,
    regimes:{
      count:regimes.length,
      positiveCount:regimes.filter(x=>x.netR>0).length,
      rows:regimes,
    },
    startDateSensitivity:{
      positiveCount:startSensitivity.filter(x=>x.netR>0).length,
      rows:startSensitivity,
    },
    timeScale,
    monteCarlo:monteCarlo(
      baselineFull.rs,
      instrument.key+"|TF004|20|5|20|1x",
      2000
    ),
  };
}

function walkForward(bars:Bar[],cost:Cost,multiplier:number){
  const n=bars.length;
  const train=Math.max(LOOKBACK+STOP_LOOKBACK+5,Math.floor(n*0.5));
  const test=Math.max(1,Math.floor(n*0.1));
  const folds=[];
  for(let start=train;start<n;start+=test){
    const end=Math.min(n,start+test);
    if(end-start<Math.max(5,Math.floor(test*0.1))) break;
    const metrics=simulate(bars,start,end,cost,multiplier);
    folds.push({
      startDate:new Date(bars[start].timestamp*1000).toISOString().slice(0,10),
      endDate:new Date(bars[end-1].timestamp*1000).toISOString().slice(0,10),
      ...metrics,
    });
  }
  return {
    folds,
    positiveFolds:folds.filter(x=>x.netR>0).length,
    netRSum:round(folds.reduce((s,x)=>s+x.netR,0)),
    worstDrawdownR:round(Math.max(0,...folds.map(x=>x.maxDrawdownR))),
  };
}

function analyze(instrument:Instrument,bars:Bar[]){
  const n=bars.length;
  const split=Math.floor(n*0.7);
  const firstDate=new Date(bars[0].timestamp*1000).toISOString().slice(0,10);
  const lastDate=new Date(bars[n-1].timestamp*1000).toISOString().slice(0,10);
  const coverageYears=round((bars[n-1].timestamp-bars[0].timestamp)/(365.2425*86400),2);
  const coverageStatus=firstDate<=REQUESTED_START?"FULL_REQUESTED_WINDOW":"PARTIAL_HISTORY";

  const stress=[0,1,1.5,2].map(multiplier=>({
    multiplier,
    fullSample:simulate(bars,LOOKBACK+1,n,instrument.cost,multiplier),
    oos70_30:simulate(bars,split,n,instrument.cost,multiplier),
    walkForward:walkForward(bars,instrument.cost,multiplier),
  }));

  return {
    symbol:instrument.key,
    label:instrument.label,
    yahooSymbol:instrument.yahooSymbol,
    costMode:instrument.costMode,
    requestedStart:REQUESTED_START,
    firstDate,
    lastDate,
    coverageYears,
    coverageStatus,
    bars:n,
    splitDate:new Date(bars[split].timestamp*1000).toISOString().slice(0,10),
    methodology:{
      timeframe:"1d",
      momentumLookback:LOOKBACK,
      initialStopLookback:STOP_LOOKBACK,
      trailingLookback:TRAILING_LOOKBACK,
      oneOpenPosition:true,
      closedBarOnly:true,
      stopFirst:true,
      chronologicalOos:"70/30",
      walkForward:"50% initial history / 10% non-overlap test windows",
      costStress:[0,1,1.5,2],
    },
    stress,
  };
}

Deno.serve(async(req)=>{
  try{
    if(!(await authorized(req))) return json({ok:false,status:"UNAUTHORIZED"},401);
    const body=await req.json().catch(()=>({})) as {symbols?:string[];runKey?:string};
    const requested=Array.isArray(body.symbols)
      ? new Set(body.symbols.map(x=>String(x).toUpperCase()))
      : null;
    const selected=requested?UNIVERSE.filter(x=>requested.has(x.key)):UNIVERSE;
    if(selected.length===0) return json({ok:false,status:"NO_MATCHING_SYMBOLS"},400);

    const today=new Date();
    const requestedEnd=today.toISOString().slice(0,10);
    const endExclusive=new Date(Date.UTC(
      today.getUTCFullYear(),today.getUTCMonth(),today.getUTCDate()+1
    )).toISOString().slice(0,10);

    const results=[];
    for(const instrument of selected){
      try{
        const loaded=await longestBars(instrument,endExclusive);
        results.push({
          ok:true,
          dataSource:loaded.source,
          ...robustnessAnalyze(instrument,loaded.bars),
        });
      }catch(error){
        results.push({
          ok:false,
          symbol:instrument.key,
          label:instrument.label,
          error:error instanceof Error?error.message:String(error),
        });
      }
      await new Promise(resolve=>setTimeout(resolve,100));
    }

    const failed=results.filter((x:any)=>!x.ok);
    const runKey=body.runKey?.trim()||(
      "TF004_ROBUSTNESS_"+selected.map(x=>x.key).join("_")+"_"+
      requestedEnd.replaceAll("-","")+"_V1"
    );
    const result={
      ok:failed.length===0,
      status:failed.length===0?"COMPLETE":"PARTIAL",
      mode:"RESEARCH_ONLY",
      brokerOrders:false,
      strategyId:STRATEGY_ID,
      requestedEnd,
      universeSize:selected.length,
      successfulCount:results.length-failed.length,
      failedCount:failed.length,
      methodology:{
        baseline:"TF-004 20/5/20",
        longestPracticalPublicHistory:true,
        chronologicalOos:"70/30",
        walkForward:"50% train then 10% non-overlap test windows",
        parameterGrid:{lookback:[10,20,40],stop:[3,5,10],trail:[10,20,40]},
        costStress:[0,0.5,1,1.5,2,3,5],
        chronologicalRegimes:6,
        startDateOffsetsYears:[0,2,5,10],
        timeAggregations:["1D","3D","5D"],
        monteCarloBootstrapIterations:2000
      },
      results,
      warnings:[
        "No parameter combination is promoted from this sweep.",
        "GROSS_ONLY remains gross-only under every cost multiplier.",
        "Public historical data is research evidence, not broker execution evidence.",
        "Monte Carlo resamples historical trade R and cannot model unseen structural breaks.",
        "This result cannot approve risk limits or broker execution."
      ]
    };

    await sql`
      insert into ai_trade.robustness_runs(run_key,strategy_id,result)
      values (${runKey},${STRATEGY_ID},${sql.json(result)})
      on conflict (run_key) do nothing
    `;

    return json(result);
  }catch(error){
    return json({
      ok:false,status:"ERROR",brokerOrders:false,
      message:error instanceof Error?error.message:String(error)
    },500);
  }
});