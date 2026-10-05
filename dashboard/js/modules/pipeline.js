import{badge}from"../utils.js";
const name=j=>j.includes("forward-shadow")?"Tín hiệu forward":j.includes("shadow-broker")?"Shadow Broker":j.includes("forward-evaluate")?"Chấm điểm":"Job";
const time=s=>s.startsWith("15 3")?"10:15 VN":s.startsWith("20 3")?"10:20 VN":s.startsWith("25 3")?"10:25 VN":s;
export function renderPipeline(crons=[]){
 return `<section class="section"><div class="section-head"><h2>Pipeline tự động mỗi ngày</h2><span class="action">3 bước</span></div><div class="grid-3">${crons.map((c,i)=>`<div class="card pipeline-card"><div class="pipeline-left"><div class="step-num">${i+1}</div><div><strong>${name(c.jobname)}</strong><small>${time(c.schedule)}</small></div></div>${badge(c.active?"ACTIVE":"OFF",c.active?"green":"gray")}</div>`).join("")}</div></section>`;
}
