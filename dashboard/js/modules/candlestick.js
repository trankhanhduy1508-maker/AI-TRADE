import{ema,empty,esc}from"../utils.js";

let chart=null;
let chartLibraryPromise=null;

const SYMBOLS=[
 ["EURUSD","EUR/USD"],["GBPUSD","GBP/USD"],["USDJPY","USD/JPY"],["AUDUSD","AUD/USD"],
 ["USDCAD","USD/CAD"],["USDCHF","USD/CHF"],["NZDUSD","NZD/USD"],["XAUUSD","XAU/USD"],
 ["USOIL","US Oil"],["BTCUSD","BTC/USD"],["ETHUSD","ETH/USD"],["US30","US30"],
 ["NAS100","NAS100"],["US500","US500"]
];
const FRAMES=[["15m","M15"],["30m","M30"],["1h","H1"],["4h","H4"],["1d","D1"]];

export function renderCandlestickShell(symbol="EURUSD",timeframe="1h",opened=false,trade=null){
 const symbolOptions=SYMBOLS.map(([value,label])=>`<option value="${value}" ${value===symbol?"selected":""}>${label}</option>`).join("");
 const frameOptions=FRAMES.map(([value,label])=>`<option value="${value}" ${value===timeframe?"selected":""}>${label}</option>`).join("");
 const side=trade?.side||trade?.direction==="UP"?"BUY":trade?.direction==="DOWN"?"SELL":null;
 const status=trade?`<span class="chart-position ${side==="BUY"?"buy":"sell"}">${side||""} · Entry ${trade.entryPrice??"—"} · SL ${trade.stopPrice??"—"} · TP ${trade.takeProfit??"— chưa đặt"}</span>`:"<span class=\"chart-position neutral\">Chưa có vị thế cho market này</span>";
 return `<section class="section">
  <div class="card chart-card">
    <div class="chart-toolbar">
      <div class="left">
        <select id="chartSymbol" aria-label="Market">${symbolOptions}</select>
        <select id="chartTimeframe" aria-label="Khung thời gian">${frameOptions}</select>
      </div>
      <button id="chartToggle" class="chart-toggle" type="button">${opened?"Ẩn biểu đồ":"Mở biểu đồ"}</button>
    </div>
    <div class="chart-trade-summary">${status}</div>
    <div id="chartContent" class="${opened?"":"hidden"}">
      <div id="chartLegend" class="chart-legend"></div>
      <div id="candlestickChart" class="chart-wrap">${opened?"":empty("Biểu đồ chỉ tải khi bạn mở.")}</div>
    </div>
  </div>
 </section>`;
}

export async function ensureChartLibrary(){
 if(window.LightweightCharts)return window.LightweightCharts;
 if(chartLibraryPromise)return chartLibraryPromise;
 chartLibraryPromise=new Promise((resolve,reject)=>{
   const s=document.createElement("script");
   s.src="https://cdn.jsdelivr.net/npm/lightweight-charts@5.0.8/dist/lightweight-charts.standalone.production.js";
   s.async=true;
   s.onload=()=>resolve(window.LightweightCharts);
   s.onerror=()=>reject(new Error("CHART_LIBRARY_LOAD_FAILED"));
   document.head.appendChild(s);
 });
 return chartLibraryPromise;
}

function addSeriesCompat(L,kind,options){
 if(kind==="candles"){
   if(L.CandlestickSeries)return chart.addSeries(L.CandlestickSeries,options);
   return chart.addCandlestickSeries(options);
 }
 if(L.LineSeries)return chart.addSeries(L.LineSeries,options);
 return chart.addLineSeries(options);
}

