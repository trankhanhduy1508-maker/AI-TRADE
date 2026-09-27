import postgres from "npm:postgres@3.4.9";

type Row = Record<string, any>;

const UNIVERSE = [
  { key:"EURUSD", label:"EUR/USD", aliases:["EURUSD"] },
  { key:"GBPUSD", label:"GBP/USD", aliases:["GBPUSD"] },
  { key:"USDJPY", label:"USD/JPY", aliases:["USDJPY"] },
  { key:"AUDUSD", label:"AUD/USD", aliases:["AUDUSD"] },
  { key:"USDCAD", label:"USD/CAD", aliases:["USDCAD"] },
  { key:"USDCHF", label:"USD/CHF", aliases:["USDCHF"] },
  { key:"NZDUSD", label:"NZD/USD", aliases:["NZDUSD"] },
  { key:"XAUUSD", label:"Gold", aliases:["XAUUSD","GOLD"] },
  { key:"BTCUSD", label:"Bitcoin", aliases:["BTCUSD","BITCOIN"] },
  { key:"USOIL", label:"WTI Oil", aliases:["USOIL","WTI","XTIUSD"] },
  { key:"US30", label:"Dow Jones / US30", aliases:["US30","DJ30","DJI","DOW"] },
  { key:"NAS100", label:"Nasdaq 100", aliases:["NAS100","USTEC","NDX","NASDAQ"] },
  { key:"US500", label:"S&P 500", aliases:["US500","SPX500","SP500","SPX"] },
];

const sql = postgres(Deno.env.get("SUPABASE_DB_URL")!, {
  prepare:false, max:1, connect_timeout:10, idle_timeout:20,
});

const json=(body:unknown,status=200)=>new Response(JSON.stringify(body),{
  status, headers:{"content-type":"application/json; charset=utf-8"}
});

async function authorized(req:Request){
  const rows=await sql`select secret from ai_trade.cron_auth where id=1`;
  const expected=String(rows[0]?.secret??"");
  return Boolean(expected) && (req.headers.get("x-ai-trade-cron")??"")===expected;
}

function norm(v:string){ return v.toUpperCase().replace(/[^A-Z0-9]/g,""); }

function resolve(available:string[], aliases:string[]){
  const normalized=available.map(symbol=>({symbol,norm:norm(symbol)}));
  for(const alias of aliases){
    const needle=norm(alias);
    const exact=normalized.find(x=>x.norm===needle);
    if(exact) return exact.symbol;
  }
  for(const alias of aliases){
    const needle=norm(alias);
    const fuzzy=normalized.find(x=>x.norm.startsWith(needle)||x.norm.endsWith(needle));
    if(fuzzy) return fuzzy.symbol;
  }
  return null;
}

Deno.serve(async(req)=>{
  try{
    if(!(await authorized(req))) return json({ok:false,status:"UNAUTHORIZED"},401);

    const token=Deno.env.get("METAAPI_TOKEN")?.trim()??"";
    const accountId=Deno.env.get("METAAPI_ACCOUNT_ID")?.trim()??"";
    if(!token||!accountId){
      return json({
        ok:true,
        status:"CONFIG_BLOCKED",
        missing:[...(token?[]:["METAAPI_TOKEN"]),...(accountId?[]:["METAAPI_ACCOUNT_ID"])],
        tradingActivated:false,
        liveMoneyLocked:true
      });
    }

    const module=await import("npm:metaapi.cloud-sdk@29.3.3/esm-node");
    const MetaApi=module.default;
    const api=new MetaApi(token);
    const account=await api.metatraderAccountApi.getAccount(accountId);

    if(String(account.platform).toLowerCase()!=="mt5") throw new Error("MT5_REQUIRED");
    if(!String(account.server??"").toLowerCase().includes("demo")) throw new Error("DEMO_SERVER_REQUIRED");
    if(String(account.state).toUpperCase()!=="DEPLOYED") await account.deploy();
    await account.waitConnected();

    const connection=account.getRPCConnection();
    await connection.connect();
    await connection.waitSynchronized();

    const info=await connection.getAccountInformation();
    if(String(info.type)!=="ACCOUNT_TRADE_MODE_DEMO") throw new Error("DEMO_ACCOUNT_REQUIRED");
    if(info.tradeAllowed===false||info.investorMode===true) throw new Error("ACCOUNT_TRADING_DISABLED");

    const symbols=(await connection.getSymbols()).map((x:unknown)=>String(x));
    const mappings=UNIVERSE.map(item=>({
      ...item,
      brokerSymbol:resolve(symbols,item.aliases),
    }));

    for(const item of mappings){
      await sql`
        insert into ai_trade.broker_symbol_map(
          instrument_key,broker_symbol,supported,aliases,checked_at,details
        )
        values(
          ${item.key},
          ${item.brokerSymbol},
          ${Boolean(item.brokerSymbol)},
          ${JSON.stringify(item.aliases)}::jsonb,
          now(),
          ${JSON.stringify({label:item.label})}::jsonb
        )
        on conflict (instrument_key) do update set
          broker_symbol=excluded.broker_symbol,
          supported=excluded.supported,
          aliases=excluded.aliases,
          checked_at=excluded.checked_at,
          details=excluded.details
      `;
    }

    return json({
      ok:true,
      status:"READY_READ_ONLY",
      accountType:String(info.type),
      availableSymbolCount:symbols.length,
      supportedCount:mappings.filter(x=>x.brokerSymbol).length,
      mappings,
      tradingActivated:false,
      liveMoneyLocked:true
    });
  }catch(error){
    return json({
      ok:false,
      status:"BLOCKED",
      error:error instanceof Error?error.message:String(error),
      tradingActivated:false,
      liveMoneyLocked:true
    },200);
  }
});