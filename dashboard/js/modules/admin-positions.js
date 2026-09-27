import{empty,fmtPrice}from"../utils.js";
export function renderAdminPositions(positions=[],selectedSymbol=""){
  if(!positions?.length)return `<section class="section admin-priority"><div class="section-head"><h2>Current open positions</h2></div><div class="card card-pad">${empty("Không có vị thế shadow đang mở.")}</div></section>`;
  const rows=positions.map(p=>{
    const side=p.side??(p.direction==="UP"?"BUY":"SELL");
    const active=p.symbol===selectedSymbol?" active":"";
    const volume=p.lot!=null?Number(p.lot).toFixed(2):(p.syntheticVolume!=null?"Shadow "+Number(p.syntheticVolume).toFixed(1):"—");
    return `<button type="button" class="position-row${active}" data-symbol="${p.symbol}">
      <span><b>${p.symbol}</b><small>${side}</small></span>
      <span><small>Entry</small><b>${fmtPrice(p.entryPrice)}</b></span>
      <span><small>SL</small><b>${fmtPrice(p.stopPrice)}</b></span>
      <span><small>Lot / Volume</small><b>${volume}</b></span>
    </button>`;
  }).join("");
  return `<section class="section admin-priority"><div class="section-head"><h2>Current open positions</h2><span class="action">${positions.length} open</span></div><div class="card positions-list">${rows}</div></section>`;
}
