const test=require('node:test'),assert=require('node:assert/strict');
const {normalize,number}=require('../../google-sites/cws-ai-trade/paper-orders.js');
const position={symbol:'EURUSD',direction:'UP',entry_ts:'2026-10-01T00:00:00Z',entry_price:'1.1',stop_price:'1.09',risk_price:'0.01',last_mark_price:'1.12',unrealized_r:'2',last_mark_ts:'2026-10-02T00:00:00Z'};
const feed=p=>({mode:'SIMULATION',strategy:'TF-013A-ARENA-ALL-MARKETS',positions:p,trades:[],asOf:'2026-10-02T00:00:00Z'});
test('Postgres numeric strings retain R and BUY direction',()=>{const r=normalize(feed([position]));assert.equal(r.positions[0].side,'BUY');assert.equal(number(r.positions[0].unrealized_r),2);assert.equal(r.rejected,0)});
test('missing, blank, boolean, NaN and corrupt rows are rejected, not zeroed',()=>{for(const bad of [null,'',true,'NaN',Infinity,undefined]){assert.equal(number(bad),null);assert.equal(normalize(feed([{...position,unrealized_r:bad}])).rejected,1)}});
test('wrong strategy and broker data cannot populate the arena',()=>{assert.throws(()=>normalize({...feed([]),mode:'LIVE'}));assert.throws(()=>normalize({...feed([]),strategy:'other'}))});
test('invalid symbol, timestamp and direction are omitted',()=>{for(const patch of [{symbol:'<img>'},{direction:'FLAT'},{last_mark_ts:null},{risk_price:0}])assert.equal(normalize(feed([{...position,...patch}])).positions.length,0)});
test('losing closed trades stay negative and history uses exit timestamp',()=>{const r=normalize({...feed([]),trades:[{...position,exit_ts:'2026-10-03T00:00:00Z',exit_price:1.08,gross_r:-2}]});assert.equal(r.trades.length,1);assert.equal(r.trades[0].gross_r,-2)});
test('old source timestamp is preserved rather than replaced by fetch time',()=>{assert.equal(normalize(feed([position])).asOf,'2026-10-02T00:00:00Z')});
test('USD summary rejects partial or inconsistent totals',()=>{
  const {checkedSummary}=require('../../google-sites/cws-ai-trade/paper-orders.js');
  const s={valid:true,gain_usd:20,loss_usd:-5,net_usd:15,open_usd:5,closed_usd:10,gain_r:2,loss_r:-1,net_r:1,open_r:.5,closed_r:.5,open_count:4,closed_count:105};
  assert.equal(checkedSummary(s).closed_count,105);
  for(const patch of [{net_usd:20},{gain_usd:null},{loss_usd:5},{valid:false}])assert.equal(checkedSummary({...s,...patch}),null);
  assert.equal(checkedSummary(s,1),null);
});
