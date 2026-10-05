// Conservative UTC daily cutoff for proxy data; not a broker-session calendar.
export function gate({signal,priorDirection=null,barTs,manualCloseTs=0,now=Date.now()/1000}) {
  if(!['UP','DOWN'].includes(signal)) return 'NO_SIGNAL';
  if(!Number.isFinite(barTs)||barTs>=Math.floor(now/86400)*86400) return 'WAIT_CLOSED_BAR';
  if(now-barTs>96*3600) return 'STALE_DATA';
  if(barTs<=manualCloseTs) return 'WAIT_NEW_BAR';
  if(priorDirection===signal) return 'WAIT_NEW_SIGNAL';
  return 'NEW_SIGNAL';
}
