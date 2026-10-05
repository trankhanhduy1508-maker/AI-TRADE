import postgres from "npm:postgres@3.4.9";
const STRATEGY_ID="TF-013A-FORWARD-DIVERSIFIED-TREND";
const sql=postgres(Deno.env.get("SUPABASE_DB_URL")!,{prepare:false,max:1,connect_timeout:10,idle_timeout:20});
const json=(body:unknown,status=200)=>new Response(JSON.stringify(body),{status,headers:{"content-type":"application/json; charset=utf-8"}});
async function authorized(req:Request){
  const rows=await sql`select secret from ai_trade.cron_auth where id=1`;
  const expected=String(rows[0]?.secret??"");
  return Boolean(expected)&&(req.headers.get("x-ai-trade-cron")??"")===expected;
}
function lesson(r:number,exitReason:string){
  if(exitReason==="EMERGENCY_STOP"){
    return r<0
      ?"Lệnh bị dừng tại stop. Giữ kỷ luật stop giúp giới hạn thiệt hại; cần theo dõi xem setup này có thường xuyên vào quá sớm trong các pha nhiễu hay không."
      :"Stop bảo vệ đã hoạt động sau khi lệnh từng có lợi thế. Cần kiểm tra liệu stop hiện tại có bảo vệ đủ lợi nhuận mà không bóp nghẹt xu hướng.";
  }
  if(exitReason==="MONTHLY_REVERSAL"){
    return r>=0
      ?"Đảo chiều theo review định kỳ đã khóa lợi nhuận. Tiếp tục giữ nguyên quy tắc, không kéo dài lệnh chỉ vì cảm giác."
      :"Đảo chiều theo review định kỳ đóng một lệnh lỗ. Đây là chi phí bình thường của trend following; cần đánh giá chuỗi nhiều lệnh thay vì một giao dịch đơn lẻ.";
  }
  return r>=0
    ?"Lệnh có kết quả dương. Không coi một lệnh thắng là xác nhận phương pháp; tiếp tục kiểm chứng cùng quy tắc trên mẫu forward lớn hơn."
    :"Lệnh có kết quả âm. Không chỉnh chiến lược theo một lệnh; kiểm tra execution, market regime và chuỗi kết quả forward trước khi thay đổi.";
}
function tags(r:number,reason:string){
  const out=[r>0?"win":r<0?"loss":"flat","forward-only","tf013a"];
  if(reason)out.push(reason.toLowerCase());
  return out;
}
Deno.serve(async req=>{
  if(!(await authorized(req)))return json({ok:false,status:"UNAUTHORIZED"},401);
  const rows=await sql`
    select t.*
    from ai_trade.forward_shadow_trades t
    left join ai_trade.forward_trade_journal j on j.source_trade_id=t.id
    where t.strategy_id=${STRATEGY_ID} and j.id is null
    order by t.id
  `;
  let inserted=0;
  for(const t of rows){
    const r=Number(t.r_10bps);
    const result=r>0?"WIN":r<0?"LOSS":"FLAT";
    const reason=String(t.exit_reason??"");
    const tradeId=`TF013A-${new Date(t.exit_ts).toISOString().slice(0,10).replaceAll("-","")}-${String(t.id).padStart(4,"0")}`;
    await sql`
      insert into ai_trade.forward_trade_journal(
        source_trade_id,strategy_id,trade_id,symbol,direction,entry_ts,exit_ts,
        r_10bps,result_label,setup,entry_reason,exit_reason,lesson,chart_timeframe,tags
      ) values(
        ${Number(t.id)},${STRATEGY_ID},${tradeId},${String(t.symbol)},${String(t.direction)},
        ${t.entry_ts},${t.exit_ts},${r},${result},
        'TF-013A diversified trend: return 21 + return 252 + SMA10/200 majority vote',
        'Tín hiệu forward hợp lệ sau khi bar đóng; entry được thực hiện ở bar kế tiếp theo execution contract.',
        ${reason||"RULE_EXIT"},
        ${lesson(r,reason)},
        '1h',
        ${JSON.stringify(tags(r,reason))}::jsonb
      )
      on conflict(source_trade_id) do nothing
    `;
    inserted++;
  }
  return json({ok:true,status:"JOURNAL_UPDATED",inserted,brokerOrders:false,liveMoneyLocked:true});
});