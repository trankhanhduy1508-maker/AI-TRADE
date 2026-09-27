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
import{renderCandlestickShell,mountCandlestick,prewarmChartLibrary}from"./modules/candlestick.js";
import{renderPerformance}from"./modules/performance.js";
import{renderSafety}from"./modules/safety.js";
import{renderTesterAdmin}from"./modules/tester-admin.js";
import{getGoogleUser,signInWithGoogle,signOutGoogle}from"./auth.js";

const token=new URLSearchParams(location.search).get("t")||"";
const api=new DashboardApi(token);
const store=new DashboardStore();
const cacheKey="cws-ai-trade-cache-"+token.slice(0,12);

function skeletonCard(title){
  return `<section class="section"><div class="section-head"><h2>${title}</h2></div><div class="card card-pad loading-card"><i></i><i></i><i></i></div></section>`;
}

function shell(){
  document.getElementById("app").innerHTML=`
    ${renderHeader()}
    <div id="errors">${renderError("")}</div>
    <div id="testerAdmin"></div>
    <div id="currentTrade">${skeletonCard("Trạng thái giao dịch")}</div>
    <div id="progress">${skeletonCard("Tiến độ")}</div>
    <div id="pipeline"></div>
    <div id="recentTrades">${skeletonCard("Giao dịch gần đây")}</div>
    <div id="trainingArena">${skeletonCard("Training Arena")}</div>
    <div id="journal"></div>
    <div id="chart">${renderCandlestickShell(CONFIG.defaultSymbol,CONFIG.defaultTimeframe,false,null)}</div>
    <div id="performance"></div>
    <div id="safety">${skeletonCard("MT5 DEMO")}</div>
    <div class="footer"><span id="updated">Đang đồng bộ dữ liệu…</span></div>`;
  bindChartControls();
  bindGoogleControls();
}

function selectedTrade(state){
  const symbol=state.selectedSymbol||CONFIG.defaultSymbol;
  if(state.currentTrade?.symbol===symbol)return state.currentTrade;
  const p=state.arena?.positions?.find(x=>x.symbol===symbol);
  if(!p)return null;
  return {
    symbol:p.symbol,
    side:p.side,
    direction:p.direction,
    entryTs:p.entryTs,
    entryPrice:p.entryPrice,
    currentPrice:p.lastMarkPrice,
    stopPrice:p.stopPrice,
    takeProfit:p.takeProfit??null,
    floatingR:p.unrealizedR,
    volumeLabel:p.volumeLabel??"Paper"
  };
}

function render(){
  const s=store.get(),o=s.overview;if(!o)return;
  document.querySelector(".topbar")?.remove();
  document.getElementById("app").insertAdjacentHTML("afterbegin",renderHeader(o.viewer??{},s.googleUser??null));
  document.getElementById("testerAdmin").innerHTML=s.testerAdmin?renderTesterAdmin(s.testerAdmin):"";
  document.getElementById("currentTrade").innerHTML=renderCurrentTrade(s.currentTrade);
  document.getElementById("progress").innerHTML=renderProgress(o.evaluation,CONFIG.sampleTargets);
  document.getElementById("pipeline").innerHTML=o.viewer?.founder?renderPipeline(o.crons):"";
  document.getElementById("recentTrades").innerHTML=renderRecentTrades(s.trades);
  document.getElementById("trainingArena").innerHTML=renderTrainingArena(s.arena??{});
  document.getElementById("journal").innerHTML=o.viewer?.founder?renderJournal(s.journal):"";
  const trade=selectedTrade(s);
  document.getElementById("chart").innerHTML=renderCandlestickShell(s.selectedSymbol,s.selectedTimeframe,Boolean(s.chartOpened),trade);
  document.getElementById("performance").innerHTML=o.viewer?.founder?renderPerformance(o.evaluation):"";
  document.getElementById("safety").innerHTML=renderSafety(o.mt5,o.gates);
  document.getElementById("updated").textContent="Cập nhật: "+new Date(o.updatedAt).toLocaleString("vi-VN")+" · refresh 60 giây";
  if(s.chartOpened)mountCandlestick(s.candles,trade);
  bindChartControls();
  bindTesterAdmin();
  bindGoogleControls();
}

function saveCache(){
  try{
    const s=store.get();
    localStorage.setItem(cacheKey,JSON.stringify({
      savedAt:Date.now(),
      overview:s.overview,testerAdmin:s.testerAdmin,currentTrade:s.currentTrade,
      trades:s.trades,journal:s.journal,arena:s.arena,
      selectedSymbol:s.selectedSymbol,selectedTimeframe:s.selectedTimeframe
    }));
  }catch{}
}

