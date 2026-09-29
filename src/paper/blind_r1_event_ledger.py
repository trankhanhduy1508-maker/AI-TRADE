"""R1-forward-only append-only research provenance gate.

NO network client, broker import, signal engine, orders, credentials or money.
This ledger quarantines every external bar as UNVERIFIED until an independent
provider/source audit. Synthetic test clocks are not eligible evidence.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import math
import os
import re
import time
from pathlib import Path

FORWARD_START_UTC = 1790726400  # 2026-09-30T00:00:00Z
GENESIS = "0" * 64
VALID_SYMBOLS = frozenset((
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF",
    "NZDUSD", "EURJPY", "GBPJPY", "EURGBP", "AUDJPY", "EURCHF",
    "NZDJPY", "BTCUSD", "ETHUSD", "XAUUSD", "XAGUSD",
    "WTI", "Brent", "S&P 500", "Nasdaq 100", "Dow Jones",
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META",
))
FIELDS = frozenset((
    "schema_version", "kind", "symbol", "timeframe", "provider",
    "provider_url", "source_bar_id", "open_ts", "close_ts",
    "retrieved_ts", "closed", "open", "high", "low", "close",
    "volume", "raw_sha256", "instrument_type",
))


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def _is_sha(s: object) -> bool:
    return isinstance(s, str) and re.fullmatch(r"[0-9a-f]{64}", s) is not None


def validate_observation(e: dict, *, now_utc: int) -> None:
    if not isinstance(e, dict) or set(e) != FIELDS:
        raise ValueError("SCHEMA_MISMATCH")
    if e["schema_version"] != 1 or e["kind"] != "BAR_CLOSED":
        raise ValueError("INVALID_EVENT_TYPE")
    if e["symbol"] not in VALID_SYMBOLS or e["timeframe"] not in ("H4", "D1"):
        raise ValueError("NOT_PREREGISTERED_INSTRUMENT")
    if not isinstance(e["source_bar_id"], str) or not e["source_bar_id"].strip():
        raise ValueError("MISSING_SOURCE_EVENT_ID")
    if not _is_sha(e["raw_sha256"]) or e["raw_sha256"] == GENESIS:
        raise ValueError("MISSING_RAW_SOURCE_HASH")
    for name in ("open_ts", "close_ts", "retrieved_ts"):
        if not isinstance(e[name], int) or isinstance(e[name], bool):
            raise ValueError("INVALID_UTC_TIMESTAMP")
    if not (e["open_ts"] < e["close_ts"] and
            FORWARD_START_UTC <= e["close_ts"] <= e["retrieved_ts"] <= now_utc):
        raise ValueError("NOT_NEW_ACTUALLY_CLOSED_FORWARD_BAR")
    if e["closed"] is not True:
        raise ValueError("UNCLOSED_CANDLE")
    if e["provider"] == "BITSTAMP_PUBLIC_OHLC":
        if e["symbol"] not in ("BTCUSD", "ETHUSD"):
            raise ValueError("BITSTAMP_SYMBOL_NOT_REGISTERED")
        if not isinstance(e["provider_url"], str) or not e["provider_url"].startswith(
                "https://www.bitstamp.net/api/v2/ohlc/"):
            raise ValueError("INVALID_BITSTAMP_SOURCE_URL")
        if e["instrument_type"] != "BITSTAMP_USD_SPOT":
            raise ValueError("MISMATCHED_INSTRUMENT_TYPE")
        if e["close_ts"]-e["open_ts"] != (
                14400 if e["timeframe"] == "H4" else 86400):
            raise ValueError("NOT_NATIVE_BITSTAMP_INTERVAL")
    elif e["provider"] == "YAHOO_FINANCE_CHART":
        if (e["symbol"] in ("BTCUSD", "ETHUSD") or
                e["timeframe"] != "D1"):
            raise ValueError("UNSUPPORTED_YAHOO_SOURCE_TF")
        if (not isinstance(e["provider_url"], str)
            or not (e["provider_url"].startswith(
                "https://query1.finance.yahoo.com/v8/finance/chart/")
                    or e["provider_url"].startswith(
                "https://query2.finance.yahoo.com/v8/finance/chart/"))):
            raise ValueError("INVALID_YAHOO_SOURCE_URL")
        if e["instrument_type"] not in (
                "YAHOO_INDICATIVE_FX", "YAHOO_FRONT_MONTH_FUTURES_PROXY",
                "YAHOO_NONTRADEABLE_INDEX", "YAHOO_STOCK_UNADJUSTED_DIVIDEND"):
            raise ValueError("UNSUPPORTED_YAHOO_INSTRUMENT_TYPE")
        if e["close_ts"]-e["open_ts"] > 86400:
            raise ValueError("INVALID_DAILY_DURATION")
    else:
        raise ValueError("PROVIDER_NOT_REGISTERED")
    numbers = (e[k] for k in ("open","high","low","close","volume"))
    if not all(type(v) in (int,float) and math.isfinite(v) for v in numbers):
        raise ValueError("NONFINITE_OHLCV")
    if min(e[k] for k in ("open","high","low","close")) <= 0:
        raise ValueError("NONPOSITIVE_OHLC")
    if (e["volume"] < 0 or
        e["high"] < max(e["open"],e["close"],e["low"]) or
        e["low"] > min(e["open"],e["close"],e["high"])):
        raise ValueError("INVALID_OHLCV")


def _read_and_verify(fp) -> tuple[str,int,dict,dict]:
    fp.seek(0)
    last_hash, count, previous, originals = GENESIS, 0, {}, {}
    for lineno,line in enumerate(fp, 1):
        try:
            item = json.loads(line)
            if set(item) != {"seq","prev_hash","event_hash","record_hash",
                             "provenance_status","event"}:
                raise ValueError("ENVELOPE_SCHEMA")
            if item["seq"] != count+1 or item["prev_hash"] != last_hash:
                raise ValueError("BROKEN_HASH_CHAIN")
            if item["provenance_status"] != "UNVERIFIED_EXTERNAL_SOURCE":
                raise ValueError("UNAUTHORIZED_PROMOTION")
            e = item["event"]
            if digest(e) != item["event_hash"]:
                raise ValueError("EVENT_HASH_MISMATCH")
            expected = digest({"seq":item["seq"],"prev_hash":item["prev_hash"],
                               "event_hash":item["event_hash"],
                               "provenance_status":item["provenance_status"]})
            if expected != item["record_hash"]:
                raise ValueError("RECORD_HASH_MISMATCH")
            key=(e["provider"],e["symbol"],e["timeframe"])
            ident=(*key,e["source_bar_id"])
            if ident in originals or e["close_ts"] <= previous.get(key,-1):
                raise ValueError("DUPLICATE_OR_NONCHRONOLOGICAL_EVENT")
            previous[key] = e["close_ts"]
            originals[ident] = digest(e)
            last_hash, count = expected, count+1
        except (ValueError,TypeError,KeyError,AttributeError) as exc:
            raise ValueError(f"CORRUPTED_LEDGER_LINE_{lineno}: {exc}") from exc
    return last_hash,count,previous,originals


def append_actual_observation(path: str | Path, e: dict) -> dict:
    """Write strictly at the *real* host UTC clock. Never paper-order send."""
    return _append(path,e,now_utc=int(time.time()))


def _append(path: str | Path, e: dict, *, now_utc: int) -> dict:
    """Injected now_utc is ONLY for deterministic unit tests."""
    validate_observation(e,now_utc=now_utc)
    p=Path(path)
    p.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(p,os.O_CREAT|os.O_RDWR|os.O_APPEND,0o600)
    with os.fdopen(fd,"a+",encoding="utf-8") as fp:
        fcntl.flock(fp,fcntl.LOCK_EX)
        prior, count, previous, originals = _read_and_verify(fp)
        key=(e["provider"],e["symbol"],e["timeframe"])
        ident=(*key,e["source_bar_id"])
        fingerprint=digest(e)
        if ident in originals:
            if originals[ident] != fingerprint:
                raise ValueError("CONFLICTING_DUPLICATE_ID")
            return {"status":"DUPLICATE_NO_WRITE","seq":count,
                    "last_record_hash":prior,
                    "forward_independence":"NOT_VERIFIED"}
        if e["close_ts"] <= previous.get(key,-1):
            raise ValueError("OUT_OF_ORDER_BAR")
        if e["provider"]=="BITSTAMP_PUBLIC_OHLC" and key in previous:
            expected=previous[key]+(
                14400 if e["timeframe"]=="H4" else 86400)
            if e["close_ts"]!=expected:
                raise ValueError("BITSTAMP_MISSING_OR_IRREGULAR_BAR")
        status="UNVERIFIED_EXTERNAL_SOURCE"
        envelope={"seq":count+1,"prev_hash":prior,"event_hash":fingerprint,
                  "provenance_status":status,"event":e}
        envelope["record_hash"]=digest({
            "seq":count+1,"prev_hash":prior,"event_hash":fingerprint,
            "provenance_status":status})
        fp.seek(0,os.SEEK_END)
        fp.write(canonical(envelope).decode("utf-8")+"\n")
        fp.flush()
        os.fsync(fp.fileno())
        return {"status":"APPENDED_QUARANTINED","seq":count+1,
                "last_record_hash":envelope["record_hash"],
                "forward_independence":"NOT_VERIFIED",
                "paper_orders_created":0}


def verify_ledger(path: str | Path) -> dict:
    with open(path,"r",encoding="utf-8") as fp:
        last,count,_,_=_read_and_verify(fp)
    return {"records":count,"last_record_hash":last,
            "source_audit":"NOT_VERIFIED",
            "paper_orders_created":0}
