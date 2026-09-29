import test from "node:test";
import assert from "node:assert/strict";
import { parseDemoAccount, parseDemoPositions, verifiedDemoSnapshot }
  from "../../supabase/functions/ai-trade-mt5-demo-validate/readback.mjs";

const utf16 = (view, start, value) => {
  for (let i = 0; i < value.length; i++)
    view.setUint16(start + i * 2, value.charCodeAt(i), true);
};
function account(mode = 1, rights = 512, server = "MetaQuotes-Demo") {
  const raw = new Uint8Array(816), view = new DataView(raw.buffer);
  raw[0] = mode;
  view.setInt32(1, rights, true);
  view.setFloat64(9, 1000, true);
  view.setFloat64(17, 20, true);
  view.setFloat64(784, -12, true);
  utf16(view, 25, "USD");
  utf16(view, 355, server);
  return raw;
}
function position() {
  const raw = new Uint8Array(352), view = new DataView(raw.buffer);
  view.setUint32(0, 1, true);
  view.setBigInt64(4, 765n, true);
  utf16(view, 28, "EURUSD");
  view.setUint32(92, 0, true);
  view.setFloat64(96, 1.10, true);
  view.setBigUint64(128, 1_000_000n, true); // 0.01 lot.
  view.setFloat64(136, -4.25, true);
  view.setUint32(348, 0, true);
  return raw;
}

test("broker-derived balance/equity/position profit and lot", () => {
  const result = verifiedDemoSnapshot(account(), position(), account());
  assert.equal(result.balance, 1000);
  assert.equal(result.equity, 1008);
  assert.equal(result.currency, "USD");
  assert.deepEqual(result.positions, [{
    ticket: "765", symbol: "EURUSD", side: "BUY", lot: 0.01,
    pnl: -4.25, openPrice: 1.1, sl: 0, tp: 0,
  }]);
});
test("empty broker position count is genuine zero, not unavailable", () => {
  assert.deepEqual(parseDemoPositions(new Uint8Array(8)), []);
  assert.throws(() => parseDemoPositions(new Uint8Array(0)), /UNAVAILABLE/);
  assert.throws(() => parseDemoPositions(new Uint8Array(4)), /UNAVAILABLE/);
});
test("reject live mode, wrong broker and non-investor rights", () => {
  assert.throws(() => parseDemoAccount(account(0)), /VALID_DEMO/);
  assert.throws(() => parseDemoAccount(account(1, 512, "Other-Demo")), /VALID_DEMO/);
  assert.throws(() => parseDemoAccount(account(1, 0)), /INVESTOR/);
});
test("detect account switch before publishing a snapshot", () => {
  assert.throws(() => verifiedDemoSnapshot(
    account(), position(), account(1, 512, "Other-Demo")
  ), /VALID_DEMO/);
});
test("reject truncated records and oversized claimed count", () => {
  assert.throws(() => parseDemoPositions(position().slice(0, 200)), /TRUNCATED/);
  const oversized = new Uint8Array(8);
  new DataView(oversized.buffer).setUint32(0, 1001, true);
  assert.throws(() => parseDemoPositions(oversized), /TRUNCATED/);
});
test("reject malformed P&L, zero lots, duplicate tickets and bad side", () => {
  const badPnl = position();
  new DataView(badPnl.buffer).setFloat64(136, Number.NaN, true);
  assert.throws(() => parseDemoPositions(badPnl), /NUMBER_INVALID/);
  const badLot = position();
  new DataView(badLot.buffer).setBigUint64(128, 0n, true);
  assert.throws(() => parseDemoPositions(badLot), /POSITION_INVALID/);
  const badSide = position();
  new DataView(badSide.buffer).setUint32(92, 2, true);
  assert.throws(() => parseDemoPositions(badSide), /POSITION_INVALID/);
  const duplicate = new Uint8Array(4 + 2 * 344 + 4);
  new DataView(duplicate.buffer).setUint32(0, 2, true);
  duplicate.set(position().slice(4, 348), 4);
  duplicate.set(position().slice(4, 348), 348);
  assert.throws(() => parseDemoPositions(duplicate), /POSITION_INVALID/);
});
