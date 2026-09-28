import{empty,fmtUsd}from"../utils.js";

function sideOf(p){return p.side??(p.direction==="UP"?"BUY":"SELL")}
function lotOf(p){
  const v=Number(p?.lot);
  return Number.isFinite(v)&&v>0?v.toFixed(2):"—";
}
function pnlOf(p){
  const v=Number(p?.floatingPL);
  return Number.isFinite(v)?v:null;
}
function aggregateBySymbol(positions=[]){
  const groups=new Map();
  for(const p of positions){
    const symbol=String(p?.symbol??"—");
    const pl=pnlOf(p);
    const current=groups.get(symbol)??{symbol,count:0,knownCount:0,total:0};
    current.count+=1;
    if(pl!=null){current.knownCount+=1;current.total+=pl}
    groups.set(symbol,current);
  }
  return [...groups.values()].sort((a,b)=>a.symbol.localeCompare(b.symbol));
}
export function renderAdminPositions(positions=[],selectedSymbol=""){
  if(!positions?.length)return `<section class="section admin-priority"><div class="section-head"><h2>Current open positions</h2></div><div class="card card-pad">${empty("Không có vị thế đang mở.")}</div></section>`;

  const pnls=positions.map(pnlOf);
  const allPnlKnown=pnls.every(v=>v!=null);
  const total=allPnlKnown?pnls.reduce((a,b)=>a+b,0):null;
  const totalClass=total==null?"":total>=0?"pos":"neg";

  const symbolRows=aggregateBySymbol(positions).map(g=>{
    const complete=g.knownCount===g.count;
    const value=complete?g.total:null;
    const cls=value==null?"":value>=0?"pos":"neg";
    return `<div class="position-summary-row">
      <span><b>${g.symbol}</b><small>${g.count} lệnh</small></span>
      <strong class="${cls}">${value==null?"—":fmtUsd(value)}</strong>
    </div>`;
  }).join("");

  const rows=positions.map(p=>{
    const side=sideOf(p);
    const active=p.symbol===selectedSymbol?" active":"";
    const pl=pnlOf(p);
    const plClass=pl==null?"":pl>=0?"pos":"neg";
    return `<button type="button" class="position-row${active}" data-symbol="${p.symbol}">
      <span><b>${p.symbol}</b></span>
      <span><small>Side</small><b class="${side==="BUY"?"side-buy":"side-sell"}">${side}</b></span>
      <span><small>Lot</small><b>${lotOf(p)}</b></span>
      <span><small>P/L</small><b class="position-pnl ${plClass}">${pl==null?"—":fmtUsd(pl)}</b></span>
    </button>`;
  }).join("");

  return `<section class="section admin-priority">
    <div class="section-head"><h2>Current open positions</h2><span class="action">${positions.length} open</span></div>
    <div class="card position-summary">
      <div class="position-summary-head"><span>Tổng theo cặp</span><small>P/L đang mở</small></div>
      ${symbolRows}
    </div>
    <div class="position-total card"><span>Tổng P/L tất cả lệnh</span><strong class="${totalClass}">${total==null?"—":fmtUsd(total)}</strong></div>
    <div class="card positions-list">${rows}</div>
  </section>`;
}
