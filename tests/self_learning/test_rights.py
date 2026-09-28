"""Synthetic-only tests for vendor ML-use permission fail-closed controls."""
from datetime import datetime, timedelta, timezone

import pytest

from src.self_learning.pipeline import GateError, build_labeled_bars
from src.self_learning.rights import require_ml_training_rights


def source(provider="fixture-only"):
    return {"source_id":"unit_synthetic","license":"CWS_OWNED",
            "market":"TEST","timeframe":"1d","provider":provider,
            "source_version":"fixture-v1","price_timezone":"UTC",
            "cost_evidence_ref":"illustrative-friction-not-a-broker-cost"}


def test_fixture_remains_research_only():
    require_ml_training_rights(source())
    with pytest.raises(GateError, match="unit fixtures"):
        require_ml_training_rights({**source(), "license":"PERMISSION_GRANTED"})


@pytest.mark.parametrize("marker", [
    {"provider":"Coinbase Exchange"},
    {"provider":"fixture-only","source_id":"coinbase_btc"},
    {"provider":"fixture-only","source_url":"https://api.exchange.coinbase.com/products/BTC-USD/candles"},
    {"provider":"fixture-only","source_version":"coinbase_ohlcv_2026"},
])
def test_coinbase_blocked_even_when_claimed_owned_or_authorized(marker):
    s={**source(),**marker,"ml_training_rights_verified":True,
       "training_rights_evidence_ref":"fictional-approval",
       "source_sha256":"a"*64}
    with pytest.raises(GateError, match="Coinbase"):
        require_ml_training_rights(s)


def test_nonfixture_requires_explicit_independent_evidence():
    s=source("third-party-feed")
    with pytest.raises(GateError, match="independent"):
        require_ml_training_rights(s)
    s["ml_training_rights_verified"]=True
    with pytest.raises(GateError, match="evidence reference"):
        require_ml_training_rights(s)
    s["training_rights_evidence_ref"]="provider-written-license-reviewed"
    with pytest.raises(GateError, match="SHA-256"):
        require_ml_training_rights(s)
    s["source_sha256"]="b"*64
    require_ml_training_rights(s)


def test_training_dataset_refuses_prohibited_provider_before_build():
    bad=source("Coinbase Exchange")
    with pytest.raises(GateError, match="Coinbase"):
        build_labeled_bars([],bad,10)


def test_attested_training_evidence_pinned_to_research_dataset():
    s={**source("cws-permitted-fixture-study"),
       "ml_training_rights_verified":True,
       "training_rights_evidence_ref":"independently-reviewed-permission-file",
       "source_sha256":"c"*64}
    base=datetime(2024,1,1,tzinfo=timezone.utc)
    bars=[{"market":"TEST","timeframe":"1d",
           "as_of":(base+timedelta(days=i)).isoformat(),"closed":True,
           "open":100+i*.01,"high":101+i*.01,
           "low":99+i*.01,"close":100.5+i*.01} for i in range(320)]
    d=build_labeled_bars(bars,s,10)
    assert d["status"]=="RESEARCH_CANDIDATE"
    assert d["source"]["source_sha256"]=="c"*64
    assert d["source"]["ml_training_rights_verified"] is True
    assert d["source"]["training_rights_evidence_ref"]=="independently-reviewed-permission-file"
    assert d["cost_mode"]=="RESEARCH_PROXY"
