"""Source-only HistData M1 BID -> strictly complete 240-minute H4 importer.

Research-only: not broker H4, never OANDA/MT5 quotes, no REST/network or
broker imports. The input was supplied by a caller; syntax and SHA-256 do
NOT establish licensing, provider authenticity, or execution prices.
Uses fixed EST (UTC-05:00) WITHOUT DST, as HistData specifies.
No history/backtest/strategy module is imported.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

H4_SECONDS = 14400
EST_FIXED = timezone(timedelta(hours=-5), name="EST_FIXED_NO_DST")
# 17:00 fixed EST = 22:00 UTC; 4-hour windows 22, 02, 06, 10, 14, 18 UTC.
H4_UTC_ANCHOR = 22 * 3600
MINUTES_PER_H4 = 240
MAX_CSV_BYTES = 32_000_000
MAX_CSV_LINE_BYTES = 256
SYMBOLS = frozenset((
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF",
    "NZDUSD", "EURJPY", "GBPJPY", "EURGBP", "AUDJPY", "EURCHF",
    "NZDJPY", "XAUUSD", "XAGUSD", "WTIUSD", "BCOUSD",
    "SPXUSD", "NSXUSD",
))
TIME_FORMAT = re.compile(rb"\d{8} \d{6}")
NUMERIC = re.compile(rb"(?:\d+(?:\.\d*)?|\.\d+)")


def _number(value: bytes, field: str, *, zero_ok: bool = False) -> Decimal:
    if not NUMERIC.fullmatch(value):
        raise ValueError("INVALID_" + field + "_DECIMAL")
    try:
        number = Decimal(value.decode("ascii"))
    except (UnicodeDecodeError, InvalidOperation) as exc:
        raise ValueError("INVALID_" + field + "_DECIMAL") from exc
    if not number.is_finite() or number < 0 or (number == 0 and not zero_ok):
        raise ValueError("INVALID_" + field + "_DECIMAL")
    return number


def _row(raw: bytes, line: int) -> tuple[int, Decimal, Decimal, Decimal, Decimal]:
    fields = raw.split(b";")
    if len(fields) != 6 or not TIME_FORMAT.fullmatch(fields[0]):
        raise ValueError(f"INVALID_HISTDATA_M1_FORMAT_LINE_{line}")
    try:
        dt = datetime.strptime(fields[0].decode("ascii"), "%Y%m%d %H%M%S")
    except (UnicodeDecodeError, ValueError) as exc:
        raise ValueError(f"INVALID_HISTDATA_M1_TIME_LINE_{line}") from exc
    if dt.second != 0:
        raise ValueError(f"NOT_M1_ALIGNED_LINE_{line}")
    ts = int(dt.replace(tzinfo=EST_FIXED).timestamp())
    o, h, l, c = (
        _number(v, field)
        for v, field in zip(fields[1:5], ("OPEN", "HIGH", "LOW", "CLOSE"))
    )
    _number(fields[5], "VOLUME", zero_ok=True)  # Volume is not source-verified.
    if h < max(o, c, l) or l > min(o, c, h):
        raise ValueError(f"INVALID_OHLC_LINE_{line}")
    return ts, o, h, l, c


def _block_start(ts: int) -> int:
    return ((ts - H4_UTC_ANCHOR) // H4_SECONDS) * H4_SECONDS + H4_UTC_ANCHOR


def derive_complete_h4(
    source_bytes: bytes, *, symbol: str, received_at_utc: int,
) -> dict:
    """Do not infer missing minutes or an account-specific spread.

    A valid H4 requires all 240 exact bid M1 timestamps. A missing minute
    invalidates the entire H4 rather than silently improving the outcome.
    """
    if symbol not in SYMBOLS:
        raise ValueError("UNREGISTERED_HISTDATA_SOURCE_SYMBOL")
    if (type(received_at_utc) is not int or received_at_utc <= 0):
        raise ValueError("INVALID_RETRIEVAL_CLOCK")
    if not isinstance(source_bytes, bytes) or not (
        0 < len(source_bytes) <= MAX_CSV_BYTES
    ):
        raise ValueError("INVALID_RAW_CSV_SIZE")
    if b"\x00" in source_bytes:
        raise ValueError("INVALID_BINARY_CSV")
    source_sha = hashlib.sha256(source_bytes).hexdigest()
    lines = source_bytes.splitlines()
    h4 = []
    errors = []
    excluded = 0
    minute_count = 0
    last_ts = None
    bucket = None
    group = []

    def close_bucket() -> None:
        nonlocal excluded
        if bucket is None:
            return
        # Do not treat missing source M1 as continuous bars.
        complete = (
            len(group) == MINUTES_PER_H4
            and group[0][0] == bucket
            and group[-1][0] == bucket + H4_SECONDS - 60
            and all(b[0] - a[0] == 60 for a, b in zip(group, group[1:]))
        )
        if not complete:
            excluded += 1
            if len(errors) < 40:
                errors.append({
                    "block_open_utc":bucket,
                    "reason":"GAP_OR_INCOMPLETE_H4",
                    "observed_m1":len(group),
                    "missing_minutes":MINUTES_PER_H4-len(group),
                })
            return
        h4.append({
            "open_ts":bucket, "close_ts":bucket+H4_SECONDS,
            "open_bid":str(group[0][1]),
            "high_bid":str(max(r[2] for r in group)),
            "low_bid":str(min(r[3] for r in group)),
            "close_bid":str(group[-1][4]),
            "m1_count":MINUTES_PER_H4,
            "native_h4":False, "instrument_type":"HISTDATA_DERIVED_H4_BID_ONLY",
        })

    for number, line in enumerate(lines, 1):
        if not line:
            continue
        if len(line) > MAX_CSV_LINE_BYTES:
            raise ValueError(f"OVERSIZE_SOURCE_LINE_{number}")
        ts, o, hi, lo, close = _row(line, number)
        if last_ts is not None and ts <= last_ts:
            raise ValueError(f"DUPLICATE_OR_UNSORTED_M1_LINE_{number}")
        if ts+60 > received_at_utc:
            raise ValueError(f"UNCLOSED_OR_FUTURE_M1_LINE_{number}")
        last_ts = ts
        minute_count += 1
        start = _block_start(ts)
        if bucket is None:
            bucket = start
        if start != bucket:
            close_bucket()
            group = []
            bucket = start
        group.append((ts, o, hi, lo, close))
    close_bucket()
    if minute_count == 0:
        raise ValueError("NO_VALID_SOURCE_MINUTES")
    return {
        "symbol":symbol, "source":"HISTDATA_GENERIC_ASCII_M1_BID",
        "source_time_zone":"UTC-05:00_FIXED_EST_NO_DST",
        "bar_alignment":"17:00_FIXED_EST_22:00_UTC",
        "raw_sha256":source_sha,
        "first_source_m1_utc":int(_row(next(l for l in lines if l),1)[0]),
        "last_source_m1_utc":last_ts,
        "received_at_utc_claimed_by_caller":received_at_utc,
        "input_provenance":"UNVERIFIED_USER_SUPPLIED_BYTES",
        "raw_data_licensed_for_storage":"NOT_VERIFIED",
        "source_native_h4":False,
        "source_native_mt5":False,
        "ask_or_spread_available":False,
        "verified_after_cost_pnl_available":False,
        "m1_observations":minute_count,
        "h4_emitted":len(h4),
        "h4_blocks_rejected":excluded,
        "h4_rejected_samples":errors,
        "status":"DERIVED_H4_BID_ONLY_EXPLORATORY",
        "bars":h4,
    }
