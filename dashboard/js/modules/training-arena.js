import{badge,fmtDate,fmtPrice}from"../utils.js";
export function renderTrainingArena(arena={positions:[],trades:[],journal:[]}){
 const ps=arena.positions??[];
 const rows=ps.map(p=>{
   const pnlUsd=p.floatingPL==null?null:Number(p.floatingPL);
   const r=Number(p.unrealizedR??0);
   const pnlLabel=pnlUsd==null?`${r>=0?"+":""}${r.toFixed(2)}R`:`${pnlUsd>=0?"+":""}${pnlUsd.toFixed(2)} USD · ${r>=0?"+":""}${r.toFixed(2)}R`;
   const lot=p.lot!=null?Number(p.lot).toFixed(2):(p.volumeLabel??"Paper");
   return `<div class="arena-row">
     <div class="pair-cell">${p.symbol}<small>${p.assetClass}</small></div>
     <div>${badge(p.side,p.side==="BUY"?"green":"red")}</div>
     <div><small>Lot</small><b>${lot}</b></div>
     <div><small>Entry</small><b>${fmtPrice(p.entryPrice)}</b></div>
     <div><small>Stop</small><b>${fmtPrice(p.stopPrice)}</b></div>
     <div class="pnl ${r>=0?"pos":"neg"}"><small>P/L</small><b>${pnlLabel}</b></div>
   </div>`;
 }).join("");
 const latest=(arena.journal??[]).slice(0,6).map(j=>`<div class="journal-item">
   <label>${j.symbol} · ${j.eventType} · ${fmtDate(j.eventTs)}</label>
   <strong>${j.lesson}</strong>
 </div>`).join("");
 return `<section class="section">
  <div class="section-head"><h2>Training Arena · Tất cả market</h2><span class="action">${ps.length} vị thế paper đang mở</span></div>
  <div class="card arena-table">
    ${rows||'<div class="empty-state">Chưa có vị thế Arena.</div>'}
  </div>
  <div class="card journal-body" style="margin-top:12px">
    <div class="section-head" style="margin-bottom:4px"><h2>Nhật ký Arena gần nhất</h2><span class="action">OPEN · MARK · CLOSE · REVERSE</span></div>
    ${latest||'<div class="journal-empty">Chưa có sự kiện Arena.</div>'}
  </div>
 </section>`;
}
