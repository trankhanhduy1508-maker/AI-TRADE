// Versioned paper sizing only. Not lots/contracts or a broker valuation.
// Quantity is fixed by entry price, never by R or risk distance.
export const PROFILE={id:'PAPER_NOTIONAL_1000_V1',notionalUsd:1000};
const usdBase=new Set(['USDJPY','USDCHF','USDCAD']);
const usdQuote=new Set(['EURUSD','GBPUSD','AUDUSD','NZDUSD','XAUUSD','USOIL','BTCUSD','ETHUSD','US30','NAS100','US500']);
const num=v=>(typeof v==='number'||(typeof v==='string'&&v.trim()!==''))&&Number.isFinite(Number(v))?Number(v):null;
export function value(row,closed=false){
  const entry=num(row.entry_price),exit=num(closed?row.exit_price:row.last_mark_price);
  if(entry===null||exit===null||entry<=0||exit<=0||!['UP','DOWN'].includes(row.direction)||(!usdBase.has(row.symbol)&&!usdQuote.has(row.symbol)))return {...row,pnl_usd:null,quantity:null,sizing_profile:PROFILE.id};
  const quantity=usdBase.has(row.symbol)?PROFILE.notionalUsd:PROFILE.notionalUsd/entry;
  const change=(row.direction==='UP'?1:-1)*(exit-entry);
  // For USD-base FX the quote P/L is converted into USD at the mark/exit rate.
  const pnl=quantity*change/(usdBase.has(row.symbol)?exit:1);
  return {...row,quantity:Number.isFinite(quantity)?quantity:null,pnl_usd:Number.isFinite(pnl)?pnl:null,sizing_profile:PROFILE.id};
}
export function summarize(positions,trades){
  const all=[...positions,...trades];
  const valid=all.every(r=>num(r.pnl_usd)!==null&&num(r.quantity)>0&&num(r.unrealized_r??r.gross_r)!==null);
  const add=(rows,key,predicate=()=>true)=>rows.reduce((sum,r)=>sum+(predicate(num(r[key]))?num(r[key]):0),0);
  const rAll=all.map(r=>({...r,result_r:r.unrealized_r??r.gross_r}));
  const summary={valid,open_count:positions.length,closed_count:trades.length,
    gain_usd:valid?add(all,'pnl_usd',v=>v>0):null,loss_usd:valid?add(all,'pnl_usd',v=>v<0):null,
    net_usd:valid?add(all,'pnl_usd'):null,open_usd:valid?add(positions,'pnl_usd'):null,closed_usd:valid?add(trades,'pnl_usd'):null,
    gain_r:valid?add(rAll,'result_r',v=>v>0):null,loss_r:valid?add(rAll,'result_r',v=>v<0):null,
    net_r:valid?add(rAll,'result_r'):null,open_r:valid?add(positions,'unrealized_r'):null,closed_r:valid?add(trades,'gross_r'):null};
  if(Object.values(summary).some(v=>typeof v==='number'&&!Number.isFinite(v)))return {...summary,valid:false,gain_usd:null,loss_usd:null,net_usd:null,open_usd:null,closed_usd:null,gain_r:null,loss_r:null,net_r:null,open_r:null,closed_r:null};
  return summary;
}
