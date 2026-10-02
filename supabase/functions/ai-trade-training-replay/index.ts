import postgres from "npm:postgres@3.4.9";
type Direction="UP"|"DOWN";
type Bar={timestamp:number;open:number;high:number;low:number;close:number};
type Inst={key:string;yahoo:string;assetClass:string};
type Pos={direction:Direction;entryTs:number;entryPrice:number;stop:number;initialStop:number;riskPrice:number};
type Trade={symbol:string;assetClass:string;direction:Direction;entryTs:number;exitTs:number;entryPrice:number;exitPrice:number;initialStop:number;grossR:number;r10:number;r20:number;exitReason:string;lessonCode:string};

const STRATEGY_ID="TF-013A-FORWARD-DIVERSIFIED-TREND";
const TARGET=10;
const sql=postgres(Deno.env.get("SUPABASE_DB_URL")!,{prepare:false,max:1,connect_timeout:10,idle_timeout:20});
const json=(b:unknown,s=200)=>new Response(JSON.stringify(b),{status:s,headers:{"content-type":"application/json; charset=utf-8"}});
const U:Inst[]=[
 {key:"EURUSD",yahoo:"EURUSD=X",assetClass:"FX"},{key:"GBPUSD",yahoo:"GBPUSD=X",assetClass:"FX"},
 {key:"USDJPY",yahoo:"USDJPY=X",assetClass:"FX"},{key:"AUDUSD",yahoo:"AUDUSD=X",assetClass:"FX"},
 {key:"USDCAD",yahoo:"CAD=X",assetClass:"FX"},{key:"USDCHF",yahoo:"CHF=X",assetClass:"FX"},
 {key:"NZDUSD",yahoo:"NZDUSD=X",assetClass:"FX"},{key:"XAUUSD",yahoo:"GC=F",assetClass:"COMMODITY"},
 {key:"USOIL",yahoo:"CL=F",assetClass:"COMMODITY"},{key:"BTCUSD",yahoo:"BTC-USD",assetClass:"CRYPTO"},
 {key:"ETHUSD",yahoo:"ETH-USD",assetClass:"CRYPTO"},{key:"US30",yahoo:"^DJI",assetClass:"INDEX"},
 {key:"NAS100",yahoo:"^NDX",assetClass:"INDEX"},{key:"US500",yahoo:"^GSPC",assetClass:"INDEX"}
];

