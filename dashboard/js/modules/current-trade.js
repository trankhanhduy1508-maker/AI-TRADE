import{badge,empty,fmtPrice,fmtUsd}from"../utils.js";
export function renderCurrentTrade(trade){
  if(!trade)return `<section class="section"><div class="section-head"><h2>Trạng thái giao dịch hiện tại</h2></div><div class="card card-pad">${empty("Chưa có lệnh forward đang mở. Hệ thống đang chờ tín hiệu mới.")}</div></section>`;
  const side=trade.side?trade.side:(trade.direction==="UP"?"BUY":"SELL");
  const pl=trade.floatingPL==null?null:Number(trade.floatingPL);
  const floatingR=Number.isFinite(Number(trade.floatingR))?Number(trade.floatingR):null;
  const floatingLabel=pl==null?(floatingR==null?"—":`${floatingR>=0?"+":""}${floatingR.toFixed(2)}R`):fmtUsd(pl);
  const lotLabel=trade.lot!=null?Number(trade.lot).toFixed(2):trade.volumeLabel??"—";
  const accountLabel=trade.mt5Login?String(trade.mt5Login):"—";
  return `<section class="section"><div class="section-head"><h2>Trạng thái giao dịch hiện tại</h2></div>
  <div class="card card-pad current-trade"><div class="trade-grid">
    <div><div class="trade-title">Lệnh đang mở</div><div class="pair-row"><div class="pair">${trade.symbol}</div>${badge(side,side==="BUY"?"green":"red")}${badge("ĐANG MỞ LỆNH","green")}</div>
      <div class="trade-fields trade-fields-6">
        <div class="field"><label>Entry</label><strong>${fmtPrice(trade.entryPrice)}</strong></div>
        <div class="field"><label>Giá hiện tại</label><strong>${fmtPrice(trade.currentPrice??trade.entryPrice)}</strong></div>
        <div class="field"><label>Stop loss</label><strong style="color:var(--red)">${fmtPrice(trade.stopPrice)}</strong></div>
        <div class="field"><label>Take profit</label><strong style="color:var(--green)">${trade.takeProfit?fmtPrice(trade.takeProfit):"TP — chưa đặt"}</strong></div>
        <div class="field"><label>Lot / Volume</label><strong>${lotLabel}</strong></div>
        <div class="field"><label>MT5 account</label><strong>${accountLabel}</strong></div>
      </div>
    </div>
    <div class="pl-card"><div class="trade-title">Floating P/L</div><div class="amount ${pl!=null&&pl<0?"negative":""}">${floatingLabel}</div>
      <div class="metric-row"><span>Floating R</span><b>${floatingR==null?"—":`${floatingR>=0?"+":""}${floatingR.toFixed(2)}R`}</b></div>
      <div class="metric-row"><span>Risk/Reward</span><b>${trade.riskReward??"—"}</b></div>
      <div class="metric-row"><span>Mô hình</span><b>${trade.mode??"SHADOW"}</b></div>
    </div>
  </div></div></section>`;
}
