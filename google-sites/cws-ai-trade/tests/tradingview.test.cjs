"use strict";
const test=require("node:test");
const assert=require("node:assert/strict");
const W=require("../tradingview.js");

test("all 16 CWS markets map to third-party hosted symbols",()=>{
  assert.equal(Object.keys(W.SYMBOLS).length,16);
  for(const s of Object.keys(W.SYMBOLS)){
    assert.match(W.SYMBOLS[s],/^[A-Z0-9]+:[A-Z0-9]+$/);
    assert.equal(W.config(s,"1h").symbol,W.SYMBOLS[s]);
  }
});

test("five supported timeframes map to TradingView native intervals",()=>{
  assert.deepEqual(W.INTERVALS,{"15m":"15","30m":"30","1h":"60","4h":"240","1d":"D"});
  assert.equal(W.config("EURUSD","4h").interval,"240");
});

test("unsupported symbols and frames do not become arbitrary script input",()=>{
  assert.equal(W.config("EURUSD<script>","1h"),null);
  assert.equal(W.config("EURUSD","evil"),null);
  assert.equal(W.mount(null,"EURUSD","1h"),null);
});

test("widget configuration is hosted only, never a first-party price API",()=>{
  const c=W.config("XAUUSD","1d");
  assert.equal(c.theme,"dark");
  assert.equal(c.support_host,"https://www.tradingview.com");
  assert.equal(W.SCRIPT,"https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js");
  assert.match(W.chartUrl("BTCUSD"),/BITSTAMP%3ABTCUSD/);
  assert.equal(Object.values(c).some(v=>typeof v==="string"&&v.includes("yahoo.com")),false);
});

test("mount retains visible official attribution and safe config",()=>{
  class Node{
    constructor(tag,doc){this.tag=tag;this.ownerDocument=doc;this.children=[];this.style={};}
    append(...items){this.children.push(...items);}
    replaceChildren(...items){this.children=[...items];}
  }
  const doc={createElement(tag){return new Node(tag,doc);},
    createTextNode(text){return {textContent:text}}};
  const host=new Node("div",doc);
  const result=W.mount(host,"EURUSD","15m");
  assert.equal(result.symbol,"FX:EURUSD");
  const outer=host.children[0];
  assert.equal(outer.className,"tradingview-widget-container");
  const attribution=outer.children[1],script=outer.children[2];
  assert.match(attribution.children[0].textContent,/TradingView/);
  assert.equal(attribution.children[0].rel,"noopener nofollow noreferrer");
  assert.equal(script.src,W.SCRIPT);
  assert.equal(JSON.parse(script.textContent).interval,"15");
  assert.equal(host.children.length,1);
  W.mount(host,"XAUUSD","1d");
  assert.equal(host.children.length,1);
});
