import postgres from "npm:postgres@3.4.9";

const sql=postgres(Deno.env.get("SUPABASE_DB_URL")!,{
  prepare:false,max:1,connect_timeout:10,idle_timeout:20
});

const json=(body:unknown,status=200)=>new Response(JSON.stringify(body),{
  status,
  headers:{"content-type":"application/json; charset=utf-8","cache-control":"no-store"}
});

async function authorized(req:Request){
  const rows=await sql`select secret from ai_trade.cron_auth where id=1`;
  const expected=String(rows[0]?.secret??"");
  const supplied=req.headers.get("x-ai-trade-cron")??"";
  return Boolean(expected)&&supplied===expected;
}

function safeServer(value:unknown){
  const server=String(value??"MetaQuotes-Demo").trim();
  if(!server||server.length>128||!/^[A-Za-z0-9 ._+-]+$/.test(server)){
    throw new Error("INVALID_SERVER");
  }
  return server;
}

Deno.serve(async(req)=>{
  try{
    if(!(await authorized(req))) return json({ok:false,status:"UNAUTHORIZED"},401);

    let payload:any={};
    if(req.method==="POST"){
      try{ payload=await req.json(); }catch{}
    }

    const tradeServer=safeServer(payload?.trade_server);
    const gwt=String(payload?.gwt??"6").replace(/\D/g,"").slice(0,2)||"6";

    const params=new URLSearchParams({
      login:"0",
      trade_server:tradeServer,
      version:"5",
      gwt
    });

    const response=await fetch("https://metatraderweb.app/trade/json",{
      method:"POST",
      headers:{
        "content-type":"application/x-www-form-urlencoded",
        "user-agent":"AI-TRADE-MT5-DEMO-HANDSHAKE/1.0",
        "origin":"https://metatraderweb.app",
        "referer":"https://metatraderweb.app/trade?version=5"
      },
      body:params.toString()
    });

    const raw=await response.text();
    let data:any={};
    try{ data=JSON.parse(raw); }catch{
      return json({
        ok:false,
        status:"NON_JSON_UPSTREAM",
        upstreamStatus:response.status,
        brokerOrders:false,
        liveMoneyLocked:true
      },502);
    }

    const enabled=data?.enabled===true;
    const hasToken=typeof data?.token==="string"&&data.token.length>0;
    const demoReady=enabled&&hasToken&&Number(data?.version)===5;

    const result={
      ok:true,
      status:demoReady?"DEMO_HANDSHAKE_READY":"DEMO_HANDSHAKE_BLOCKED",
      mode:"HANDSHAKE_ONLY",
      tradeServer:String(data?.trade_server??tradeServer),
      version:Number(data?.version??5),
      enabled,
      hasKey:typeof data?.key==="string"&&data.key.length>0,
      hasToken,
      signalServer:typeof data?.signal_server==="string"?data.signal_server:null,
      company:typeof data?.company==="string"?data.company:null,
      demoType:Array.isArray(data?.demo_type)?data.demo_type:[],
      demoLeverage:Array.isArray(data?.demo_leverage)?data.demo_leverage:[],
      geo:data?.geo&&typeof data.geo==="object"?{
        country:data.geo.country??null,
        city:data.geo.city??null
      }:null,
      blocker:demoReady?null:(
        !enabled?"WEBTERMINAL_DISABLED_FOR_CURRENT_EGRESS":
        !hasToken?"WEBTERMINAL_TOKEN_NOT_GRANTED":
        "MT5_DEMO_HANDSHAKE_NOT_READY"
      ),
      secretValuesExposed:false,
      accountCreated:false,
      brokerOrders:false,
      liveMoneyLocked:true
    };

    await sql`
      insert into ai_trade.events(event_type,result,details)
      values(
        'mt5_demo_handshake',
        ${result.status},
        ${JSON.stringify({
          tradeServer:result.tradeServer,
          version:result.version,
          enabled:result.enabled,
          hasKey:result.hasKey,
          hasToken:result.hasToken,
          signalServer:result.signalServer,
          blocker:result.blocker,
          accountCreated:false,
          brokerOrders:false
        })}::jsonb
      )
    `;

    return json(result);
  }catch(error){
    return json({
      ok:false,
      status:"ERROR",
      message:error instanceof Error?error.message:String(error),
      accountCreated:false,
      brokerOrders:false,
      liveMoneyLocked:true
    },500);
  }
});