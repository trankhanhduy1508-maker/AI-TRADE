(function(){
"use strict";
const S=window.CWSPortfolio;
const API="https://oziktadfeenydvgobudr.supabase.co/functions/v1/ai-trade-dashboard";
const BOOK="https://raw.githubusercontent.com/trankhanhduy1508-maker/AI-TRADE/2e9ae2e17e449f1b1574963103454f4a38226b94/knowledge/CWS_TRADING_MASTERBOOK_V3_DISTILLED_2026-09-28.md";
const SUPPORTED=new Set(["EURUSD","GBPUSD","USDJPY","AUDUSD","USDCAD","USDCHF","NZDUSD","XAUUSD","BTCUSD","ETHUSD","USOIL","US30","NAS100","US500"]);
const $=id=>document.getElementById(id);
let positions=[], mode="none", symbol="EURUSD", tf="1h", candles=[], lastQuestion="", lastHits=[];
let book=[{title:"Quản lý rủi ro",body:"Trước khi entry phải xác định setup, trigger, invalidation, stop distance, số tiền có thể mất và portfolio exposure. Không nới stop để gỡ lỗ.",source:"Masterbook - kiến thức cốt lõi"},{title:"Expectancy",body:"Expectancy = win rate × average win − loss rate × average loss. Không nhìn win rate một mình, phải đo payoff, chi phí và drawdown.",source:"Masterbook - kiến thức cốt lõi"},{title:"Bài học Gold từ CWS",body:"Historical OOS của Gold từng +116.17R, best trade +112.57R, bỏ ba winner lớn còn -14.22R. Next-open gap-aware: OOS -99.15R và walk-forward -160.51R. Không dùng headline thay cho kiểm chứng execution.",source:"Bằng chứng nghiên cứu CWS"}];
const escape=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const money=(n,plus=true)=>n==null||!Number.isFinite(n)?"—":(plus&&n>0?"+":n<0?"-":"")+"$"+Math.abs(n).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2});
const lot=n=>n==null||!Number.isFinite(n)?"—":n.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:4});
const sign=n=>n==null?"":n<0?"negative":"positive";
const text=(id,value)=>{$(id).textContent=value;};
const sample=()=>[["XAUUSD","BUY",.15,284.5],["EURUSD","SELL",1,12.5],["EURUSD","SELL",2,-48.7],["GBPUSD","BUY",.1,52.3],["AUDUSD","BUY",.3,76.14],["NZDUSD","SELL",.1,-18.6],["USDJPY","BUY",.2,41.32],["USDCHF","SELL",.2,-27.1],["USDCAD","BUY",.1,19.75],["EURJPY","SELL",.15,-44.8],["BTCUSD","BUY",.05,162.4],["ETHUSD","SELL",.1,-68.3],["NAS100","BUY",.2,118.6],["US30","SELL",.1,-52.4],["US500","BUY",.2,96.3],["XAGUSD","SELL",.3,-23.5],["USOIL","BUY",.2,92.15]].map(p=>({symbol:p[0],side:p[1],lot:p[2],floatingPL:p[3]}));

