import{badge,empty,fmtPrice,fmtUsd}from"../utils.js";
export function renderCurrentTrade(trade){
  if(!trade)return `<section class="section"><div class="section-head"><h2>Trạng thái giao dịch hiện tại</h2></div><div class="card card-pad">${empty("Chưa có lệnh forward đang mở. Hệ thống đang chờ tín hiệu mới.")}</div></section>`;
  const side=trade.side?trade.side:(trade.direction==="UP"?"BUY":"SELL");
  const pl=Number(trade.floatingPL??0);
  return `<section class="section"><div class="section-head"><h2>Trạng thái giao dịch hiện tại</h2></div>
  <div class="card card-pad current-trade"><div class="trade-grid">
    <div><div class="trade-title">Lệnh đang mở</div><div class="pair-row"><div class="pair">${trade.symbol}</div>${badge(side,side==="BUY"?"green":"red")}${badge("ĐANG MỞ LỆNH","green")}</div>
      <div class="trade-fields">
        <div class="field"><label>Entry</label><strong>${fmtPrice(trade.entryPrice)}</strong></div>
        <div class="field"><label>Giá hiện tại</label><strong>${fmtPrice(trade.currentPrice??trade.entryPrice)}</strong></div>
        <div class="field"><label>Stop loss</label><strong style="color:var(--red)">${fmtPrice(trade.stopPrice)}</strong></div>
        <div class="field"><label>Take profit</label><strong style="color:var(--green)">${trade.takeProfit?fmtPrice(trade.takeProfit):"—"}</strong></div>
        <div class="field"><label>Khối lượng</label><strong>${trade.volumeLabel??"Shadow 1.0"}</strong></div>
      </div>
    </div>
    <div class="pl-card"><div class="trade-title">Floating P/L</div><div class="amount">${fmtUsd(pl)}</div><div class="metric-row"><span>Risk/Reward</span><b>${trade.riskReward??"—"}</b></div><div class="metric-row"><span>Mô hình</span><b>SHADOW</b></div></div>
  </div></div></section>`;
}