export async function mountCandlestick(candles=[],trade=null){
 const el=document.getElementById("candlestickChart");
 if(!el)return;
 if(chart){try{chart.remove()}catch{}chart=null}
 if(!candles.length){
   el.innerHTML=empty("Chưa tải được dữ liệu nến cho market/khung thời gian này.");
   return;
 }
 let L;
 try{L=await ensureChartLibrary()}catch{
   el.innerHTML=empty("Không tải được thư viện biểu đồ.");
   return;
 }

 chart=L.createChart(el,{
   width:Math.max(el.clientWidth,320),
   height:Math.max(el.clientHeight,420),
   layout:{background:{type:L.ColorType?.Solid??"solid",color:"#07111d"},textColor:"#9badc6",fontSize:12},
   grid:{vertLines:{color:"rgba(255,255,255,.035)"},horzLines:{color:"rgba(255,255,255,.035)"}},
   rightPriceScale:{borderColor:"rgba(255,255,255,.12)",scaleMargins:{top:.08,bottom:.08},autoScale:true},
   timeScale:{
     borderColor:"rgba(255,255,255,.12)",timeVisible:true,secondsVisible:false,
     rightOffset:6,barSpacing:11,minBarSpacing:4,fixLeftEdge:false,fixRightEdge:false,
     lockVisibleTimeRangeOnResize:true
   },
   crosshair:{mode:L.CrosshairMode?.Normal??0},
   handleScroll:{mouseWheel:true,pressedMouseMove:true,horzTouchDrag:true,vertTouchDrag:false},
   handleScale:{axisPressedMouseMove:true,mouseWheel:true,pinch:true},
   kineticScroll:{mouse:true,touch:true}
 });

 const cs=addSeriesCompat(L,"candles",{
   upColor:"#18d7a0",downColor:"#ff5b78",
   borderVisible:false,wickUpColor:"#18d7a0",wickDownColor:"#ff5b78",
   priceLineVisible:false,lastValueVisible:true
 });
 cs.setData(candles.map(c=>({time:c.time,open:Number(c.open),high:Number(c.high),low:Number(c.low),close:Number(c.close)})));

 const closes=candles.map(c=>Number(c.close));
 const fast=ema(closes,21),slow=ema(closes,50);
 const f=addSeriesCompat(L,"line",{color:"#45a9ff",lineWidth:2,priceLineVisible:false,lastValueVisible:false});
 f.setData(candles.map((c,i)=>({time:c.time,value:fast[i]})));
 const s=addSeriesCompat(L,"line",{color:"#f5a742",lineWidth:2,priceLineVisible:false,lastValueVisible:false});
 s.setData(candles.map((c,i)=>({time:c.time,value:slow[i]})));

 if(trade){
   const lines=[
     [trade.entryPrice,trade.side||trade.direction==="UP"?"BUY Entry":"SELL Entry","#45a9ff"],
     [trade.stopPrice,"SL","#ff5b78"],
     [trade.takeProfit,"TP","#2ee6a6"]
   ];
   for(const [price,title,color] of lines){
     if(Number.isFinite(Number(price))){
       cs.createPriceLine({price:Number(price),color,lineWidth:2,lineStyle:2,axisLabelVisible:true,title});
     }
   }
   const entryTime=trade.entryTs?Math.floor(new Date(trade.entryTs).getTime()/1000):candles.at(-1)?.time;
   const marker={time:entryTime,position:(trade.side==="SELL"||trade.direction==="DOWN")?"aboveBar":"belowBar",color:(trade.side==="SELL"||trade.direction==="DOWN")?"#ff5b78":"#2ee6a6",shape:(trade.side==="SELL"||trade.direction==="DOWN")?"arrowDown":"arrowUp",text:(trade.side||trade.direction==="UP"?"BUY":"SELL")};
   try{
     if(typeof L.createSeriesMarkers==="function")L.createSeriesMarkers(cs,[marker]);
     else if(typeof cs.setMarkers==="function")cs.setMarkers([marker]);
   }catch{}
 }

 const barsToShow=Math.min(72,candles.length);
 if(barsToShow>=20){
   chart.timeScale().setVisibleLogicalRange({from:candles.length-barsToShow-2,to:candles.length+4});
 }else{
   chart.timeScale().fitContent();
 }

 const last=candles.at(-1);
 const legend=document.getElementById("chartLegend");
 if(legend)legend.innerHTML=`<span><i class="legend-line" style="background:#45a9ff"></i>EMA 21</span>
 <span><i class="legend-line" style="background:#f5a742"></i>EMA 50</span>
 ${last?`<span>O ${Number(last.open).toFixed(5)} · H ${Number(last.high).toFixed(5)} · L ${Number(last.low).toFixed(5)} · C ${Number(last.close).toFixed(5)}</span>`:""}`;

 new ResizeObserver(()=>{
   if(chart&&el.clientWidth)chart.applyOptions({width:el.clientWidth,height:Math.max(el.clientHeight,420)});
 }).observe(el);
}

export function prewarmChartLibrary(){
 const warm=()=>ensureChartLibrary().catch(()=>{});
 if("requestIdleCallback" in window)window.requestIdleCallback(warm,{timeout:2500});
 else setTimeout(warm,1200);
}
