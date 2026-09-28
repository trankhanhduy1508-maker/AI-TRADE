import{badge,empty,fmtUsd}from"../utils.js";
export function renderCurrentTrade(trade){
  if(!trade)return `<section class="section"><div class="section-head"><h2>Trạng thái giao dịch hiện tại</h2></div><div class="card card-pad">${empty("Chưa có lệnh forward đang mở. Hệ thống đang chờ tín hiệu mới.")}</div></section>`;
  const side=trade.side?trade.side:(trade.direction==="UP"?"BUY":"SELL");
  const pl=trade.floatingPL==null?null:Number(trade.floatingPL);
  const floatingLabel=pl==null?"—":fmtUsd(pl);
  const plClass=pl==null?"":pl<0?"neg":"pos";
  const lot=Number(trade.lot);
  const lotLabel=Number.isFinite(lot)&&lot>0?lot.toFixed(2):"—";
  return `<section class="section"><div class="section-head"><h2>Trạng thái giao dịch hiện tại</h2></div>
  <div class="card card-pad current-trade compact-trade">
    <div class="compact-position">
      <div><small>Cặp giao dịch</small><strong class="compact-symbol">${trade.symbol}</strong></div>
      <div><small>Lệnh</small>${badge(side,side==="BUY"?"green":"red")}</div>
      <div><small>Lot</small><strong>${lotLabel}</strong></div>
      <div><small>P/L</small><strong class="${plClass}">${floatingLabel}</strong></div>
    </div>
  </div></section>`;
}
