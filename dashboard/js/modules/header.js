import{esc}from"../utils.js";
export function renderHeader(){
  return `<header class="topbar">
    <div class="brand">
      <div class="brand-mark"><svg viewBox="0 0 24 24" fill="none"><path d="M5 18V11M10 18V7M15 18V4M20 18V9" stroke="#43d6ff" stroke-width="2.6" stroke-linecap="round"/></svg></div>
      <div><h1>AI-TRADE Forward Monitor</h1><p>TF-013A · dữ liệu live từ Supabase</p></div>
    </div>
    <div class="live"><i class="live-dot"></i>LIVE</div>
  </header>`;
}
export function renderError(msg=""){return `<div class="error-box" id="errorBox" style="display:${msg?"block":"none"}">${esc(msg)}</div>`}
