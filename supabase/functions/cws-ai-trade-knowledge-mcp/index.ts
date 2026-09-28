// Read-only CWS Trading Masterbook MCP. All sources are already public in the owner's repository.
const RAW="https://raw.githubusercontent.com/trankhanhduy1508-maker/AI-TRADE/2e9ae2e17e449f1b1574963103454f4a38226b94/";
const API="https://oziktadfeenydvgobudr.supabase.co/functions/v1/ai-trade-dashboard";
const BOOK=["knowledge/CWS_TRADING_MASTERBOOK_V3_DISTILLED_2026-09-28.md","knowledge/PRACTITIONER_DISTILLED_V1.md"];
const REPORTS=["reports/MULTIASSET_10Y_BACKTEST_2026-09-27.md","reports/TF004_MAXIMUM_ROBUSTNESS_VALIDATION_2026-09-27.md"];
const MARKETS=new Set(["EURUSD","GBPUSD","USDJPY","AUDUSD","USDCAD","USDCHF","NZDUSD","XAUUSD","BTCUSD","ETHUSD","USOIL","US30","NAS100","US500"]);
const TFS=new Set(["15m","30m","1h","4h","1d"]);
const TOOLS=[
{name:"search_masterbook",description:"Search the publicly published distilled CWS Trading Masterbook and practitioner lessons. Does not include private full EPUB.",inputSchema:{type:"object",properties:{query:{type:"string",minLength:2,maxLength:350},limit:{type:"integer",minimum:1,maximum:5}},required:["query"],additionalProperties:false}},
{name:"search_backtest_evidence",description:"Search documented CWS backtests, walk-forward and execution realism; research only.",inputSchema:{type:"object",properties:{query:{type:"string",minLength:2,maxLength:350},limit:{type:"integer",minimum:1,maximum:5}},required:["query"],additionalProperties:false}},
{name:"get_public_candles",description:"Get public research candles only, not broker quotes or trade orders.",inputSchema:{type:"object",properties:{symbol:{type:"string"},timeframe:{type:"string"},limit:{type:"integer",minimum:5,maximum:120}},required:["symbol","timeframe"],additionalProperties:false}},
{name:"read_safety_gates",description:"Read invariant no-order/no-live-money capabilities.",inputSchema:{type:"object",properties:{},additionalProperties:false}}
];
const H={"access-control-allow-origin":"*","access-control-allow-headers":"authorization,content-type,accept,mcp-protocol-version","access-control-allow-methods":"GET,POST,OPTIONS"};
const response=(v,s=200)=>new Response(JSON.stringify(v),{status:s,headers:{...H,"content-type":"application/json; charset=utf-8"}});
const rpc=(id,result)=>({jsonrpc:"2.0",id,result});
const err=(id,code,message)=>({jsonrpc:"2.0",id,error:{code,message}});
const good=(data)=>({content:[{type:"text",text:JSON.stringify(data,null,2)}],structuredContent:data});
const fail=(msg)=>({isError:true,content:[{type:"text",text:msg}]});
const norm=s=>String(s||"").normalize("NFD").replace(/[\u0300-\u036f]/g,"").replace(/đ/g,"d").toLowerCase().replace(/[^a-z0-9]+/g," ");
const tokens=s=>norm(s).split(/\s+/).filter(x=>x.length>2&&!["toi","ban","mot","nhung","theo","trong","duoc","cua","voi","cho"].includes(x)).slice(0,25);
let CACHE=new Map();
async function load(path){
 const old=CACHE.get(path);if(old&&Date.now()-old.time<300000)return old.text;
 const r=await fetch(RAW+path,{signal:AbortSignal.timeout(12000)});
 if(!r.ok)throw Error("SOURCE_HTTP_"+r.status+" "+path);
 const text=await r.text();if(text.length>260000)throw Error("SOURCE_TOO_LARGE");
 CACHE.set(path,{text,time:Date.now()});return text;
}
function passages(md,path){
 let title="CWS AI Trade",buffer="",out=[];
 const flush=()=>{const t=buffer.trim().replace(/\s+/g," ");for(let i=0;i<t.length;i+=1150){const p=t.slice(i,i+1400);if(p.length>35)out.push({title,excerpt:p,source_path:path,source_url:RAW+path});}buffer="";};
 md.split(/\r?\n/).forEach(line=>{
   if(/^#{1,3} /.test(line)){flush();title=line.replace(/^#+\s*/,"");}
   else if(line.trim())buffer+=" "+line.trim();
 });flush();return out;
}
async function search(query,limit,paths){
 const ts=tokens(query);if(!ts.length)throw Error("QUERY_TOO_SHORT");
 let matches=[],unavailable=[];
 for(const path of paths){
   try{for(const p of passages(await load(path),path)){
     const title=norm(p.title),body=norm(p.excerpt);
     const score=ts.reduce((a,t)=>a+(title.includes(t)?5:0)+(body.includes(t)?2:0),0);
     if(score)matches.push({...p,score});
   }}catch(e){unavailable.push({path,error:String(e.message||e)});}
 }
 matches.sort((a,b)=>b.score-a.score);
 return {query,matches:matches.slice(0,Math.min(5,Math.max(1,Number(limit)||3))),unavailable,source_scope:"PUBLIC_DISTILLED_NOT_FULL_PRIVATE_EPUB",brokerOrders:false,liveMoneyLocked:true};
}
async function call(name,args){
 if(name==="search_masterbook")return good(await search(String(args.query||""),args.limit,BOOK));
 if(name==="search_backtest_evidence")return good(await search(String(args.query||""),args.limit,REPORTS));
 if(name==="read_safety_gates")return good({brokerOrders:false,liveMoneyLocked:true,privateBrokerData:false,privateCredentials:false,canExecute:false,note:"Chỉ nghiên cứu. Không cấp quyền broker, risk hay The5ers."});
 if(name==="get_public_candles"){
   const symbol=String(args.symbol||"").toUpperCase(),tf=String(args.timeframe||"").toLowerCase();
   if(!MARKETS.has(symbol)||!TFS.has(tf))throw Error("UNSUPPORTED_SYMBOL_OR_TIMEFRAME");
   const url=new URL(API);url.searchParams.set("format","preview-candles");url.searchParams.set("symbol",symbol);url.searchParams.set("timeframe",tf);
   const r=await fetch(url,{signal:AbortSignal.timeout(18000)});
   if(!r.ok)throw Error("PUBLIC_MARKET_HTTP_"+r.status);
   const data=await r.json();
   return good({symbol,timeframe:tf,candles:(data.candles||[]).slice(-Math.min(120,Math.max(5,Number(args.limit)||30))),brokerOrders:false,brokerQuote:false,liveMoneyLocked:true});
 }
 throw Error("UNKNOWN_TOOL");
}
Deno.serve(async req=>{
 if(req.method==="OPTIONS")return new Response(null,{status:204,headers:H});
 if(req.method==="GET")return response({ok:true,service:"cws-ai-trade-knowledge-mcp",readOnly:true,tools:TOOLS.length,liveMoneyLocked:true});
 if(req.method!=="POST")return response({error:"method not allowed"},405);
 let b;try{b=await req.json();}catch{return response(err(null,-32700,"Parse error"),400);}
 if(String(b?.method||"").startsWith("notifications/"))return new Response(null,{status:202,headers:H});
 const id=b?.id??null;
 if(b?.jsonrpc!=="2.0")return response(err(id,-32600,"Invalid request"),400);
 if(b.method==="initialize")return response(rpc(id,{protocolVersion:b.params?.protocolVersion||"2025-03-26",capabilities:{tools:{listChanged:false}},serverInfo:{name:"cws-ai-trade-knowledge",version:"0.1.0"}}));
 if(b.method==="ping")return response(rpc(id,{}));
 if(b.method==="tools/list")return response(rpc(id,{tools:TOOLS}));
 if(b.method==="tools/call"){try{return response(rpc(id,await call(String(b.params?.name||""),b.params?.arguments||{})));}catch(e){return response(rpc(id,fail(String(e.message||e))));}}
 return response(err(id,-32601,"Method not found"),404);
});