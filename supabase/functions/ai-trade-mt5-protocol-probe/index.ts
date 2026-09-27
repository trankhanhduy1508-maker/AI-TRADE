const json=(b:unknown,s=200)=>new Response(JSON.stringify(b),{status:s,headers:{"content-type":"application/json; charset=utf-8"}});

function contexts(text:string,needle:string,radius=500,max=20){
  const out:string[]=[];
  const lower=text.toLowerCase(), n=needle.toLowerCase();
  let from=0;
  while(out.length<max){
    const i=lower.indexOf(n,from);
    if(i<0) break;
    out.push(text.slice(Math.max(0,i-radius),Math.min(text.length,i+n.length+radius)));
    from=i+n.length;
  }
  return out;
}

Deno.serve(async(req)=>{
  try{
    const base="https://trade.mql5.com/trade?version=5";
    const htmlRes=await fetch(base,{headers:{"user-agent":"Mozilla/5.0 AI-TRADE protocol probe"}});
    const html=await htmlRes.text();
    const scriptMatches=[...html.matchAll(/<script[^>]+src=["']([^"']*mt5[^"']*\.js[^"']*)["']/gi)].map(m=>m[1]);
    const allScriptMatches=[...html.matchAll(/<script[^>]+src=["']([^"']+\.js[^"']*)["']/gi)].map(m=>m[1]);
    const versionMatch=html.match(/"script_version"\s*:\s*"([^"]+)"/i);
    const scriptVersion=versionMatch?.[1]??null;
    const candidates=scriptVersion?[
      "https://trade.mql5.com/trade/res/js/mt4.en.js?t="+scriptVersion,
      "https://trade.mql5.com/trade/res/js/mt5.en.js?t="+scriptVersion
    ]:[];
    const bundles:any[]=[];
    let js="";
    for(const url of candidates){
      try{
        const r=await fetch(url,{headers:{"user-agent":"Mozilla/5.0 AI-TRADE protocol probe","referer":base}});
        const text=await r.text();
        bundles.push({url,status:r.status,length:text.length,preview:text.slice(0,500)});
        if(r.ok&&text.length>js.length) js=text;
      }catch(error){
        bundles.push({url,status:null,length:0,error:error instanceof Error?error.message:String(error)});
      }
    }
    const scriptUrl=bundles.sort((a,b)=>b.length-a.length)[0]?.url??null;
    const jsStatus=bundles.find(x=>x.url===scriptUrl)?.status??null;

    const keywords=["demo","register","registration","email","phone","server","openaccount","newaccount","trade_server","MetaQuotes-Demo","account","deposit","leverage","hedge","password"];
    const snippets:Record<string,string[]>={};
    for(const k of keywords) snippets[k]=contexts(js,k,900,20);

    const urls=[...js.matchAll(/https?:\\?\/\\?\/[A-Za-z0-9._~:/?#\[\]@!    const scriptMatches=[...html.matchAll(/<script[^>]+src=["']([^"']*mt5[^"']*\.js[^"']*)["']/gi)].map(m=>m[1]);
    const allScriptMatches=[...html.matchAll(/<script[^>]+src=["']([^"']+\.js[^"']*)["']/gi)].map(m=>m[1]);
    const chosen=scriptMatches[0]??allScriptMatches.find(x=>/\/trade\/res\/js\/mt5/i.test(x))??null;
    const scriptUrl=chosen?new URL(chosen,"https://trade.mql5.com").toString():null;

    let js="",jsStatus:number|null=null;
    if(scriptUrl){
      const jsRes=await fetch(scriptUrl,{headers:{"user-agent":"Mozilla/5.0 AI-TRADE protocol probe","referer":base}});
      jsStatus=jsRes.status;
      js=await jsRes.text();
    }

    const keywords=["demo","register","registration","email","phone","server","openaccount","newaccount","trade_server","MetaQuotes-Demo","account"];
    const snippets:Record<string,string[]>={};
    for(const k of keywords) snippets[k]=contexts(js,k,700,12);

    const urls=[...js.matchAll(/https?:\\?\/\\?\/[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+/g)]
      .map(m=>m[0].replace(/\\\//g,"/"))
      .filter((v,i,a)=>a.indexOf(v)===i)
      .slice(0,200);

    const relativePaths=[...js.matchAll(/["'](\/[A-Za-z0-9._~!$&()*+,;=:@%/?#-]{3,})["']/g)]
      .map(m=>m[1])
      .filter((v,i,a)=>a.indexOf(v)===i)
      .filter(v=>/demo|account|register|trade|server|login/i.test(v))
      .slice(0,200);'()*+,;=%-]+/g)]
      .map(m=>m[0].replace(/\\\//g,"/"))
      .filter((v,i,a)=>a.indexOf(v)===i)
      .slice(0,400);

    const relativePaths=[...js.matchAll(/["'](\/[A-Za-z0-9._~!    const scriptMatches=[...html.matchAll(/<script[^>]+src=["']([^"']*mt5[^"']*\.js[^"']*)["']/gi)].map(m=>m[1]);
    const allScriptMatches=[...html.matchAll(/<script[^>]+src=["']([^"']+\.js[^"']*)["']/gi)].map(m=>m[1]);
    const chosen=scriptMatches[0]??allScriptMatches.find(x=>/\/trade\/res\/js\/mt5/i.test(x))??null;
    const scriptUrl=chosen?new URL(chosen,"https://trade.mql5.com").toString():null;

    let js="",jsStatus:number|null=null;
    if(scriptUrl){
      const jsRes=await fetch(scriptUrl,{headers:{"user-agent":"Mozilla/5.0 AI-TRADE protocol probe","referer":base}});
      jsStatus=jsRes.status;
      js=await jsRes.text();
    }

    const keywords=["demo","register","registration","email","phone","server","openaccount","newaccount","trade_server","MetaQuotes-Demo","account"];
    const snippets:Record<string,string[]>={};
    for(const k of keywords) snippets[k]=contexts(js,k,700,12);

    const urls=[...js.matchAll(/https?:\\?\/\\?\/[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+/g)]
      .map(m=>m[0].replace(/\\\//g,"/"))
      .filter((v,i,a)=>a.indexOf(v)===i)
      .slice(0,200);

    const relativePaths=[...js.matchAll(/["'](\/[A-Za-z0-9._~!$&()*+,;=:@%/?#-]{3,})["']/g)]
      .map(m=>m[1])
      .filter((v,i,a)=>a.indexOf(v)===i)
      .filter(v=>/demo|account|register|trade|server|login/i.test(v))
      .slice(0,200);()*+,;=:@%/?#-]{3,})["']/g)]
      .map(m=>m[1])
      .filter((v,i,a)=>a.indexOf(v)===i)
      .filter(v=>/demo|account|register|trade|server|login|user|open/i.test(v))
      .slice(0,400);

    return json({
      ok:true,
      htmlStatus:htmlRes.status,
      htmlLength:html.length,
      htmlHasMetaQuotesDemo:/MetaQuotes-Demo/i.test(html),
      htmlDemoContexts:contexts(html,"Open a Demo Account",600,5),
      htmlPreview:html.slice(0,12000),
      allScriptMatches,
      scriptMatches,
      scriptVersion,
      candidates,
      bundles,
      scriptUrl,
      jsStatus,
      jsLength:js.length,
      snippets,
      urls,
      relativePaths,
      brokerOrders:false,
      liveMoneyLocked:true
    });
  }catch(error){
    return json({ok:false,status:"ERROR",message:error instanceof Error?error.message:String(error),brokerOrders:false,liveMoneyLocked:true},500);
  }
});