async function authorized(req:Request){
 const rows=await sql`select secret from ai_trade.cron_auth where id=1`;
 return Boolean(rows[0]?.secret)&&(req.headers.get("x-ai-trade-cron")??"")===String(rows[0].secret);
}
function n(v:unknown){const x=Number(v);return Number.isFinite(x)?x:null}
function monthKey(ts:number){return new Date(ts*1000).toISOString().slice(0,7)}
function sma(b:Bar[],i:number,p:number){if(i+1<p)return null;let s=0;for(let k=i-p+1;k<=i;k++)s+=b[k].close;return s/p}
function signal(b:Bar[],i:number):Direction|null{
 if(i<252)return null;
 const f=sma(b,i,10),s=sma(b,i,200);if(f===null||s===null)return null;
 const votes=[b[i].close-b[i-21].close,b[i].close-b[i-252].close,f-s].map(x=>x>0?1:x<0?-1:0);
 const score=votes.reduce((a,c)=>a+c,0);return score>0?"UP":score<0?"DOWN":null;
}
function atr(b:Bar[],p=20){
 const tr:number[]=[],a=Array(b.length).fill(NaN);
 for(let i=0;i<b.length;i++)tr.push(i===0?b[i].high-b[i].low:Math.max(b[i].high-b[i].low,Math.abs(b[i].high-b[i-1].close),Math.abs(b[i].low-b[i-1].close)));
 if(b.length<=p)return a;let s=0;for(let i=1;i<=p;i++)s+=tr[i];a[p]=s/p;
 for(let i=p+1;i<b.length;i++)a[i]=(a[i-1]*(p-1)+tr[i])/p;return a;
}
async function bars(symbol:string){
 const end=Math.floor(Date.now()/1000),start=end-9*365*86400;
 const url="https://query1.finance.yahoo.com/v8/finance/chart/"+encodeURIComponent(symbol)+
   "?period1="+start+"&period2="+end+"&interval=1d&events=history&includeAdjustedClose=true";
 const r=await fetch(url,{headers:{"user-agent":"AI-TRADE-training-replay/1.0"}});
 if(!r.ok)throw new Error("YAHOO_HTTP_"+r.status);
 const p=await r.json(),res=p?.chart?.result?.[0],q=res?.indicators?.quote?.[0],ts:number[]=res?.timestamp??[];
 if(!q)throw new Error("NO_DATA");
 const out:Bar[]=[];
 for(let i=0;i<ts.length;i++){
   const open=n(q.open?.[i]),high=n(q.high?.[i]),low=n(q.low?.[i]),close=n(q.close?.[i]);
   if(open===null||high===null||low===null||close===null||open<=0||high<=0||low<=0||close<=0)continue;
   out.push({timestamp:Number(ts[i]),open,high,low,close});
 }
 out.sort((a,b)=>a.timestamp-b.timestamp);
 if(out.length<600)throw new Error("INSUFFICIENT_BARS_"+out.length);
 return out;
}
function closeTrade(inst:Inst,pos:Pos,exitTs:number,exitPrice:number,reason:string):Trade{
 const gross=pos.direction==="UP"?exitPrice-pos.entryPrice:pos.entryPrice-exitPrice;
 const grossR=gross/pos.riskPrice,r10=(gross-pos.entryPrice*.001)/pos.riskPrice,r20=(gross-pos.entryPrice*.002)/pos.riskPrice;
 const lessonCode=reason==="EMERGENCY_STOP"?(r10<0?"STOP_LOSS_DISCIPLINE":"STOP_PROTECTED_GAIN"):(r10>=0?"REVERSAL_LOCKED_TREND":"REVERSAL_ACCEPTED_LOSS");
 return {symbol:inst.key,assetClass:inst.assetClass,direction:pos.direction,entryTs:pos.entryTs,exitTs,entryPrice:pos.entryPrice,exitPrice,initialStop:pos.initialStop,grossR,r10,r20,exitReason:reason,lessonCode};
}
function replay(inst:Inst,b:Bar[]){
 const a=atr(b,20);let pos:Pos|null=null,pending:Direction|null=null,reviewMonth=monthKey(b[252].timestamp),all:Trade[]=[];
 for(let i=253;i<b.length;i++){
   const bar=b[i];
   if(pending){
     if(pos&&pos.direction!==pending){all.push(closeTrade(inst,pos,bar.timestamp,bar.open,"MONTHLY_REVERSAL"));pos=null}
     if(!pos){
       const av=a[i-1];if(av>0&&Number.isFinite(av)){const risk=4*av;pos={direction:pending,entryTs:bar.timestamp,entryPrice:bar.open,stop:pending==="UP"?bar.open-risk:bar.open+risk,initialStop:pending==="UP"?bar.open-risk:bar.open+risk,riskPrice:risk}}
     }
     pending=null;
   }
   if(pos){
     const hit=pos.direction==="UP"?bar.low<=pos.stop:bar.high>=pos.stop;
     if(hit){const exit=pos.direction==="UP"?Math.min(pos.stop,bar.open):Math.max(pos.stop,bar.open);all.push(closeTrade(inst,pos,bar.timestamp,exit,"EMERGENCY_STOP"));pos=null}
   }
   const mk=monthKey(bar.timestamp);
   if(mk!==reviewMonth){const sig=signal(b,i);reviewMonth=mk;if(sig&&(!pos||pos.direction!==sig))pending=sig}
 }
 return all.slice(-TARGET);
}
function symbolLesson(symbol:string,trades:Trade[]){
 const wins=trades.filter(t=>t.r10>0).length,losses=trades.filter(t=>t.r10<0).length,net=trades.reduce((s,t)=>s+t.r10,0);
 const stops=trades.filter(t=>t.exitReason==="EMERGENCY_STOP").length,revs=trades.length-stops,avg=trades.length?net/trades.length:0;
 let lesson="";
 if(!trades.length)lesson="Chưa đủ giao dịch replay để rút kinh nghiệm.";
 else if(net>0&&stops<=trades.length/2)lesson=`${symbol}: 10 lệnh gần nhất cho thấy trend capture tạo lợi thế dương; giữ kỷ luật đảo chiều tháng, không nới stop chỉ vì một lệnh thắng.`;
 else if(net>0)lesson=`${symbol}: tổng R dương nhưng nhiều lệnh kết thúc bằng stop; cần theo dõi nhiễu và chuỗi stop, chưa được phép giảm khoảng stop theo cảm tính.`;
 else if(stops>revs)lesson=`${symbol}: replay âm và phần lớn bị stop; market này dễ nhiễu với cấu hình hiện tại. Ghi nhận để quan sát forward, không retune TF-013A từ 10 mẫu.`;
 else lesson=`${symbol}: replay âm chủ yếu quanh các lần reversal; trend regime gần đây không thuận lợi. Chấp nhận loss theo luật và chờ mẫu lớn hơn.`;
 return {wins,losses,net,avg,stops,revs,lesson};
}

