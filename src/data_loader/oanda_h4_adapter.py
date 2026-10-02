"""Parse authorized OANDA fxPractice historical native H4/D responses.

RESEARCH ONLY. Intentionally NO network/bearer-token/order-send code.
OANDA historical candle prices can differ from a practice account's live
price group: parse/source authenticity is NOT verified execution evidence.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
PRACTICE_ENDPOINT = "https://api-fxpractice.oanda.com"
SOURCE_TYPE = "OANDA_PRACTICE_HISTORICAL_MBA_NOT_ACCOUNT_EXECUTION"
CANONICAL_ALIGNMENT = {"dailyAlignment": "17",
                       "alignmentTimezone": "America/New_York",
                       "weeklyAlignment": "Friday", "smooth": "false"}


def build_historical_read_url(instrument: str, *,
                              granularity: str = "H4",
                              count: int = 5000) -> str:
    """Construct strictly a practice historical GET URL, never an order URL."""
    if not isinstance(instrument, str) or not re.fullmatch(
            r"[A-Z0-9]{2,12}_[A-Z0-9]{2,12}", instrument):
        raise ValueError("INVALID_OANDA_INSTRUMENT_ID")
    if granularity not in ("H4", "D"):
        raise ValueError("ONLY_NATIVE_H4_OR_D_SUPPORTED")
    if type(count) is not int or not 1 <= count <= 5000:
        raise ValueError("INVALID_OANDA_PAGE_SIZE")
    query = {"granularity": granularity, "price": "MBA", "count": count,
             **CANONICAL_ALIGNMENT}
    return (PRACTICE_ENDPOINT + "/v3/instruments/" + instrument +
            "/candles?" + urlencode(query))


def _utc_start(source: object) -> int:
    if not isinstance(source, str) or not re.fullmatch(
        r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,9})?(?:Z|[+-]\d\d:\d\d)",
        source,
    ):
        raise ValueError("INVALID_OANDA_CANDLE_TIME")
    fraction = source.split(".", 1)[1].split("Z")[0].split("+")[0].split("-")[0] if "." in source else ""
    if fraction and fraction.strip("0"):
        raise ValueError("SUBSECOND_NONALIGNED_CANDLE")
    try:
        dt = datetime.fromisoformat(source.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("INVALID_OANDA_CANDLE_TIME") from exc
    if dt.utcoffset() is None or dt.minute or dt.second:
        raise ValueError("NONALIGNED_CANDLE_TIME")
    timestamp = int(dt.timestamp())
    if timestamp < 0:
        raise ValueError("UNSUPPORTED_PRE_EPOCH_TIME")
    return timestamp


def _closing_time(start: int, granularity: str) -> int:
    if granularity == "H4":
        local = datetime.fromtimestamp(start, tz=timezone.utc).astimezone(NY)
        if local.minute != 0 or local.hour not in (1, 5, 9, 13, 17, 21):
            raise ValueError("H4_NOT_EXPECTED_NEW_YORK_ALIGNMENT")
        # H4 is aligned to New York day boundaries. Across a DST shift,
        # adding 14400 UTC seconds may silently assert the wrong close.
        # Quarantine that exceptional window until a real broker response
        # confirms its candle boundary; never invent the elapsed period.
        if local.utcoffset() != (local + timedelta(hours=4)).utcoffset():
            raise ValueError("DST_H4_CLOSE_BOUNDARY_UNVERIFIED")
        return start + 14400
    local = datetime.fromtimestamp(start, tz=timezone.utc).astimezone(NY)
    if (local.hour, local.minute, local.second) != (17, 0, 0):
        raise ValueError("D_NOT_EXPECTED_17_NY_ALIGNMENT")
    return int((local + timedelta(days=1)).timestamp())


def _ohlc(component: dict, name: str) -> dict:
    if not isinstance(component, dict) or set(component) != {"o", "h", "l", "c"}:
        raise ValueError("INCOMPLETE_" + name + "_OHLC")
    values = {}
    for key in ("o","h","l","c"):
        value = component[key]
        if isinstance(value, bool) or not isinstance(value, (str,int,float)):
            raise ValueError("INVALID_" + name + "_OHLC")
        try:
            number=float(value)
        except ValueError as exc:
            raise ValueError("INVALID_" + name + "_OHLC") from exc
        if not math.isfinite(number) or number<=0:
            raise ValueError("INVALID_" + name + "_OHLC")
        values[key] = number
    if values["h"]<max(values["o"],values["c"],values["l"]) or (
            values["l"]>min(values["o"],values["c"],values["h"])):
        raise ValueError("INCONSISTENT_" + name + "_OHLC")
    return values


def parse_historical_page(raw: bytes, *, instrument: str,
                          granularity: str, retrieved_at_utc: int,
                          request_url: str) -> dict:
    """Validate a complete received provider page; never invent missing bars.

    retrieved_at_utc must be recorded by an independently audited caller.
    Feeding this parser arbitrary bytes does NOT authenticate the source.
    """
    if not isinstance(raw,bytes) or len(raw)==0 or len(raw)>15_000_000:
        raise ValueError("INVALID_RAW_RESPONSE")
    if type(retrieved_at_utc) is not int or retrieved_at_utc<=0:
        raise ValueError("INVALID_RETRIEVAL_CLOCK")
    expected_prefix=build_historical_read_url(instrument,granularity=granularity,
                                               count=5000).split("?")[0]+"?"
    if not isinstance(request_url,str) or not request_url.startswith(expected_prefix):
        raise ValueError("NOT_APPROVED_PRACTICE_CANDLE_URL")
    from urllib.parse import parse_qs, urlsplit
    query=parse_qs(urlsplit(request_url).query,keep_blank_values=True)
    required={"granularity":granularity,"price":"MBA",**CANONICAL_ALIGNMENT}
    if any(query.get(k)!=[v] for k,v in required.items()):
        raise ValueError("H4_REQUEST_ALIGNMENT_OR_PRICE_CHANGED")
    if set(query)!=(set(required)|{"count"}):
        raise ValueError("UNREGISTERED_CANDLE_QUERY")
    actual_count=query.get("count",[""])[0]
    if not actual_count.isdigit() or not 1<=int(actual_count)<=5000:
        raise ValueError("INVALID_CANDLE_REQUEST_COUNT")
    try:
        body=json.loads(raw)
    except (ValueError,UnicodeDecodeError) as exc:
        raise ValueError("INVALID_PROVIDER_JSON") from exc
    if not isinstance(body,dict) or body.get("instrument")!=instrument or (
            body.get("granularity")!=granularity):
        raise ValueError("PROVIDER_INSTRUMENT_OR_TF_MISMATCH")
    candles=body.get("candles")
    if not isinstance(candles,list) or len(candles)>int(actual_count) or not candles:
        raise ValueError("INVALID_PROVIDER_CANDLE_COUNT")
    accepted=[]
    seen=set()
    rejected_unclosed=0
    last_start=None
    gaps=[]
    for original in candles:
        if not isinstance(original,dict) or not isinstance(original.get("complete"),bool):
            raise ValueError("INVALID_COMPLETE_FLAG")
        start=_utc_start(original.get("time"))
        end=_closing_time(start,granularity)
        if last_start is not None and start<=last_start:
            raise ValueError("DUPLICATE_OR_UNSORTED_PROVIDER_BAR")
        if start in seen:
            raise ValueError("DUPLICATE_PROVIDER_BAR")
        if last_start is not None and granularity=="H4" and start-last_start>14400:
            gaps.append({"prior_open_ts":last_start,"next_open_ts":start,
                         "calendar_verified":False,
                         "note":"May be valid market closure; never fabricate bars"})
        seen.add(start)
        last_start=start
        if not original["complete"]:
            rejected_unclosed+=1
            continue
        if end>retrieved_at_utc:
            raise ValueError("SOURCE_CLOSE_FUTURE_TO_RETRIEVAL")
        for key in ("mid","bid","ask"):
            if key not in original:
                raise ValueError("MISSING_PROVIDER_PRICE_COMPONENT")
        mid,bid,ask=(_ohlc(original[name],name) for name in ("mid","bid","ask"))
        for key in ("o","c"):
            if bid[key]>ask[key] or not bid[key]<=mid[key]<=ask[key]:
                raise ValueError("CROSSED_OR_INCONSISTENT_BID_ASK")
        volume=original.get("volume")
        if type(volume) is not int or volume<0:
            raise ValueError("INVALID_TICK_VOLUME")
        accepted.append({
            "open_ts":start,"close_ts":end,
            "mid":mid,"bid":bid,"ask":ask,"tick_volume":volume,
            "source_id":instrument+":"+granularity+":"+str(start),
            "source_record_sha256":hashlib.sha256(json.dumps(
                original,sort_keys=True,separators=(",",":"),allow_nan=False
                ).encode("utf-8")).hexdigest(),
        })
    return {
        "instrument":instrument,"granularity":granularity,"source":SOURCE_TYPE,
        "request_url":request_url,"retrieved_at_utc":retrieved_at_utc,
        "response_sha256":hashlib.sha256(raw).hexdigest(),
        "accepted_completed_candles":len(accepted),
        "rejected_unclosed":rejected_unclosed,
        "gaps_needing_market_calendar_review":gaps,
        "credentials_used_by_parser":False,"broker_order_calls":0,
        "verified_account_execution_costs":False,
        "status":"PROVIDER_BYTES_PARSED_SOURCE_AND_LICENSE_NOT_AUDITED",
        "candles":accepted,
    }
