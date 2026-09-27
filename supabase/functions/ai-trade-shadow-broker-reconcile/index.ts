import postgres from "npm:postgres@3.4.9";

const STRATEGY_ID="TF-013A-FORWARD-DIVERSIFIED-TREND";
const sql=postgres(Deno.env.get("SUPABASE_DB_URL")!,{
  prepare:false,max:1,connect_timeout:10,idle_timeout:20
});

const json=(body:unknown,status=200)=>new Response(JSON.stringify(body),{
  status,
  headers:{"content-type":"application/json; charset=utf-8"}
});

async function authorized(req:Request){
  const rows=await sql`select secret from ai_trade.cron_auth where id=1`;
  const expected=String(rows[0]?.secret??"");
  return Boolean(expected)&&(req.headers.get("x-ai-trade-cron")??"")===expected;
}

function iso(value:unknown){
  const d=value instanceof Date?value:new Date(String(value));
  if(Number.isNaN(d.getTime()))throw new Error("INVALID_TIMESTAMP");
  return d.toISOString();
}

function entryOrderId(symbol:string,entryTs:unknown){
  return [STRATEGY_ID,symbol,"ENTRY",iso(entryTs)].join("|");
}

function exitOrderId(symbol:string,exitTs:unknown,tradeId:unknown){
  return [STRATEGY_ID,symbol,"EXIT",iso(exitTs),String(tradeId)].join("|");
}

function opposite(direction:string){
  return direction==="UP"?"SELL":"BUY";
}
function entrySide(direction:string){
  return direction==="UP"?"BUY":"SELL";
}

async function insertEntry(args:{
  symbol:string;
  direction:string;
  entryTs:unknown;
  entryPrice:number;
  stopPrice:number;
  sourceTradeId?:number|null;
  source:string;
}){
  const id=entryOrderId(args.symbol,args.entryTs);
  const rows=await sql`
    insert into ai_trade.shadow_broker_orders(
      client_order_id,strategy_id,symbol,bar_ts,action,side,
      requested_price,fill_price,stop_price,visible_stop,
      synthetic_volume,status,compliance_state,source_trade_id,reason,
      broker_orders,live_money_locked,metadata
    ) values(
      ${id},${STRATEGY_ID},${args.symbol},${args.entryTs},'ENTRY',
      ${entrySide(args.direction)},
      ${args.entryPrice},${args.entryPrice},${args.stopPrice},true,
      1,'FILLED','OK',${args.sourceTradeId??null},'FORWARD_SIGNAL',
      false,true,
      ${JSON.stringify({
        executionModel:"SHADOW_ONLY",
        normalizedVolume:1,
        accountRiskApproved:false,
        source:args.source,
        visibleStop:true
      })}::jsonb
    )
    on conflict(client_order_id) do nothing
    returning id
  `;
  return rows.length;
}

async function insertExit(args:{
  tradeId:number;
  symbol:string;
  direction:string;
  exitTs:unknown;
  exitPrice:number;
  reason:string;
}){
  const id=exitOrderId(args.symbol,args.exitTs,args.tradeId);
  const rows=await sql`
    insert into ai_trade.shadow_broker_orders(
      client_order_id,strategy_id,symbol,bar_ts,action,side,
      requested_price,fill_price,stop_price,visible_stop,
      synthetic_volume,status,compliance_state,source_trade_id,reason,
      broker_orders,live_money_locked,metadata
    ) values(
      ${id},${STRATEGY_ID},${args.symbol},${args.exitTs},'EXIT',
      ${opposite(args.direction)},
      ${args.exitPrice},${args.exitPrice},null,false,
      1,'FILLED','OK',${args.tradeId},${args.reason},
      false,true,
      ${JSON.stringify({
        executionModel:"SHADOW_ONLY",
        normalizedVolume:1,
        accountRiskApproved:false,
        source:"forward_shadow_trades"
      })}::jsonb
    )
    on conflict(client_order_id) do nothing
    returning id
  `;
  return rows.length;
}

