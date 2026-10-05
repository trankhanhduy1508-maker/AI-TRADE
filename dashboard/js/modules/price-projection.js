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
  const entry=Number(trade?.entryPrice);
  const targetPrice=Number(target);
  const spec=trade?.symbolSpec;
  if(!Number.isFinite(lot)||lot<=0)return{value:null,reason:"LOT_UNAVAILABLE"};
  if(!Number.isFinite(entry)||!Number.isFinite(targetPrice))return{value:null,reason:"PRICE_UNAVAILABLE"};
  if(!spec?.supported)return{value:null,reason:"SYMBOL_SPEC_UNAVAILABLE"};

  const direction=(trade.side==="SELL"||trade.direction==="DOWN")?-1:1;
  const contractSize=Number(spec.contractSize);
  const accountCurrency=String(spec.accountCurrency||"").toUpperCase();
  const profitCurrency=String(spec.currencyProfit||"").toUpperCase();
  const baseCurrency=String(spec.currencyBase||"").toUpperCase();
  const calcMode=Number(spec.calcMode);

  if(Number.isFinite(contractSize)&&contractSize>0&&accountCurrency&&profitCurrency&&[0,2,4].includes(calcMode)){
    const profit=(targetPrice-entry)*contractSize*lot*direction;
    if(profitCurrency===accountCurrency)return{value:profit,reason:null};
    if(accountCurrency==="USD"&&baseCurrency==="USD"&&profitCurrency!=="USD"&&targetPrice>0){
      return{value:profit/targetPrice,reason:null};
    }
  }

  const tickSize=Number(spec.tickSize);
  const tickValue=Number(spec.tickValue);
  if(Number.isFinite(tickSize)&&tickSize>0&&Number.isFinite(tickValue)&&tickValue>0&&accountCurrency){
    return{value:((targetPrice-entry)/tickSize)*tickValue*lot*direction,reason:null};
  }

  if(!Number.isFinite(contractSize)||contractSize<=0||!accountCurrency||!profitCurrency){
    return{value:null,reason:"CONTRACT_METADATA_UNAVAILABLE"};
  }
  return{value:null,reason:"CURRENCY_CONVERSION_UNAVAILABLE"};
}
function unavailableDetail(reason){
  if(reason==="LOT_UNAVAILABLE")return"Chưa có lot thật của vị thế.";
  if(reason==="SYMBOL_SPEC_UNAVAILABLE")return"Market này không có contract specification trên MetaQuotes-Demo.";
  if(reason==="CURRENCY_CONVERSION_UNAVAILABLE")return"Thiếu tỷ giá chuyển đổi sang currency tài khoản.";
  return"Thiếu contract/tick/account metadata cần thiết.";
}
export function renderProjection(trade,target=null){
  if(!trade||!Number.isFinite(Number(target))){
    return '<span class="projection-muted">Chạm hoặc rê trên chart để chọn mức giá mục tiêu.</span>';
  }
  const estimate=estimatePl(trade,target);
  const pl=estimate.value;
  const plLabel=pl==null?"P/L chưa đủ dữ liệu để tính chính xác":`${pl>=0?"+":"-"}$${Math.abs(pl).toFixed(2)}`;
  const detail=pl==null?`<small class="projection-note">${unavailableDetail(estimate.reason)}</small>`:"";
  return `<div class="projection-grid">
    <span><small>Target</small><b>${fmtPrice(target)}</b></span>
    <span><small>Δ Entry</small><b>${distanceLabel(trade.symbol,trade.entryPrice,target)}</b></span>
    <span><small>Estimated P/L</small><b>${plLabel}</b>${detail}</span>
  </div>`;
}
