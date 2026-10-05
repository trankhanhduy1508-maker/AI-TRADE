"use strict";
const test=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const root=path.resolve(__dirname,"../../..");
const read=p=>fs.readFileSync(path.join(root,p),"utf8");
const mt5=require("../founder-mt5.js");

test("dashboard hides total Lot, retains position Lot for risk and audit",()=>{
 const html=read("google-sites/cws-ai-trade/index.html");
 const app=read("google-sites/cws-ai-trade/app.js");
 const model=read("google-sites/cws-ai-trade/portfolio.js");
 assert.match(html,/Số cặp có vị thế/);
 assert.doesNotMatch(html,/id="totalLot"|Số cặp \/ Tổng Lot/);
 assert.doesNotMatch(app,/text\("totalLot"/);
 assert.match(html,/<th>Lot<\/th>/);
 assert.match(model,/totalLot/);
});

test("Android is branded CWS AutoTrade and retains the same package ID",()=>{
 assert.match(read("android/app/src/main/res/values/strings.xml"),/>CWS AutoTrade<\/string>/);
 assert.match(read("android/app/build.gradle"),/applicationId 'vn\.cws\.aitrade'/);
 const builder=read("scripts/build_cws_trade_static.py");
 assert.match(builder,/CWS AutoTrade · DEMO LOCKED/);
 assert.match(builder,/manifest\["short_name"\] = "CWS AutoTrade"/);
});

test("MT5 verification needs login, password and the exact authorized server",()=>{
 assert.deepEqual(mt5.demoPayload("123456","MetaQuotes-Demo","demo-pass"),
  {login:"123456",server:"MetaQuotes-Demo",password:"demo-pass"});
 assert.equal(mt5.demoPayload("123456","MetaQuotes-Demo",""),null);
 assert.equal(mt5.demoPayload("123456","Unauthorized-Live","demo-pass"),null);
 assert.equal(mt5.demoPayload("123456","MetaQuotes-Demo ","demo-pass"),null);
});

test("broker credentials are gated behind Founder auth and cannot place orders",()=>{
 const api=read("supabase/functions/ai-trade-founder-mt5/index.ts");
 assert.match(api,/GOOGLE_FOUNDER_REQUIRED/);
 assert.match(api,/parseFounderDemoLogin\(payload\)/);
 assert.match(api,/verifyPassword:password/);
 assert.match(api,/data\.verified!==true/);
 assert.doesNotMatch(api,/samePassword\(password/);
 assert.match(api,/BROKER_DEMO_NOT_VERIFIED/);
 assert.match(api,/liveMoneyLocked:true/);
 assert.doesNotMatch(api,/order_send|create_market_order|insert into ai_trade\.order_intents/i);
 const workflow=read(".github/workflows/cws-ai-trade-android-debug.yml");
 assert.doesNotMatch(workflow,/assembleDebug|upload-artifact|gradle/);
});

test("Founder credential parser rejects invalid secrets without changing supplied password",async()=>{
 const {parseFounderDemoLogin}=await import('../../../supabase/functions/ai-trade-founder-mt5/demo-login-contract.mjs');
 const valid={login:'123456',server:'MetaQuotes-Demo',password:'demo-pass'};
 assert.deepEqual(parseFounderDemoLogin(valid),valid);
 for(const body of [null,{...valid,server:'Real'},{...valid,password:''},{...valid,password:'bad\npass'},{...valid,login:123456}]){
  assert.throws(()=>parseFounderDemoLogin(body),/INVALID_DEMO_CREDENTIAL_FORMAT/);
 }
});