Deno.serve(async req=>{
 try{
  if(!(await authorized(req)))return json({ok:false,status:"UNAUTHORIZED"},401);
  const runKey="TF013A_REPLAY_10X14_"+new Date().toISOString().slice(0,10).replaceAll("-","");
  const perSymbol=await Promise.all(U.map(async inst=>{
    try{const b=await bars(inst.yahoo);const trades=replay(inst,b);return {inst,trades,error:null};}
    catch(e){return {inst,trades:[] as Trade[],error:e instanceof Error?e.message:String(e)}}
  }));
  await sql`delete from ai_trade.training_replay_trades where run_key=${runKey}`;
  await sql`delete from ai_trade.training_replay_lessons where run_key=${runKey}`;
  let completed=0,symbolsWithTarget=0;
  const summaries:any[]=[];
  for(const item of perSymbol){
    const {inst,trades,error}=item;completed+=trades.length;if(trades.length>=TARGET)symbolsWithTarget++;
    for(let i=0;i<trades.length;i++){
      const t=trades[i];
      await sql`insert into ai_trade.training_replay_trades(
        run_key,strategy_id,symbol,asset_class,sequence_no,direction,entry_ts,exit_ts,
        entry_price,exit_price,initial_stop,gross_r,r_10bps,r_20bps,exit_reason,lesson_code
      ) values(
        ${runKey},${STRATEGY_ID},${t.symbol},${t.assetClass},${i+1},${t.direction},
        to_timestamp(${t.entryTs}),to_timestamp(${t.exitTs}),${t.entryPrice},${t.exitPrice},
        ${t.initialStop},${t.grossR},${t.r10},${t.r20},${t.exitReason},${t.lessonCode}
      ) on conflict(run_key,symbol,sequence_no) do update set
        direction=excluded.direction,entry_ts=excluded.entry_ts,exit_ts=excluded.exit_ts,
        entry_price=excluded.entry_price,exit_price=excluded.exit_price,initial_stop=excluded.initial_stop,
        gross_r=excluded.gross_r,r_10bps=excluded.r_10bps,r_20bps=excluded.r_20bps,
        exit_reason=excluded.exit_reason,lesson_code=excluded.lesson_code`;
    }
    const s=symbolLesson(inst.key,trades);
    await sql`insert into ai_trade.training_replay_lessons(
      run_key,strategy_id,scope,symbol,trade_count,wins,losses,net_r_10bps,avg_r_10bps,
      max_loss_r,stop_exit_count,reversal_exit_count,lesson
    ) values(
      ${runKey},${STRATEGY_ID},'SYMBOL',${inst.key},${trades.length},${s.wins},${s.losses},
      ${s.net},${s.avg},${trades.length?Math.min(...trades.map(t=>t.r10)):0},${s.stops},${s.revs},${s.lesson}
    ) on conflict(run_key,scope,symbol) do update set
      trade_count=excluded.trade_count,wins=excluded.wins,losses=excluded.losses,
      net_r_10bps=excluded.net_r_10bps,avg_r_10bps=excluded.avg_r_10bps,
      max_loss_r=excluded.max_loss_r,stop_exit_count=excluded.stop_exit_count,
      reversal_exit_count=excluded.reversal_exit_count,lesson=excluded.lesson`;
    summaries.push({symbol:inst.key,count:trades.length,wins:s.wins,losses:s.losses,netR10:s.net,avgR10:s.avg,stopExits:s.stops,reversalExits:s.revs,lesson:s.lesson,error});
  }
  const all=summaries.filter(s=>s.count>0),net=all.reduce((x,s)=>x+s.netR10,0),wins=all.reduce((x,s)=>x+s.wins,0),losses=all.reduce((x,s)=>x+s.losses,0);
  const portfolioLesson=net>0
    ?"Replay đa thị trường đang dương ở mẫu huấn luyện. Bài học chính là giữ tính đa dạng và kỷ luật stop/reversal; không dùng replay này để tự cấp quyền trade."
    :"Replay đa thị trường đang âm ở mẫu huấn luyện. Bài học chính là chưa có bằng chứng đủ để tăng rủi ro; tiếp tục forward và không retune từ mẫu nhỏ.";
  await sql`insert into ai_trade.training_replay_lessons(
    run_key,strategy_id,scope,symbol,trade_count,wins,losses,net_r_10bps,avg_r_10bps,
    max_loss_r,stop_exit_count,reversal_exit_count,lesson
  ) values(
    ${runKey},${STRATEGY_ID},'PORTFOLIO',null,${completed},${wins},${losses},${net},
    ${completed?net/completed:0},
    ${completed?Math.min(...perSymbol.flatMap(x=>x.trades.map(t=>t.r10))):0},
    ${perSymbol.flatMap(x=>x.trades).filter(t=>t.exitReason==="EMERGENCY_STOP").length},
    ${perSymbol.flatMap(x=>x.trades).filter(t=>t.exitReason==="MONTHLY_REVERSAL").length},
    ${portfolioLesson}
  ) on conflict(run_key,scope,symbol) do nothing`;
  const result={ok:true,status:"TRAINING_REPLAY_COMPLETE",runKey,strategyId:STRATEGY_ID,mode:"REPLAY_ONLY",universeSize:U.length,targetTradesPerSymbol:TARGET,completedTrades:completed,symbolsWithTarget,brokerOrders:false,liveMoneyLocked:true,forwardEvidenceContaminated:false,summaries,portfolioLesson};
  await sql`insert into ai_trade.training_replay_runs(run_key,strategy_id,universe_size,target_trades_per_symbol,completed_trades,symbols_with_target,result)
    values(${runKey},${STRATEGY_ID},${U.length},${TARGET},${completed},${symbolsWithTarget},${JSON.stringify(result)}::jsonb)
    on conflict(run_key) do update set completed_trades=excluded.completed_trades,symbols_with_target=excluded.symbols_with_target,result=excluded.result`;
  return json(result);
 }catch(e){return json({ok:false,status:"ERROR",message:e instanceof Error?e.message:String(e),brokerOrders:false,liveMoneyLocked:true},500)}
});