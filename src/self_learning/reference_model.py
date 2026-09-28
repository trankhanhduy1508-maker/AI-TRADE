"""Deterministic ECB reference-rate research, not executable broker prices.

Only the official, already-published ECB EXR.D.USD.EUR.SP00.A reference-rate
observations are suitable inputs. This module neither accesses a broker nor
exposes raw rates, model weights, probabilities or predictions publicly.
"""
from __future__ import annotations

import csv
from datetime import date
from hashlib import sha256
from io import StringIO
import json
from math import exp, isfinite, log, sqrt
import re
from typing import Any

from .pipeline import GateError, _digest

SERIES = 'EXR.D.USD.EUR.SP00.A'
START = date(2023, 1, 1)
END = date(2026, 9, 25)
PREREG_COMMIT = '2c6ed583173f4f050d85362b63491df02a02ce90'
COST_BPS = 10.0
HYPER = {'learning_rate': 0.12, 'epochs': 600, 'l2': 0.03,
         'confidence_threshold': 0.55, 'max_z': 8.0}
FEATURES = ('lagged_reference_return', 'mean_abs_5_reference_returns')
LICENSE_URL = 'https://www.ecb.europa.eu/stats/ecb_statistics/governance_and_quality_framework/html/usage_policy.en.html'
SOURCE_URL = 'https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A'
REQUIRED = ('KEY', 'FREQ', 'CURRENCY', 'CURRENCY_DENOM', 'EXR_TYPE', 'EXR_SUFFIX',
            'TIME_PERIOD', 'OBS_VALUE', 'OBS_STATUS')


def parse_ecb_csv(content: str) -> list[dict[str, str]]:
    """Check original official CSV columns and series; retain raw rate string."""
    if not isinstance(content, str) or len(content) > 4_000_000:
        raise GateError('missing or excessively large ECB CSV')
    reader = csv.DictReader(StringIO(content, newline=''))
    if not reader.fieldnames or not set(REQUIRED).issubset(reader.fieldnames):
        raise GateError('missing required official ECB CSV columns')
    result = []
    for row in reader:
        if None in row or any(row.get(k) is None for k in REQUIRED):
            raise GateError('malformed ECB CSV row')
        if (row['KEY'], row['FREQ'], row['CURRENCY'], row['CURRENCY_DENOM'],
            row['EXR_TYPE'], row['EXR_SUFFIX'], row['OBS_STATUS']) != (SERIES, 'D', 'USD', 'EUR', 'SP00', 'A', 'A'):
            raise GateError('unexpected ECB series, currency or observation status')
        try:
            day = date.fromisoformat(row['TIME_PERIOD'])
        except ValueError as exc:
            raise GateError('invalid reference date') from exc
        if day < START or day > END:
            raise GateError('observation is outside the preregistered closed window')
        raw = row['OBS_VALUE']
        if not re.fullmatch(r'\d+(?:\.\d+)?', raw):
            raise GateError('invalid original official rate')
        value = float(raw)
        if not isfinite(value) or not 0 < value < 10:
            raise GateError('out-of-range official rate')
        result.append({'date': day.isoformat(), 'value': raw})
    if not result:
        raise GateError('official CSV has no observations')
    return result


def merge_observations(*windows: list[dict[str, str]]) -> list[dict[str, str]]:
    if not windows:
        raise GateError('no official source windows')
    merged = {}
    for window in windows:
        for row in window:
            d, v = row['date'], row['value']
            if d in merged and merged[d] != v:
                raise GateError('conflicting ECB reference observation')
            merged[d] = v
    obs = [{'date': k, 'value': v} for k, v in sorted(merged.items())]
    if len(obs) < 400:
        raise GateError('fewer than 400 actual ECB reference observations')
    if obs[-1]['date'] != END.isoformat():
        raise GateError('missing the preregistered last published observation')
    for a, b in zip(obs, obs[1:]):
        gap = (date.fromisoformat(b['date']) - date.fromisoformat(a['date'])).days
        if gap < 1 or gap > 12:
            raise GateError('ECB reference observation sequence is not credible')
    return obs


