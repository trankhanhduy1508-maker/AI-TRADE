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
import{renderAdminStatus}from"./modules/admin-status.js";
import{renderAdminPositions}from"./modules/admin-positions.js";
import{getGoogleUser,signInWithGoogle,signOutGoogle}from"./auth.js";

const params=new URLSearchParams(location.search);
const token=params.get("t")||"";
const adminPreview=params.get("mode")==="admin-preview";
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
    <div id="adminStatus">${skeletonCard("System status")}</div>
    <div id="adminPositions"></div>
    <div id="currentTrade">${skeletonCard("Trạng thái giao dịch")}</div>
    <div id="chart">${renderCandlestickShell(CONFIG.defaultSymbol,CONFIG.defaultTimeframe,false,null)}</div>
    <div id="progress">${skeletonCard("Tiến độ")}</div>
    <div id="safety">${skeletonCard("MT5 DEMO")}</div>
    <div id="pipeline"></div>
    <div id="trainingArena">${skeletonCard("Training Arena")}</div>
    <div id="performance"></div>
    <div id="recentTrades">${skeletonCard("Giao dịch gần đây")}</div>
    <div id="journal"></div>
    <div id="testerAdmin"></div>
    <div class="footer"><span id="updated">Đang đồng bộ dữ liệu…</span><span id="latency"></span></div>`;
  bindChartControls();
  bindGoogleControls();
}

function selectedTrade(state){
  const symbol=state.selectedSymbol||CONFIG.defaultSymbol;
  let trade=null;
  if(state.currentTrade?.symbol===symbol)trade={...state.currentTrade};
  if(!trade){
    const p=state.shadowPositions?.find(x=>x.symbol===symbol);
    if(p)trade={
      symbol:p.symbol,
      side:p.side??(p.direction==="UP"?"BUY":"SELL"),
      direction:p.direction,
      entryTs:p.entryTs,
      entryPrice:p.entryPrice,
      stopPrice:p.stopPrice,
      takeProfit:p.takeProfit??null,
      floatingPL:null,
      floatingR:null,
      volumeLabel:p.syntheticVolume!=null?"Shadow "+Number(p.syntheticVolume).toFixed(1):"—",
      mode:"SHADOW_ONLY"
    };
  }
  if(!trade){
    const p=state.arena?.positions?.find(x=>x.symbol===symbol);
    if(p)trade={
      symbol:p.symbol,side:p.side,direction:p.direction,entryTs:p.entryTs,
      entryPrice:p.entryPrice,currentPrice:p.lastMarkPrice,stopPrice:p.stopPrice,
      takeProfit:p.takeProfit??null,floatingR:p.unrealizedR,
      volumeLabel:p.volumeLabel??"Paper",mode:"PAPER_TRAINING_ARENA"
    };
  }
  if(!trade)return null;
  trade.symbolSpec=state.symbolSpecs?.[symbol]??null;
  const latest=state.candles?.at(-1);
  if(latest&&state.selectedSymbol===symbol)trade.currentPrice=Number(latest.close);
  const entry=Number(trade.entryPrice),stop=Number(trade.stopPrice),mark=Number(trade.currentPrice);
  const risk=Math.abs(entry-stop);
  if(Number.isFinite(mark)&&Number.isFinite(entry)&&risk>0){
    trade.floatingR=(trade.side==="SELL"||trade.direction==="DOWN")?(entry-mark)/risk:(mark-entry)/risk;
  }
  return trade;
}

function render(){
  const s=store.get(),o=s.overview;if(!o)return;
  const founder=Boolean(o.viewer?.founder);
  document.body.classList.toggle("founder-console",founder);
  document.querySelector(".topbar")?.remove();
  document.getElementById("app").insertAdjacentHTML("afterbegin",renderHeader(o.viewer??{},s.googleUser??null));
  document.getElementById("adminStatus").innerHTML=founder?renderAdminStatus(o,s.shadowPositions??[]):"";
  document.getElementById("adminPositions").innerHTML=founder?renderAdminPositions(s.shadowPositions??[],s.selectedSymbol):"";
  const trade=selectedTrade(s);
  document.getElementById("currentTrade").innerHTML=renderCurrentTrade(trade);
  document.getElementById("chart").innerHTML=renderCandlestickShell(s.selectedSymbol,s.selectedTimeframe,Boolean(s.chartOpened),trade);
  document.getElementById("progress").innerHTML=renderProgress(o.evaluation,CONFIG.sampleTargets);
  document.getElementById("safety").innerHTML=renderSafety(o.mt5,o.gates);
  document.getElementById("pipeline").innerHTML=founder?renderPipeline(o.crons):"";
  document.getElementById("trainingArena").innerHTML=renderTrainingArena(s.arena??{});
  document.getElementById("performance").innerHTML=founder?renderPerformance(o.evaluation):"";
  document.getElementById("recentTrades").innerHTML=renderRecentTrades(s.trades);
  document.getElementById("journal").innerHTML=founder?renderJournal(s.journal):"";
  document.getElementById("testerAdmin").innerHTML=founder&&s.testerAdmin?renderTesterAdmin(s.testerAdmin):"";
  document.getElementById("updated").textContent="Cập nhật: "+new Date(o.updatedAt).toLocaleString("vi-VN")+" · refresh 60 giây";
  const timings=api.getTimings();
  document.getElementById("latency").textContent=Object.keys(timings).length?" · API "+Object.entries(timings).map(([k,v])=>k+" "+v+"ms").join(" · "):"";
  if(s.chartOpened)mountCandlestick(s.candles,trade);
  bindChartControls();
  bindAdminPositions();
  bindTesterAdmin();
  bindGoogleControls();
}

function saveCache(){
  try{
    const s=store.get();
    localStorage.setItem(cacheKey,JSON.stringify({
      savedAt:Date.now(),overview:s.overview,testerAdmin:s.testerAdmin,currentTrade:s.currentTrade,
      shadowPositions:s.shadowPositions,trades:s.trades,journal:s.journal,arena:s.arena,
      symbolSpecs:s.symbolSpecs,
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
  if(adminPreview){
    const symbol=document.getElementById("chartSymbol")?.value||s.selectedSymbol||CONFIG.defaultSymbol;
    const timeframe=document.getElementById("chartTimeframe")?.value||s.selectedTimeframe||CONFIG.defaultTimeframe;
    document.getElementById("chart").innerHTML=renderCandlestickShell(symbol,timeframe,true,null);
    const holder=document.getElementById("candlestickChart");
    if(holder)holder.innerHTML='<div class="chart-loading">Đang tải market data công khai…</div>';
    try{
      const u=new URL(CONFIG.apiBase);
      u.searchParams.set("format","preview-candles");
      u.searchParams.set("symbol",symbol);
      u.searchParams.set("timeframe",timeframe);
      const r=await fetch(u,{cache:"no-store"});
      if(!r.ok)throw new Error("PREVIEW_CANDLES_"+r.status);
      const data=await r.json();
      const candles=data.candles??[];
      store.set({selectedSymbol:symbol,selectedTimeframe:timeframe,chartOpened:true,candles});
      await mountCandlestick(candles,null);
    }catch{
      if(holder)holder.innerHTML='<div class="empty-state">Admin Preview — market data hiện không tải được.</div>';
    }
    bindChartControls();
    return;
  }
  const symbol=document.getElementById("chartSymbol")?.value||s.selectedSymbol||CONFIG.defaultSymbol;
  const timeframe=document.getElementById("chartTimeframe")?.value||s.selectedTimeframe||CONFIG.defaultTimeframe;
  const holder=document.getElementById("candlestickChart");
  if(holder)holder.innerHTML='<div class="chart-loading">Đang tải '+symbol+' · '+timeframe.toUpperCase()+'…</div>';
  try{
    const [candles,specResult]=await Promise.all([
      api.getFeature("candles",{symbol,timeframe,limit:220}),
      api.getFeature("symbol-spec",{symbol}).catch(()=>({supported:false,spec:null,unavailableReason:"SPEC_REQUEST_FAILED"}))
    ]);
    const prior=store.get();
    const symbolSpec=specResult?.spec
      ?{...specResult.spec,supported:true}
      :{supported:false,reason:specResult?.unavailableReason??"SPEC_UNAVAILABLE"};
    store.set({
      candles:candles.candles??[],
      symbolSpecs:{...(prior.symbolSpecs??{}),[symbol]:symbolSpec},
      selectedSymbol:symbol,selectedTimeframe:timeframe,chartOpened:true
    });
    const current=store.get();
    const trade=selectedTrade(current);
    document.getElementById("chart").innerHTML=renderCandlestickShell(symbol,timeframe,true,trade);
    await mountCandlestick(current.candles,trade);
    bindChartControls();
    bindAdminPositions();
    const latency=document.getElementById("latency");
    if(latency){const timings=api.getTimings();latency.textContent=" · API "+Object.entries(timings).map(([k,v])=>k+" "+v+"ms").join(" · ")}
  }catch{
    const chart=document.getElementById("candlestickChart");
    if(chart)chart.innerHTML='<div class="empty-state">Không tải được dữ liệu cho market/khung thời gian này.</div>';
  }
}

function bindChartControls(){
  const tf=document.getElementById("chartTimeframe");
  if(tf&&!tf.dataset.bound){
    tf.dataset.bound="1";
    tf.addEventListener("change",()=>{store.set({selectedTimeframe:tf.value});reloadChart()});
  }
  const symbol=document.getElementById("chartSymbol");
  if(symbol&&!symbol.dataset.bound){
    symbol.dataset.bound="1";
    symbol.addEventListener("change",()=>{store.set({selectedSymbol:symbol.value,candles:[]});reloadChart()});
  }
  const toggle=document.getElementById("chartToggle");
  if(toggle&&!toggle.dataset.bound){
    toggle.dataset.bound="1";
    toggle.addEventListener("click",async()=>{
      if(store.get().chartOpened){store.set({chartOpened:false});render()}
      else await reloadChart();
    });
  }
}

function bindAdminPositions(){
  document.querySelectorAll(".position-row[data-symbol]").forEach(btn=>{
    if(btn.dataset.bound)return;
    btn.dataset.bound="1";
    btn.addEventListener("click",()=>{
      store.set({selectedSymbol:btn.dataset.symbol,candles:[],chartOpened:true});
      reloadChart();
    });
  });
}

function bindGoogleControls(){
  const login=document.getElementById("googleLoginBtn");
  if(login&&!login.dataset.bound){login.dataset.bound="1";login.addEventListener("click",signInWithGoogle)}
  const account=document.getElementById("googleAccountBtn");
  if(account&&!account.dataset.bound){account.dataset.bound="1";account.addEventListener("click",signOutGoogle)}
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
      try{await api.founderAction(tokenId,action);await load()}
      finally{btn.disabled=false}
    });
  });
}

async function load(){
  const error=document.getElementById("errorBox");
  if(error)error.style.display="none";
  try{
    if(adminPreview){
      const previewOverview={
        preview:true,
        viewer:{founder:true,accessRole:"FOUNDER",subjectLabel:"Founder Preview"},
        evaluation:{state:"UNAVAILABLE"},
        mt5:{connected:false},
        gates:{liveMoneyLocked:true},
        crons:[],
        updatedAt:new Date().toISOString()
      };
      store.set({
        overview:previewOverview,
        testerAdmin:null,currentTrade:null,shadowPositions:[],
        trades:[],journal:[],arena:{positions:[],trades:[],journal:[]},
        selectedSymbol:CONFIG.defaultSymbol,selectedTimeframe:CONFIG.defaultTimeframe,
        chartOpened:true
      });
      render();
      const pos=document.getElementById("adminPositions");
      if(pos)pos.innerHTML='<section class="section admin-priority"><div class="section-head"><h2>Current open positions</h2></div><div class="card card-pad"><div class="empty-state">Admin Preview — vị thế runtime bị ẩn cho đến khi xác thực Founder.</div></div></section>';
      const trade=document.getElementById("currentTrade");
      if(trade)trade.innerHTML='<section class="section"><div class="section-head"><h2>Trạng thái giao dịch hiện tại</h2></div><div class="card card-pad"><div class="empty-state">Admin Preview — Entry / SL / TP / Lot / P&L unavailable khi chưa xác thực Founder.</div></div></section>';
      const box=document.getElementById("errorBox");
      if(box){box.textContent="ADMIN PREVIEW — giao diện Founder/Admin thật, dữ liệu runtime được ẩn cho đến khi xác thực Founder.";box.style.display="block"}
      const holder=document.getElementById("candlestickChart");
      if(holder)holder.innerHTML='<div class="empty-state">Admin Preview — chart runtime unavailable khi chưa xác thực Founder.</div>';
      return;
    }
    if(!token)throw new Error("Thiếu token dashboard trong link.");

    const googlePromise=getGoogleUser().catch(()=>null);
    const overviewPromise=api.getOverview();
    const currentPromise=api.getFeature("current").catch(()=>({currentTrade:null,openPositions:[]}));
    const tradesPromise=api.getFeature("trades",{limit:12}).catch(()=>({trades:[]}));
    const arenaPromise=api.getFeature("arena").catch(()=>({positions:[],trades:[],journal:[]}));

    const overview=await overviewPromise;
    store.set({overview});
    render();

    const adminPromise=overview.viewer?.founder?api.getFeature("admin-testers").catch(()=>({testers:[]})):Promise.resolve(null);
    const journalPromise=overview.viewer?.founder?api.getFeature("journal",{limit:12}).catch(()=>({journal:[]})):Promise.resolve({journal:[]});

    const [googleUser,current,trades,arena,testerAdmin,journal]=await Promise.all([
      googlePromise,currentPromise,tradesPromise,arenaPromise,adminPromise,journalPromise
    ]);
    const currentState=store.get();
    const shadowPositions=(current.openPositions??[]).map(p=>({...p,side:p.side??(p.direction==="UP"?"BUY":"SELL")}));
    const symbol=current.currentTrade?.symbol||currentState.selectedSymbol||CONFIG.defaultSymbol;

    store.set({
      googleUser,testerAdmin,currentTrade:current.currentTrade??null,shadowPositions,
      trades:trades.trades??[],journal:journal.journal??[],arena,selectedSymbol:symbol
    });
    render();
    saveCache();

    if(overview.viewer?.founder&&!store.get().chartOpened){
      requestAnimationFrame(()=>reloadChart());
    }
  }catch(e){
    const box=document.getElementById("errorBox");
    if(box){box.textContent="Không tải được dashboard: "+e.message;box.style.display="block"}
  }
}

shell();
hydrateCache();
prewarmChartLibrary();
load();
if(!adminPreview)setInterval(load,CONFIG.refreshMs);
