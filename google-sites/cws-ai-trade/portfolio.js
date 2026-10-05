(function (root, factory) {
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.CWSPortfolio = api;
})(typeof window === "object" ? window : globalThis, function () {
  "use strict";
  var MARKET_ORDER = [
    "XAUUSD","EURUSD","GBPUSD","AUDUSD","NZDUSD","USDJPY",
    "USDCHF","USDCAD","EURJPY","BTCUSD","ETHUSD",
    "NAS100","US30","US500","XAGUSD","USOIL"
  ];
  function numOrNull(value) {
    if (value === null || value === undefined || value === "") return null;
    var n = Number(value);
    return Number.isFinite(n) ? n : null;
  }
  function positionOf(raw) {
    if (!raw || typeof raw !== "object") throw new Error("Vị thế không hợp lệ");
    var symbol = String(raw.symbol || "").trim().toUpperCase();
    if (!/^[A-Z0-9_.-]{3,20}$/.test(symbol)) throw new Error("Mã cặp giao dịch không hợp lệ");
    var rawSide = String(raw.side || raw.direction || "").toUpperCase();
    var side = rawSide === "UP" ? "BUY" : rawSide === "DOWN" ? "SELL" : rawSide;
    if (side !== "BUY" && side !== "SELL") throw new Error("Hướng phải là BUY hoặc SELL");
    var lot = numOrNull(raw.lot);
    var floatingPL = numOrNull(raw.floatingPL);
    if (lot !== null && (lot <= 0 || lot > 1000)) throw new Error("Lot phải lớn hơn 0 và không vượt 1000");
    if (floatingPL !== null && Math.abs(floatingPL) > 1e9) throw new Error("P/L vượt giới hạn hiển thị");
    return {symbol:symbol, side:side, lot:lot, floatingPL:floatingPL};
  }
  function parsePositions(input) {
    var rows = Array.isArray(input) ? input : input && Array.isArray(input.positions) ? input.positions : null;
    if (!rows) throw new Error("JSON phải là mảng vị thế hoặc có trường positions");
    if (rows.length > 10000) throw new Error("Tệp có quá nhiều vị thế");
    return rows.map(positionOf);
  }
  function aggregate(positions) {
    var bySymbol = new Map();
    var positionGain = 0, positionLoss = 0;
    for (var i = 0; i < positions.length; i++) {
      var p = positionOf(positions[i]);
      var g = bySymbol.get(p.symbol);
      if (!g) {
        g = {symbol:p.symbol,side:p.side,mixed:false,count:0,totalLot:0,lotKnown:0,totalPL:0,plKnown:0};
        bySymbol.set(p.symbol,g);
      }
      if (g.side !== p.side) g.mixed = true;
      g.count++;
      if (p.lot !== null) { g.lotKnown++; g.totalLot += p.lot; }
      if (p.floatingPL !== null) {
        g.plKnown++; g.totalPL += p.floatingPL;
        positionGain += Math.max(0,p.floatingPL);
        positionLoss += Math.min(0,p.floatingPL);
      }
    }
    var groups = Array.from(bySymbol.values()).map(function (g) {
      return {
        symbol:g.symbol,
        side:g.mixed ? "HỖN HỢP" : g.side,
        count:g.count,
        lot:g.lotKnown === g.count ? Math.round(g.totalLot * 1e8) / 1e8 : null,
        floatingPL:g.plKnown === g.count ? Math.round(g.totalPL * 100) / 100 : null
      };
    });
    groups.sort(function (a,b) {
      var ai = MARKET_ORDER.indexOf(a.symbol), bi = MARKET_ORDER.indexOf(b.symbol);
      if (ai < 0) ai = 1000;
      if (bi < 0) bi = 1000;
      return ai - bi || a.symbol.localeCompare(b.symbol);
    });
    var completePL = positions.length > 0 && groups.every(function (g) { return g.floatingPL !== null; });
    var completeLot = positions.length > 0 && groups.every(function (g) { return g.lot !== null; });
    var gain = null, loss = null, net = null, totalLot = null;
    if (completePL) {
      gain = positionGain;
      loss = positionLoss;
      net = gain + loss;
      gain = Math.round(gain * 100) / 100;
      loss = Math.round(loss * 100) / 100;
      net = Math.round(net * 100) / 100;
    }
    if (completeLot) totalLot = Math.round(groups.reduce(function (sum,g) { return sum + g.lot; },0)*1e8)/1e8;
    return {groups:groups,gain:gain,loss:loss,net:net,totalLot:totalLot,pairCount:groups.length,completePL:completePL,completeLot:completeLot};
  }
  return {MARKET_ORDER:MARKET_ORDER,positionOf:positionOf,parsePositions:parsePositions,aggregate:aggregate,numOrNull:numOrNull};
});