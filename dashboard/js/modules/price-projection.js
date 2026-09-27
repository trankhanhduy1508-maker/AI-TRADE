function fmtPrice(v){
  const n=Number(v);
  if(!Number.isFinite(n))return "—";
  if(Math.abs(n)>=1000)return n.toFixed(2);
  if(Math.abs(n)>=100)return n.toFixed(3);
  return n.toFixed(5);
}
function distanceLabel(symbol,entry,target){
  const delta=Number(target)-Number(entry);
  if(!Number.isFinite(delta))return "—";
  if(["EURUSD","GBPUSD","AUDUSD","USDCAD","USDCHF","NZDUSD"].includes(symbol)){
    return `${delta>=0?"+":""}${(delta/0.0001).toFixed(1)} pip`;
  }
  if(symbol==="USDJPY")return `${delta>=0?"+":""}${(delta/0.01).toFixed(1)} pip`;
  return `${delta>=0?"+":""}${delta.toFixed(Math.abs(delta)<10?3:2)} point`;
}
function estimatePl(trade,target){
  const lot=Number(trade?.lot);
  const tickSize=Number(trade?.symbolSpec?.tickSize);
  const tickValue=Number(trade?.symbolSpec?.tickValue);
  const entry=Number(trade?.entryPrice);
  if(![lot,tickSize,tickValue,entry,Number(target)].every(Number.isFinite)||lot<=0||tickSize<=0)return null;
  const direction=(trade.side==="SELL"||trade.direction==="DOWN")?-1:1;
  return ((Number(target)-entry)/tickSize)*tickValue*lot*direction;
}
export function renderProjection(trade,target=null){
  if(!trade||!Number.isFinite(Number(target))){
    return '<span class="projection-muted">Chạm hoặc rê trên chart để chọn mức giá mục tiêu.</span>';
  }
  const pl=estimatePl(trade,target);
  const plLabel=pl==null?"P/L chưa đủ dữ liệu để tính chính xác":`${pl>=0?"+":"-"}$${Math.abs(pl).toFixed(2)}`;
  return `<div class="projection-grid">
    <span><small>Target</small><b>${fmtPrice(target)}</b></span>
    <span><small>Δ Entry</small><b>${distanceLabel(trade.symbol,trade.entryPrice,target)}</b></span>
    <span><small>Estimated P/L</small><b>${plLabel}</b></span>
  </div>`;
}
