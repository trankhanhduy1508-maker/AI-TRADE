import{fmtR}from"../utils.js";
export function renderPerformance(e={}){
 return `<section class="section"><div class="section-head"><h2>Tổng quan hiệu suất</h2><span class="action">Forward only</span></div><div class="grid-3">
   <div class="card summary-card"><small>Net R @ 10bps</small><strong class="${Number(e.netR10bps)>=0?"green":"red"}">${fmtR(e.netR10bps)}</strong></div>
   <div class="card summary-card"><small>Expectancy</small><strong class="${Number(e.expectancyR10bps)>=0?"green":"red"}">${fmtR(e.expectancyR10bps)}</strong></div>
   <div class="card summary-card"><small>Profit factor</small><strong>${e.profitFactorR10bps==null?"—":Number(e.profitFactorR10bps).toFixed(2)}</strong></div>
   <div class="card summary-card"><small>Max drawdown</small><strong class="red">${fmtR(e.maxDrawdownR10bps)}</strong></div>
   <div class="card summary-card"><small>Net R @ 20bps</small><strong class="${Number(e.netR20bps)>=0?"green":"red"}">${fmtR(e.netR20bps)}</strong></div>
   <div class="card summary-card"><small>Positive markets</small><strong>${Number(e.positiveMarkets??0)}</strong></div>
 </div></section>`;
}
