"""Run fixed expanding-history walk-forward research folds."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.backtest.costs import CostModel
from src.backtest.engine import RuleEngineSignalEvaluator
from src.backtest.spec import load_strategy_spec
from src.backtest.validation import run_walk_forward
from src.data_loader.pipeline import load_and_clean
from src.strategies.time_series_momentum import TimeSeriesMomentumEvaluator


def _factory(spec):
    if spec.signal_model == "TIME_SERIES_MOMENTUM":
        return TimeSeriesMomentumEvaluator
    return RuleEngineSignalEvaluator


def _cost_model(path: Path | None, key: str | None) -> CostModel:
    if path is None:
        return CostModel.zero()
    with path.open("r", encoding="utf-8") as handle:
        profile = json.load(handle)
    profiles = profile.get("profiles")
    if profiles is not None:
        if not key or key not in profiles:
            raise SystemExit("--cost-key must select a profile entry")
        values = profiles[key]
        profile_id = f"{profile['profile_id']}:{key}"
    else:
        values = profile
        profile_id = profile["profile_id"]
    return CostModel(profile_id=profile_id, **values)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--train-fraction", type=float, default=0.5)
    parser.add_argument("--test-fraction", type=float, default=0.1)
    parser.add_argument("--cost-profile", type=Path, default=None)
    parser.add_argument("--cost-key", default=None)
    args = parser.parse_args()

    if not 0 < args.train_fraction < 1 or not 0 < args.test_fraction < 1:
        raise SystemExit("fractions must be between 0 and 1")
    loaded = load_and_clean(str(args.csv))
    bars = loaded["bars"]
    train_bars = int(len(bars) * args.train_fraction)
    test_bars = max(1, int(len(bars) * args.test_fraction))
    spec = load_strategy_spec(args.spec)
    costs = _cost_model(args.cost_profile, args.cost_key)
    folds = run_walk_forward(
        bars,
        spec,
        _factory(spec),
        train_bars=train_bars,
        test_bars=test_bars,
        cost_model=costs,
    )
    print(
        json.dumps(
            {
                "csv": str(args.csv),
                "strategy_id": spec.strategy_id,
                "bars": len(bars),
                "train_bars": train_bars,
                "test_bars": test_bars,
                "cost_profile": costs.profile_id,
                "folds": [
                    {
                        "train_end": fold.train_end,
                        "test_end": fold.test_end,
                        "metrics": fold.result.metrics,
                        "open_position": fold.result.open_position is not None,
                    }
                    for fold in folds
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
