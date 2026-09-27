import postgres from "npm:postgres@3.4.9";

const STRATEGY_ID="TF-013A-FORWARD-DIVERSIFIED-TREND";
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

function round(v:number,d=6){
  const p=10**d;
  return Math.round(v*p)/p;
}

function maxDrawdown(rs:number[]){
  let equity=0,peak=0,maxDd=0;
  for(const r of rs){
    equity+=r;
    peak=Math.max(peak,equity);
    maxDd=Math.max(maxDd,peak-equity);
  }
  return maxDd;
}

Deno.serve(async(req)=>{
  try{
    if(!(await authorized(req)))return json({ok:false,status:"UNAUTHORIZED"},401);

    const trades=await sql`
      select id,symbol,exit_ts,
             r_10bps::float8 as r10,
             r_20bps::float8 as r20
      from ai_trade.forward_shadow_trades
      where strategy_id=${STRATEGY_ID}
      order by exit_ts,id
    `;

    const closedTrades=trades.length;
    const rs10=trades.map(t=>Number(t.r10));
    const rs20=trades.map(t=>Number(t.r20));
    const netR10=rs10.reduce((a,b)=>a+b,0);
    const netR20=rs20.reduce((a,b)=>a+b,0);
    const expectancy10=closedTrades?netR10/closedTrades:0;

    let grossProfit=0,grossLoss=0;
    for(const r of rs10){
      if(r>0)grossProfit+=r;
      else if(r<0)grossLoss+=Math.abs(r);
    }
    const profitFactor10=grossLoss>0?grossProfit/grossLoss:(grossProfit>0?999:null);

    const dd10=maxDrawdown(rs10);
    const returnToDd10=dd10>0?netR10/dd10:(netR10>0?999:null);

    const byMarket=new Map<string,number>();
    for(const t of trades){
      const symbol=String(t.symbol);
      byMarket.set(symbol,(byMarket.get(symbol)??0)+Number(t.r10));
    }
    const marketsWithTrades=byMarket.size;
    const positiveMarketValues=[...byMarket.values()].filter(v=>v>0);
    const positiveMarkets=positiveMarketValues.length;
    const positiveTotal=positiveMarketValues.reduce((a,b)=>a+b,0);
    const dominance=positiveTotal>0
      ? Math.max(...positiveMarketValues)/positiveTotal
      : null;

    let elapsedDays=0;
    if(closedTrades){
      const firstTs=new Date(String(trades[0].exit_ts)).getTime();
      const now=Date.now();
      elapsedDays=Math.max(0,Math.floor((now-firstTs)/86400000));
    }

    const [integrity]=await sql`
      select
        count(distinct (symbol,bar_ts)) filter(
          where status='FLAGGED'
             or compliance_state='MULTI_MUTATION_SAME_BAR'
        )::int as flagged_bars,
        count(*) filter(
          where action='ENTRY' and visible_stop=false
        )::int as entry_without_visible_stop
      from ai_trade.shadow_broker_orders
      where strategy_id=${STRATEGY_ID}
    `;

    const flaggedBars=Number(integrity?.flagged_bars??0);
    const entryWithoutVisibleStop=Number(integrity?.entry_without_visible_stop??0);

    const evidenceReady=
      closedTrades>=50 &&
      elapsedDays>=120 &&
      marketsWithTrades>=8;

    const gates={
      minimumEvidence:{
        closedTrades:{value:closedTrades,pass:closedTrades>=50,required:50},
        elapsedDays:{value:elapsedDays,pass:elapsedDays>=120,required:120},
        marketsWithTrades:{value:marketsWithTrades,pass:marketsWithTrades>=8,required:8}
      },
      performance:{
        netR10bps:{value:round(netR10),pass:netR10>0},
        expectancyR10bps:{value:round(expectancy10),pass:expectancy10>0},
        profitFactorR10bps:{
          value:profitFactor10===null?null:round(profitFactor10),
          pass:profitFactor10!==null&&profitFactor10>1
        },
        returnToDrawdown10bps:{
          value:returnToDd10===null?null:round(returnToDd10),
          pass:returnToDd10!==null&&returnToDd10>0.5
        },
        positiveMarkets:{value:positiveMarkets,pass:positiveMarkets>=5,required:5},
        marketDominance:{
          value:dominance===null?null:round(dominance),
          pass:dominance!==null&&dominance<=0.40,
          max:0.40
        },
        netR20bps:{value:round(netR20),pass:netR20>0}
      },
      integrity:{
        flaggedBars:{value:flaggedBars,pass:flaggedBars===0},
        entryWithoutVisibleStop:{
          value:entryWithoutVisibleStop,
          pass:entryWithoutVisibleStop===0
        },
        duplicateClientOrderId:{
          value:0,
          pass:true,
          enforcedBy:"UNIQUE(client_order_id)"
        }
      }
    };

    const candidatePass=
      netR10>0 &&
      expectancy10>0 &&
      profitFactor10!==null && profitFactor10>1 &&
      returnToDd10!==null && returnToDd10>0.5 &&
      positiveMarkets>=5 &&
      dominance!==null && dominance<=0.40 &&
      netR20>0 &&
      flaggedBars===0 &&
      entryWithoutVisibleStop===0;

    const evaluationState=
      !evidenceReady
        ? "COLLECTING"
        : candidatePass
          ? "FORWARD_CANDIDATE"
          : "FORWARD_REJECT";

    const result={
      ok:true,
      status:evaluationState,
      strategyId:STRATEGY_ID,
      researchOnly:true,
      brokerOrders:false,
      liveMoneyLocked:true,
      accountRiskApproved:false,
      metrics:{
        closedTrades,
        elapsedDays,
        marketsWithTrades,
        positiveMarkets,
        netR10bps:round(netR10),
        expectancyR10bps:round(expectancy10),
        profitFactorR10bps:profitFactor10===null?null:round(profitFactor10),
        maxDrawdownR10bps:round(dd10),
        returnToDrawdown10bps:returnToDd10===null?null:round(returnToDd10),
        netR20bps:round(netR20),
        marketPositiveContributionDominance:dominance===null?null:round(dominance),
        flaggedBars,
        entryWithoutVisibleStop
      },
      gates
    };

    await sql`
      insert into ai_trade.forward_evaluation_snapshots(
        strategy_id,evaluation_state,closed_trades,elapsed_days,
        markets_with_trades,positive_markets,
        net_r_10bps,expectancy_r_10bps,profit_factor_r_10bps,
        max_drawdown_r_10bps,return_to_drawdown_10bps,
        net_r_20bps,market_positive_contribution_dominance,
        flagged_bars,entry_without_visible_stop,gates
      ) values(
        ${STRATEGY_ID},${evaluationState},${closedTrades},${elapsedDays},
        ${marketsWithTrades},${positiveMarkets},
        ${netR10},${expectancy10},${profitFactor10},
        ${dd10},${returnToDd10},
        ${netR20},${dominance},
        ${flaggedBars},${entryWithoutVisibleStop},
        ${JSON.stringify(gates)}::jsonb
      )
    `;

    return json(result);
  }catch(error){
    return json({
      ok:false,status:"ERROR",
      message:error instanceof Error?error.message:String(error),
      brokerOrders:false,liveMoneyLocked:true
    },500);
  }
});