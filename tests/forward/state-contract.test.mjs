import test from 'node:test';
import assert from 'node:assert/strict';
import {decodePosition} from '../../supabase/functions/ai-trade-forward-shadow/state-contract.mjs';
const valid={direction:'UP',entryTs:1790947800,entryPrice:100,stop:90,initialStop:90,riskPrice:10};
test('object and legacy JSON string round-trip preserve stop and direction',()=>{
 assert.deepEqual(decodePosition(valid),valid);
 assert.deepEqual(decodePosition(JSON.stringify(valid)),valid);
});
test('empty state remains empty',()=>{assert.equal(decodePosition(null),null);});
test('corrupt position cannot become a trade or silently disappear',()=>{
 for(const x of [undefined,'bad',{},[],{...valid,direction:'undefined'}, {...valid,stop:null}, {...valid,riskPrice:0}, {...valid,entryPrice:NaN}, {...valid,initialStop:110}, {...valid,entryTs:1.5}])
  assert.throws(()=>decodePosition(x),/POSITION_STATE_INVALID/);
});
test('short state and tightened trailing stop remain valid',()=>{
 const short={...valid,direction:'DOWN',stop:105,initialStop:110};
 assert.deepEqual(decodePosition(short),short);
 assert.deepEqual(decodePosition({...valid,stop:110}),{...valid,stop:110});
});
