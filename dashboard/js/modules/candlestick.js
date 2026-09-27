import{ema,empty,esc}from"../utils.js";
let chart=null;
export function renderCandlestickShell(symbol="EURUSD",timeframe="1h"){
 return `<section class="section"><div class="section-head"><h2>Biểu đồ nến Nhật</h2><span class="action">Chart forward context</span></div>
  <div class="card chart-card">
    <div class="chart-toolbar"><div class="left"><select id="chartSymbol"><option>${esc(symbol)}</option></select><select id="chartTimeframe"><option value="1h">${esc(timeframe.toUpperCase())}</option></select></div><span class="badge blue">LIVE DATA</span></div>
    <div id="chartLegend" class="chart-legend"></div><div id="candlestickChart" class="chart-wrap"></div>
  </div></section>`;
}
export function mountCandlestick(candles=[],trade=null){
 const el=document.getElementById("candlestickChart");if(!el)return;
 if(chart){try{chart.remove()}catch{}chart=null}
 if(!candles.length||!window.LightweightCharts){el.innerHTML=empty("Chưa tải được dữ liệu nến cho market này.");return}
 const L=window.LightweightCharts;
 chart=L.createChart(el,{width:el.clientWidth,height:el.clientHeight,layout:{background:{type:L.ColorType.Solid,color:"#07111d"},textColor:"#8ea0b8"},grid:{vertLines:{color:"rgba(255,255,255,.04)"},horzLines:{color:"rgba(255,255,255,.04)"}},rightPriceScale:{borderColor:"rgba(255,255,255,.12)"},timeScale:{borderColor:"rgba(255,255,255,.12)",timeVisible:true,secondsVisible:false},crosshair:{mode:1}});
 const cs=chart.addCandlestickSeries({upColor:"#2ee6a6",downColor:"#ff5b78",borderUpColor:"#2ee6a6",borderDownColor:"#ff5b78",wickUpColor:"#2ee6a6",wickDownColor:"#ff5b78"});
 cs.setData(candles.map(c=>({time:c.time,open:Number(c.open),high:Number(c.high),low:Number(c.low),close:Number(c.close)})));
 const closes=candles.map(c=>Number(c.close));const fast=ema(closes,21),slow=ema(closes,50);
 const f=chart.addLineSeries({color:"#45a9ff",lineWidth:2});f.setData(candles.map((c,i)=>({time:c.time,value:fast[i]})));
 const s=chart.addLineSeries({color:"#f5a742",lineWidth:2});s.setData(candles.map((c,i)=>({time:c.time,value:slow[i]})));
 if(trade){
   const lines=[[trade.entryPrice,"Entry","#45a9ff"],[trade.stopPrice,"SL","#ff5b78"],[trade.takeProfit,"TP","#2ee6a6"]];
   for(const [price,title,color] of lines){if(Number.isFinite(Number(price)))cs.createPriceLine({price:Number(price),color,lineWidth:1,lineStyle:2,axisLabelVisible:true,title})}
 }
 chart.timeScale().fitContent();
 const last=candles.at(-1);document.getElementById("chartLegend").innerHTML=`<span><i class="legend-line" style="background:#45a9ff"></i>EMA 21</span><span><i class="legend-line" style="background:#f5a742"></i>EMA 50</span>${last?`<span>O ${last.open} · H ${last.high} · L ${last.low} · C ${last.close}</span>`:""}`;
 new ResizeObserver(()=>{if(chart&&el.clientWidth)chart.applyOptions({width:el.clientWidth,height:el.clientHeight})}).observe(el);
}
