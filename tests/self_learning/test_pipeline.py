import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from src.self_learning.pipeline import GateError, build_labeled_bars, chronological_split, read_only_signal, stage_knowledge


def source():
    return {"source_id":"feed1","license":"CWS_OWNED","market":"EURUSD","timeframe":"1d",
            "provider":"fixture-only","source_version":"test-v1","price_timezone":"UTC",
            "cost_evidence_ref":"fixture-illustration-not-broker"}


def fixture_bars(n=320):
    base=datetime(2025,1,1,tzinfo=timezone.utc)
    return [{"market":"EURUSD","timeframe":"1d","as_of":(base+timedelta(days=i)).isoformat(),
             "closed":True,"open":1+i/10000,"high":1.002+i/10000,"low":0.998+i/10000,
             "close":1.001+i/10000} for i in range(n)]


def test_knowledge_quarantine_and_version(tmp_path):
    root=tmp_path/'repo'; root.mkdir(); (root/'master.md').write_text('CWS authored evidence',encoding='utf-8')
    record={"source_id":"cws_masterbook_v3","source_path":"master.md","rights_ref":"CWS founder authored",
            "license":"CWS_OWNED","claim_type":"BOOK_LESSON","created_at":"2026-09-28T00:00:00+07:00",
            "market":"MULTI_ASSET","timeframe":"N/A","evidence_level":"HYPOTHESIS"}
    out=stage_knowledge(root,record,tmp_path/'q')
    assert out['status']=='QUARANTINED' and out['knowledge_version'].startswith('kv1-')
    assert json.loads(next((tmp_path/'q').glob('*.json')).read_text())['source_sha256']==out['source_sha256']
    with pytest.raises(FileExistsError): stage_knowledge(root,record,tmp_path/'q')
    record['source_path']='../escape.md'
    (tmp_path/'escape.md').write_text('unsafe')
    with pytest.raises(GateError): stage_knowledge(root,record,tmp_path/'q')


def test_knowledge_license_and_hash_fail_closed(tmp_path):
    root=tmp_path/'repo'; root.mkdir(); (root/'doc.md').write_text('content')
    r={"source_id":"doc_123","source_path":"doc.md","rights_ref":"source","license":"COPYRIGHT_UNVERIFIED",
       "claim_type":"BOOK_LESSON","created_at":"2026-09-28T00:00:00Z","market":"FX",
       "timeframe":"1d","evidence_level":"CLAIM"}
    with pytest.raises(GateError): stage_knowledge(root,r,tmp_path/'q')
    r.update(license='CWS_OWNED',expected_sha256='0'*64)
    with pytest.raises(GateError): stage_knowledge(root,r,tmp_path/'q')


def test_numerical_dataset_split_and_no_lookahead():
    d=build_labeled_bars(fixture_bars(),source(),12)
    assert d['row_count']==318 and d['cost_mode']=='RESEARCH_PROXY'
    first=d['rows'][0]
    assert first['as_of']==fixture_bars()[1]['as_of']
    # Next-bar return minus 12 bps, not current-bar close/open.
    nxt=fixture_bars()[2]
    assert first['target_next_bar_net_return']==pytest.approx(nxt['close']/nxt['open']-1-0.0012)
    splits=chronological_split(d)
    assert max(r['as_of'] for r in splits['train']) < min(r['as_of'] for r in splits['validation'])
    assert max(r['as_of'] for r in splits['validation']) < min(r['as_of'] for r in splits['oos'])
    assert len(splits['train'])+len(splits['validation'])+len(splits['oos'])==316


@pytest.mark.parametrize('change',[
    lambda b: b[8].update(closed=False),
    lambda b: b[8].update(market='BTCUSD'),
    lambda b: b[8].update(as_of=b[7]['as_of']),
    lambda b: b[8].update(high=-1),
    lambda b: b[8].update(close=float('nan')),
])
def test_bad_bars_rejected(change):
    b=fixture_bars(); change(b)
    with pytest.raises(GateError): build_labeled_bars(b,source(),12)


def test_missing_license_cost_small_data_abstain():
    with pytest.raises(GateError): build_labeled_bars(fixture_bars(15),source(),12)
    s=source(); s['license']='UNVERIFIED'
    with pytest.raises(GateError): build_labeled_bars(fixture_bars(),s,12)
    with pytest.raises(GateError): build_labeled_bars(fixture_bars(),source(),-1)
    signal=read_only_signal()
    assert signal['signal_or_abstain']=='ABSTAIN' and signal['gate_status']=='LOCKED'
    assert signal['broker_orders'] is False and signal['status']=='MODEL_NOT_TRAINED'
