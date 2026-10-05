const test=require('node:test'),assert=require('node:assert/strict');
const {payload,accountText}=require('../../google-sites/cws-ai-trade/session-client.js');
test('MT5 web login requires exact DEMO server and does not remember passwords',()=>{
 assert.deepEqual(payload('123456','secret','MetaQuotes-Demo'),{login:123456,password:'secret',server:'MetaQuotes-Demo',remember:false});
 for(const args of [['123','secret','MetaQuotes-Demo'],['123456','','MetaQuotes-Demo'],['123456','secret','Live'],['123456','secret\n','MetaQuotes-Demo']])assert.equal(payload(...args),null);
});
test('login status never presents cached account as an executed order',()=>{
 assert.match(accountText({status:'CONNECTED',account:{login:123456,server:'MetaQuotes-Demo',trade_mode:'DEMO',trade_permission:'TRADING_ALLOWED',balance:1000,equity:1000},order_send_enabled:false,orders_sent:0}),/chưa bật/);
 assert.match(accountText({status:'CONNECTED',account:{trade_mode:'REAL'}}),/không hợp lệ/);
});
