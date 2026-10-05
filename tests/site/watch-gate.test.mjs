import {test} from 'node:test';
import assert from 'node:assert/strict';
import {gate} from '../../supabase/functions/ai-trade-training-arena/watch-gate.mjs';
const now=Date.parse('2026-10-05T12:00:00Z')/1000;
const barTs=Date.parse('2026-10-04T00:00:00Z')/1000;
test('no trade without a signal or on an unfinished day',()=>{assert.equal(gate({signal:null,barTs,now}),'NO_SIGNAL');assert.equal(gate({signal:'UP',barTs:now-100,now}),'WAIT_CLOSED_BAR')});
test('old prices and bars before manual closure do not open orders',()=>{assert.equal(gate({signal:'UP',barTs:now-120*3600,now}),'STALE_DATA');assert.equal(gate({signal:'UP',barTs,manualCloseTs:now-10,now}),'WAIT_NEW_BAR')});
test('same old trend waits, changed trend permits a new signal',()=>{assert.equal(gate({signal:'UP',priorDirection:'UP',barTs,now}),'WAIT_NEW_SIGNAL');assert.equal(gate({signal:'DOWN',priorDirection:'UP',barTs,now}),'NEW_SIGNAL')});
