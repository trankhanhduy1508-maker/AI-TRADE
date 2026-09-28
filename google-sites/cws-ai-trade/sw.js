/* CWS AI Trade PWA: public static shell only. No caching of private data, market API or position files. */
"use strict";
const ROOT="/functions/v1/cws-ai-trade-site/app/";
const CACHE="cws-ai-trade-static-v5";
const BOOK="https://raw.githubusercontent.com/trankhanhduy1508-maker/AI-TRADE/2e9ae2e17e449f1b1574963103454f4a38226b94/knowledge/CWS_TRADING_MASTERBOOK_V3_DISTILLED_2026-09-28.md";
const CDN="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js";
const CORE=[
  ROOT,
  ROOT+"?asset=styles.css",
  ROOT+"?asset=portfolio.js",
  ROOT+"?asset=tradingview.js",
  ROOT+"?asset=app.js",
  ROOT+"?asset=pwa.js",
  ROOT+"?asset=manifest.webmanifest",
  ROOT+"?asset=icon-192.png",
  ROOT+"?asset=icon-512.png"
];
self.addEventListener("install",event=>{
  event.waitUntil((async()=>{
    const cache=await caches.open(CACHE);
    await cache.addAll(CORE);
    // Optional public-only files. Failure must not block app installation.
    for(const url of [CDN,BOOK]){
      try{
        const controller=new AbortController();
        const timer=setTimeout(()=>controller.abort(),7000);
        try{
          const response=await fetch(url,{signal:controller.signal});
          if(response.ok)await cache.put(url,response.clone());
        }finally{clearTimeout(timer);}
      }catch{/* Offline shell is still installable without optional resources. */}
    }
    self.skipWaiting();
  })());
});
self.addEventListener("activate",event=>{
  event.waitUntil((async()=>{
    const names=await caches.keys();
    await Promise.all(names.filter(n=>n.startsWith("cws-ai-trade-static-")&&n!==CACHE).map(n=>caches.delete(n)));
    await self.clients.claim();
  })());
});
self.addEventListener("fetch",event=>{
  const request=event.request;
  if(request.method!=="GET")return;
  const u=new URL(request.url);
  if(u.href===CDN||u.href===BOOK){
    event.respondWith((async()=>{
      const cache=await caches.open(CACHE);
      const hit=await cache.match(request);
      if(hit)return hit;
      const response=await fetch(request);
      if(response.ok)await cache.put(request,response.clone());
      return response;
    })());
    return;
  }
  if(u.origin!==self.location.origin||!u.pathname.startsWith(ROOT))return;
  // Never cache any API request, token-bearing URL, user file or unknown path.
  if(u.searchParams.has("t")||u.searchParams.has("token")||u.searchParams.has("authorization"))return;
  if(request.mode==="navigate"){
    event.respondWith((async()=>{
      try{
        const result=await fetch(request);
        if(result.ok&&result.headers.get("content-type")?.includes("text/html")){
          const cache=await caches.open(CACHE);
          await cache.put(ROOT,result.clone());
        }
        return result;
      }catch{
        const cache=await caches.open(CACHE);
        return await cache.match(ROOT)||new Response("CWS AI Trade chưa có giao diện offline",{status:503,headers:{"content-type":"text/plain; charset=utf-8"}});
      }
    })());
    return;
  }
  const asset=u.searchParams.get("asset");
  const safeAsset=["styles.css","portfolio.js","tradingview.js","app.js","pwa.js","manifest.webmanifest","icon-192.png","icon-512.png"].includes(asset);
  const safePath=false;
  if(!safeAsset&&!safePath)return;
  event.respondWith((async()=>{
    const cache=await caches.open(CACHE);
    const hit=await cache.match(request);
    if(hit)return hit;
    const response=await fetch(request);
    if(response.ok)await cache.put(request,response.clone());
    return response;
  })());
});
