import{badge,fmtDate}from"../utils.js";

export function renderTesterAdmin(data={}){
  const testers=data.testers??[];
  const rows=testers.map(t=>{
    const state=String(t.entitlement_state??"");
    return `<div class="tester-row" data-token-id="${t.id}">
      <div><strong>${t.subject_label||t.label||("Account "+t.id)}</strong><small>${t.access_role} · ${state}</small></div>
      <div><small>Tester hết hạn</small><b>${fmtDate(t.tester_expires_at)}</b></div>
      <div class="tester-actions">
        <button data-action="TO_CUSTOMER_FREE">Khách thường</button>
        <button data-action="RESTORE_TESTER">Tester 30 ngày</button>
        <button data-action="SUSPEND">Khóa</button>
      </div>
    </div>`;
  }).join("");
  return `<section class="section">
    <div class="section-head"><h2>Founder · Quản lý Tester</h2><span class="action">${badge("FOUNDER ONLY","yellow")}</span></div>
    <div class="card tester-admin">${rows||'<div class="empty-state">Chưa có tester.</div>'}</div>
  </section>`;
}