def build_reference_dataset(obs: list[dict[str, str]], *, fixture_only: bool = False) -> dict[str, Any]:
    """Create supervised one-reference-step horizon without fabricated OHLC."""
    normalized = merge_observations(obs)
    prices = [float(row['value']) for row in normalized]
    changes = [prices[i] / prices[i - 1] - 1 for i in range(1, len(prices))]
    rows = []
    for i in range(5, len(prices) - 1):
        lagged = changes[i - 1]
        variability = sum(abs(v) for v in changes[i - 5:i]) / 5
        net = prices[i + 1] / prices[i] - 1 - COST_BPS / 10_000
        rows.append({'as_of': normalized[i]['date'], FEATURES[0]: lagged,
                     FEATURES[1]: variability, 'target_next_reference_net_return': net,
                     'target_positive_after_proxy': int(net > 0)})
    source = {'provider': 'ECB Data Portal', 'series': SERIES,
              'data_start': normalized[0]['date'], 'data_end': normalized[-1]['date'],
              'license_url': LICENSE_URL, 'attribution': 'Source: ECB statistics.',
              'rights_scope': 'UNIT_FIXTURE' if fixture_only else 'INTERNAL_RESEARCH_ONLY',
              'note': 'Reference quotes for information only, not broker OHLC or execution fills'}
    signature = {'schema_version': 1, 'source': source, 'original_observations': normalized,
                 'cost_bps': COST_BPS, 'rows': rows}
    return {'dataset_version': 'ecb-dv1-' + _digest(signature)[:20],
            'status': 'UNIT_FIXTURE' if fixture_only else 'RESEARCH_CANDIDATE',
            'source': source, 'original_observations': normalized,
            'cost_bps': COST_BPS, 'row_count': len(rows), 'rows': rows}


def _sigmoid(z: float) -> float:
    if z >= 0:
        return 1 / (1 + exp(-z))
    e = exp(z)
    return e / (1 + e)


def _label(row: dict[str, Any]) -> int:
    y, net = row.get('target_positive_after_proxy'), row.get('target_next_reference_net_return')
    if type(y) is not int or y not in (0, 1) or not isinstance(net, (float, int)) or not isfinite(net) or y != int(net > 0):
        raise GateError('invalid or inconsistent research label')
    return y


def _vector(row: dict[str, Any]) -> list[float]:
    vals = [row.get(feature) for feature in FEATURES]
    if any(not isinstance(v, (int, float)) or not isfinite(v) for v in vals):
        raise GateError('missing or nonfinite causal feature')
    return [float(v) for v in vals]


