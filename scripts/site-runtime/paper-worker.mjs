// The enclosing Site remains owner-only. The API key is a server-only runtime secret.
export async function serve(request, env, assets, upstreamFetch=fetch) {
  const path = new URL(request.url).pathname;
  if(path === "/api/paper-orders") {
    if(request.method !== "GET") return new Response(null,{status:405});
    if(!env.CWS_PAPER_FEED_KEY) return new Response('{"error":"FEED_NOT_CONFIGURED"}',{status:503});
    try {
      const response = await upstreamFetch("https://oziktadfeenydvgobudr.supabase.co/functions/v1/ai-trade-paper-feed", {
        headers:{authorization:"Bearer "+env.CWS_PAPER_FEED_KEY},signal:AbortSignal.timeout(30000)
      });
      if(!response.ok) throw new Error("feed unavailable");
      return new Response(await response.text(),{headers:{"content-type":"application/json; charset=utf-8","cache-control":"private, no-store"}});
    } catch { return new Response('{"error":"FEED_UNAVAILABLE"}',{status:503,headers:{"content-type":"application/json","cache-control":"no-store"}}); }
  }
  if(request.method!=="GET" && request.method!=="HEAD") return new Response(null,{status:405});
  const asset = assets[path === "/" ? "/index.html" : path];
  if(!asset) return new Response("Not found",{status:404});
  const bytes = Uint8Array.from(atob(asset.body),c=>c.charCodeAt(0));
  return new Response(request.method==="HEAD"?null:bytes,{headers:{"content-type":asset.type,"cache-control":"no-cache","x-content-type-options":"nosniff"}});
}
