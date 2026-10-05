import test from 'node:test';
import assert from 'node:assert/strict';
let evaluate;
try { ({ordinaryDemoPreflight:evaluate}=await import('../../supabase/functions/ai-trade-mt5-session/ordinary-demo-preflight.mjs')); } catch {}
const context=()=>({
 session:{account_login:123456,server:'MetaQuotes-Demo',trade_permission:'TRADING_ALLOWED'},
 config:{enabled:true,demo_send_enabled:true,strategy_id:'TF-013A-FORWARD-DIVERSIFIED-TREND'},
 policy:{profile:'ORDINARY_MT5_DEMO',account_login:'123456',server:'MetaQuotes-Demo',approved:true,approval_evidence:'fixture-only',max_trade_risk_fraction:.01,max_portfolio_risk_fraction:.02,max_drawdown_fraction:.03,max_consecutive_losses:3,max_total_volume:.01},
 providerConfigured:true,
 broker:{verified:true,login:'123456',server:'MetaQuotes-Demo',mode:'DEMO',tradeAllowed:true,readOnly:false,fresh:true},
 controls:{known:true,kill_active:false,paused:false,reconciled:true},
 strategyValidated:true,executionLaneImplemented:true
});
test('ordinary DEMO preflight exists',()=>assert.equal(typeof evaluate,'function'));
test('malformed or missing state fails closed without crashing',()=>{
 assert.equal(typeof evaluate,'function');
 for(const c of [null,undefined,{}, {session:null,config:null,policy:null,broker:null,controls:null}]){
  assert.equal(evaluate(c).preflight_ready,false);
 }
});
test('all preconditions do not themselves enable an order',()=>{
 assert.equal(typeof evaluate,'function');const r=evaluate(context());
 assert.equal(r.preflight_ready,true);assert.equal(r.order_send_enabled,false);assert.equal(r.orders_sent,0);
 assert.equal(r.profile,'ORDINARY_MT5_DEMO');assert.equal(r.prop_approval_required,false);
});
test('cached login does not become fresh broker execution proof',()=>{
 assert.equal(typeof evaluate,'function');const c=context();delete c.broker;
 assert.ok(evaluate(c).blockers.includes('BROKER_STATE_UNVERIFIED'));
});
test('real or different account cannot pass',()=>{
 assert.equal(typeof evaluate,'function');for(const changes of [{mode:'REAL'},{login:'654321'},{server:'Other-Demo'},{readOnly:true},{tradeAllowed:false}]){
  const c=context();Object.assign(c.broker,changes);assert.equal(evaluate(c).preflight_ready,false);
 }
});
test('risk flags need explicit finite approved limits and account binding',()=>{
 assert.equal(typeof evaluate,'function');for(const changes of [{approved:false},{max_trade_risk_fraction:null},{max_total_volume:NaN},{max_consecutive_losses:2.5},{account_login:'654321'},{approval_evidence:''}]){
  const c=context();Object.assign(c.policy,changes);assert.ok(evaluate(c).blockers.includes('RISK_NOT_APPROVED'));
 }
});
test('funded profile is not reclassified as ordinary DEMO',()=>{
 assert.equal(typeof evaluate,'function');const c=context();c.policy.profile='THE5ERS';
 assert.ok(evaluate(c).blockers.includes('RISK_NOT_APPROVED'));
});
test('restart/kill/missing strategy and execution readiness remain blocked',()=>{
 assert.equal(typeof evaluate,'function');for(const key of ['strategyValidated','executionLaneImplemented','providerConfigured']){
 const c=context();c[key]=false;assert.equal(evaluate(c).preflight_ready,false);
 }for(const changes of [{known:false},{kill_active:true},{paused:true},{reconciled:false}]){
 const c=context();Object.assign(c.controls,changes);assert.equal(evaluate(c).preflight_ready,false);
 }
});
