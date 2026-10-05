import test from 'node:test';
import assert from 'node:assert/strict';
import {corsHeaders} from '../../supabase/functions/ai-trade-mt5-session/web-origin.mjs';
test('only published CWS web origin can read credential responses',()=>{
 const origin='https://cws-autotrade-lab.trankhanhduy1508.chatgpt.site';
 assert.equal(corsHeaders(origin)['access-control-allow-origin'],origin);
 for(const bad of ['https://evil.test',origin+'.evil.test','null'])assert.equal(corsHeaders(bad),null);
 assert.equal(corsHeaders(''),null);
});
