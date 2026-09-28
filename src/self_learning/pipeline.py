"""Offline, research-only ingestion and dataset gates for CWS AI Trade.

No network, Supabase writes, broker adapter, model promotion, or live execution.
"""
from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any

LICENSES = {"CWS_OWNED", "PERMISSION_GRANTED", "CC_BY_4_0", "CC0_1_0"}
CLAIM_TYPES = {"PRACTITIONER_CLAIM", "BOOK_LESSON", "CWS_BACKTEST_EVIDENCE",
               "MARKET_OBSERVATION", "HYPOTHESIS", "RULE", "REJECTED_CLAIM"}


class GateError(ValueError):
    """Fail-closed gate; the rejected record must not enter a candidate dataset."""


def _time(value: Any) -> datetime:
    if not isinstance(value, str):
        raise GateError("timestamp must be an ISO 8601 string with timezone")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise GateError("invalid ISO 8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise GateError("timezone is required")
    return parsed


def _digest(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                             separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def stage_knowledge(repo_root: Path, record: dict[str, Any], quarantine_dir: Path) -> dict[str, Any]:
    """Snapshot lawful source metadata; NEVER approve, train or publish automatically."""
    required = ("source_id", "source_path", "rights_ref", "license", "claim_type",
                "created_at", "market", "timeframe", "evidence_level")
    if any(not isinstance(record.get(key), str) or not record[key].strip() for key in required):
        raise GateError("missing required provenance field")
    if not re.fullmatch(r"[A-Za-z0-9_-]{3,80}", record["source_id"]):
        raise GateError("invalid source_id")
    if record["license"] not in LICENSES or record["claim_type"] not in CLAIM_TYPES:
        raise GateError("unsupported license or claim type")
    _time(record["created_at"])
    root = repo_root.resolve(strict=True)
    src = (root / record["source_path"]).resolve(strict=True)
    if not src.is_relative_to(root) or not src.is_file() or src.suffix.lower() not in {".md", ".txt", ".json"}:
        raise GateError("source must be an allowed file inside the repository")
    data = src.read_bytes()
    if not data or len(data) > 5_000_000:
        raise GateError("source is empty or over 5 MB")
    data.decode("utf-8", errors="strict")
    content_hash = sha256(data).hexdigest()
    expected = record.get("expected_sha256")
    if expected is not None and expected != content_hash:
        raise GateError("source hash mismatch")
    payload = {key: record[key] for key in required}
    payload.update(source_sha256=content_hash, status="QUARANTINED", schema_version=1,
                   knowledge_version="kv1-" + _digest({**payload, "source_sha256": content_hash})[:20])
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    target = quarantine_dir / (record["source_id"] + "-" + content_hash[:12] + ".json")
    # Exclusive creation: re-staging must not silently overwrite a prior audit record.
    with target.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    return payload


def build_labeled_bars(bars: list[dict[str, Any]], source: dict[str, Any],
                       round_trip_cost_bps: float) -> dict[str, Any]:
    """Closed-bar features at t; labels use next bar open->close, net of research costs.

    This is a research dataset, not actual broker execution or broker-net P/L.
    """
    required = ("source_id", "license", "market", "timeframe", "provider",
                "source_version", "price_timezone", "cost_evidence_ref")
    if any(not isinstance(source.get(k), str) or not source[k].strip() for k in required):
        raise GateError("missing market-data provenance or cost assumption")
    if source["license"] not in LICENSES:
        raise GateError("market data license has not been cleared")
    if not isinstance(round_trip_cost_bps, (int, float)) or not 0 <= round_trip_cost_bps <= 500:
        raise GateError("invalid explicit round-trip cost")
    if len(bars) < 300:
        raise GateError("at least 300 real closed bars required")
    parsed = []
    prev_ts = None
    for row in bars:
        if row.get("closed") is not True or row.get("market") != source["market"] or row.get("timeframe") != source["timeframe"]:
            raise GateError("bar incomplete or market/timeframe mismatch")
        ts = _time(row.get("as_of"))
        if prev_ts is not None and ts <= prev_ts:
            raise GateError("duplicate/out-of-order bar")
        prev_ts = ts
        try:
            op, hi, lo, cl = (float(row[key]) for key in ("open", "high", "low", "close"))
        except (KeyError, TypeError, ValueError) as exc:
            raise GateError("invalid OHLC") from exc
        from math import isfinite
        if not all(isfinite(v) and v > 0 for v in (op, hi, lo, cl)) or lo > min(op, cl) or hi < max(op, cl) or lo > hi:
            raise GateError("invalid OHLC bounds or nonfinite price")
        parsed.append((ts.isoformat(), op, hi, lo, cl))
    # Every label uses one subsequent bar. No incomplete final label, no future price in features.
    rows = []
    for i in range(1, len(parsed) - 1):
        ts, op, hi, lo, cl = parsed[i]
        next_op, next_cl = parsed[i + 1][1], parsed[i + 1][4]
        gross = next_cl / next_op - 1
        net = gross - round_trip_cost_bps / 10_000
        rows.append({"as_of": ts, "feature_prev_return": cl / parsed[i-1][4] - 1,
                     "feature_bar_range": (hi-lo)/op, "target_next_bar_net_return": net,
                     "target_positive_after_cost": int(net > 0)})
    signature = {"schema_version": 1, "source": {k: source[k] for k in required},
                 "round_trip_cost_bps": float(round_trip_cost_bps), "rows": rows}
    return {"dataset_version": "dv1-" + _digest(signature)[:20], "status": "RESEARCH_CANDIDATE",
            "market": source["market"], "timeframe": source["timeframe"],
            "source_id": source["source_id"], "cost_mode": "RESEARCH_PROXY",
            "source": signature["source"], "round_trip_cost_bps": float(round_trip_cost_bps),
            "row_count": len(rows), "rows": rows}


def chronological_split(dataset: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Time-ordered 60/20/20. Purge one sample at boundaries (one-bar horizon)."""
    if dataset.get("status") != "RESEARCH_CANDIDATE":
        raise GateError("only validated research datasets may be split")
    rows = dataset.get("rows", [])
    n = len(rows)
    if n < 298 or any(_time(rows[i]["as_of"]) >= _time(rows[i+1]["as_of"]) for i in range(n-1)):
        raise GateError("insufficient or non-chronological rows")
    a, b = int(n*.6), int(n*.8)
    result = {"train": rows[:a], "validation": rows[a+1:b], "oos": rows[b+1:]}
    if min(map(len, result.values())) < 40:
        raise GateError("split too small")
    return result


def read_only_signal() -> dict[str, Any]:
    """Without independently approved model evidence, always abstain."""
    return {"model_version": None, "data_version": None, "as_of": None,
            "market": None, "timeframe": None, "evidence_refs": [],
            "status": "MODEL_NOT_TRAINED", "signal_or_abstain": "ABSTAIN",
            "uncertainty": None, "gate_status": "LOCKED",
            "broker_orders": False, "mode": "RESEARCH"}
