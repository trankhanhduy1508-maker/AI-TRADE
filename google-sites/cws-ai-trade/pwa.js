/* Install UI only works from the CWS-owned, direct HTTPS PWA URL, not from a Google Sites iframe. */
(function(){
"use strict";
const BASE="/functions/v1/cws-ai-trade-site/app/";
const button=document.getElementById("pwaInstallBtn");
const hint=document.getElementById("pwaInstallHint");
const onApp=location.pathname===BASE&&window.top===window.self;
const standalone=()=>window.matchMedia?.("(display-mode: standalone)")?.matches||navigator.standalone===true;
let deferred=null;
if(!onApp){if(hint)hint.hidden=true;return;}
if(standalone()){if(button)button.hidden=true;if(hint)hint.hidden=true;}
else if(hint)hint.hidden=false;
window.addEventListener("beforeinstallprompt",event=>{
  event.preventDefault();
  deferred=event;
  if(button&&!standalone())button.hidden=false;
  if(hint)hint.textContent="Web App đã sẵn sàng cài đặt.";
});
window.addEventListener("appinstalled",()=>{
  deferred=null;
  if(button)button.hidden=true;
  if(hint){hint.hidden=false;hint.textContent="Đã cài CWS AI Trade. Mở ứng dụng từ màn hình chính.";}
});
if(button)button.addEventListener("click",async()=>{
  if(!deferred)return;
  button.disabled=true;
  try{
    deferred.prompt();
    await deferred.userChoice;
  }finally{
    deferred=null;button.hidden=true;button.disabled=false;
  }
});
if("serviceWorker" in navigator){
  window.addEventListener("load",async()=>{
    try{
      const reg=await navigator.serviceWorker.register(BASE+"sw.js",{scope:BASE,updateViaCache:"none"});
      if(reg?.update)reg.update().catch(()=>{});
    }catch(error){
      if(hint)hint.textContent="Chưa lưu ngoại tuyến được. Vẫn có thể sử dụng website khi có mạng.";
      console.warn("CWS PWA offline not ready",error);
    }
  });
}
const view=new URLSearchParams(location.search).get("view");
if(["dashboard","portfolio","book","chat"].includes(view)){
  const nav=document.querySelector('[data-view="'+view+'"]');
  if(nav)nav.click();
}
})();