/* CWS public chart: official, third-party hosted TradingView widget.
 * CWS does not fetch, re-host, train on or claim rights over widget market data.
 * External widget/network may be unavailable when the PWA is offline.
 */
(function(root,factory){
  const api=factory();
  if(typeof module==="object"&&module.exports)module.exports=api;
  else root.CWSTradingView=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(){
"use strict";
const SCRIPT="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js";
const SYMBOLS=Object.freeze({
  EURUSD:"FX:EURUSD",GBPUSD:"FX:GBPUSD",USDJPY:"FX:USDJPY",
  AUDUSD:"FX:AUDUSD",NZDUSD:"FX:NZDUSD",USDCAD:"FX:USDCAD",
  USDCHF:"FX:USDCHF",EURJPY:"FX:EURJPY",
  XAUUSD:"OANDA:XAUUSD",XAGUSD:"OANDA:XAGUSD",
  BTCUSD:"BITSTAMP:BTCUSD",ETHUSD:"BITSTAMP:ETHUSD",
  USOIL:"TVC:USOIL",US30:"TVC:DJI",NAS100:"NASDAQ:NDX",
  US500:"SP:SPX"
});
const INTERVALS=Object.freeze({"15m":"15","30m":"30","1h":"60","4h":"240","1d":"D"});
function config(symbol,timeframe){
  if(!Object.prototype.hasOwnProperty.call(SYMBOLS,symbol)||
     !Object.prototype.hasOwnProperty.call(INTERVALS,timeframe))return null;
  return {autosize:true,symbol:SYMBOLS[symbol],interval:INTERVALS[timeframe],
    timezone:"Etc/UTC",theme:"dark",style:"1",locale:"vi",
    backgroundColor:"#0b1422",gridColor:"rgba(69, 98, 130, 0.20)",
    allow_symbol_change:true,withdateranges:true,hide_side_toolbar:false,
    hide_top_toolbar:false,hide_legend:false,hide_volume:false,
    save_image:false,calendar:false,details:false,
    support_host:"https://www.tradingview.com"};
}
function chartUrl(symbol){
  const s=SYMBOLS[symbol];
  return s?"https://www.tradingview.com/chart/?symbol="+encodeURIComponent(s):
    "https://www.tradingview.com/chart/";
}
function mount(host,symbol,timeframe,onError){
  const options=config(symbol,timeframe);
  if(!host||typeof host.replaceChildren!=="function"||!options)return null;
  const doc=host.ownerDocument;
  host.replaceChildren();
  const outer=doc.createElement("div");
  outer.className="tradingview-widget-container";
  outer.style.height="100%";outer.style.width="100%";
  const inner=doc.createElement("div");
  inner.className="tradingview-widget-container__widget";
  inner.style.height="calc(100% - 28px)";inner.style.width="100%";
  const attribution=doc.createElement("div");
  attribution.className="tradingview-widget-copyright";
  const a=doc.createElement("a");
  a.href=chartUrl(symbol);a.target="_blank";a.rel="noopener nofollow noreferrer";
  a.textContent="Xem "+symbol+" trên TradingView";
  attribution.append(a,doc.createTextNode(" · Biểu đồ bởi TradingView"));
  const script=doc.createElement("script");
  script.type="text/javascript";script.src=SCRIPT;script.async=true;
  script.textContent=JSON.stringify(options);
  if(typeof onError==="function")script.onerror=onError;
  outer.append(inner,attribution,script);
  host.append(outer);
  return options;
}
return {SYMBOLS,INTERVALS,SCRIPT,config,chartUrl,mount};
});
