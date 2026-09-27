import{badge,esc}from"../utils.js";
export function renderAdminStatus(overview={},positions=[]){
  const evalState=String(overview?.evaluation?.state??"UNAVAILABLE");
  const mt5Connected=Boolean(overview?.mt5?.connected);
  const liveLocked=overview?.gates?.liveMoneyLocked!==false;
  const count=Array.isArray(positions)?positions.length:0;
  return `<section class="section admin-priority" aria-label="System status">
    <div class="section-head"><h2>System status</h2><span class="action">FOUNDER</span></div>
    <div class="card admin-status-grid">
      <div class="admin-status-item"><small>Engine</small>${badge("ONLINE","green")}</div>
      <div class="admin-status-item"><small>Forward</small>${badge(esc(evalState),evalState==="FORWARD_REJECT"?"red":evalState==="COLLECTING"?"yellow":"green")}</div>
      <div class="admin-status-item"><small>Open positions</small><strong>${count}</strong></div>
      <div class="admin-status-item"><small>MT5 DEMO</small>${badge(mt5Connected?"CONNECTED":"UNAVAILABLE",mt5Connected?"green":"gray")}</div>
      <div class="admin-status-item"><small>Live money</small>${badge(liveLocked?"LOCKED":"UNAVAILABLE",liveLocked?"yellow":"gray")}</div>
    </div>
  </section>`;
}
