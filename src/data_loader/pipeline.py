"""End-to-end data loading pipeline.

Combines CSV loading, validation, and cleaning steps into a single convenient function
(BACKTEST_ENGINE.md steps 1-3: Market Data → Data Validation → Data Cleaning).
"""

from src.rule_engine.types import Bar
from src.data_loader.csv_loader import load_csv
from src.data_loader.cleaner import sort_and_dedupe, remove_invalid, detect_outliers


def load_and_clean(path: str, max_pct_jump: float = 0.10) -> dict:
    """Load CSV, validate, and clean OHLCV data in one pipeline.

    Steps (per BACKTEST_ENGINE.md section 2.2):
    1. Market Data (CSV loading)
    2. Data Validation (check constraints)
    3. Data Cleaning (sort, dedupe, detect outliers, remove invalid)

    Args:
        path: Path to CSV file
        max_pct_jump: Max allowed price jump percentage (default 0.10 = 10%)

    Returns:
        dict: {
            "bars": list[Bar],                # Clean, valid bars
            "n_duplicates_removed": int,      # Count of duplicate timestamps removed
            "invalid_removed": list[ValidationIssue],  # Removed invalid bars
            "outlier_indices": list[int],     # Indices in final bars list with price jumps
        }

    Raises:
        ValueError: If CSV loading fails
    """
    # Step 1: Load CSV
    bars = load_csv(path)

    # Step 3: Sort and dedupe (done before validation to have clean data)
    sorted_bars, n_duplicates = sort_and_dedupe(bars)

    # Step 2: Validate and remove invalid
    valid_bars, invalid_issues = remove_invalid(sorted_bars)

    # Step 3: Detect outliers (on final cleaned bars)
    outlier_indices = detect_outliers(valid_bars, max_pct_jump=max_pct_jump)

    return {
        "bars": valid_bars,
        "n_duplicates_removed": n_duplicates,
        "invalid_removed": invalid_issues,
        "outlier_indices": outlier_indices,
    }
