import postgres from "npm:postgres@3.4.9";
type Direction="UP"|"DOWN";
type Bar={timestamp:number;open:number;high:number;low:number;close:number};
type Inst={key:string;yahoo:string;assetClass:string};
const STRATEGY_ID="TF-013A-ARENA-ALL-MARKETS";
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
 const end=Math.floor(Date.now()/1000),start=end-3*365*86400;
 const url="https://query1.finance.yahoo.com/v8/finance/chart/"+encodeURIComponent(symbol)+
   "?period1="+start+"&period2="+end+"&interval=1d&events=history&includeAdjustedClose=true";
 const r=await fetch(url,{headers:{"user-agent":"AI-TRADE-training-arena/1.0"}});
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
 if(out.length<300)throw new Error("INSUFFICIENT_BARS_"+out.length);
 return out;
}
function lessonOpen(symbol:string,dir:Direction){
 return `${symbol}: mở paper ${dir==="UP"?"BUY":"SELL"} theo tín hiệu TF-013A hiện tại. Quan sát cách giá phản ứng với stop 4 ATR; không suy luận từ một lệnh đơn lẻ.`;
}
function lessonClose(r:number,reason:string){
 if(reason==="STOP") return r<0
   ?"Lệnh chạm stop. Ghi nhận market regime và chuỗi stop; không tự nới stop sau một lệnh lỗ."
   :"Stop đã khóa kết quả dương. Ghi nhận nhưng không tăng rủi ro chỉ vì một lệnh thắng.";
 return r>=0
   ?"Đảo chiều đóng lệnh có lời. Giữ kỷ luật thay vì cố đoán đỉnh đáy."
   :"Đảo chiều đóng lệnh lỗ. Trend following chấp nhận nhiều lệnh lỗ nhỏ để chờ xu hướng lớn.";
}
async function journal(symbol:string,eventType:string,ts:number,dir:Direction|null,price:number|null,stop:number|null,realized:number|null,unrealized:number|null,reason:string,lesson:string,meta:any={}){
 await sql`insert into ai_trade.training_arena_journal(
   strategy_id,symbol,event_type,event_ts,direction,price,stop_price,realized_r,unrealized_r,
   setup,reason,lesson,metadata
 ) values(
   ${STRATEGY_ID},${symbol},${eventType},to_timestamp(${ts}),${dir},${price},${stop},
   ${realized},${unrealized},
   'TF-013A arena: return21 + return252 + SMA10/200 vote, paper-only',
   ${reason},${lesson},${JSON.stringify(meta)}::jsonb
 )`;
}
Deno.serve(async req=>{
 try{
  if(!(await authorized(req)))return json({ok:false,status:"UNAUTHORIZED"},401);
  let opened=0,closed=0,marked=0,errors:any[]=[];
  for(const inst of U){
   try{
    const b=await bars(inst.yahoo),i=b.length-1,bar=b[i],a=atr(b,20),sig=signal(b,i);
    if(!sig)continue;
    const rows=await sql`select * from ai_trade.training_arena_positions where strategy_id=${STRATEGY_ID} and symbol=${inst.key} limit 1`;
    const existing=rows[0];
    if(!existing){
      const risk=4*a[i];
      if(!(risk>0&&Number.isFinite(risk)))throw new Error("ATR_INVALID");
      const stop=sig==="UP"?bar.close-risk:bar.close+risk;
      await sql`insert into ai_trade.training_arena_positions(
        strategy_id,symbol,asset_class,direction,entry_ts,entry_price,stop_price,risk_price,
        last_mark_ts,last_mark_price,unrealized_r,opened_reason
      ) values(
        ${STRATEGY_ID},${inst.key},${inst.assetClass},${sig},to_timestamp(${bar.timestamp}),
        ${bar.close},${stop},${risk},to_timestamp(${bar.timestamp}),${bar.close},0,
        'ARENA_INITIAL_SIGNAL'
      ) on conflict(strategy_id,symbol) do nothing`;
      await journal(inst.key,"OPEN",bar.timestamp,sig,bar.close,stop,null,0,"ARENA_INITIAL_SIGNAL",lessonOpen(inst.key,sig),{assetClass:inst.assetClass});
      opened++;continue;
    }
    const dir=String(existing.direction) as Direction;
    const entry=Number(existing.entry_price),stop=Number(existing.stop_price),risk=Number(existing.risk_price);
    let exitReason:string|null=null,exitPrice:number|null=null;
    const hit=dir==="UP"?bar.low<=stop:bar.high>=stop;
    if(hit){exitReason="STOP";exitPrice=dir==="UP"?Math.min(stop,bar.open):Math.max(stop,bar.open)}
    else if(sig!==dir){exitReason="REVERSAL";exitPrice=bar.close}
    if(exitReason&&exitPrice!==null){
      const gross=dir==="UP"?exitPrice-entry:entry-exitPrice;
      const grossR=gross/risk,r10=(gross-entry*.001)/risk,r20=(gross-entry*.002)/risk;
      await sql`insert into ai_trade.training_arena_trades(
        strategy_id,symbol,asset_class,direction,entry_ts,exit_ts,entry_price,exit_price,
        initial_stop,risk_price,gross_r,r_10bps,r_20bps,exit_reason
      ) values(
        ${STRATEGY_ID},${inst.key},${inst.assetClass},${dir},${existing.entry_ts},to_timestamp(${bar.timestamp}),
        ${entry},${exitPrice},${stop},${risk},${grossR},${r10},${r20},${exitReason}
      ) on conflict(strategy_id,symbol,entry_ts,exit_ts) do nothing`;
      await journal(inst.key,exitReason==="REVERSAL"?"REVERSE":"CLOSE",bar.timestamp,dir,exitPrice,stop,r10,null,exitReason,lessonClose(r10,exitReason),{assetClass:inst.assetClass});
      await sql`delete from ai_trade.training_arena_positions where strategy_id=${STRATEGY_ID} and symbol=${inst.key}`;
      closed++;
      if(exitReason==="REVERSAL"){
        const newRisk=4*a[i],newStop=sig==="UP"?bar.close-newRisk:bar.close+newRisk;
        await sql`insert into ai_trade.training_arena_positions(
          strategy_id,symbol,asset_class,direction,entry_ts,entry_price,stop_price,risk_price,
          last_mark_ts,last_mark_price,unrealized_r,opened_reason
        ) values(
          ${STRATEGY_ID},${inst.key},${inst.assetClass},${sig},to_timestamp(${bar.timestamp}),
          ${bar.close},${newStop},${newRisk},to_timestamp(${bar.timestamp}),${bar.close},0,'ARENA_REVERSAL_SIGNAL'
        )`;
        await journal(inst.key,"OPEN",bar.timestamp,sig,bar.close,newStop,null,0,"ARENA_REVERSAL_SIGNAL",lessonOpen(inst.key,sig),{assetClass:inst.assetClass});
        opened++;
      }
    }else{
      const unreal=dir==="UP"?(bar.close-entry)/risk:(entry-bar.close)/risk;
      await sql`update ai_trade.training_arena_positions set
        last_mark_ts=to_timestamp(${bar.timestamp}),last_mark_price=${bar.close},
        unrealized_r=${unreal},updated_at=now()
        where strategy_id=${STRATEGY_ID} and symbol=${inst.key}`;
      await journal(inst.key,"MARK",bar.timestamp,dir,bar.close,stop,null,unreal,"DAILY_MARK",
        `${inst.key}: cập nhật paper position. Floating ${unreal>=0?"+":""}${unreal.toFixed(2)}R; tiếp tục quan sát theo luật, không can thiệp cảm tính.`,
        {assetClass:inst.assetClass});
      marked++;
    }
   }catch(e){errors.push({symbol:inst.key,error:e instanceof Error?e.message:String(e)})}
  }
  const [counts]=await sql`
    select
      (select count(*) from ai_trade.training_arena_positions where strategy_id=${STRATEGY_ID})::int as positions_open,
      (select count(*) from ai_trade.training_arena_trades where strategy_id=${STRATEGY_ID})::int as trades_closed
  `;
  const result={ok:true,status:"TRAINING_ARENA_UPDATED",strategyId:STRATEGY_ID,universeSize:U.length,opened,closed,marked,positionsOpen:Number(counts?.positions_open??0),tradesClosed:Number(counts?.trades_closed??0),errors,brokerOrders:false,liveMoneyLocked:true,contaminatesForward:false};
  await sql`insert into ai_trade.training_arena_runs(strategy_id,status,positions_open,trades_closed,result)
    values(${STRATEGY_ID},'TRAINING_ARENA_UPDATED',${result.positionsOpen},${result.tradesClosed},${JSON.stringify(result)}::jsonb)`;
  return json(result);
 }catch(e){return json({ok:false,status:"ERROR",message:e instanceof Error?e.message:String(e),brokerOrders:false,liveMoneyLocked:true},500)}
});