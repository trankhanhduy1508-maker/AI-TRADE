const test=require("node:test");
const assert=require("node:assert/strict");
const m=require("../founder-mt5.js");
const site={origin:"https://trankhanhduy1508-maker.github.io",pathname:"/AI-TRADE/mt5-login.html"};
test("OAuth only on official Web App",()=>{
 assert.equal(m.trustedLocation(site),true);
 for(const origin of ["https://raw.githack.com","https://evil.example","http://trankhanhduy1508-maker.github.io"])
  assert.equal(m.authUrl({...site,origin}),null);
});
test("OAuth redirect stays first-party and never includes credentials",()=>{
 const url=new URL(m.authUrl(site));
 assert.equal(url.origin,"https://oziktadfeenydvgobudr.supabase.co");
 assert.equal(url.searchParams.get("provider"),"google");
 assert.equal(url.searchParams.get("redirect_to"),site.origin+site.pathname);
 assert.equal(url.searchParams.get("password"),null);
});
test("accept only linked-demo payload shape",()=>{
 assert.deepEqual(m.demoPayload("123456","MetaQuotes-Demo","abcdef"),
  {login:"123456",server:"MetaQuotes-Demo",password:"abcdef"});
});
test("reject REAL accounts and untrusted server",()=>{
 assert.equal(m.demoPayload("123456","Live-Server","abcdef"),null);
 assert.equal(m.demoPayload("123456","MetaQuotes-Demo ","abcdef"),null);
});
test("reject invalid account numbers and passwords",()=>{
 assert.equal(m.demoPayload("123<script>","MetaQuotes-Demo","abcdef"),null);
 assert.equal(m.demoPayload("000000","MetaQuotes-Demo","abcdef"),null);
 assert.equal(m.demoPayload("123456","MetaQuotes-Demo","x"),null);
 assert.equal(m.demoPayload("123456","MetaQuotes-Demo","x".repeat(33)),null);
});
test("never claim prior verification means connected live socket",()=>{
 const s=m.visualStatus({login:"123456",server:"MetaQuotes-Demo",recentlyVerified:false},
  {liveMoneyLocked:true,autoTradeActive:false});
 assert.match(s,/HẾT HẠN/);assert.match(s,/Auto Trade: LOCKED/);
});
test("missing or invalid live-money lock fails closed",()=>{
 assert.match(m.visualStatus({},{}),/KHÔNG XÁC ĐỊNH/);
});
test("no private account is invented",()=>{
 assert.match(m.visualStatus(null,{liveMoneyLocked:true}),/Chưa có tài khoản/);
});
