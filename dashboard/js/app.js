import{CONFIG}from"./config.js";
import{DashboardApi}from"./api.js";
import{DashboardStore}from"./store.js";
import{renderHeader,renderError}from"./modules/header.js";
import{renderCurrentTrade}from"./modules/current-trade.js";
import{renderProgress}from"./modules/progress.js";
import{renderPipeline}from"./modules/pipeline.js";
import{renderRecentTrades}from"./modules/recent-trades.js";
import{renderTrainingArena}from"./modules/training-arena.js";
import{renderJournal}from"./modules/journal.js";
import{renderCandlestickShell,mountCandlestick}from"./modules/candlestick.js";
import{renderPerformance}from"./modules/performance.js";
import{renderSafety}from"./modules/safety.js";
import{renderTesterAdmin}from"./modules/tester-admin.js";

const token=new URLSearchParams(location.search).get("t")||"";
const api=new DashboardApi(token);
const store=new DashboardStore();

function shell(){
  document.getElementById("app").innerHTML=`
    ${renderHeader()}
    <div id="errors">${renderError("")}</div>
    <div id="testerAdmin"></div>
    <div id="currentTrade"></div>
    <div id="progress"></div>
    <div id="pipeline"></div>
    <div id="recentTrades"></div>
    <div id="trainingArena"></div>
    <div id="journal"></div>
    <div id="chart"></div>
    <div id="performance"></div>
    <div id="safety"></div>
    <div class="footer"><span id="updated">Đang tải dữ liệu…</span></div>`;
}

function render(){
  const s=store.get(),o=s.overview;if(!o)return;
  document.querySelector(".topbar")?.remove();
  document.getElementById("app").insertAdjacentHTML("afterbegin",renderHeader(o.viewer??{}));
  document.getElementById("testerAdmin").innerHTML=s.testerAdmin?renderTesterAdmin(s.testerAdmin):""; 
  document.getElementById("currentTrade").innerHTML=renderCurrentTrade(s.currentTrade);
  document.getElementById("progress").innerHTML=renderProgress(o.evaluation,CONFIG.sampleTargets);
  document.getElementById("pipeline").innerHTML=o.viewer?.founder?renderPipeline(o.crons):"";
  document.getElementById("recentTrades").innerHTML=renderRecentTrades(s.trades);
  document.getElementById("trainingArena").innerHTML=renderTrainingArena(s.arena??{});
  document.getElementById("journal").innerHTML=o.viewer?.founder?renderJournal(s.journal):"";
  document.getElementById("chart").innerHTML=renderCandlestickShell(s.selectedSymbol,s.selectedTimeframe,Boolean(s.chartOpened));
  document.getElementById("performance").innerHTML=o.viewer?.founder?renderPerformance(o.evaluation):"";
  document.getElementById("safety").innerHTML=renderSafety(o.mt5,o.gates);
  document.getElementById("updated").textContent="Cập nhật: "+new Date(o.updatedAt).toLocaleString("vi-VN")+" · refresh 30 giây";
  if(s.chartOpened)mountCandlestick(s.candles,s.currentTrade);
  bindChartControls();
  bindTesterAdmin();
}

async function reloadChart(){
  const s=store.get();
  const symbol=document.getElementById("chartSymbol")?.value||s.selectedSymbol||CONFIG.defaultSymbol;
  const timeframe=document.getElementById("chartTimeframe")?.value||s.selectedTimeframe||CONFIG.defaultTimeframe;
  try{
    const candles=await api.getFeature("candles",{symbol,timeframe,limit:160});
    store.set({candles:candles.candles??[],selectedSymbol:symbol,selectedTimeframe:timeframe,chartOpened:true});
    const current=store.get();
    document.getElementById("chart").innerHTML=renderCandlestickShell(symbol,timeframe,true);
    mountCandlestick(current.candles,current.currentTrade);
    bindChartControls();
  }catch(e){
    const chart=document.getElementById("candlestickChart");
    if(chart)chart.innerHTML='<div class="empty-state">Không tải được dữ liệu cho khung thời gian này.</div>';
  }
}

function bindChartControls(){
  const tf=document.getElementById("chartTimeframe");
  if(tf&&!tf.dataset.bound){
    tf.dataset.bound="1";
    tf.addEventListener("change",()=>{
      if(store.get().chartOpened)reloadChart();
      else store.set({selectedTimeframe:tf.value});
    });
  }
  const symbol=document.getElementById("chartSymbol");
  if(symbol&&!symbol.dataset.bound){
    symbol.dataset.bound="1";
    symbol.addEventListener("change",()=>{
      if(store.get().chartOpened)reloadChart();
      else store.set({selectedSymbol:symbol.value});
    });
  }
  const toggle=document.getElementById("chartToggle");
  if(toggle&&!toggle.dataset.bound){
    toggle.dataset.bound="1";
    toggle.addEventListener("click",async()=>{
      const s=store.get();
      if(s.chartOpened){
        store.set({chartOpened:false});
        const current=store.get();
        document.getElementById("chart").innerHTML=renderCandlestickShell(current.selectedSymbol,current.selectedTimeframe,false);
        bindChartControls();
      }else{
        await reloadChart();
      }
    });
  }
}

function bindTesterAdmin(){
  document.querySelectorAll(".tester-actions button").forEach(btn=>{
    if(btn.dataset.bound)return;
    btn.dataset.bound="1";
    btn.addEventListener("click",async()=>{
      const row=btn.closest(".tester-row");
      const tokenId=Number(row?.dataset.tokenId||0);
      const action=btn.dataset.action;
      if(!tokenId||!action)return;
      btn.disabled=true;
      try{
        await api.founderAction(tokenId,action);
        await load();
      }finally{
        btn.disabled=false;
      }
    });
  });
}

async function load(){
  const error=document.getElementById("errorBox");
  if(error)error.style.display="none";
  try{
    if(!token)throw new Error("Thiếu token dashboard trong link.");
    const overview=await api.getOverview();
    const testerAdmin=overview.viewer?.founder?await api.getFeature("admin-testers").catch(()=>({testers:[]})):null;
    const current=await api.getFeature("current").catch(()=>({currentTrade:null}));
    const trades=await api.getFeature("trades",{limit:12}).catch(()=>({trades:[]}));
    const journal=await api.getFeature("journal",{limit:12}).catch(()=>({journal:[]}));
    const arena=await api.getFeature("arena").catch(()=>({positions:[],trades:[],journal:[]}));
    const symbol=current.currentTrade?.symbol||trades.trades?.[0]?.symbol||store.get().selectedSymbol||CONFIG.defaultSymbol;
    store.set({overview,testerAdmin,currentTrade:current.currentTrade??null,trades:trades.trades??[],journal:journal.journal??[],arena,selectedSymbol:symbol});
    render();
  }catch(e){
    const box=document.getElementById("errorBox");if(box){box.textContent="Không tải được dashboard: "+e.message;box.style.display="block"}
  }
}

shell();
load();
setInterval(load,CONFIG.refreshMs);
