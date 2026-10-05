import {value,summarize,PROFILE} from "./paper-pnl.mjs";
import {fetchQuote,mark} from "./quote-mark.mjs";
import postgres from "npm:postgres@3.4.9";
const sql = postgres(Deno.env.get("SUPABASE_DB_URL")!, {prepare:false,max:1,connect_timeout:10,idle_timeout:20});
const strategy = "TF-013A-ARENA-ALL-MARKETS";
const json = (data:unknown,status=200) => new Response(JSON.stringify(data), {status,headers:{"content-type":"application/json; charset=utf-8","cache-control":"private, no-store"}});
Deno.serve(async req => {
  if(req.method!=="GET") return json({error:"METHOD_NOT_ALLOWED"},405);
  const token = req.headers.get("authorization")?.match(/^Bearer ([a-f0-9]{64})$/)?.[1];
  if(!token) return json({error:"UNAUTHORIZED"},401);
  try {
    const bytes = await crypto.subtle.digest("SHA-256",new TextEncoder().encode(token));
    const hash = Array.from(new Uint8Array(bytes),x=>x.toString(16).padStart(2,"0")).join("");
    const readers = await sql`select id from ai_trade.paper_feed_readers where key_hash=${hash} and enabled=true`;
    if(!readers.length) return json({error:"UNAUTHORIZED"},401);
    // Read-only, single-strategy projection. No broker accounts, credentials or raw candles.
    const positions = await sql`select symbol, asset_class, direction, entry_ts, entry_price, stop_price, risk_price, last_mark_ts, last_mark_price, unrealized_r, updated_at from ai_trade.training_arena_positions where strategy_id=${strategy} order by symbol`;
    const trades = await sql`select id, symbol, asset_class, direction, entry_ts, exit_ts, entry_price, exit_price, gross_r, r_10bps, exit_reason from ai_trade.training_arena_trades where strategy_id=${strategy} order by exit_ts desc`;
    const watch = await sql`select symbol,status,last_signal,last_bar_ts,updated_at from ai_trade.training_arena_watch where strategy_id=${strategy} order by symbol`;
    const runs = await sql`select status, created_at from ai_trade.training_arena_runs where strategy_id=${strategy} order by created_at desc limit 1`;
    const markedPositions=await Promise.all(positions.map(async p=>{try{return mark(p,await fetchQuote(p.symbol));}catch{return {...p,quote_status:"UNAVAILABLE_OR_STALE",quote_source:"Stored daily mark"};}}));
    const valuedPositions=markedPositions.map(p=>value(p));
    const valuedTrades=trades.map(t=>value(t,true));
    const summary=summarize(valuedPositions,valuedTrades);
    return json({mode:"SIMULATION",strategy,updateFrequency:"on_view_60s",quoteCheckedAt:new Date().toISOString(),quoteRefreshSeconds:60,asOf:runs[0]?.created_at??null,runStatus:runs[0]?.status??null,positions:valuedPositions,trades:valuedTrades.slice(0,100),summary,sizing:PROFILE,watch,historyLimit:100});
  } catch { return json({error:"FEED_UNAVAILABLE"},503); }
});
