/** Read-only MetaQuotes-DEMO cmd 3/4 decoder pinned to cloudQuant/pymt5 e7b5a8d.

 * Broker-only values. Never accept cached DB data, credentials, or live mode.

 * This module has no order methods and no network or storage access. */

function bytes(value) {
  if (!(value instanceof Uint8Array)) throw new Error("BROKER_PAYLOAD_UNAVAILABLE");
  return value;
}

function fixedUtf16(raw, at, size) {
  if (at < 0 || at + size > raw.length || size % 2) throw new Error("BROKER_FIELD_TRUNCATED");
  let out = "";
  for (let i = at; i < at + size; i += 2) {
    const char = raw[i] | (raw[i + 1] << 8);
    if (char === 0) break;
    out += String.fromCharCode(char);
  }
  return out;
}

function finite64(view, at) {
  const value = view.getFloat64(at, true);
  if (!Number.isFinite(value)) throw new Error("BROKER_NUMBER_INVALID");
  return value;
}

function parseDemoAccount(value) {
  const raw = bytes(value);
  // Pinned pymt5 ACCOUNT_WEB_MAIN_SCHEMA: 816-byte fixed header, build e7b5a8d.
  if (raw.length < 816) throw new Error("BROKER_ACCOUNT_TRUNCATED");
  const view = new DataView(raw.buffer, raw.byteOffset, raw.byteLength);
  const mode = raw[0];
  const rights = view.getInt32(1, true);
  const balance = finite64(view, 9);
  const credit = finite64(view, 17);
  const currency = fixedUtf16(raw, 25, 64);
  const server = fixedUtf16(raw, 355, 128);
  const profit = finite64(view, 784);
  const equity = balance + credit + profit; // Same broker fields as pinned pymt5.
  if (mode !== 1 || server !== "MetaQuotes-Demo"
      || !/^[A-Z]{3,8}$/.test(currency) || !Number.isFinite(equity)) {
    throw new Error("BROKER_NOT_VALID_DEMO");
  }
  // An investor credential must be reflected as investor or read-only rights.
  if ((rights & (8 | 512)) === 0) throw new Error("INVESTOR_RIGHTS_NOT_VERIFIED");
  return {mode: "DEMO", server, currency, balance, equity};
}

function parseDemoPositions(value) {
  const raw = bytes(value);
  // Pinned pymt5 POSITION_SCHEMA: 344-byte records, cmd=4 count + order-count.
  const SIZE = 344;
  if (raw.length < 8) throw new Error("BROKER_POSITIONS_UNAVAILABLE");
  const view = new DataView(raw.buffer, raw.byteOffset, raw.byteLength);
  const count = view.getUint32(0, true);
  if (count > 1000 || raw.length < 8 + count * SIZE) {
    throw new Error("BROKER_POSITIONS_TRUNCATED");
  }
  const positions = [];
  const seen = new Set();
  for (let i = 0; i < count; i++) {
    const at = 4 + i * SIZE;
    const ticket = view.getBigInt64(at, true);
    const symbol = fixedUtf16(raw, at + 24, 64);
    const action = view.getUint32(at + 88, true);
    const openPrice = finite64(view, at + 92);
    const sl = finite64(view, at + 108);
    const tp = finite64(view, at + 116);
    const rawVolume = view.getBigUint64(at + 124, true);
    const pnl = finite64(view, at + 132);
    const id = String(ticket);
    if (ticket <= 0n || seen.has(id)
        || !/^[A-Za-z0-9._-]{2,32}$/.test(symbol)
        || action > 1 || rawVolume === 0n
        || rawVolume > BigInt(Number.MAX_SAFE_INTEGER)
        || openPrice < 0 || sl < 0 || tp < 0) {
      throw new Error("BROKER_POSITION_INVALID");
    }
    seen.add(id);
    const lot = Number(rawVolume) / 100_000_000;
    if (!Number.isFinite(lot) || lot <= 0) throw new Error("BROKER_LOT_INVALID");
    positions.push({ticket: id, symbol, side: action === 0 ? "BUY" : "SELL",
      lot, pnl, openPrice, sl, tp});
  }
  return positions;
}

function verifiedDemoSnapshot(beforeRaw, positionRaw, afterRaw) {
  const first = parseDemoAccount(beforeRaw);
  const positions = parseDemoPositions(positionRaw);
  const last = parseDemoAccount(afterRaw);
  if (first.server !== last.server || first.currency !== last.currency
      || first.mode !== last.mode) throw new Error("BROKER_ACCOUNT_CHANGED");
  return {balance: last.balance, equity: last.equity, currency: last.currency,
    positions, server: last.server, mode: last.mode};
}

export { parseDemoAccount, parseDemoPositions, verifiedDemoSnapshot };
