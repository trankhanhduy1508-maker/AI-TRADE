(function(root){
  "use strict";
  const number=v => (typeof v==="number" || (typeof v==="string" && v.trim()!=="")) && Number.isFinite(Number(v)) ? Number(v) : null;
  const date=v => typeof v==="string" && Number.isFinite(Date.parse(v)) ? v : null;
  function normalize(feed){
    if(!feed || feed.mode!=="SIMULATION" || feed.strategy!=="TF-013A-ARENA-ALL-MARKETS" || !Array.isArray(feed.positions) || !Array.isArray(feed.trades)) throw new Error("INVALID_FEED");
    let rejected=0;
    const valid=(row,closed)=>{
      if(!row || !/^[A-Z0-9]{3,12}$/.test(row.symbol) || !["UP","DOWN"].includes(row.direction) || !date(row.entry_ts)) return false;
      const required=closed?["entry_price","exit_price","gross_r"]:["entry_price","stop_price","risk_price","last_mark_price","unrealized_r"];
      if(required.some(k=>number(row[k])===null)) return false;
      if(required.filter(k=>!k.endsWith("_r")).some(k=>number(row[k])<=0)) return false;
      return Boolean(date(closed?row.exit_ts:row.last_mark_ts));
    };
    function rows(input,closed){return input.filter(r=>{const ok=valid(r,closed);if(!ok)rejected++;return ok;}).map(r=>({...r,side:r.direction==="UP"?"BUY":"SELL"}));}
    return {positions:rows(feed.positions,false),trades:rows(feed.trades,true),asOf:date(feed.asOf),rejected};
  }
  const api={number,normalize};
  if(typeof module!=="undefined" && module.exports) module.exports=api;
  root.CWSPaperOrders=api;
  if(!root.document) return;
  const $=id=>document.getElementById(id);
  const host=$("paperOrders"); if(!host) return;
  const format=v=>number(v)===null?"—":number(v).toLocaleString("en-US",{maximumFractionDigits:5});
  const rformat=v=>number(v)===null?"—":(number(v)>=0?"+":"")+number(v).toFixed(3)+" R";
  const time=v=>v?new Date(v).toLocaleString("vi-VN"):"Chưa có thời điểm";
  function cell(tr,value,cls){const td=document.createElement("td");td.textContent=value;if(cls)td.className=cls;tr.append(td);return td;}
  function table(id,rows,closed){
    const body=$(id);body.replaceChildren();
    if(!rows.length){const tr=document.createElement("tr");const td=cell(tr,closed?"Chưa có lệnh đóng.":"Chưa có vị thế mô phỏng đang mở.");td.colSpan=7;body.append(tr);return;}
    rows.forEach(row=>{
      const tr=document.createElement("tr");
      cell(tr,row.symbol);cell(tr,row.side,row.side==="BUY"?"positive":"negative");
      cell(tr,format(row.entry_price));cell(tr,format(closed?row.exit_price:row.stop_price));
      if(!closed) cell(tr,format(row.last_mark_price));
      const result=number(closed?row.gross_r:row.unrealized_r);
      cell(tr,rformat(result),result>=0?"positive":"negative");
      cell(tr,time(closed?row.exit_ts:row.last_mark_ts));
      if(closed) cell(tr,row.exit_reason==="USER_CLOSE"?"Theo yêu cầu":row.exit_reason==="REVERSAL"?"Đảo chiều":row.exit_reason==="STOP"?"Chạm stop":"Đóng theo quy tắc");
      body.append(tr);
    });
  }
  let busy=false,last=null;
  async function refresh(){
    if(busy) return;busy=true;$("paperRefresh").disabled=true;
    try{
      const response=await fetch("/api/paper-orders",{cache:"no-store",credentials:"same-origin",signal:AbortSignal.timeout(35000)});
      if(!response.ok) throw new Error("UNAVAILABLE");
      last=normalize(await response.json());
      table("paperOpenRows",last.positions,false);table("paperClosedRows",last.trades,true);
      $("paperOpenCount").textContent=last.positions.length;
      $("paperClosedCount").textContent=last.trades.length;
      $("paperOpenR").textContent=last.rejected?"—":rformat(last.positions.reduce((s,p)=>s+number(p.unrealized_r),0));
      $("paperClosedR").textContent=last.rejected?"—":rformat(last.trades.reduce((s,p)=>s+number(p.gross_r),0));
      const age=last.asOf?Date.now()-Date.parse(last.asOf):Infinity;
      $("paperStatus").textContent=age>36*3600000?"DỮ LIỆU CŨ":"MÔ PHỎNG · D1";
      $("paperUpdated").textContent="Bot cập nhật: "+time(last.asOf)+" · Tải bảng: "+time(new Date().toISOString())+(last.rejected?" · Có "+last.rejected+" dòng lỗi, đã ẩn.":"");
      $("paperError").hidden=true;
    }catch{
      $("paperStatus").textContent="CHƯA TẢI ĐƯỢC";
      $("paperError").hidden=false;
      $("paperError").textContent=last?"Mất kết nối. Bảng bên dưới là dữ liệu đã tải trước đó; chưa xác nhận cập nhật mới.":"Chưa tải được lệnh. Hãy kiểm tra kết nối và bấm Làm mới. Không có lệnh minh họa được chèn vào bảng này.";
    }finally{busy=false;$("paperRefresh").disabled=false;}
  }
  $("paperRefresh").addEventListener("click",refresh);
  refresh();setInterval(()=>{if(!document.hidden)refresh();},60000);
  document.addEventListener("visibilitychange",()=>{if(!document.hidden)refresh();});
})(typeof window!=="undefined"?window:globalThis);
