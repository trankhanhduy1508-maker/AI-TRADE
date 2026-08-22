"""Run the deterministic signal-only engine against one cleaned CSV."""

import argparse
import json
import sys
from pathlib import Path

# Allow this script to be invoked directly from the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.backtest.engine import RuleEngineSignalEvaluator, run_backtest
from src.backtest.spec import load_strategy_spec
from src.data_loader.pipeline import load_and_clean


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--max-bars", type=int, default=None)
    args = parser.parse_args()

    loaded = load_and_clean(str(args.csv))
    bars = loaded["bars"]
    if args.max_bars is not None:
        if args.max_bars < 1:
            raise SystemExit("--max-bars must be positive")
        bars = bars[: args.max_bars]
    result = run_backtest(
        bars, load_strategy_spec(args.spec), RuleEngineSignalEvaluator()
    )
    print(
        json.dumps(
            {
                "csv": str(args.csv),
                "bars": len(bars),
                "duplicates_removed": loaded["n_duplicates_removed"],
                "invalid_removed": len(loaded["invalid_removed"]),
                "outlier_indices": len(loaded["outlier_indices"]),
                "metrics": result.metrics,
                "open_position": result.open_position is not None,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
