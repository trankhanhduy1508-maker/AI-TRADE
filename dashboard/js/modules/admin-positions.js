import{empty,fmtUsd}from"../utils.js";

function sideOf(p){return p.side??(p.direction==="UP"?"BUY":"SELL")}
function pnlOf(p){
  const v=Number(p?.floatingPL);
  return Number.isFinite(v)?v:null;
}
function realLotOf(p){
  const v=Number(p?.lot);
  return Number.isFinite(v)&&v>0?v:null;
}
function aggregateBySymbol(positions=[]){
  const groups=new Map();
  for(const p of positions){
    const symbol=String(p?.symbol??"—");
    const pl=pnlOf(p);
    const lot=realLotOf(p);
    const side=sideOf(p);
    const current=groups.get(symbol)??{
      symbol,
      side,
      mixedSide:false,
      count:0,
      knownPnlCount:0,
      totalPnl:0,
      knownLotCount:0,
      totalLot:0,
    };
    current.count+=1;
    if(current.side!==side)current.mixedSide=true;
    if(pl!=null){current.knownPnlCount+=1;current.totalPnl+=pl}
    if(lot!=null){current.knownLotCount+=1;current.totalLot+=lot}
    groups.set(symbol,current);
  }
  return [...groups.values()].sort((a,b)=>a.symbol.localeCompare(b.symbol));
}
export function renderAdminPositions(positions=[],selectedSymbol=""){
  if(!positions?.length)return `<section class="section admin-priority"><div class="section-head"><h2>Current open positions</h2></div><div class="card card-pad">${empty("Không có vị thế đang mở.")}</div></section>`;

  const groups=aggregateBySymbol(positions);
  const pnls=positions.map(pnlOf);
  const allPnlKnown=pnls.every(v=>v!=null);
  const total=allPnlKnown?pnls.reduce((a,b)=>a+b,0):null;
  const totalClass=total==null?"":total>=0?"pos":"neg";

  const rows=groups.map(g=>{
    const side=g.mixedSide?"MIXED":g.side;
    const active=g.symbol===selectedSymbol?" active":"";
    const lotComplete=g.knownLotCount===g.count;
    const pnlComplete=g.knownPnlCount===g.count;
    const lot=lotComplete?g.totalLot:null;
    const pl=pnlComplete?g.totalPnl:null;
    const plClass=pl==null?"":pl>=0?"pos":"neg";
    const sideClass=side==="BUY"?"side-buy":side==="SELL"?"side-sell":"";
    return `<button type="button" class="position-row${active}" data-symbol="${g.symbol}">
      <span><b>${g.symbol}</b></span>
      <span><small>Side</small><b class="${sideClass}">${side}</b></span>
      <span><small>Lot</small><b>${lot==null?"—":lot.toFixed(2)}</b></span>
      <span><small>P/L</small><b class="position-pnl ${plClass}">${pl==null?"—":fmtUsd(pl)}</b></span>
    </button>`;
  }).join("");

  return `<section class="section admin-priority">
    <div class="section-head"><h2>Current open positions</h2><span class="action">${groups.length} cặp</span></div>
    <div class="position-total card"><span>Tổng P/L tất cả vị thế</span><strong class="${totalClass}">${total==null?"—":fmtUsd(total)}</strong></div>
    <div class="card positions-list">${rows}</div>
  </section>`;
}
