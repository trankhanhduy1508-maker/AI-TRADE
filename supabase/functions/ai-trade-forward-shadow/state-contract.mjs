/** Decode historical storage without inventing missing position fields. */
export function decodePosition(raw) {
 if(raw===null)return null;
 let p=raw;
 if(typeof p==='string'){
  try{p=JSON.parse(p);}catch{throw Error('POSITION_STATE_INVALID');}
 }
 if(!p || typeof p!=='object' || Array.isArray(p) || !['UP','DOWN'].includes(p.direction))
  throw Error('POSITION_STATE_INVALID');
 for(const k of ['entryTs','entryPrice','stop','initialStop','riskPrice'])
  if(typeof p[k]!=='number' || !Number.isFinite(p[k]) || p[k]<=0)throw Error('POSITION_STATE_INVALID');
 if(!Number.isInteger(p.entryTs))throw Error('POSITION_STATE_INVALID');
 const risk=p.direction==='UP'?p.entryPrice-p.initialStop:p.initialStop-p.entryPrice;
 if(risk<=0 || Math.abs(risk-p.riskPrice)>Math.max(1e-8,p.riskPrice*1e-6))
  throw Error('POSITION_STATE_INVALID');
 return {direction:p.direction,entryTs:p.entryTs,entryPrice:p.entryPrice,stop:p.stop,initialStop:p.initialStop,riskPrice:p.riskPrice};
}