function hydrateCache(){
  try{
    const raw=localStorage.getItem(cacheKey);if(!raw)return;
    const cached=JSON.parse(raw);
    if(!cached?.savedAt||Date.now()-cached.savedAt>10*60*1000)return;
    store.set({...cached,chartOpened:false,candles:[]});
    render();
  }catch{}
}

async function reloadChart(){
  const s=store.get();
  const symbol=document.getElementById("chartSymbol")?.value||s.selectedSymbol||CONFIG.defaultSymbol;
  const timeframe=document.getElementById("chartTimeframe")?.value||s.selectedTimeframe||CONFIG.defaultTimeframe;
  const holder=document.getElementById("candlestickChart");
  if(holder)holder.innerHTML='<div class="chart-loading">Đang tải '+symbol+' · '+timeframe.toUpperCase()+'…</div>';
  try{
    const candles=await api.getFeature("candles",{symbol,timeframe,limit:220});
    store.set({candles:candles.candles??[],selectedSymbol:symbol,selectedTimeframe:timeframe,chartOpened:true});
    const current=store.get();
    const trade=selectedTrade(current);
    document.getElementById("chart").innerHTML=renderCandlestickShell(symbol,timeframe,true,trade);
    await mountCandlestick(current.candles,trade);
    bindChartControls();
  }catch(e){
    const chart=document.getElementById("candlestickChart");
    if(chart)chart.innerHTML='<div class="empty-state">Không tải được dữ liệu cho market/khung thời gian này.</div>';
  }
}

function bindChartControls(){
  const tf=document.getElementById("chartTimeframe");
  if(tf&&!tf.dataset.bound){
    tf.dataset.bound="1";
    tf.addEventListener("change",()=>{
      store.set({selectedTimeframe:tf.value});
      if(store.get().chartOpened)reloadChart();
      else render();
    });
  }
  const symbol=document.getElementById("chartSymbol");
  if(symbol&&!symbol.dataset.bound){
    symbol.dataset.bound="1";
    symbol.addEventListener("change",()=>{
      store.set({selectedSymbol:symbol.value,candles:[]});
      if(store.get().chartOpened)reloadChart();
      else render();
    });
  }
  const toggle=document.getElementById("chartToggle");
  if(toggle&&!toggle.dataset.bound){
    toggle.dataset.bound="1";
    toggle.addEventListener("click",async()=>{
      const s=store.get();
      if(s.chartOpened){
        store.set({chartOpened:false});
        render();
      }else{
        await reloadChart();
      }
    });
  }
}

function bindGoogleControls(){
  const login=document.getElementById("googleLoginBtn");
  if(login&&!login.dataset.bound){
    login.dataset.bound="1";
    login.addEventListener("click",signInWithGoogle);
  }
  const account=document.getElementById("googleAccountBtn");
  if(account&&!account.dataset.bound){
    account.dataset.bound="1";
    account.addEventListener("click",signOutGoogle);
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
      }finally{btn.disabled=false}
    });
  });
}

async function load(){
  const error=document.getElementById("errorBox");
  if(error)error.style.display="none";
  try{
    if(!token)throw new Error("Thiếu token dashboard trong link.");

    const googlePromise=getGoogleUser().catch(()=>null);
    const overviewPromise=api.getOverview();

    const overview=await overviewPromise;
    store.set({overview});
    render();

    const requests=[
      googlePromise,
      overview.viewer?.founder?api.getFeature("admin-testers").catch(()=>({testers:[]})):Promise.resolve(null),
      api.getFeature("current").catch(()=>({currentTrade:null})),
      api.getFeature("trades",{limit:12}).catch(()=>({trades:[]})),
      overview.viewer?.founder?api.getFeature("journal",{limit:12}).catch(()=>({journal:[]})):Promise.resolve({journal:[]}),
      api.getFeature("arena").catch(()=>({positions:[],trades:[],journal:[]}))
    ];
    const [googleUser,testerAdmin,current,trades,journal,arena]=await Promise.all(requests);
    const currentState=store.get();
    const symbol=current.currentTrade?.symbol||currentState.selectedSymbol||CONFIG.defaultSymbol;

    store.set({
      googleUser,
      testerAdmin,
      currentTrade:current.currentTrade??null,
      trades:trades.trades??[],
      journal:journal.journal??[],
      arena,
      selectedSymbol:symbol
    });
    render();
    saveCache();
  }catch(e){
    const box=document.getElementById("errorBox");
    if(box){box.textContent="Không tải được dashboard: "+e.message;box.style.display="block"}
  }
}

shell();
hydrateCache();
prewarmChartLibrary();
load();
setInterval(load,CONFIG.refreshMs);
