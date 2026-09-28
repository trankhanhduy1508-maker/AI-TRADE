"use strict";
const test=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");

const ROOT=path.resolve(__dirname,"../../..");
const src=p=>fs.readFileSync(path.join(ROOT,p),"utf8");

test("public CWS app does not request or redistribute Yahoo candle JSON",()=>{
  const app=src("google-sites/cws-ai-trade/app.js");
  const dash=src("supabase/functions/ai-trade-dashboard/index.ts");
  assert.doesNotMatch(app,/preview-candles|query1\.finance\.yahoo\.com/);
  const start=dash.indexOf('if(publicFormat==="preview-candles"){');
  const end=dash.indexOf('const token=url.searchParams.get("t")??"";',start);
  assert.ok(start>0&&end>start);
  const route=dash.slice(start,end);
  assert.match(route,/PUBLIC_MARKET_DATA_REDISPLAY_LICENSE_UNVERIFIED/);
  assert.match(route,/status:451/);
  assert.doesNotMatch(route,/yahooCandles\s*\(/);
  assert.match(route,/broker_orders:false/);
});

test("frozen Edge API bundle retains unchanged assets while canonical Web App moves to static hosting",()=>{
  const site=src("supabase/functions/cws-ai-trade-site/index.ts");
  const anchor="const ASSETS=",start=site.indexOf(anchor)+anchor.length;
  const end=site.indexOf(";\n",start);
  assert.ok(start>anchor.length&&end>start);
  const bundle=JSON.parse(site.slice(start,end));
  for(const name of ["styles.css","portfolio.js","tradingview.js",
                     "pwa.js","manifest.webmanifest"]){
    assert.equal(bundle[name],src("google-sites/cws-ai-trade/"+name),name);
  }
  // The legacy Edge HTML/SW are deliberately frozen at v11. Their HTML
  // response is text/plain, so new Web App changes belong to static hosting.
  assert.notEqual(bundle["index.html"],src("google-sites/cws-ai-trade/index.html"));
  assert.notEqual(bundle["sw.js"],src("google-sites/cws-ai-trade/sw.js"));
  assert.notEqual(bundle["app.js"],src("google-sites/cws-ai-trade/app.js"));
  assert.match(bundle["index.html"],/MODEL_NOT_APPROVED/);
  assert.match(src("google-sites/cws-ai-trade/index.html"),/mt5-login\.html/);
  assert.match(src("google-sites/cws-ai-trade/sw.js"),/u\.pathname===ROOT/);
  assert.match(site,/https:\/\/s3\.tradingview\.com/);
  assert.match(site,/frame-src https:\/\/\*\.tradingview\.com/);
  assert.match(site,/"tradingview\.js":"application\/javascript; charset=utf-8"/);
});

test("PWA caches first-party widget shell, never third-party market stream",()=>{
  const html=src("google-sites/cws-ai-trade/index.html");
  const sw=src("google-sites/cws-ai-trade/sw.js");
  const a=html.indexOf('?asset=tradingview.js'),b=html.indexOf('?asset=app.js');
  assert.ok(a>0&&b>a);
  assert.match(sw,/cws-ai-trade-static-v5/);
  assert.match(sw,/ROOT\+"\?asset=tradingview\.js"/);
  assert.doesNotMatch(sw,/cache\.put\([^\n]*tradingview\.com/);
  assert.match(html,/hostedChart/);
  assert.match(html,/Google Sites chưa xuất bản/);
});
