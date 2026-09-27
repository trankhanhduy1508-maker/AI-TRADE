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

    const today=new Date();
    const requestedEnd=today.toISOString().slice(0,10);
    const endExclusive=new Date(Date.UTC(
      today.getUTCFullYear(),today.getUTCMonth(),today.getUTCDate()+1
    )).toISOString().slice(0,10);

    const results=[];
    for(const instrument of UNIVERSE){
      try{
        const bars=await yahooBars(instrument.yahooSymbol,REQUESTED_START,endExclusive);
        results.push({ok:true,...analyze(instrument,bars)});
      }catch(error){
        results.push({
          ok:false,
          symbol:instrument.key,
          label:instrument.label,
          yahooSymbol:instrument.yahooSymbol,
          costMode:instrument.costMode,
          error:error instanceof Error?error.message:String(error),
        });
      }
      await new Promise(resolve=>setTimeout(resolve,100));
    }

    const successful=results.filter((x:any)=>x.ok);
    const failed=results.filter((x:any)=>!x.ok);
    const runKey="TF004_MISSING_ASSETS_2016_"+requestedEnd.replaceAll("-","")+"_V1";
    const result={
      ok:failed.length===0,
      status:failed.length===0?"COMPLETE":"PARTIAL",
      mode:"RESEARCH_ONLY",
      brokerOrders:false,
      strategyId:STRATEGY_ID,
      requestedStart:REQUESTED_START,
      requestedEnd,
      universeSize:UNIVERSE.length,
      successfulCount:successful.length,
      failedCount:failed.length,
      results,
      warnings:[
        "GROSS_ONLY markets are not net-profitability evidence.",
        "Yahoo daily data is a research proxy, not broker execution data.",
        "This backtest does not approve any risk limit or broker execution.",
        "Assets with PARTIAL_HISTORY must not be described as having a full 10-year backtest."
      ],
    };

    await sql`
      insert into ai_trade.backtest_runs(
        run_key,strategy_id,requested_start,requested_end,universe_size,result
      )
      values(
        ${runKey},${STRATEGY_ID},${REQUESTED_START}::date,
        ${requestedEnd}::date,${UNIVERSE.length},
        ${sql.json(result)}
      )
      on conflict (run_key) do nothing
    `;

    return json(result);
  }catch(error){
    return json({
      ok:false,status:"ERROR",
      message:error instanceof Error?error.message:String(error),
      brokerOrders:false,
    },500);
  }
});
