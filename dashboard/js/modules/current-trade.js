import{badge,empty,fmtUsd}from"../utils.js";
export function renderCurrentTrade(trade){
  if(!trade)return `<section class="section"><div class="section-head"><h2>Trạng thái giao dịch hiện tại</h2></div><div class="card card-pad">${empty("Chưa có lệnh forward đang mở. Hệ thống đang chờ tín hiệu mới.")}</div></section>`;
  const side=trade.side?trade.side:(trade.direction==="UP"?"BUY":"SELL");
  const isPaper=trade.mode==="PAPER_TRAINING_ARENA";
  const plRaw=isPaper?trade.floatingR:trade.floatingPL;
  const pl=plRaw==null?null:Number(plRaw);
  const floatingLabel=pl==null||!Number.isFinite(pl)?"—":isPaper?`${pl>=0?"+":""}${pl.toFixed(2)}R`:fmtUsd(pl);
  const plClass=pl==null||!Number.isFinite(pl)?"":pl<0?"neg":"pos";
  const lotRaw=isPaper?trade.paperLot:trade.lot;
  const lot=Number(lotRaw);
  const lotLabel=Number.isFinite(lot)&&lot>0?lot.toFixed(2):"—";
  return `<section class="section"><div class="section-head"><h2>Trạng thái giao dịch hiện tại</h2></div>
  <div class="card card-pad current-trade compact-trade">
    <div class="compact-position">
      <div><small>Cặp giao dịch</small><strong class="compact-symbol">${trade.symbol}</strong></div>
      <div><small>Lệnh</small>${badge(side,side==="BUY"?"green":"red")}</div>
      <div><small>${isPaper?"Paper Lot":"Lot"}</small><strong>${lotLabel}</strong></div>
      <div><small>${isPaper?"P/L (R)":"P/L"}</small><strong class="${plClass}">${floatingLabel}</strong></div>
    </div>
  </div></section>`;
}
