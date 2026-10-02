import{badge,empty,fmtDate,fmtUsd}from"../utils.js";
export function renderJournal(entries=[]){
  if(!entries.length)return `<section class="section"><div class="section-head"><h2>Nhật ký rút kinh nghiệm</h2><span class="action">Tự ghi sau mỗi lệnh</span></div><div class="card journal-empty">${empty("Chưa có lệnh đóng nên chưa có nhật ký. Sau lệnh đầu tiên, hệ thống sẽ ghi setup, lý do vào/thoát và bài học.")}</div></section>`;
  const j=entries[0];
  const pnl=Number(j.pnlUsd??j.r10bps??0);
  return `<section class="section"><div class="section-head"><h2>Nhật ký rút kinh nghiệm</h2><span class="action">Lệnh gần nhất</span></div>
  <div class="journal-grid">
    <div class="card journal-meta">
      <div class="journal-item"><label>Trade ID</label><strong>${j.tradeId??j.id??"—"}</strong></div>
      <div class="journal-item"><label>Cặp</label><strong>${j.symbol??"—"}</strong></div>
      <div class="journal-item"><label>Thời gian đóng</label><strong>${fmtDate(j.exitTs)}</strong></div>
      <div class="journal-item"><label>Kết quả</label><strong style="color:${pnl>=0?"var(--green)":"var(--red)"}">${j.pnlUsd!=null?fmtUsd(pnl):((pnl>0?"+":"")+pnl.toFixed(2)+"R")}</strong></div>
      <div style="margin-top:10px">${badge(pnl>=0?"WIN":"LOSS",pnl>=0?"green":"red")}</div>
    </div>
    <div class="card journal-body">
      <div class="journal-item"><label>Setup</label><strong>${j.setup??"TF-013A diversified trend"}</strong></div>
      <div class="journal-item"><label>Lý do vào lệnh</label><strong>${j.entryReason??"Tín hiệu forward hợp lệ theo chiến lược đã khóa."}</strong></div>
      <div class="journal-item"><label>Lý do thoát lệnh</label><strong>${j.exitReason??"Theo quy tắc thoát của forward engine."}</strong></div>
      <div class="journal-item"><label>Bài học</label><strong>${j.lesson??"Chưa đủ dữ liệu để rút bài học cụ thể."}</strong></div>
    </div>
  </div></section>`;
}
