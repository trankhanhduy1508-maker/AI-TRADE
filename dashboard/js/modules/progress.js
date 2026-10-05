import{pct}from"../utils.js";
export function renderProgress(e,targets){
 const cards=[["Closed trades",e.closedTrades,targets.trades],["Số ngày",e.elapsedDays,targets.days],["Market có trade",e.marketsWithTrades,targets.markets]];
 return `<section class="section"><div class="section-head"><h2>Tiến độ đủ mẫu</h2><span class="action">Gate forward</span></div><div class="grid-3">${cards.map(([label,v,t])=>`<div class="card progress-card"><div class="progress-head"><span>${label}</span><strong>${v}/${t}</strong></div><div class="bar"><i style="width:${pct(v,t)}%"></i></div></div>`).join("")}</div></section>`;
}
