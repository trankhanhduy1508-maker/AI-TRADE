"""Read-only R1 source receipt journal: metadata and hashes, never raw prices.

This is NOT a licence, provider audit, next-open execution or trading signal.
The injected clock exists only for deterministic tests. No broker/HTTP APIs.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import time
from pathlib import Path

FORWARD_START_UTC = 1790726400  # 2026-09-30T00:00:00Z
ZERO_HASH = "0" * 64
SOURCES = {
    ("HISTDATA_GENERIC_ASCII_M1_BID", "EURUSD"): "DERIVED_H4_BID_ONLY",
    ("KRAKEN_SPOT_NATIVE_H4", "BTCUSD"): "NATIVE_H4_KRAKEN_SPOT",
    ("KRAKEN_SPOT_NATIVE_H4", "ETHUSD"): "NATIVE_H4_KRAKEN_SPOT",
    ("BITSTAMP_PUBLIC_OHLC", "BTCUSD"): "NATIVE_H4_BITSTAMP_SPOT",
    ("BITSTAMP_PUBLIC_OHLC", "ETHUSD"): "NATIVE_H4_BITSTAMP_SPOT",
}
FIELDS = frozenset({"source", "symbol", "source_kind", "first_open_ts",
                    "last_close_ts", "completed_h4", "rejected_h4"})


def _canonical(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def _hash(obj: object) -> str:
    return hashlib.sha256(_canonical(obj)).hexdigest()


def _check_event(event: dict) -> None:
    if not isinstance(event, dict) or set(event) != {
            "v", "source", "symbol", "source_kind", "first_open_ts",
            "last_close_ts", "captured_at_utc", "completed_h4", "rejected_h4",
            "raw_sha256", "evidence_class", "data_rights", "fee_status"}:
        raise ValueError("RECEIPT_SCHEMA_MISMATCH")
    if type(event["v"]) is not int or event["v"] != 1 or event["source"] not in {p for p, _ in SOURCES}:
        raise ValueError("UNREGISTERED_PROVIDER_OR_VERSION")
    if SOURCES.get((event["source"], event["symbol"])) != event["source_kind"]:
        raise ValueError("NATIVE_DERIVED_OR_INSTRUMENT_MISMATCH")
    if (event["evidence_class"] != "SOURCE_ONLY_UNVERIFIED" or
            event["data_rights"] != "NOT_AUDITED" or
            event["fee_status"] != "NOT_VERIFIED"):
        raise ValueError("UNAUTHORIZED_EVIDENCE_PROMOTION")
    if (not isinstance(event["raw_sha256"], str) or
            not re.fullmatch("[0-9a-f]{64}", event["raw_sha256"]) or
            event["raw_sha256"] == ZERO_HASH):
        raise ValueError("INVALID_RAW_SOURCE_HASH")
    for name in ("first_open_ts", "last_close_ts", "captured_at_utc",
                 "completed_h4", "rejected_h4"):
        if type(event[name]) is not int:
            raise ValueError("INVALID_RECEIPT_NUMBER")
    if not (0 < event["first_open_ts"] < event["last_close_ts"] <=
            event["captured_at_utc"] and
            event["completed_h4"] >= 0 and event["rejected_h4"] >= 0 and
            event["completed_h4"] + event["rejected_h4"] > 0):
        raise ValueError("INVALID_RECEIPT_TIME_OR_COUNTS")
    if event["source_kind"].startswith("NATIVE_H4") and (
            event["first_open_ts"] % 14400 or
            event["last_close_ts"] % 14400):
        raise ValueError("INVALID_NATIVE_H4_ALIGNMENT")


def _verify(fp) -> tuple[int, str, dict]:
    fp.seek(0)
    seq, previous_hash, latest = 0, ZERO_HASH, {}
    for line_number, line in enumerate(fp, 1):
        try:
            item = json.loads(line)
            if set(item) != {"seq", "prev_hash", "event", "record_hash"}:
                raise ValueError("BAD_ENVELOPE")
            event = item["event"]
            _check_event(event)
            if item["seq"] != seq + 1 or item["prev_hash"] != previous_hash:
                raise ValueError("BROKEN_HASH_CHAIN")
            if _hash({k: item[k] for k in ("seq", "prev_hash", "event")}) != item["record_hash"]:
                raise ValueError("RECEIPT_HASH_MISMATCH")
            key = (event["source"], event["symbol"])
            if event["last_close_ts"] <= latest.get(key, -1):
                raise ValueError("DUPLICATE_OR_NONCHRONOLOGICAL_RECEIPT")
            latest[key] = event["last_close_ts"]
            seq, previous_hash = item["seq"], item["record_hash"]
        except (ValueError, TypeError, KeyError) as exc:
            raise ValueError(f"CORRUPT_RECEIPT_LINE_{line_number}:{exc}") from exc
    return seq, previous_hash, latest


def _record(path: str | Path, *, source_bytes: bytes,
            metadata: dict, captured_at_utc: int) -> dict:
    if (type(captured_at_utc) is not int or captured_at_utc <= 0 or
            type(source_bytes) is not bytes or not 0 < len(source_bytes) <= 4_000_000 or
            not isinstance(metadata, dict) or set(metadata) != FIELDS):
        raise ValueError("BAD_RECEIPT_INPUT")
    event = dict(metadata, v=1, captured_at_utc=captured_at_utc,
                 raw_sha256=hashlib.sha256(source_bytes).hexdigest(),
                 evidence_class="SOURCE_ONLY_UNVERIFIED",
                 data_rights="NOT_AUDITED", fee_status="NOT_VERIFIED")
    _check_event(event)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(p, os.O_CREAT | os.O_RDWR | os.O_APPEND, 0o600)
    with os.fdopen(fd, "a+", encoding="utf-8") as fp:
        fcntl.flock(fp, fcntl.LOCK_EX)
        seq, prior, latest = _verify(fp)
        key = (event["source"], event["symbol"])
        if event["last_close_ts"] <= latest.get(key, -1):
            raise ValueError("DUPLICATE_OR_NONCHRONOLOGICAL_RECEIPT")
        item = {"seq": seq + 1, "prev_hash": prior, "event": event}
        item["record_hash"] = _hash(item)
        fp.seek(0, os.SEEK_END)
        fp.write(_canonical(item).decode("utf-8") + "\n")
        fp.flush()
        os.fsync(fp.fileno())
    return {"status": "METADATA_RECEIPT_UNVERIFIED", "seq": seq + 1,
            "record_hash": item["record_hash"], "raw_bytes_persisted": False,
            "paper_fills_created": 0, "orders_sent": 0,
            "eligible_forward_observations": 0}


def record_source_receipt(path: str | Path, *, source_bytes: bytes,
                          metadata: dict) -> dict:
    """Production entry: actual host UTC recorded locally, still UNVERIFIED."""
    return _record(path, source_bytes=source_bytes, metadata=metadata,
                   captured_at_utc=int(time.time()))


def verify_source_receipts(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as fp:
        seq, digest, _ = _verify(fp)
    return {"records": seq, "head_hash": digest,
            "raw_prices_stored": False, "forward_claim": "NONE"}
