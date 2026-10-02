"""Run the deterministic signal-only engine against one cleaned CSV."""

import argparse
import json
import sys
from pathlib import Path

# Allow this script to be invoked directly from the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.backtest.costs import CostModel
from src.backtest.engine import RuleEngineSignalEvaluator, run_backtest
from src.backtest.spec import load_strategy_spec
from src.backtest.validation import run_is_oos
from src.data_loader.pipeline import load_and_clean
from src.strategies.time_series_momentum import TimeSeriesMomentumEvaluator


def _evaluator_factory(spec):
    if spec.signal_model == "TIME_SERIES_MOMENTUM":
        return TimeSeriesMomentumEvaluator
    return RuleEngineSignalEvaluator


def _evaluator(spec):
    return _evaluator_factory(spec)()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--max-bars", type=int, default=None)
    parser.add_argument("--split-fraction", type=float, default=None)
    parser.add_argument("--cost-profile", type=Path, default=None)
    parser.add_argument("--cost-key", default=None)
    args = parser.parse_args()

    loaded = load_and_clean(str(args.csv))
    bars = loaded["bars"]
    if args.max_bars is not None:
        if args.max_bars < 1:
            raise SystemExit("--max-bars must be positive")
        bars = bars[: args.max_bars]

    cost_model = CostModel.zero()
    if args.cost_profile is not None:
        with args.cost_profile.open("r", encoding="utf-8") as handle:
            profile = json.load(handle)
        profiles = profile.get("profiles")
        if profiles is not None:
            if not args.cost_key or args.cost_key not in profiles:
                raise SystemExit("--cost-key must select a profile entry")
            values = profiles[args.cost_key]
            profile_id = f"{profile['profile_id']}:{args.cost_key}"
        else:
            values = profile
            profile_id = profile["profile_id"]
        cost_model = CostModel(profile_id=profile_id, **values)

    spec = load_strategy_spec(args.spec)
    if args.split_fraction is None:
        result = run_backtest(
            bars,
            spec,
            _evaluator(spec),
            cost_model=cost_model,
        )
        payload = {
            "metrics": result.metrics,
            "open_position": result.open_position is not None,
        }
    else:
        if not 0 < args.split_fraction < 1:
            raise SystemExit("--split-fraction must be between 0 and 1")
        split_index = int(len(bars) * args.split_fraction)
        is_result, oos_result = run_is_oos(
            bars,
            spec,
            _evaluator_factory(spec),
            split_index=split_index,
            cost_model=cost_model,
        )
        payload = {
            "split_index": split_index,
            "split_timestamp": bars[split_index].timestamp,
            "in_sample": {
                "metrics": is_result.metrics,
                "open_position": is_result.open_position is not None,
            },
            "out_of_sample": {
                "metrics": oos_result.metrics,
                "open_position": oos_result.open_position is not None,
                "oos_status": "PRELIMINARY",
            },
        }
    print(
        json.dumps(
            {
                "csv": str(args.csv),
                "bars": len(bars),
                "duplicates_removed": loaded["n_duplicates_removed"],
                "invalid_removed": len(loaded["invalid_removed"]),
                "outlier_indices": len(loaded["outlier_indices"]),
                "cost_profile": cost_model.profile_id,
                **payload,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