function show(view){
  document.querySelectorAll(".view").forEach(e=>e.classList.toggle("active",e.id==="view-"+view));
  document.querySelectorAll("[data-view]").forEach(e=>e.classList.toggle("active",e.dataset.view===view));
  $("sidebar").classList.remove("mobile-open");
  if(view==="dashboard")requestAnimationFrame(()=>draw(candles));
}
function renderPortfolio(){
  const v=S.aggregate(positions),map=new Map(v.groups.map(g=>[g.symbol,g]));
  text("totalGain",money(v.gain));text("totalLoss",money(v.loss,false));text("netPL",money(v.net));
  text("portfolioNet",money(v.net));text("pairCount",positions.length?String(v.pairCount):"—");text("totalLot",lot(v.totalLot));
  $("netPL").className=sign(v.net);$("portfolioNet").className=sign(v.net);
  const label=mode==="demo"?"MINH HỌA":mode==="manual"?"NHẬP THỦ CÔNG":"CHƯA KẾT NỐI";
  text("portfolioSource",label);text("portfolioModeTag",label);text("dataChip",label);
  $("dataChip").classList.toggle("demo",mode==="demo");
  text("sourceDescription",mode==="demo"?"Giá công khai · P/L minh họa, không phải lệnh thật":mode==="manual"?"Giá công khai · Vị thế nhập thủ công, chưa xác minh broker":"Giá công khai · Chưa kết nối vị thế Founder");
  const order=S.MARKET_ORDER.concat(v.groups.filter(g=>!S.MARKET_ORDER.includes(g.symbol)).map(g=>g.symbol));
  $("portfolioRows").innerHTML=order.map(m=>{
    const g=map.get(m),side=g?g.side:"—",pl=g?g.floatingPL:null;
    const klass=side==="BUY"?"tag-buy":side==="SELL"?"tag-sell":side==="HỖN HỢP"?"tag-mixed":"tag-none";
    return "<tr><td>"+escape(m)+"</td><td><span class='"+klass+"'>"+escape(side)+"</span></td><td>"+lot(g?g.lot:null)+"</td><td class='"+sign(pl)+"'>"+money(pl)+"</td></tr>";
  }).join("");
  $("portfolioDetails").innerHTML=v.groups.length?v.groups.map(g=>"<div class='portfolio-detail-row'><b>"+escape(g.symbol)+"</b><b>"+escape(g.side)+"</b><b>"+lot(g.lot)+" lot</b><b class='"+sign(g.floatingPL)+"'>"+money(g.floatingPL)+"</b></div>").join(""):"<p class='muted'>Chưa có vị thế. Hãy nạp JSON hoặc bật dữ liệu minh họa.</p>";
}
async function readPositions(file){
  if(!file)return;
  if(file.size>1024*1024)throw Error("JSON vượt 1MB");
  positions=S.parsePositions(JSON.parse(await file.text()));
  mode="manual";text("sampleToggle","Xem thử bằng dữ liệu MINH HỌA");
  renderPortfolio();show("portfolio");
}
function message(s){text("chartMessage",s);$("chartMessage").classList.toggle("hidden",!s);}
async function loadChart(){
  text("chartSymbol",symbol);text("chartTf",tf.toUpperCase());message("Đang tải nến thực…");
  text("sidePrice","—");text("sideMarketStatus","Đang tải feed");candles=[];draw([]);
  if(!SUPPORTED.has(symbol)){message("Chưa có feed công khai cho "+symbol+". Không dùng nến giả.");text("sideMarketStatus","Feed chưa hỗ trợ");return;}
  const url=new URL(API);url.searchParams.set("format","preview-candles");url.searchParams.set("symbol",symbol);url.searchParams.set("timeframe",tf);
  const oldSymbol=symbol,oldTf=tf,ctrl=new AbortController(),timeout=setTimeout(()=>ctrl.abort(),23000);
  try{
    const r=await fetch(url,{signal:ctrl.signal,cache:"no-store",credentials:"omit"});
    if(!r.ok)throw Error("HTTP "+r.status);
    const result=await r.json();
    const data=(Array.isArray(result.candles)?result.candles:[]).map(c=>({time:c.time||c.date,open:Number(c.open),high:Number(c.high),low:Number(c.low),close:Number(c.close),volume:Number(c.volume||0)})).filter(c=>[c.open,c.high,c.low,c.close].every(Number.isFinite)&&c.high>=Math.max(c.open,c.close)&&c.low<=Math.min(c.open,c.close));
    if(!data.length)throw Error("Không có nến");
    if(oldSymbol!==symbol||oldTf!==tf)return;
    candles=data;text("sidePrice",data[data.length-1].close.toLocaleString("en-US",{maximumFractionDigits:5}));
    text("sideMarketStatus","Giá công khai · Có thể trễ");const timeRaw=data[data.length-1].time;const timeMs=typeof timeRaw==="number"?(timeRaw<1e12?timeRaw*1000:timeRaw):Date.parse(String(timeRaw));text("chartUpdated","Nến công khai: "+(Number.isFinite(timeMs)?new Date(timeMs).toLocaleString("vi-VN"):String(timeRaw)));message("");draw(data);
  }catch(e){if(oldSymbol===symbol&&oldTf===tf){message("Không lấy được nến thực. Chưa vẽ dữ liệu giả.");text("sideMarketStatus","Feed tạm không khả dụng");text("chartUpdated","Chưa có dữ liệu");}}
  finally{clearTimeout(timeout);}
}
function draw(data){
  const c=$("priceChart"),ctx=c.getContext("2d"),bounds=c.getBoundingClientRect(),w=Math.max(240,Math.floor(bounds.width)),h=Math.max(200,Math.floor(bounds.height)),ratio=Math.min(window.devicePixelRatio||1,2);
  c.width=w*ratio;c.height=h*ratio;ctx.setTransform(ratio,0,0,ratio,0,0);ctx.fillStyle="#0a1627";ctx.fillRect(0,0,w,h);
  if(!data.length)return;
  const left=12,right=61,top=15,bottom=30,gw=w-left-right,gh=h-top-bottom;
  const bars=data.slice(-Math.max(10,Math.floor(gw/7)));
  let lo=Math.min(...bars.map(x=>x.low)),hi=Math.max(...bars.map(x=>x.high));const pad=Math.max((hi-lo)*.05,hi*.0001);lo-=pad;hi+=pad;
  const y=v=>top+(hi-v)/(hi-lo)*gh*.8,step=gw/bars.length,body=Math.max(2,step*.64);
  ctx.font="10px system-ui";ctx.strokeStyle="#21364e";ctx.fillStyle="#8aa1bd";
  for(let i=0;i<=4;i++){const yy=top+gh*.8*i/4;ctx.beginPath();ctx.moveTo(left,yy);ctx.lineTo(w-right,yy);ctx.stroke();ctx.fillText((hi-(hi-lo)*i/4).toFixed(hi>100?2:5),w-right+5,yy+3);}
  const maxVol=Math.max(...bars.map(x=>x.volume||0),1);
  bars.forEach((b,i)=>{
    const x=left+step*(i+.5),up=b.close>=b.open,color=up?"#26d7a4":"#ff627e";
    ctx.strokeStyle=color;ctx.fillStyle=color;ctx.beginPath();ctx.moveTo(x,y(b.high));ctx.lineTo(x,y(b.low));ctx.stroke();
    ctx.fillRect(x-body/2,Math.min(y(b.open),y(b.close)),body,Math.max(1,Math.abs(y(b.close)-y(b.open))));
    ctx.globalAlpha=.38;ctx.fillRect(x-body/2,h-bottom-(b.volume||0)/maxVol*gh*.16,body,(b.volume||0)/maxVol*gh*.16);ctx.globalAlpha=1;
  });
  const last=bars[bars.length-1];ctx.strokeStyle="#2cdbac";ctx.setLineDash([4,3]);ctx.beginPath();ctx.moveTo(left,y(last.close));ctx.lineTo(w-right,y(last.close));ctx.stroke();ctx.setLineDash([]);
  ctx.fillStyle="#26d7a4";ctx.fillRect(w-right-1,y(last.close)-9,right,18);ctx.fillStyle="#0b1625";ctx.font="bold 10px system-ui";ctx.fillText(last.close.toLocaleString("en-US",{maximumFractionDigits:hi>100?2:5}),w-right+3,y(last.close)+3);
}
const norm=s=>String(s||"").normalize("NFD").replace(/[\u0300-\u036f]/g,"").replace(/đ/g,"d").toLowerCase().replace(/[^a-z0-9]+/g," ");
const words=s=>norm(s).trim().split(/\s+/).filter(w=>w.length>2&&!["toi","ban","mot","nhung","cua","theo","trong","nay","cho","voi","duoc"].includes(w)).slice(0,30);
function search(q,n=3){
  const terms=words(q);if(!terms.length)return[];
  return book.map(b=>({b,score:terms.reduce((v,t)=>v+(norm(b.title).includes(t)?6:0)+(norm(b.body).includes(t)?2:0),0)})).filter(x=>x.score>0).sort((a,b)=>b.score-a.score).slice(0,n).map(x=>x.b);
}
function renderResults(items){
  $("bookResults").innerHTML=items.length?items.map(b=>"<article class='result-card'><h3>"+escape(b.title)+"</h3><p>"+escape(b.body.slice(0,1200))+"</p><small>Nguồn: "+escape(b.source)+"</small></article>").join(""):"<div class='result-card'>Không thấy bằng chứng phù hợp. Thử từ khóa khác hoặc nạp EPUB đầy đủ.</div>";
}
async function loadBook(){
  try{
    const r=await fetch(BOOK,{cache:"force-cache",credentials:"omit"});if(!r.ok)throw Error("book "+r.status);
    let title="Masterbook";const chunks=[];let raw="";
    const flush=()=>{for(let i=0;i<raw.length;i+=750){const part=raw.slice(i,i+850);if(part.length>40)chunks.push({title,body:part,source:"CWS Masterbook · bản đúc kết"});}raw="";};
    (await r.text()).split(/\r?\n/).forEach(line=>{if(/^#{1,3} /.test(line)){flush();title=line.replace(/^#+\s*/,"");}else if(line.trim()&&!line.startsWith("|"))raw+=" "+line.trim();});flush();
    if(chunks.length)book=chunks.concat(book);
    text("bookBadge",chunks.length+" đoạn");
    text("bookUploadStatus","Đã nạp bản đúc kết. Nạp EPUB để có đủ chương.");
  }catch{text("bookBadge","Bản cơ bản");text("bookUploadStatus","Bản cơ bản sẵn dùng. Có thể nạp EPUB đầy đủ.");}
}
async function importEpub(file){
  if(!file)return;if(file.size>15*1024*1024)throw Error("EPUB vượt 15 MB");if(!window.JSZip)throw Error("Thư viện đọc EPUB không khả dụng");
  text("bookUploadStatus","Đang đọc EPUB trong trình duyệt…");
  const zip=await JSZip.loadAsync(file,{checkCRC32:true});
  let paths=Object.keys(zip.files).filter(n=>/\/text\/ch\d+\.xhtml$/i.test(n)).sort();
  if(!paths.length)paths=Object.keys(zip.files).filter(n=>/\.xhtml$/i.test(n)&&!/nav|cover|toc|title_page/i.test(n)).sort();
  if(!paths.length||paths.length>250)throw Error("Không có chương đọc được hoặc EPUB quá lớn");
  const sections=[];let total=0;
  for(const path of paths){
    const html=await zip.file(path).async("string"),doc=new DOMParser().parseFromString(html,"application/xhtml+xml");
    const heading=doc.querySelector("h1,h2,h3,title");const title=heading?heading.textContent.trim():path;
    const elems=Array.from(doc.querySelectorAll("p,li,blockquote,h1,h2,h3"));const paragraphs=elems.length?elems.map(e=>e.textContent.replace(/\s+/g," ").trim()):[doc.documentElement.textContent.replace(/\s+/g," ").trim()];
    for(const p of paragraphs){if(p.length<35)continue;for(let i=0;i<p.length;i+=750){const chunk=p.slice(i,i+850);total+=chunk.length;if(total>2*1024*1024)throw Error("EPUB có quá nhiều chữ");sections.push({title,body:chunk,source:"EPUB: "+file.name+" · "+title});}}
  }
  if(!sections.length)throw Error("Không trích được chữ EPUB");
  book=sections.concat(book);text("bookBadge","EPUB "+paths.length+" chương");
  text("bookUploadStatus","Đã nạp "+paths.length+" chương / "+sections.length+" đoạn. Không tải sách lên máy chủ.");renderResults(sections.slice(0,3));
}
function addMessage(body,role,sources=[]){
  const msg=document.createElement("div");msg.className="message "+role;msg.textContent=body;
  if(sources.length){const small=document.createElement("small");small.textContent="Nguồn: "+sources.map(s=>s.title).join(" · ");msg.appendChild(small);}
  $("conversation").appendChild(msg);$("conversation").scrollTop=$("conversation").scrollHeight;
}
function promptForChatGPT(){
  const q=lastQuestion||$("chatInput").value.trim()||"Giúp tôi học CWS Trading Masterbook";
  const refs=lastQuestion===q?lastHits:search(q);
  return "Bạn là AI nghiên cứu CWS AI Trade. Dữ liệu dưới đây là trích dẫn từ CWS Trading Masterbook, không tự thêm thông tin hay tự gửi lệnh. Phân biệt rõ paper/demo/live, ghi rủi ro và thông tin còn thiếu.\n\nCâu hỏi: "+q+"\n\n"+refs.map((b,i)=>"Nguồn "+(i+1)+": "+b.title+"\n"+b.body.slice(0,1100)).join("\n\n")+"\n\nTrạng thái danh mục: "+(mode==="demo"?"DỮ LIỆU MINH HỌA, KHÔNG PHẢI TIỀN THẬT":mode==="manual"?"Dữ liệu nhập thủ công, chưa xác minh broker":"Chưa kết nối broker")+". Chỉ phân tích, không cho phép đặt lệnh.";
}
async function copyPrompt(){const v=promptForChatGPT();try{if(!navigator.clipboard?.writeText)throw Error("clipboard unavailable");await navigator.clipboard.writeText(v);text("copyForChatGPT","Đã sao chép · Dán vào ChatGPT");}catch{const old=document.getElementById("cwsCopyFallback");if(old)old.remove();const overlay=document.createElement("div");overlay.id="cwsCopyFallback";overlay.style.cssText="position:fixed;inset:0;z-index:9999;background:#07121cee;display:flex;align-items:center;justify-content:center;padding:16px";const box=document.createElement("div");box.style.cssText="width:min(720px,100%);background:#12243a;color:#e9f3ff;border:1px solid #4775a0;border-radius:14px;padding:16px";const title=document.createElement("p");title.textContent="Trình duyệt chặn sao chép tự động. Chạm giữ văn bản bên dưới để sao chép, sau đó dán vào ChatGPT.";const textarea=document.createElement("textarea");textarea.value=v;textarea.readOnly=true;textarea.style.cssText="width:100%;height:45vh;background:#091728;color:#e8f4ff;padding:12px;border:1px solid #4775a0;border-radius:8px";const close=document.createElement("button");close.textContent="Đóng";close.type="button";close.style.cssText="margin-top:10px;padding:10px 18px;background:#2176b5;color:white;border:0;border-radius:8px";close.addEventListener("click",()=>overlay.remove());box.append(title,textarea,close);overlay.append(box);document.body.appendChild(overlay);textarea.focus();textarea.select();text("copyForChatGPT","Chọn và sao chép thủ công");}}
function bind(){
  document.querySelectorAll("[data-view]").forEach(b=>b.addEventListener("click",()=>show(b.dataset.view)));
  $("menuBtn").addEventListener("click",()=>$("sidebar").classList.toggle("mobile-open"));
  $("symbolSelect").addEventListener("change",e=>{symbol=e.target.value;loadChart();});
  document.querySelectorAll("#timeframes button").forEach(b=>b.addEventListener("click",()=>{tf=b.dataset.tf;document.querySelectorAll("#timeframes button").forEach(x=>x.classList.toggle("active",x===b));loadChart();}));
  $("positionInput").addEventListener("change",async e=>{try{await readPositions(e.target.files[0]);}catch(err){alert("JSON lỗi: "+err.message);}e.target.value="";});
  $("sampleToggle").addEventListener("click",()=>{if(mode==="demo"){positions=[];mode="none";text("sampleToggle","Xem thử bằng dữ liệu MINH HỌA");}else{positions=sample();mode="demo";text("sampleToggle","Tắt dữ liệu MINH HỌA");}renderPortfolio();});
  $("bookInput").addEventListener("change",async e=>{try{await importEpub(e.target.files[0]);}catch(err){text("bookUploadStatus","Lỗi EPUB: "+err.message);}e.target.value="";});
  $("bookSearch").addEventListener("click",()=>renderResults(search($("bookQuery").value,7)));
  $("bookQuery").addEventListener("keydown",e=>{if(e.key==="Enter"){e.preventDefault();renderResults(search(e.target.value,7));}});
  $("chatForm").addEventListener("submit",e=>{e.preventDefault();const q=$("chatInput").value.trim();if(!q)return;$("chatInput").value="";lastQuestion=q;addMessage(q,"user");lastHits=search(q);if(!lastHits.length){addMessage("Không tìm thấy bằng chứng phù hợp. Nạp EPUB đầy đủ hoặc thay từ khóa; tôi không bịa tín hiệu.","bot");return;}addMessage("Các đoạn liên quan trong Masterbook:\n\n"+lastHits.map((s,i)=>(i+1)+". "+s.title+"\n"+s.body.slice(0,680)).join("\n\n")+"\n\nĐây là tra cứu sách, không phải xác nhận lệnh giao dịch.","bot",lastHits);});
  $("copyForChatGPT").addEventListener("click",copyPrompt);
  $("openChatGPT").addEventListener("click",()=>{copyPrompt().catch(()=>{});});
  window.addEventListener("resize",()=>{if(candles.length)draw(candles);});
}
if(!S){document.body.textContent="Thiếu mô-đun tính danh mục";return;}
bind();renderPortfolio();loadBook();loadChart();
})();