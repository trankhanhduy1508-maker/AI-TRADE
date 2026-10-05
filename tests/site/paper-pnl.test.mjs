import {test} from 'node:test';
import assert from 'node:assert/strict';
import {value,summarize} from '../../supabase/functions/ai-trade-paper-feed/paper-pnl.mjs';
const row={symbol:'BTCUSD',direction:'UP',entry_price:100,last_mark_price:102,unrealized_r:.8};
test('USD comes from entry price, fixed quantity and mark; changing R cannot change USD',()=>{
  assert.equal(value(row).quantity,10);assert.equal(value(row).pnl_usd,20);
  assert.equal(value({...row,unrealized_r:99}).pnl_usd,20);
  assert.equal(value({...row,risk_price:10000}).pnl_usd,20);
});
test('SELL signs and closed trades use exit, never stale last mark',()=>{
  assert.equal(value({...row,direction:'DOWN'}).pnl_usd,-20);
  assert.equal(value({...row,exit_price:98,last_mark_price:999,gross_r:-1},true).pnl_usd,-20);
});
test('FX quoted in JPY/CAD/CHF is converted to USD',()=>{
  const p=value({...row,symbol:'USDJPY',entry_price:150,last_mark_price:153});
  assert.equal(p.quantity,1000);assert.ok(Math.abs(p.pnl_usd-3000/153)<1e-9);
});
test('all-history gains and losses stay separate from net, including more than 100 trades',()=>{
  const open=[value(row),value({...row,direction:'DOWN'})];
  const trades=Array.from({length:105},()=>value({...row,exit_price:102,gross_r:.8},true));
  const s=summarize(open,trades);assert.equal(s.closed_count,105);assert.equal(s.gain_usd,2120);assert.equal(s.loss_usd,-20);assert.equal(s.net_usd,2100);assert.equal(s.open_usd,0);
});
test('missing/unsupported/invalid values are unknown, not zero, and totals fail closed',()=>{
  for(const patch of [{entry_price:null},{entry_price:''},{last_mark_price:0},{last_mark_price:'NaN'},{symbol:'EURJPY'},{direction:'FLAT'}]){
    const p=value({...row,...patch});assert.equal(p.pnl_usd,null);assert.equal(summarize([p],[]).net_usd,null);
  }
});
