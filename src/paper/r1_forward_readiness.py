"""R1 quote timing and safety preflight, offline and RESEARCH-ONLY.

This module does not promote caller-supplied audit flags to real-world proof.
No broker import, HTTP client, scheduling, trading signal, or order API.
"""
from __future__ import annotations

import math
import re

FORWARD_START_UTC = 1_790_726_400  # 2026-09-30 00:00 UTC
MAX_NEXT_OPEN_DELAY_SECONDS = 30
FIELDS = frozenset({
    "symbol", "timeframe", "source_bar_id", "bar_close_ts",
    "bar_retrieved_ts", "quote_source_ts", "quote_received_ts",
    "decision_ts", "quote_raw_sha256", "provider", "bid", "ask",
    "authorization_verified", "kill_switch_off", "costs_audited",
    "cost_evidence_sha256", "data_rights_approved",
})


def assess_forward_quote(event: dict, *, now_utc: int) -> dict:
    """Check chronology without minting a paper fill or a verified cost claim.

    Injected now_utc supports fixtures ONLY. Production capture must use an
    independent trusted clock and externally verified provider/fee evidence.
    """
    def reject(reason: str) -> dict:
        return {"status": "REJECTED", "reason": reason,
                "paper_fills_created": 0, "orders_sent": 0,
                "forward_evidence_verified": False}

    if type(now_utc) is not int or now_utc <= 0:
        return reject("INVALID_CLOCK")
    if not isinstance(event, dict) or set(event) != FIELDS:
        return reject("SCHEMA_MISMATCH")
    if event["timeframe"] != "H4" or event["provider"] != "BROKER_READ_ONLY":
        return reject("UNSUPPORTED_QUOTE_VENUE_OR_TIMEFRAME")
    if not isinstance(event["symbol"], str) or not event["symbol"].strip() or (
            not isinstance(event["source_bar_id"], str) or
            not event["source_bar_id"].strip()):
        return reject("MISSING_PROVENANCE_ID")
    if not all(event[name] is True for name in (
            "authorization_verified", "kill_switch_off", "costs_audited",
            "data_rights_approved")):
        return reject("AUTH_COST_RIGHTS_OR_KILL_SWITCH_BLOCKED")
    for name in ("quote_raw_sha256", "cost_evidence_sha256"):
        if not isinstance(event[name], str) or not re.fullmatch(
                r"[0-9a-f]{64}", event[name]) or event[name] == "0" * 64:
            return reject("MISSING_SOURCE_OR_COST_HASH")
    names = ("bar_close_ts", "bar_retrieved_ts", "quote_source_ts",
             "quote_received_ts", "decision_ts")
    if any(type(event[name]) is not int for name in names):
        return reject("INVALID_EVENT_TIMESTAMP")
    close, bar_seen, quote_ts, quote_seen, decision = (event[n] for n in names)
    if close < FORWARD_START_UTC or not (
            close <= bar_seen <= quote_ts <= quote_seen <= decision <= now_utc):
        return reject("HISTORICAL_OR_NONCAUSAL_EVENT")
    if quote_ts - close > MAX_NEXT_OPEN_DELAY_SECONDS or (
            decision - quote_ts > MAX_NEXT_OPEN_DELAY_SECONDS):
        return reject("NOT_CONTEMPORANEOUS_NEXT_OPEN_QUOTE")
    bid, ask = event["bid"], event["ask"]
    if (type(bid) not in (float, int) or type(ask) not in (float, int)
            or not math.isfinite(bid) or not math.isfinite(ask)
            or bid <= 0 or ask < bid):
        return reject("INVALID_OR_CROSSED_BID_ASK")
    return {"status": "TIMING_INTEGRITY_ONLY_AWAITING_INDEPENDENT_AUDIT",
            "spread_price_observed": ask - bid,
            "caller_audit_flags_are_proof": False,
            "paper_fills_created": 0, "orders_sent": 0,
            "forward_evidence_verified": False}
