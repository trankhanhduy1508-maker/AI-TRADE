import {test} from 'node:test';
import assert from 'node:assert/strict';
import {serve} from '../../scripts/site-runtime/paper-worker.mjs';
const request=new Request('https://site.example/api/paper-orders');
test('feed key stays upstream only; private no-store response',async()=>{
  const r=await serve(request,{CWS_PAPER_FEED_KEY:'test-key'},{},async(url,options)=>{
    assert.equal(options.headers.authorization,'Bearer test-key');
    assert.match(url,/ai-trade-paper-feed$/);
    return new Response('{"mode":"SIMULATION"}');
  });
  assert.equal(r.status,200);assert.match(r.headers.get('cache-control'),/no-store/);assert.ok(!(await r.text()).includes('test-key'));
});
test('missing secret, upstream denial and outages fail closed',async()=>{
  assert.equal((await serve(request,{},{})).status,503);
  assert.equal((await serve(request,{CWS_PAPER_FEED_KEY:'test'},{},async()=>new Response('private detail',{status:401}))).status,503);
  assert.equal((await serve(request,{CWS_PAPER_FEED_KEY:'test'},{},async()=>{throw new Error('secret')})).status,503);
});
test('POST never reaches feed, unknown paths never reveal server code',async()=>{
  assert.equal((await serve(new Request(request.url,{method:'POST'}),{},{},()=>assert.fail())).status,405);
  assert.equal((await serve(new Request('https://site.example/server/index.js'),{},{})).status,404);
});
test('static shell and HEAD preserve content types',async()=>{
  const assets={'/index.html':{type:'text/html; charset=utf-8',body:btoa('<html>shell</html>')}};
  assert.equal(await (await serve(new Request('https://site.example/'),{},assets)).text(),'<html>shell</html>');
  const head=await serve(new Request('https://site.example/',{method:'HEAD'}),{},assets);assert.equal(await head.text(),'');
});
