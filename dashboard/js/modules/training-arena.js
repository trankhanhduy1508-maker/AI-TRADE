import{badge,fmtDate}from"../utils.js";
export function renderTrainingArena(arena={positions:[],trades:[],journal:[]}){
 const ps=arena.positions??[];
 const allRKnown=ps.length>0&&ps.every(p=>Number.isFinite(Number(p.unrealizedR)));
 const totalR=allRKnown?ps.reduce((sum,p)=>sum+Number(p.unrealizedR),0):null;
 const rows=ps.map(p=>{
   const pnlR=p.unrealizedR==null?null:Number(p.unrealizedR);
   const pnlLabel=Number.isFinite(pnlR)?`${pnlR>=0?"+":""}${pnlR.toFixed(2)}R`:"—";
   const lotNum=Number(p.paperLot);
   const lot=Number.isFinite(lotNum)&&lotNum>0?lotNum.toFixed(2):"—";
   const pnlClass=Number.isFinite(pnlR)?(pnlR>=0?"pos":"neg"):"";
   return `<div class="arena-row arena-row-simple">
     <div class="pair-cell">${p.symbol}<small>${p.assetClass}</small></div>
     <div>${badge(p.side,p.side==="BUY"?"green":"red")}</div>
     <div><small>Paper Lot</small><b>${lot}</b></div>
     <div class="pnl ${pnlClass}"><small>P/L (R)</small><b>${pnlLabel}</b></div>
   </div>`;
 }).join("");
 const latest=(arena.journal??[]).slice(0,6).map(j=>`<div class="journal-item">
   <label>${j.symbol} · ${j.eventType} · ${fmtDate(j.eventTs)}</label>
   <strong>${j.lesson}</strong>
 </div>`).join("");
 return `<section class="section">
  <div class="section-head"><h2>Training Arena · Tất cả market</h2><span class="action">${ps.length} vị thế paper · P/L theo R</span></div>
  <div class="position-total card"><span>Tổng P/L Arena (R)</span><strong class="${totalR==null?"":totalR>=0?"pos":"neg"}">${totalR==null?"—":`${totalR>=0?"+":""}${totalR.toFixed(2)}R`}</strong></div>
  <div class="card arena-table">
    ${rows||'<div class="empty-state">Chưa có vị thế Arena.</div>'}
  </div>
  <div class="card journal-body" style="margin-top:12px">
    <div class="section-head" style="margin-bottom:4px"><h2>Nhật ký Arena gần nhất</h2><span class="action">OPEN · MARK · CLOSE · REVERSE</span></div>
    ${latest||'<div class="journal-empty">Chưa có sự kiện Arena.</div>'}
  </div>
 </section>`;
}
