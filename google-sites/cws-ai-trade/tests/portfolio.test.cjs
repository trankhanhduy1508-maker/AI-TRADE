"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const S = require("../portfolio.js");
const trade = (symbol, side, lot, floatingPL) => ({symbol, side, lot, floatingPL});

test("16 markets are the universe, not invented positions", () => {
  assert.equal(S.MARKET_ORDER.length, 16);
  const p = S.aggregate([]);
  assert.equal(p.pairCount, 0);
  assert.equal(p.totalLot, null);
  assert.equal(p.gain, null);
  assert.equal(p.loss, null);
  assert.equal(p.net, null);
});

test("same symbol offsets net but preserves gross profit and gross loss", () => {
  const p = S.aggregate([trade("EURUSD", "BUY", 1, 20),trade("EURUSD", "SELL", 2, -5)]);
  assert.equal(p.pairCount, 1);
  assert.deepEqual(p.groups.map(g => [g.symbol,g.side,g.lot,g.floatingPL]), [["EURUSD","HỖN HỢP",3,15]]);
  assert.deepEqual([p.gain,p.loss,p.net,p.totalLot],[20,-5,15,3]);
});

test("same direction gains and losses also stay separate", () => {
  const p = S.aggregate([trade("EURUSD","BUY",0.1,20),trade("EURUSD","BUY",0.2,-5)]);
  assert.deepEqual([p.groups[0].side,p.groups[0].lot,p.groups[0].floatingPL],["BUY",0.3,15]);
  assert.deepEqual([p.gain,p.loss,p.net],[20,-5,15]);
});

test("multi-pair gain, loss, net and totals are position-accurate", () => {
  const p = S.aggregate([trade("EURUSD","BUY",1,20),trade("EURUSD","SELL",2,-5),trade("GBPUSD","BUY",1,-7),trade("XAUUSD","SELL",0.5,3)]);
  assert.equal(p.pairCount,3);
  assert.deepEqual([p.gain,p.loss,p.net,p.totalLot],[23,-12,11,4.5]);
});

test("missing P/L in any position fails closed for all monetary totals", () => {
  const p = S.aggregate([trade("EURUSD","BUY",1,20),trade("EURUSD","SELL",2,null)]);
  assert.deepEqual([p.gain,p.loss,p.net,p.totalLot],[null,null,null,3]);
  assert.equal(p.groups[0].floatingPL,null);
  assert.equal(p.completePL,false);
});

test("missing Lot in any position fails closed for total Lot independently", () => {
  const p = S.aggregate([trade("EURUSD","BUY",1,20),trade("EURUSD","SELL",null,-5)]);
  assert.deepEqual([p.gain,p.loss,p.net,p.totalLot],[20,-5,15,null]);
  assert.equal(p.groups[0].lot,null);
  assert.equal(p.completeLot,false);
});

test("paper R and synthetic volume are never cast into broker P/L or Lot", () => {
  const p = S.aggregate([{symbol:"EURUSD",side:"BUY",synthetic_volume:9,unrealizedR:3}]);
  assert.equal(p.groups[0].lot,null);
  assert.equal(p.groups[0].floatingPL,null);
  assert.equal(p.gain,null);
  assert.equal(p.totalLot,null);
});

test("JSON import validates side, lot and explicit numeric values", () => {
  assert.equal(S.parsePositions({positions:[trade("eurusd","UP","0.25","10")]} )[0].side,"BUY");
  assert.throws(()=>S.parsePositions({positions:[trade("EURUSD","BUY",-1,10)]}),/Lot/);
  assert.throws(()=>S.parsePositions({positions:[trade("EURUSD","HOLD",1,10)]}),/Hướng/);
  assert.equal(S.parsePositions({positions:[trade("EURUSD","BUY",1,Number.NaN)]})[0].floatingPL,null);
});
