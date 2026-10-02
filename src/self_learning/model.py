"""Deterministic, standard-library research ML baseline, with no broker integration.

This module accepts ONLY a validated chronological research dataset produced by
pipeline.build_labeled_bars. It never approves, publishes, or sends trading orders.
The final OOS segment is scored once; walk-forward uses only the prior 80%.
"""
from __future__ import annotations

from hashlib import sha256
from math import exp, log, sqrt, isfinite
import json
from typing import Any

from .pipeline import GateError, chronological_split, _digest

FEATURES = ("feature_prev_return", "feature_bar_range")
HYPERPARAMETERS = {"learning_rate": 0.12, "epochs": 600, "l2": 0.03,
                   "confidence_threshold": 0.55, "max_z": 8.0}


def _sigmoid(value: float) -> float:
    if value >= 0:
        return 1.0 / (1.0 + exp(-value))
    e = exp(value)
    return e / (1.0 + e)


def _features(row: dict[str, Any]) -> list[float]:
    values = [row.get(name) for name in FEATURES]
    if any(not isinstance(v, (int, float)) or not isfinite(v) for v in values):
        raise GateError("missing or nonfinite causal feature")
    return list(map(float, values))


def _label(row: dict[str, Any]) -> int:
    value = row.get("target_positive_after_cost")
    if type(value) is not int or value not in (0, 1):
        raise GateError("invalid binary research label")
    if not isinstance(row.get("target_next_bar_net_return"), (int, float)) or not isfinite(row["target_next_bar_net_return"]):
        raise GateError("invalid research return")
    if int(row["target_next_bar_net_return"] > 0) != value:
        raise GateError("label is inconsistent with after-cost return")
    return value


