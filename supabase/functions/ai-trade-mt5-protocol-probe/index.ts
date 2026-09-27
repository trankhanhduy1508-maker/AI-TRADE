import postgres from "npm:postgres@3.4.9";

const sql=postgres(Deno.env.get("SUPABASE_DB_URL")!,{prepare:false,max:1,connect_timeout:10,idle_timeout:20});
const json=(b:unknown,s=200)=>new Response(JSON.stringify(b),{status:s,headers:{"content-type":"application/json; charset=utf-8"}});

async function authorized(req:Request){
  const rows=await sql`select secret from ai_trade.cron_auth where id=1`;
  const expected=String(rows[0]?.secret??"");
  return Boolean(expected)&&(req.headers.get("x-ai-trade-cron")??"")===expected;
}

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
    if(!(await authorized(req))) return json({ok:false,status:"UNAUTHORIZED"},401);

    const base="https://trade.mql5.com/trade?version=5";
    const htmlRes=await fetch(base,{headers:{"user-agent":"Mozilla/5.0 AI-TRADE protocol probe"}});
    const html=await htmlRes.text();
    const scriptMatches=[...html.matchAll(/<script[^>]+src=["']([^"']*mt5[^"']*\.js[^"']*)["']/gi)].map(m=>m[1]);
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
      .slice(0,200);

    return json({
      ok:true,
      htmlStatus:htmlRes.status,
      htmlLength:html.length,
      htmlHasMetaQuotesDemo:/MetaQuotes-Demo/i.test(html),
      htmlDemoContexts:contexts(html,"Open a Demo Account",600,5),
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