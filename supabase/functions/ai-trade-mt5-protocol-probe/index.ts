const json=(body:unknown,status=200)=>new Response(JSON.stringify(body),{
  status,
  headers:{"content-type":"application/json; charset=utf-8"}
});

function contexts(text:string,needle:string,radius=700,max=12){
  const out:string[]=[];
  const lower=text.toLowerCase();
  const target=needle.toLowerCase();
  let cursor=0;
  while(out.length<max){
    const idx=lower.indexOf(target,cursor);
    if(idx<0) break;
    out.push(text.slice(Math.max(0,idx-radius),Math.min(text.length,idx+target.length+radius)));
    cursor=idx+target.length;
  }
  return out;
}

function uniq<T>(items:T[]){
  return [...new Set(items)];
}

Deno.serve(async()=>{
  try{
    const base="https://trade.mql5.com/trade?version=5";
    const headers={
      "user-agent":"Mozilla/5.0 AI-TRADE protocol probe",
      "accept":"text/html,application/xhtml+xml,application/javascript,*/*"
    };

    const htmlRes=await fetch(base,{headers});
    const html=await htmlRes.text();
    const versionMatch=html.match(/"script_version"\s*:\s*"([^"]+)"/i);
    const scriptVersion=versionMatch?.[1]??null;

    const candidates=scriptVersion?[
      "https://trade.mql5.com/trade/res/js/mt4.en.js?t="+scriptVersion,
      "https://trade.mql5.com/trade/res/js/mt5.en.js?t="+scriptVersion
    ]:[];

    const bundles:{url:string;status:number|null;length:number;preview:string;body?:string;error?:string}[]=[];
    for(const url of candidates){
      try{
        const res=await fetch(url,{headers:{...headers,"referer":base}});
        const body=await res.text();
        bundles.push({
          url,
          status:res.status,
          length:body.length,
          preview:body.slice(0,400),
          body
        });
      }catch(error){
        bundles.push({
          url,
          status:null,
          length:0,
          preview:"",
          error:error instanceof Error?error.message:String(error)
        });
      }
    }

    const best=[...bundles].filter(x=>x.status===200).sort((a,b)=>b.length-a.length)[0]??null;
    const js=best?.body??"";

    const keywords=[
      "Open a Demo Account",
      "demo",
      "register",
      "registration",
      "email",
      "e-mail",
      "phone",
      "name",
      "deposit",
      "leverage",
      "hedge",
      "password",
      "MetaQuotes-Demo",
      "trade_server",
      "openaccount",
      "newaccount",
      "createaccount",
      "websocket",
      "wss://",
      "account"
    ];

    const snippets:Record<string,string[]>={};
    for(const keyword of keywords){
      snippets[keyword]=contexts(js,keyword,900,20);
    }

    const absoluteUrls=uniq(
      [...js.matchAll(/(?:https?|wss?):\\?\/\\?\/[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+/g)]
        .map(m=>m[0].replace(/\\\//g,"/"))
    ).slice(0,500);

    const routeLiterals=uniq(
      [...js.matchAll(/["'](\/[A-Za-z0-9._~!$&()*+,;=:@%/?#-]{3,})["']/g)]
        .map(m=>m[1])
        .filter(v=>/demo|account|register|trade|server|login|user|open|auth/i.test(v))
    ).slice(0,500);

    const interestingStrings=uniq(
      [...js.matchAll(/["']([^"'\\]{3,160})["']/g)]
        .map(m=>m[1])
        .filter(v=>/demo|register|account|email|phone|deposit|leverage|hedge|password|server|login/i.test(v))
    ).slice(0,800);

    return json({
      ok:true,
      htmlStatus:htmlRes.status,
      htmlLength:html.length,
      htmlHasMetaQuotesDemo:/MetaQuotes-Demo/i.test(html),
      htmlPreview:html.slice(0,5000),
      scriptVersion,
      bundles:bundles.map(({body,...rest})=>rest),
      selectedBundle:best?{url:best.url,status:best.status,length:best.length}:null,
      snippets,
      absoluteUrls,
      routeLiterals,
      interestingStrings,
      brokerOrders:false,
      liveMoneyLocked:true
    });
  }catch(error){
    return json({
      ok:false,
      status:"ERROR",
      message:error instanceof Error?error.message:String(error),
      brokerOrders:false,
      liveMoneyLocked:true
    },500);
  }
});