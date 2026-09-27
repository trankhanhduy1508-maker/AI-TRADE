import{badge,fmtDate,fmtPrice}from"../utils.js";
export function renderTrainingArena(arena={positions:[],trades:[],journal:[]}){
 const ps=arena.positions??[];
 const rows=ps.map(p=>`<div class="trade-row">
   <div class="pair-cell">${p.symbol}</div>
   <div class="time">${p.assetClass}</div>
   <div>${badge(p.side,p.side==="BUY"?"green":"red")}</div>
   <div class="status">OPEN</div>
   <div>${fmtPrice(p.entryPrice)}</div>
   <div class="pnl ${Number(p.unrealizedR)>=0?"pos":"neg"}">${Number(p.unrealizedR)>=0?"+":""}${Number(p.unrealizedR).toFixed(2)}R</div>
 </div>`).join("");
 const latest=(arena.journal??[]).slice(0,6).map(j=>`<div class="journal-item">
   <label>${j.symbol} · ${j.eventType} · ${fmtDate(j.eventTs)}</label>
   <strong>${j.lesson}</strong>
 </div>`).join("");
 return `<section class="section">
  <div class="section-head"><h2>Training Arena · Tất cả market</h2><span class="action">${ps.length} vị thế paper đang mở</span></div>
  <div class="card table">
    <div class="trade-row head"><div>Cặp</div><div>Nhóm</div><div>Hướng</div><div>Trạng thái</div><div>Entry</div><div>Floating R</div></div>
    ${rows||'<div class="empty-state">Chưa có vị thế Arena.</div>'}
  </div>
  <div class="card journal-body" style="margin-top:12px">
    <div class="section-head" style="margin-bottom:4px"><h2>Nhật ký Arena gần nhất</h2><span class="action">OPEN · MARK · CLOSE · REVERSE</span></div>
    ${latest||'<div class="journal-empty">Chưa có sự kiện Arena.</div>'}
  </div>
 </section>`;
}