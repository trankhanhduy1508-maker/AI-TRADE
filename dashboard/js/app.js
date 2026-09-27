import{CONFIG}from"./config.js";
import{DashboardApi}from"./api.js";
import{DashboardStore}from"./store.js";
import{renderHeader,renderError}from"./modules/header.js";
import{renderCurrentTrade}from"./modules/current-trade.js";
import{renderProgress}from"./modules/progress.js";
import{renderPipeline}from"./modules/pipeline.js";
import{renderRecentTrades}from"./modules/recent-trades.js";
import{renderJournal}from"./modules/journal.js";
import{renderCandlestickShell,mountCandlestick}from"./modules/candlestick.js";
import{renderPerformance}from"./modules/performance.js";
import{renderSafety}from"./modules/safety.js";

const token=new URLSearchParams(location.search).get("t")||"";
const api=new DashboardApi(token);
const store=new DashboardStore();

function shell(){
  document.getElementById("app").innerHTML=`
    ${renderHeader()}
    <div id="errors">${renderError("")}</div>
    <div id="currentTrade"></div>
    <div id="progress"></div>
    <div id="pipeline"></div>
    <div id="recentTrades"></div>
    <div id="journal"></div>
    <div id="chart"></div>
    <div id="performance"></div>
    <div id="safety"></div>
    <div class="footer"><span id="updated">Đang tải dữ liệu…</span></div>`;
}

function render(){
  const s=store.get(),o=s.overview;if(!o)return;
  document.getElementById("currentTrade").innerHTML=renderCurrentTrade(s.currentTrade);
  document.getElementById("progress").innerHTML=renderProgress(o.evaluation,CONFIG.sampleTargets);
  document.getElementById("pipeline").innerHTML=renderPipeline(o.crons);
  document.getElementById("recentTrades").innerHTML=renderRecentTrades(s.trades);
  document.getElementById("journal").innerHTML=renderJournal(s.journal);
  document.getElementById("chart").innerHTML=renderCandlestickShell(s.selectedSymbol,s.selectedTimeframe);
  document.getElementById("performance").innerHTML=renderPerformance(o.evaluation);
  document.getElementById("safety").innerHTML=renderSafety(o.mt5,o.gates);
  document.getElementById("updated").textContent="Cập nhật: "+new Date(o.updatedAt).toLocaleString("vi-VN")+" · refresh 30 giây";
  mountCandlestick(s.candles,s.currentTrade);
}

async function load(){
  const error=document.getElementById("errorBox");
  if(error)error.style.display="none";
  try{
    if(!token)throw new Error("Thiếu token dashboard trong link.");
    const overview=await api.getOverview();
    const current=await api.getFeature("current").catch(()=>({currentTrade:null}));
    const trades=await api.getFeature("trades",{limit:12}).catch(()=>({trades:[]}));
    const journal=await api.getFeature("journal",{limit:12}).catch(()=>({journal:[]}));
    const symbol=current.currentTrade?.symbol||trades.trades?.[0]?.symbol||store.get().selectedSymbol||CONFIG.defaultSymbol;
    const candles=await api.getFeature("candles",{symbol,timeframe:store.get().selectedTimeframe,limit:160}).catch(()=>({candles:[]}));
    store.set({overview,currentTrade:current.currentTrade??null,trades:trades.trades??[],journal:journal.journal??[],candles:candles.candles??[],selectedSymbol:symbol});
    render();
  }catch(e){
    const box=document.getElementById("errorBox");if(box){box.textContent="Không tải được dashboard: "+e.message;box.style.display="block"}
  }
}

shell();
load();
setInterval(load,CONFIG.refreshMs);
