export const qs=(s,r=document)=>r.querySelector(s);
export const qsa=(s,r=document)=>[...r.querySelectorAll(s)];
export const esc=(v)=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]));
export const pct=(v,t)=>Math.max(0,Math.min(100,Math.round((Number(v)||0)/Math.max(1,Number(t)||1)*100)));
export const fmtR=(v)=>{const n=Number(v);return Number.isFinite(n)?`${n>0?"+":""}${n.toFixed(2)}R`:"—"};
export const fmtUsd=(v)=>{const n=Number(v);return Number.isFinite(n)?`${n>0?"+":""}${n.toFixed(2)} USD`:"—"};
export const fmtPrice=(v,d=5)=>{const n=Number(v);return Number.isFinite(n)?n.toFixed(d):"—"};
export const fmtDate=(v)=>v?new Date(v).toLocaleString("vi-VN"):"—";
export const sideBadge=(side)=>side==="BUY"?"green":side==="SELL"?"red":"gray";
export const stateBadge=(s)=>["ACTIVE","CONNECTED","COLLECTING","WIN","OPEN"].includes(s)?"green":["SELL","LOSS","FORWARD_REJECT","ERROR"].includes(s)?"red":["BLOCKED_APPROVAL","LOCKED","CHƯA CÓ","CHƯA DUYỆT"].includes(s)?"yellow":"blue";
export const badge=(label,tone=stateBadge(label))=>`<span class="badge ${tone}">${esc(label)}</span>`;
export const empty=(text)=>`<div class="empty-state">${esc(text)}</div>`;
export function ema(values,period){
  if(!values?.length)return[];
  const k=2/(period+1);let prev=Number(values[0]);
  return values.map((v,i)=>{const n=Number(v);prev=i===0?n:n*k+prev*(1-k);return prev});
}
