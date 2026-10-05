"""Only invented ECB-formatted fixtures are used in these unit tests."""
from datetime import date, timedelta
from math import sin
import pytest
from src.self_learning.pipeline import GateError
from src.self_learning.reference_model import (
    SERIES, parse_ecb_csv, merge_observations, build_reference_dataset,
    train_reference_candidate, PREREG_COMMIT,
)

HEADER = 'KEY,FREQ,CURRENCY,CURRENCY_DENOM,EXR_TYPE,EXR_SUFFIX,TIME_PERIOD,OBS_VALUE,OBS_STATUS\n'

def fixture_obs(n=650):
    current=date(2023, 1, 2)
    rows=[]
    i=0
    end=date(2026, 9, 25)
    while current<=end:
        if current.weekday()<5:
            if i%3 != 1 or current==end:
                price=1.08+0.09*sin(i/4.7)+.012*sin(i/1.8)
                rows.append({'date':current.isoformat(), 'value':f'{price:.5f}'})
            i+=1
        current+=timedelta(days=1)
    return rows[:n] if n<len(rows) else rows

def test_parse_exact_official_series_and_immutability():
    csv=HEADER+f'{SERIES},D,USD,EUR,SP00,A,2023-01-02,1.0683,A\n'
    assert parse_ecb_csv(csv)==[{'date':'2023-01-02','value':'1.0683'}]
    with pytest.raises(GateError,match='series'):
        parse_ecb_csv(csv.replace('USD,EUR','GBP,EUR'))
    with pytest.raises(GateError,match='status'):
        parse_ecb_csv(csv.replace(',1.0683,A',',1.0683,E'))
    with pytest.raises(GateError,match='window'):
        parse_ecb_csv(csv.replace('2023-01-02','2026-09-28'))


def test_chronological_version_and_candidate_are_deterministic():
    ds=build_reference_dataset(fixture_obs(),fixture_only=True)
    c1=train_reference_candidate(ds,code_sha='a'*40)
    c2=train_reference_candidate(ds,code_sha='a'*40)
    assert c1==c2
    assert c1['status'] in {'REJECTED','CANDIDATE_NOT_APPROVED'}
    assert not c1['public_inference'] and not c1['broker_orders'] and c1['live_money_locked']
    assert c1['signal_or_abstain']=='ABSTAIN' and c1['gate_status']=='LOCKED'
    assert c1['source']['rights_scope']=='UNIT_FIXTURE'
    assert len(c1['evaluation']['walk_forward_dev_only'])==3
    assert c1['evaluation']['oos']['count']>100
    assert c1['splits']['train'][1]<c1['splits']['validation'][0]<c1['splits']['validation'][1]<c1['splits']['oos'][0]
    assert c1['model']['feature_names']==['lagged_reference_return','mean_abs_5_reference_returns']
    o=c1['evaluation']['oos']
    assert o['research_only_cost_2x_return_sum']==pytest.approx(o['research_only_proxy_return_sum']-.001*o['research_only_selected'])
    assert c1['protocol_commit']==PREREG_COMMIT


def test_fail_closed_on_conflicting_provider_data():
    obs=fixture_obs()
    with pytest.raises(GateError,match='conflicting'):
        merge_observations(obs, [{'date':obs[0]['date'],'value':'2.1234'}])
    with pytest.raises(GateError,match='last published'):
        merge_observations(obs[:-1])
    with pytest.raises(GateError,match='400'):
        merge_observations(obs[:100])


def test_reject_tampering_with_features_labels_and_registration():
    ds=build_reference_dataset(fixture_obs(),fixture_only=True)
    ds['rows'][1]['target_positive_after_proxy']=7
    with pytest.raises(GateError,match='version'):
        train_reference_candidate(ds,code_sha='a'*40)
    ds=build_reference_dataset(fixture_obs(),fixture_only=True)
    ds['source']['rights_scope']='UNKNOWN'
    with pytest.raises(GateError):
        train_reference_candidate(ds,code_sha='a'*40)
    ds=build_reference_dataset(fixture_obs(),fixture_only=True)
    with pytest.raises(GateError,match='SHA'):
        train_reference_candidate(ds,code_sha='not-real')
    with pytest.raises(GateError,match='SHA'):
        train_reference_candidate(ds,code_sha='a'*40,prereg_sha='b'*40)
