import{badge,fmtDate}from"../utils.js";
export function renderSafety(mt5={},gates={}){
 return `<section class="section"><div class="section-head"><h2>Trạng thái hệ thống & Safety</h2></div><div class="grid-2">
  <div class="card card-pad"><h3>MT5 DEMO</h3>
    <div class="metric-row"><span>Kết nối</span><b>${badge(mt5.connected?"CONNECTED":"OFF",mt5.connected?"green":"red")}</b></div>
    <div class="metric-row"><span>Server</span><b>${mt5.server||"—"}</b></div>
    <div class="metric-row"><span>Loại tài khoản</span><b>${mt5.accountType||"—"}</b></div>
    <div class="metric-row"><span>Verify gần nhất</span><b>${fmtDate(mt5.lastVerifiedAt)}</b></div>
  </div>
  <div class="card card-pad"><h3>Safety gates</h3>
    <div class="metric-row"><span>The5ers</span><b>${badge(gates.the5ersReadiness||"—")}</b></div>
    <div class="metric-row"><span>Written approval</span><b>${gates.automationApprovalVerified?"VERIFIED":"CHƯA CÓ"}</b></div>
    <div class="metric-row"><span>Risk profile</span><b>${gates.riskProfileApproved?"APPROVED":"CHƯA DUYỆT"}</b></div>
    <div class="metric-row"><span>DEMO send</span><b>${gates.demoSendEnabled?"ON":"OFF"}</b></div>
    <div class="metric-row"><span>Live money</span><b>${badge("LOCKED","yellow")}</b></div>
  </div></div></section>`;
}