def _fit(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if len(rows) < 80:
        raise GateError("fewer than 80 chronological training examples")
    labels = [_label(r) for r in rows]
    if min(sum(labels), len(labels) - sum(labels)) < 8:
        raise GateError("one class is too small for a meaningful research baseline")
    x = [_features(r) for r in rows]
    means = [sum(v[j] for v in x) / len(x) for j in range(len(FEATURES))]
    stdevs = [max(sqrt(sum((v[j] - means[j]) ** 2 for v in x) / len(x)), 1e-8)
              for j in range(len(FEATURES))]
    bound = HYPERPARAMETERS["max_z"]
    normalized = [[max(-bound, min(bound, (v[j] - means[j]) / stdevs[j]))
                   for j in range(len(FEATURES))] for v in x]
    weights = [0.0] * (len(FEATURES) + 1)
    weights[0] = log(sum(labels) / (len(labels) - sum(labels)))
    rate, penalty = HYPERPARAMETERS["learning_rate"], HYPERPARAMETERS["l2"]
    for _ in range(HYPERPARAMETERS["epochs"]):
        gradients = [0.0] * len(weights)
        for v, y in zip(normalized, labels):
            err = _sigmoid(weights[0] + sum(w * f for w, f in zip(weights[1:], v))) - y
            gradients[0] += err
            for j in range(len(v)):
                gradients[j + 1] += err * v[j]
        weights[0] -= rate * gradients[0] / len(rows)
        for j in range(1, len(weights)):
            weights[j] -= rate * (gradients[j] / len(rows) + penalty * weights[j])
    return {"intercept": weights[0], "weights": weights[1:],
            "feature_names": list(FEATURES), "train_mean": means, "train_std": stdevs,
            "train_positive_rate": sum(labels) / len(labels),
            "hyperparameters": dict(HYPERPARAMETERS), "train_count": len(rows)}


def _predict(model: dict[str, Any], row: dict[str, Any]) -> float:
    x = _features(row)
    b = model["hyperparameters"]["max_z"]
    z = model["intercept"] + sum(
        w * max(-b, min(b, (value - mean) / sd))
        for w, value, mean, sd in zip(model["weights"], x, model["train_mean"], model["train_std"])
    )
    return _sigmoid(z)


def _metrics(model: dict[str, Any], rows: list[dict[str, Any]], cost_bps: float) -> dict[str, Any]:
    if not rows:
        raise GateError("empty evaluation segment")
    eps = 1e-12
    baseline_p = model["train_positive_rate"]
    actual = [_label(r) for r in rows]
    preds = [_predict(model, r) for r in rows]
    threshold = HYPERPARAMETERS["confidence_threshold"]
    selected = [r for r, p in zip(rows, preds) if p >= threshold]
    stressed = [float(r["target_next_bar_net_return"]) - cost_bps / 10000
                for r in selected]
    return {"count": len(rows), "positives": sum(actual),
            "brier": sum((p - y)**2 for p, y in zip(preds, actual)) / len(rows),
            "naive_prevalence_brier": sum((baseline_p - y)**2 for y in actual) / len(rows),
            "log_loss": -sum(y*log(max(eps, min(1-eps,p))) +
                             (1-y)*log(max(eps, min(1-eps,1-p)))
                             for p,y in zip(preds,actual))/len(rows),
            "research_only_selected": len(selected),
            "research_only_net_return_sum": sum(float(r["target_next_bar_net_return"]) for r in selected),
            "research_only_cost_2x_return_sum": sum(stressed),
            "note": "Research proxy on next-open-to-close labels; not broker fills, paper trades or live P/L"}


def train_candidate(dataset: dict[str, Any], code_sha: str,
                    pre_registered: bool = False) -> dict[str, Any]:
    """Fit a *candidate* only after preregistration; do not auto-promote."""
    if not pre_registered:
        raise GateError("research hypothesis and evaluation must be preregistered")
    if not isinstance(code_sha, str) or len(code_sha) != 40 or any(c not in "0123456789abcdef" for c in code_sha):
        raise GateError("verified 40-character Git code commit SHA required")
    if dataset.get("cost_mode") != "RESEARCH_PROXY" or not str(dataset.get("dataset_version", "")).startswith("dv1-"):
        raise GateError("dataset is not a versioned, cost-declared research candidate")
    source, bps, rows = dataset.get("source"), dataset.get("round_trip_cost_bps"), dataset.get("rows")
    from .rights import require_ml_training_rights
    require_ml_training_rights(source)
    if not isinstance(source, dict) or not isinstance(rows, list) or not isinstance(bps, (int, float)) or not isfinite(bps) or not 0 <= bps <= 500:
        raise GateError("source metadata, rows or explicit cost are invalid")
    try:
        sig = {"schema_version": 1, "source": source, "round_trip_cost_bps": bps, "rows": rows}
        expected = "dv1-" + _digest(sig)[:20]
    except (TypeError, ValueError, KeyError) as exc:
        raise GateError("dataset snapshot cannot be hashed") from exc
    if expected != dataset["dataset_version"] or dataset.get("row_count") != len(rows):
        raise GateError("dataset snapshot differs from its pinned version")
    slices = chronological_split(dataset)
    train, validation, oos = (slices[s] for s in ("train", "validation", "oos"))
    candidate = _fit(train)
    # Walk-forward only before sealed OOS (train + validation); never reuse OOS for model selection.
    development = train + validation
    folds = []
    # 3 expanding folds with 50%, 60%, 70% training / subsequent ~10% test,
    # re-fitting within each fold using ONLY earlier observations.
    for proportion in (0.50, 0.60, 0.70):
        begin = int(len(development) * proportion)
        end = min(len(development), begin + max(40, int(len(development) * 0.10)))
        if end > len(development) or end - begin < 40:
            raise GateError("insufficient observations for preregistered walk-forward")
        prior = development[:begin-1]  # purge horizon-one boundary
        future = development[begin:end]
        prior_model = _fit(prior)
        folds.append({"train_count": len(prior), "test_as_of": [future[0]["as_of"], future[-1]["as_of"]],
                      "metrics": _metrics(prior_model, future, bps)})
    evaluation = {"train": _metrics(candidate, train, bps),
                  "validation": _metrics(candidate, validation, bps),
                  "oos": _metrics(candidate, oos, bps), "walk_forward_dev_only": folds}
    identity = {"code_sha": code_sha, "dataset_version": dataset["dataset_version"],
                "candidate": candidate, "protocol": "chronological_60_20_20_purged_1",
                "evaluation": evaluation}
    blob = json.dumps(identity, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return {"model_version": "mc1-" + sha256(blob).hexdigest()[:20],
            "status": "CANDIDATE_NOT_APPROVED", "mode": "RESEARCH",
            "broker_orders": False, "live_money_locked": True, **identity}


def candidate_insight(candidate: dict[str, Any] | None, *, approved: bool = False) -> dict[str, Any]:
    """The public API is fail-closed until approval + separate deployment evidence."""
    if not approved or candidate is None:
        return {"model_version": None, "as_of": None, "data_version": None,
                "status": "MODEL_NOT_APPROVED" if candidate else "MODEL_NOT_TRAINED",
                "signal_or_abstain": "ABSTAIN", "gate_status": "LOCKED",
                "broker_orders": False, "uncertainty": None}
    raise GateError("model promotion requires a distinct audited production inference implementation")
