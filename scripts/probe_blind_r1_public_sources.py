"""One-shot read-only public-source connectivity probe (no research returns).

Bitstamp public OHLC endpoints only; NO broker auth, POST, demo/live
trading, position sizing or order transport. Records only SHA-256 and
source integrity metadata, never source prices or an independent edge.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import sys
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

FORWARD_CUTOFF = 1790726400
SOURCES = {"BTCUSD":"btcusd","ETHUSD":"ethusd"}
STEPS = {"H4":14400,"D1":86400}
LIMIT = 8


def _validate_source_payload(body: dict, *, symbol: str,
                             step: int, retrieved_utc: int) -> dict:
    if not isinstance(body,dict) or not isinstance(body.get("data"),dict):
        raise ValueError("NOT_BITSTAMP_DATA")
    candles=body["data"].get("ohlc")
    if not isinstance(candles,list) or not 1<=len(candles)<=LIMIT:
        raise ValueError("INVALID_PROVIDER_COUNT")
    timestamps=[]
    for row in candles:
        if not isinstance(row,dict):
            raise ValueError("INVALID_CANDLE")
        try:
            ts=int(row["timestamp"])
            values=[float(row[k]) for k in ("open","high","low","close","volume")]
        except (KeyError,TypeError,ValueError,OverflowError) as exc:
            raise ValueError("INVALID_OHLCV") from exc
        o,h,l,c,v=values
        if (ts<0 or ts%step or ts+step>retrieved_utc or
            not all(math.isfinite(z) for z in values) or
            min(o,h,l,c)<=0 or v<0 or
            h<max(o,c,l) or l>min(o,c,h)):
            raise ValueError("UNCLOSED_OR_INVALID_PROVIDER_BAR")
        if timestamps and ts<=timestamps[-1]:
            raise ValueError("DUPLICATE_OR_UNSORTED_PROVIDER_BAR")
        timestamps.append(ts)
    gaps=[(a,b) for a,b in zip(timestamps,timestamps[1:]) if b-a!=step]
    return {
        "symbol":symbol,"bars_received":len(timestamps),
        "first_open_utc":timestamps[0],
        "last_open_utc":timestamps[-1],
        "last_closed_utc":timestamps[-1]+step,
        "source_timeframe":"H4" if step==14400 else "D1",
        "native_source_interval_seconds":step,
        "integrity_status":"SOURCE_BARS_HAVE_GAPS" if gaps else "BARS_STRUCTURALLY_VALID",
        "source_gaps":len(gaps),
        "historical_ohlc_replay_only":True,
        "independence_status":"NOT_VERIFIED",
        "broker_execution_fees_verified":False,
        "order_send_calls":0,
    }


def _fetch_public_ohlc(symbol: str, timeframe: str) -> dict:
    market=SOURCES[symbol]
    step=STEPS[timeframe]
    url=(f"https://www.bitstamp.net/api/v2/ohlc/{market}/"
         f"?step={step}&limit={LIMIT}&exclude_current_candle=true")
    out={"symbol":symbol,"timeframe":timeframe,"provider_url":url,
         "read_only":True,"account_authenticated":False,
         "status":"SOURCE_UNAVAILABLE",
         "independent_forward_trades":0,"order_send_calls":0}
    try:
        req=Request(url,method="GET",headers={
            "Accept":"application/json",
            "User-Agent":"CWS-AutoTrade-source-integrity-study/1.0"})
        with urlopen(req, timeout=14) as response:
            final=response.geturl()
            if urlsplit(final).scheme!="https" or (
                    urlsplit(final).hostname!="www.bitstamp.net"):
                raise ValueError("UNTRUSTED_REDIRECT")
            raw=response.read(1_000_001)
        if not 1<=len(raw)<=1_000_000:
            raise ValueError("INVALID_RAW_SIZE")
        now=int(time.time())
        parsed=_validate_source_payload(json.loads(raw),symbol=symbol,
                                        step=step,retrieved_utc=now)
        out.update(parsed)
        out.update({
            "status":"SOURCE_INTEGRITY_OBSERVED",
            "response_sha256":hashlib.sha256(raw).hexdigest(),
            "retrieved_at_utc":now,
            "forward_start_utc":FORWARD_CUTOFF,
            "forward_classification":"HISTORICAL_SOURCE_PROBE_NOT_PAPER",
            "retention":"METADATA_ONLY_RAW_NOT_STORED",
        })
    except (HTTPError,URLError,OSError,ValueError,KeyError,
            TypeError,json.JSONDecodeError) as exc:
        out["status"]="SOURCE_UNAVAILABLE"
        out["failure_class"]=type(exc).__name__
        # No exception body to avoid logging provider/auth/network details.
    return out


def self_test() -> None:
    step=14400
    start=1767225600  # offline synthetic Jan 2026 UTC epoch
    rows=[{"timestamp":str(start+i*step),"open":"100","high":"102",
           "low":"99","close":"101","volume":"1"} for i in range(8)]
    out=_validate_source_payload({"data":{"ohlc":rows}},
                                 symbol="BTCUSD",step=step,
                                 retrieved_utc=start+9*step)
    assert out["bars_received"]==8 and out["source_gaps"]==0
    assert out["historical_ohlc_replay_only"]
    assert not out["broker_execution_fees_verified"]
    try:
        rows[0]["high"]="99"
        _validate_source_payload({"data":{"ohlc":rows}},
                                 symbol="BTCUSD",step=step,
                                 retrieved_utc=start+9*step)
    except ValueError:
        pass
    else:
        raise AssertionError("BAD_CANDLE_NOT_REJECTED")
    print("SYNTHETIC_SOURCE_PARSER_PASS")


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--probe",action="store_true")
    args=p.parse_args()
    if args.self_test:
        self_test()
        if not args.probe:
            return 0
    if not args.probe:
        p.error("choose --self-test or --probe")
    results=[]
    for symbol in SOURCES:
        for tf in STEPS:
            r=_fetch_public_ohlc(symbol,tf)
            results.append(r)
            print("SOURCE",symbol,tf,r["status"],
                  r.get("bars_received",0),r.get("failure_class",""),flush=True)
    report={"date_utc":datetime.now(timezone.utc).isoformat(),
            "kind":"PUBLIC_READ_ONLY_SOURCE_CONNECTIVITY_ONLY",
            "forward_trades":0,"real_broker_orders":0,"rows":results,
            "all_broker_fees_verified":False,
            "no_independent_edge_claim":True}
    print("PROBE_METADATA_JSON",json.dumps(report,sort_keys=True,
                                      separators=(",",":")),flush=True)
    if not any(r["status"]=="SOURCE_INTEGRITY_OBSERVED" for r in results):
        print("SOURCE_INTEGRATION_FAIL_CLOSED: no valid provider response")
        return 2
    print("SOURCE_CONNECTIVITY_OBSERVED_NOT_FORWARD_OR_BROKER_EXECUTION")
    return 0

if __name__=="__main__":
    sys.exit(main())
