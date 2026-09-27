import{esc}from"../utils.js";
export function renderHeader(viewer={},googleUser=null){
  const founder=Boolean(viewer?.founder);
  const label=founder?"FOUNDER":viewer?.role==="TESTER"?"TESTER":"CUSTOMER";
  const name=googleUser?.user_metadata?.full_name||googleUser?.user_metadata?.name||googleUser?.email||"";
  return `<header class="topbar">
    <div class="brand">
      <div class="brand-mark"><svg viewBox="0 0 24 24" fill="none"><path d="M5 18V11M10 18V7M15 18V4M20 18V9" stroke="#43d6ff" stroke-width="2.6" stroke-linecap="round"/></svg></div>
      <div><h1>CWS AI Trade</h1><p>${founder?"Founder Console":"Demo / Paper Experience"}</p></div>
    </div>
    <div class="header-actions">
      ${googleUser
        ?`<button id="googleAccountBtn" class="google-login connected" type="button" title="Đăng xuất Google"><span class="google-dot">G</span><span>${esc(name)}</span></button>`
        :`<button id="googleLoginBtn" class="google-login" type="button"><span class="google-dot">G</span><span>Đăng nhập Google</span></button>`}
      <span class="badge ${founder?"yellow":"blue"}">${esc(label)}</span>
      <div class="live"><i class="live-dot"></i>LIVE</div>
    </div>
  </header>`;
}
export function renderError(msg=""){return `<div class="error-box" id="errorBox" style="display:${msg?"block":"none"}">${esc(msg)}</div>`}
