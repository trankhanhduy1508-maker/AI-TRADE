Deno.serve(()=>new Response(JSON.stringify({
  ok:false,
  status:"RESEARCH_PROBE_RETIRED",
  accountCreated:false,
  brokerOrders:false,
  liveMoneyLocked:true
}),{
  status:410,
  headers:{"content-type":"application/json; charset=utf-8","cache-control":"no-store"}
}));
