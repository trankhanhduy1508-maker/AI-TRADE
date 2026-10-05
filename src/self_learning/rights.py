"""Fail-closed market-data ML training rights gate.

This is a prerequisite to building CWS training datasets, not a legal opinion
or an automatic license grant. Actual vendor rights must be independently
reviewed before setting the attestation fields. Unit fixtures are never a
substitute for a licensed production market feed.
"""
from __future__ import annotations

import re
from typing import Any

from .pipeline import GateError

FIXTURE_PROVIDERS = frozenset({"fixture-only", "synthetic-test-only"})
PROHIBITED_PROVIDER_TERMS = frozenset({"coinbase"})
APPROVED_SOURCE_LICENSES = frozenset(
    {"CWS_OWNED", "PERMISSION_GRANTED", "CC_BY_4_0", "CC0_1_0"}
)
RIGHTS_FIELDS = (
    "ml_training_rights_verified", "training_rights_evidence_ref", "source_sha256"
)


def require_ml_training_rights(source: dict[str, Any]) -> None:
    """Deny known disallowed feeds; require independently verified ML rights.

    Coinbase Market Data Terms updated 2026-08-07, section 3(5) prohibit
    AI/ML use even internally without prior written consent. CWS has no
    verified consent; block all Coinbase-derived datasets rather than trust
    a caller-supplied PERMISSION_GRANTED or CWS_OWNED flag.

    Other nonfixture providers require an evidence reference, a pinned source
    digest and a documented human verification. Passing this guard is NOT
    permission to distribute vendor data/models or promote a model.
    """
    if not isinstance(source, dict):
        raise GateError("market data source metadata is required")
    identity = " ".join(str(source.get(field, "")) for field in (
        "provider", "source_id", "source_version", "source_url", "data_url"
    )).casefold()
    if any(marker in identity for marker in PROHIBITED_PROVIDER_TERMS):
        raise GateError(
            "Coinbase market data ML training is prohibited without prior "
            "written consent; no verified CWS consent is recorded"
        )
    if source.get("license") not in APPROVED_SOURCE_LICENSES:
        raise GateError("unverified market-data license")
    provider = source.get("provider")
    if not isinstance(provider, str) or not provider.strip():
        raise GateError("missing market-data provider")
    if provider.casefold() in FIXTURE_PROVIDERS:
        if source["license"] != "CWS_OWNED":
            raise GateError("unit fixtures must be declared test-owned")
        return
    if source.get("ml_training_rights_verified") is not True:
        raise GateError("independent ML-training-rights verification required")
    reference = source.get("training_rights_evidence_ref")
    if not isinstance(reference, str) or not reference.strip() or len(reference) > 2048:
        raise GateError("a recorded training-rights evidence reference is required")
    raw_digest = source.get("source_sha256")
    if not isinstance(raw_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", raw_digest):
        raise GateError("a pinned 64-character source SHA-256 is required")
