// Display-only mark overlay. Never changes strategy state, stops or executions.
export const SYMBOLS={EURUSD:'EURUSD=X',GBPUSD:'GBPUSD=X',USDJPY:'USDJPY=X',AUDUSD:'AUDUSD=X',USDCAD:'CAD=X',USDCHF:'CHF=X',NZDUSD:'NZDUSD=X',XAUUSD:'GC=F',USOIL:'CL=F',BTCUSD:'BTC-USD',ETHUSD:'ETH-USD',US30:'^DJI',NAS100:'^NDX',US500:'^GSPC'};
const num=v=>typeof v==='number'&&Number.isFinite(v)?v:null;
export function parseQuote(payload,now=Date.now()){
 const m=payload?.chart?.result?.[0]?.meta;
 const price=num(m?.regularMarketPrice),seconds=num(m?.regularMarketTime);
 if(price===null||price<=0||seconds===null||seconds*1000>now+60000)throw new Error('INVALID_QUOTE');
 return {price,ts:new Date(seconds*1000).toISOString(),source:'Yahoo Finance',proxy:m?.symbol==='GC=F'||m?.symbol==='CL=F'};
}
export function mark(row,quote,now=Date.now()){
 const stamp=Date.parse(quote?.ts),previous=Date.parse(row.last_mark_ts),entry=Date.parse(row.entry_ts);
 const fresh=Number.isFinite(stamp)&&stamp>=entry&&stamp>=previous&&stamp<=now+60000&&now-stamp<=20*60000;
 const price=num(quote?.price),risk=Number(row.risk_price),start=Number(row.entry_price);
 if(!fresh||price===null||price<=0||!Number.isFinite(risk)||risk<=0||!Number.isFinite(start)||!['UP','DOWN'].includes(row.direction))return {...row,quote_status:'UNAVAILABLE_OR_STALE',quote_source:'Stored daily mark'};
 return {...row,last_mark_price:price,last_mark_ts:quote.ts,unrealized_r:(row.direction==='UP'?1:-1)*(price-start)/risk,quote_status:'RECENT',quote_source:quote.source,quote_proxy:quote.proxy};
}
const cache=new Map();
export async function fetchQuote(symbol,fetcher=fetch,now=Date.now()){
 const upstream=SYMBOLS[symbol];if(!upstream)throw new Error('UNSUPPORTED');
 const hit=cache.get(symbol);if(hit&&now-hit.fetchedAt<15000)return hit.quote;
 let failure;
 for(const host of ['query1.finance.yahoo.com','query2.finance.yahoo.com']){
  try{
   const response=await fetcher('https://'+host+'/v8/finance/chart/'+encodeURIComponent(upstream)+'?interval=1m&range=1d',{headers:{'user-agent':'CWS-Paper-Marks/1.0'},signal:AbortSignal.timeout(7000),cache:'no-store'});
   if(!response.ok)throw new Error('QUOTE_UNAVAILABLE');
   const quote=parseQuote(await response.json(),now);cache.set(symbol,{fetchedAt:now,quote});return quote;
  }catch(error){failure=error;}
 }
 throw failure;
}
