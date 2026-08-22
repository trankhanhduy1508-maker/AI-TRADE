"""Machine-readable strategy-spec contract for the P1 backtest path."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class StrategySpec:
    strategy_id: str
    risk_mode: str
    provenance: dict[str, str] = field(default_factory=dict)
    signal_model: str = "RULE_ENGINE"
    lookback_bars: int = 20
    entry_timing: str = "CLOSE"
    stop_lookback_bars: int = 5
    stop_buffer_price: float = 0.0
    reward_risk: float = 1.5
    score_threshold: float = 80.0
    spread_pips: float = 2.0
    slippage_price: float = 0.0
    position_policy: str = "ONE_OPEN"
    ambiguous_bar_policy: str = "STOP_FIRST"


def strategy_spec_from_dict(raw: dict[str, Any]) -> StrategySpec:
    """Validate and construct a StrategySpec from JSON-compatible data."""

    strategy_id = str(raw.get("strategy_id", "")).strip()
    if not strategy_id:
        raise ValueError("strategy_id is required")

    risk_mode = str(raw.get("risk_mode", "")).upper()
    if risk_mode != "SIGNAL_ONLY":
        raise ValueError("risk_mode must be SIGNAL_ONLY")

    provenance = raw.get("provenance")
    if not isinstance(provenance, dict) or not provenance:
        raise ValueError("provenance must be a non-empty object")

    signal_model = str(raw.get("signal_model", "RULE_ENGINE")).upper()
    if signal_model not in {"RULE_ENGINE", "TIME_SERIES_MOMENTUM"}:
        raise ValueError("signal_model is not implemented")

    lookback_bars = int(raw.get("lookback_bars", 20))
    if lookback_bars < 1:
        raise ValueError("lookback_bars must be positive")

    entry_timing = str(raw.get("entry_timing", "CLOSE")).upper()
    if entry_timing != "CLOSE":
        raise ValueError("only CLOSE entry_timing is implemented")

    position_policy = str(raw.get("position_policy", "ONE_OPEN")).upper()
    if position_policy != "ONE_OPEN":
        raise ValueError("only ONE_OPEN position_policy is implemented")

    ambiguous_policy = str(
        raw.get("ambiguous_bar_policy", "STOP_FIRST")
    ).upper()
    if ambiguous_policy != "STOP_FIRST":
        raise ValueError("only STOP_FIRST ambiguous_bar_policy is implemented")

    stop_lookback = int(raw.get("stop_lookback_bars", 5))
    reward_risk = float(raw.get("reward_risk", 1.5))
    score_threshold = float(raw.get("score_threshold", 80.0))
    spread_pips = float(raw.get("spread_pips", 2.0))
    slippage_price = float(raw.get("slippage_price", 0.0))
    stop_buffer_price = float(raw.get("stop_buffer_price", 0.0))

    if stop_lookback < 1:
        raise ValueError("stop_lookback_bars must be positive")
    if reward_risk <= 0:
        raise ValueError("reward_risk must be positive")
    if not 0 <= score_threshold <= 100:
        raise ValueError("score_threshold must be between 0 and 100")
    if spread_pips < 0 or slippage_price < 0 or stop_buffer_price < 0:
        raise ValueError("costs and stop buffer cannot be negative")

    return StrategySpec(
        strategy_id=strategy_id,
        risk_mode=risk_mode,
        provenance={str(key): str(value) for key, value in provenance.items()},
        signal_model=signal_model,
        lookback_bars=lookback_bars,
        entry_timing=entry_timing,
        stop_lookback_bars=stop_lookback,
        stop_buffer_price=stop_buffer_price,
        reward_risk=reward_risk,
        score_threshold=score_threshold,
        spread_pips=spread_pips,
        slippage_price=slippage_price,
        position_policy=position_policy,
        ambiguous_bar_policy=ambiguous_policy,
    )


def load_strategy_spec(path: str | Path) -> StrategySpec:
    """Load and validate a machine-readable strategy spec from JSON."""

    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load strategy spec {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError("strategy spec root must be an object")
    return strategy_spec_from_dict(raw)
