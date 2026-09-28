import copy
import pytest
from src.self_learning.pipeline import GateError, build_labeled_bars
from src.self_learning.model import train_candidate, candidate_insight


def fixture_dataset(n=1100):
    from datetime import datetime, timedelta, timezone
    from math import sin
    base=datetime(2021,1,1,tzinfo=timezone.utc)
    out=[]
    for i in range(n):
        op=100+2*sin(i/7)+i*.009
        cl=op+1.3*sin(i/3+0.1)
        out.append({"market":"TEST","timeframe":"1d","as_of":(base+timedelta(days=i)).isoformat(),
                    "closed":True,"open":op,"high":max(op,cl)+0.25,
                    "low":min(op,cl)-0.25,"close":cl})
    return build_labeled_bars(out,{"source_id":"unit_fixture","license":"CWS_OWNED","market":"TEST",
            "timeframe":"1d","provider":"synthetic-test-only","source_version":"fixture-v1",
            "price_timezone":"UTC","cost_evidence_ref":"unit-test-only"},10)


def test_training_is_deterministic_and_never_promotes():
    d=fixture_dataset()
    c1=train_candidate(d,"a"*40,pre_registered=True)
    c2=train_candidate(d,"a"*40,pre_registered=True)
    assert c1==c2
    assert c1["status"]=="CANDIDATE_NOT_APPROVED"
    assert not c1["broker_orders"] and c1["live_money_locked"]
    assert 0<=c1["evaluation"]["oos"]["brier"]<=1
    assert len(c1["evaluation"]["walk_forward_dev_only"])==3
    assert c1["evaluation"]["oos"]["count"]>100
    selected=c1["evaluation"]["oos"]["research_only_selected"]
    assert c1["evaluation"]["oos"]["research_only_cost_2x_return_sum"] == pytest.approx(
        c1["evaluation"]["oos"]["research_only_net_return_sum"] - selected * .001
    )
    assert candidate_insight(c1)["signal_or_abstain"]=="ABSTAIN"
    with pytest.raises(GateError): candidate_insight(c1, approved=True)


def test_refuse_unregistered_or_unpinned_training():
    d=fixture_dataset()
    with pytest.raises(GateError): train_candidate(d,"a"*40,pre_registered=False)
    with pytest.raises(GateError): train_candidate(d,"fake-sha",pre_registered=True)
    d["cost_mode"]="BROKER_NET_FAKE"
    with pytest.raises(GateError): train_candidate(d,"a"*40,pre_registered=True)


def test_refuse_malformed_or_contaminated_labels():
    d=fixture_dataset()
    d["rows"][2]["target_positive_after_cost"]=7
    with pytest.raises(GateError): train_candidate(d,"a"*40,pre_registered=True)
    d=fixture_dataset()
    d["rows"][10]["feature_prev_return"]=float("nan")
    with pytest.raises(GateError): train_candidate(d,"a"*40,pre_registered=True)
    d=fixture_dataset()
    d["rows"][10]["feature_prev_return"]+=0.000001
    with pytest.raises(GateError,match="snapshot"):
        train_candidate(d,"a"*40,pre_registered=True)


def test_no_training_artifact_when_untrained():
    d=candidate_insight(None)
    assert d["status"]=="MODEL_NOT_TRAINED"
    assert d["signal_or_abstain"]=="ABSTAIN"
    assert d["gate_status"]=="LOCKED"
    assert d["broker_orders"] is False
