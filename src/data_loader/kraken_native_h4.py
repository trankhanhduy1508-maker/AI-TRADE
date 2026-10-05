"""Offline Kraken spot-native H4 integrity parser; never sends orders or HTTP.

A public endpoint is not a market-data licence. The caller must separately
verify retention, commercial use, account costs, and actual clock provenance.
"""
from __future__ import annotations

import hashlib
import json
from decimal import Decimal, InvalidOperation

INTERVAL = 14_400
MAX_BYTES = 4_000_000
PAIRS = {"BTCUSD": "BTC/USD", "ETHUSD": "ETH/USD"}


def _unique_object(items: list[tuple[str, object]]) -> dict:
    obj = {}
    for key, value in items:
        if key in obj:
            raise ValueError("DUPLICATE_JSON_KEY")
        obj[key] = value
    return obj


def _decimal(value: object, *, zero_ok: bool = False) -> Decimal:
    if not isinstance(value, str):
        raise ValueError("NONSTRING_SOURCE_DECIMAL")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("INVALID_SOURCE_DECIMAL") from exc
    if not number.is_finite() or number < 0 or (number == 0 and not zero_ok):
        raise ValueError("INVALID_SOURCE_DECIMAL")
    return number


def parse_kraken_spot_h4(raw: bytes, *, symbol: str, retrieved_at_utc: int) -> dict:
    """Accept only a Kraken assetVersion=1 H4 response supplied by the caller.

    Kraken documents that the final row is ALWAYS the open candle. Drop it
    unconditionally, including when an injected test clock is later.
    """
    if symbol not in PAIRS:
        raise ValueError("UNREGISTERED_KRAKEN_PAIR")
    if type(retrieved_at_utc) is not int or retrieved_at_utc <= 0:
        raise ValueError("INVALID_RETRIEVAL_CLOCK")
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise ValueError("INVALID_SOURCE_SIZE")
    try:
        payload = json.loads(raw, object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("INVALID_PROVIDER_JSON") from exc
    if not isinstance(payload, dict) or set(payload) != {"error", "result"}:
        raise ValueError("INVALID_PROVIDER_ENVELOPE")
    if payload["error"] != []:
        raise ValueError("PROVIDER_RETURNED_ERROR")
    result = payload["result"]
    pair = PAIRS[symbol]
    if not isinstance(result, dict) or set(result) != {pair, "last"}:
        raise ValueError("PROVIDER_PAIR_OR_SCHEMA_MISMATCH")
    rows = result[pair]
    if not isinstance(rows, list) or not 2 <= len(rows) <= 720:
        raise ValueError("NO_COMPLETED_H4_OR_OVERSIZE")
    if type(result["last"]) is not int or result["last"] < 0:
        raise ValueError("INVALID_PROVIDER_CURSOR")
    bars = []
    previous = None
    for row in rows[:-1]:
        if not isinstance(row, list) or len(row) != 8:
            raise ValueError("INVALID_OHLC_ROW")
        start, opening, high, low, closing, vwap, volume, count = row
        if type(start) is not int or start < 0 or start % INTERVAL:
            raise ValueError("INVALID_H4_TIME_ALIGNMENT")
        if previous is not None and start != previous + INTERVAL:
            raise ValueError("GAP_DUPLICATE_OR_UNSORTED_H4")
        if start + INTERVAL > retrieved_at_utc:
            raise ValueError("UNCLOSED_OR_FUTURE_H4")
        o, h, l, c, w, v = (_decimal(x, zero_ok=(i == 5)) for i, x in
                            enumerate((opening, high, low, closing, vwap, volume)))
        if h < max(o, l, c, w) or l > min(o, h, c, w):
            raise ValueError("INVALID_H4_OHLC_OR_VWAP")
        if type(count) is not int or count < 0:
            raise ValueError("INVALID_TRADE_COUNT")
        bars.append({"open_ts": start, "close_ts": start + INTERVAL,
                     "open": str(o), "high": str(h), "low": str(l),
                     "close": str(c), "vwap": str(w), "volume": str(v),
                     "trade_count": count, "native_h4": True})
        previous = start
    return {"symbol": symbol, "venue_pair": pair,
            "source": "KRAKEN_SPOT_NATIVE_H4", "source_timeframe": "H4",
            "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "retrieved_at_utc_claimed_by_caller": retrieved_at_utc,
            "completed_h4": len(bars), "discarded_current_candle": 1,
            "provider_source_audited": False,
            "actual_capture_clock_verified": False,
            "commercial_rights_and_storage": "NOT_VERIFIED",
            "venue_execution_costs_verified": False,
            "broker_mt5_equivalent": False, "independent_forward": False,
            "status": "OFFLINE_NATIVE_H4_INTEGRITY_ONLY", "bars": bars}