def _fit(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if len(rows) < 80:
        raise GateError('reference model requires >=80 training examples')
    ys = [_label(row) for row in rows]
    positives = sum(ys)
    if min(positives, len(rows) - positives) < 8:
        raise GateError('both research classes require >=8 observations')
    x = [_vector(row) for row in rows]
    means = [sum(v[j] for v in x) / len(x) for j in range(2)]
    stds = [max(sqrt(sum((v[j] - means[j]) ** 2 for v in x) / len(x)), 1e-8) for j in range(2)]
    xx = [[max(-HYPER['max_z'], min(HYPER['max_z'], (v[j] - means[j]) / stds[j]))
           for j in range(2)] for v in x]
    weights = [log(positives / (len(rows) - positives)), 0.0, 0.0]
    for _ in range(HYPER['epochs']):
        gradients = [0.0, 0.0, 0.0]
        for vec, target in zip(xx, ys):
            err = _sigmoid(weights[0] + weights[1] * vec[0] + weights[2] * vec[1]) - target
            gradients[0] += err
            gradients[1] += err * vec[0]
            gradients[2] += err * vec[1]
        weights[0] -= HYPER['learning_rate'] * gradients[0] / len(rows)
        for j in (1, 2):
            weights[j] -= HYPER['learning_rate'] * (gradients[j] / len(rows) + HYPER['l2'] * weights[j])
    return {'intercept': weights[0], 'weights': weights[1:],
            'feature_names': list(FEATURES), 'train_mean': means, 'train_std': stds,
            'train_positive_rate': positives / len(rows), 'train_count': len(rows),
            'hyperparameters': dict(HYPER)}


def _predict(model: dict[str, Any], row: dict[str, Any]) -> float:
    x = _vector(row)
    bound = model['hyperparameters']['max_z']
    z = model['intercept'] + sum(w * max(-bound, min(bound, (v - mu) / sd))
                                 for w, v, mu, sd in zip(model['weights'], x, model['train_mean'], model['train_std']))
    return _sigmoid(z)


def _metrics(model: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        raise GateError('empty reference evaluation segment')
    y = [_label(r) for r in rows]
    preds = [_predict(model, r) for r in rows]
    p0 = model['train_positive_rate']
    selected = [r for r, p in zip(rows, preds) if p >= HYPER['confidence_threshold']]
    net = sum(float(r['target_next_reference_net_return']) for r in selected)
    return {'count': len(rows), 'positives': sum(y),
            'brier': sum((p - label) ** 2 for p, label in zip(preds, y)) / len(rows),
            'naive_prevalence_brier': sum((p0 - label) ** 2 for label in y) / len(rows),
            'log_loss': -sum(label * log(max(1e-12, min(1 - 1e-12, p))) +
                             (1 - label) * log(max(1e-12, min(1 - 1e-12, 1 - p)))
                             for p, label in zip(preds, y)) / len(rows),
            'research_only_selected': len(selected),
            'research_only_proxy_return_sum': net,
            'research_only_cost_2x_return_sum': net - len(selected) * COST_BPS / 10_000,
            'note': 'ECB published reference changes; no execution-price, broker, paper or real P/L'}


def train_reference_candidate(dataset: dict[str, Any], *, code_sha: str,
                              prereg_sha: str = PREREG_COMMIT) -> dict[str, Any]:
    if prereg_sha != PREREG_COMMIT or not re.fullmatch(r'[0-9a-f]{40}', code_sha):
        raise GateError('unverified or missing fixed preregistration/code SHA')
    if dataset.get('status') not in ('RESEARCH_CANDIDATE', 'UNIT_FIXTURE') or dataset.get('cost_bps') != COST_BPS:
        raise GateError('invalid research scope or cost protocol')
    sig = {'schema_version': 1, 'source': dataset['source'],
           'original_observations': dataset['original_observations'],
           'cost_bps': COST_BPS, 'rows': dataset['rows']}
    if dataset['dataset_version'] != 'ecb-dv1-' + _digest(sig)[:20] or dataset['row_count'] != len(dataset['rows']):
        raise GateError('candidate data differs from immutable source/dataset version')
    # Rebuild from unmodified rates: a valid recomputed digest alone is not enough
    # to permit an altered label, shifted timestamp or invented feature.
    expected = build_reference_dataset(dataset['original_observations'],
                                       fixture_only=dataset['status'] == 'UNIT_FIXTURE')
    if dataset != expected:
        raise GateError('dataset features/labels do not match original published references')
    rows = dataset['rows']
    n = len(rows)
    a, b = int(n * .6), int(n * .8)
    train, val, oos = rows[:a], rows[a + 1:b], rows[b + 1:]
    if min(len(train), len(val), len(oos)) < 40:
        raise GateError('insufficient chronological validation/OOS samples')
    model = _fit(train)
    development = train + val
    folds = []
    for frac in (.50, .60, .70):
        start = int(len(development) * frac)
        end = min(len(development), start + max(40, int(len(development) * .1)))
        prior, future = development[:start - 1], development[start:end]
        if len(future) < 40:
            raise GateError('insufficient preregistered walk-forward data')
        folds.append({'train_count': len(prior),
                      'test_as_of': [future[0]['as_of'], future[-1]['as_of']],
                      'metrics': _metrics(_fit(prior), future)})
    evaluation = {'train': _metrics(model, train), 'validation': _metrics(model, val),
                  'oos': _metrics(model, oos), 'walk_forward_dev_only': folds}
    o = evaluation['oos']
    wf_positive = sum(f['metrics']['brier'] < f['metrics']['naive_prevalence_brier'] for f in folds)
    reason = []
    if not o['brier'] < o['naive_prevalence_brier']:
        reason.append('OOS_BRIER_BASELINE_FAIL')
    if wf_positive < 2:
        reason.append('WALK_FORWARD_STABILITY_FAIL')
    if o['research_only_selected'] < 5:
        reason.append('INSUFFICIENT_SELECTED_SAMPLES')
    if not o['research_only_cost_2x_return_sum'] > 0:
        reason.append('COST_2X_STRESS_FAIL')
    status = 'REJECTED' if reason else 'CANDIDATE_NOT_APPROVED'
    artifact = {'source': dataset['source'], 'dataset_version': dataset['dataset_version'],
                'model': model, 'evaluation': evaluation, 'status': status,
                'reject_reasons': reason, 'protocol_commit': PREREG_COMMIT,
                'code_sha': code_sha, 'splits': {
                    'train': [train[0]['as_of'], train[-1]['as_of']],
                    'validation': [val[0]['as_of'], val[-1]['as_of']],
                    'oos': [oos[0]['as_of'], oos[-1]['as_of']]},
                'public_inference': False, 'broker_orders': False,
                'live_money_locked': True, 'signal_or_abstain': 'ABSTAIN', 'gate_status': 'LOCKED'}
    identity = json.dumps(artifact, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
    artifact['model_version'] = 'ecb-mc1-' + sha256(identity).hexdigest()[:20]
    return artifact