Deno.serve(async(req)=>{
  try{
    if(!(await authorized(req)))return json({ok:false,status:"UNAUTHORIZED"},401);

    const trades=await sql`
      select id,symbol,direction,entry_ts,exit_ts,
             entry_price::float8 as entry_price,
             exit_price::float8 as exit_price,
             initial_stop::float8 as initial_stop,
             exit_reason
      from ai_trade.forward_shadow_trades
      where strategy_id=${STRATEGY_ID}
      order by id
    `;

    let inserted=0;
    for(const t of trades){
      inserted+=await insertEntry({
        symbol:String(t.symbol),
        direction:String(t.direction),
        entryTs:t.entry_ts,
        entryPrice:Number(t.entry_price),
        stopPrice:Number(t.initial_stop),
        sourceTradeId:Number(t.id),
        source:"forward_shadow_trades"
      });
      inserted+=await insertExit({
        tradeId:Number(t.id),
        symbol:String(t.symbol),
        direction:String(t.direction),
        exitTs:t.exit_ts,
        exitPrice:Number(t.exit_price),
        reason:String(t.exit_reason??"EXIT")
      });
    }

    const states=await sql`
      select symbol,position
      from ai_trade.forward_shadow_state
      where strategy_id=${STRATEGY_ID}
        and position is not null
      order by symbol
    `;

    for(const s of states){
      const p=s.position as Record<string,unknown>;
      const entryTsSec=Number(p.entryTs);
      const entryPrice=Number(p.entryPrice);
      const stop=Number(p.stop);
      const direction=String(p.direction??"");
      if(!Number.isFinite(entryTsSec)||!Number.isFinite(entryPrice)||!Number.isFinite(stop)){
        throw new Error("INVALID_FORWARD_POSITION_"+String(s.symbol));
      }
      if(direction!=="UP"&&direction!=="DOWN"){
        throw new Error("INVALID_FORWARD_DIRECTION_"+String(s.symbol));
      }
      const entryTs=new Date(entryTsSec*1000);
      inserted+=await insertEntry({
        symbol:String(s.symbol),
        direction,
        entryTs,
        entryPrice,
        stopPrice:stop,
        source:"forward_shadow_state"
      });
    }

    await sql`delete from ai_trade.shadow_broker_positions where strategy_id=${STRATEGY_ID}`;

    for(const s of states){
      const p=s.position as Record<string,unknown>;
      const entryTsSec=Number(p.entryTs);
      const entryTs=new Date(entryTsSec*1000);
      const direction=String(p.direction);
      const symbol=String(s.symbol);
      const entryPrice=Number(p.entryPrice);
      const stop=Number(p.stop);
      const oid=entryOrderId(symbol,entryTs);

      await sql`
        insert into ai_trade.shadow_broker_positions(
          strategy_id,symbol,direction,entry_ts,entry_price,stop_price,
          synthetic_volume,source_client_order_id,updated_at
        ) values(
          ${STRATEGY_ID},${symbol},${direction},${entryTs},
          ${entryPrice},${stop},1,${oid},now()
        )
        on conflict(strategy_id,symbol) do update set
          direction=excluded.direction,
          entry_ts=excluded.entry_ts,
          entry_price=excluded.entry_price,
          stop_price=excluded.stop_price,
          synthetic_volume=excluded.synthetic_volume,
          source_client_order_id=excluded.source_client_order_id,
          updated_at=now()
      `;
    }

    await sql`
      update ai_trade.shadow_broker_orders o
      set status='FLAGGED',
          compliance_state='MULTI_MUTATION_SAME_BAR'
      where o.strategy_id=${STRATEGY_ID}
        and exists(
          select 1
          from ai_trade.shadow_broker_orders x
          where x.strategy_id=o.strategy_id
            and x.symbol=o.symbol
            and x.bar_ts=o.bar_ts
          group by x.strategy_id,x.symbol,x.bar_ts
          having count(*)>1
        )
    `;

    const [summary]=await sql`
      select
        count(*)::int as order_count,
        count(*) filter(where status='FLAGGED')::int as flagged_order_count,
        count(distinct (symbol,bar_ts)) filter(where status='FLAGGED')::int as flagged_bar_count
      from ai_trade.shadow_broker_orders
      where strategy_id=${STRATEGY_ID}
    `;
    const [pos]=await sql`
      select count(*)::int as position_count
      from ai_trade.shadow_broker_positions
      where strategy_id=${STRATEGY_ID}
    `;

    const result={
      ok:true,
      status:"SHADOW_BROKER_RECONCILED",
      strategyId:STRATEGY_ID,
      brokerOrders:false,
      liveMoneyLocked:true,
      accountRiskApproved:false,
      normalizedVolume:1,
      ordersInsertedThisRun:inserted,
      orderCount:Number(summary?.order_count??0),
      flaggedOrderCount:Number(summary?.flagged_order_count??0),
      flaggedBarCount:Number(summary?.flagged_bar_count??0),
      openPositionCount:Number(pos?.position_count??0),
      invariant:{
        visibleStopRequiredOnEntry:true,
        noPyramiding:true,
        idempotentClientOrderId:true,
        sameBarMultiMutation:"FLAG_NOT_EXECUTE"
      }
    };

    await sql`
      insert into ai_trade.shadow_broker_runs(
        strategy_id,status,orders_inserted,positions_open,flagged_bars,result
      ) values(
        ${STRATEGY_ID},'SHADOW_BROKER_RECONCILED',${inserted},
        ${Number(pos?.position_count??0)},
        ${Number(summary?.flagged_bar_count??0)},
        ${JSON.stringify(result)}::jsonb
      )
    `;

    return json(result);
  }catch(error){
    return json({
      ok:false,
      status:"ERROR",
      message:error instanceof Error?error.message:String(error),
      brokerOrders:false,
      liveMoneyLocked:true
    },500);
  }
});
