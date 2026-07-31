"""Data cleaning for OHLCV bars.

Implements data cleaning steps: sort, dedupe, detect outliers, remove invalid
(BACKTEST_ENGINE.md step 3, DATA_REQUIREMENTS.md section 1).
"""

from src.rule_engine.types import Bar
from src.data_loader.validator import ValidationIssue, validate


def sort_and_dedupe(bars: list[Bar]) -> tuple[list[Bar], int]:
    """Sort bars by timestamp (ascending) and remove duplicates.

    Keeps the first occurrence of each timestamp (by input order).
    Uses string comparison for ISO 8601 timestamps (assumes fixed format).

    Args:
        bars: Unsorted or duplicate-containing bars

    Returns:
        tuple: (sorted_unique_bars, n_duplicates_removed)
    """
    # Track which timestamps we've seen (preserve first occurrence)
    seen = set()
    unique = []

    for bar in bars:
        if bar.timestamp not in seen:
            unique.append(bar)
            seen.add(bar.timestamp)

    n_duplicates = len(bars) - len(unique)

    # Sort by timestamp (string comparison works for ISO 8601 fixed format)
    sorted_bars = sorted(unique, key=lambda b: b.timestamp)

    return sorted_bars, n_duplicates


def detect_outliers(bars: list[Bar], max_pct_jump: float = 0.10) -> list[int]:
    """Detect bars with price jumps exceeding threshold vs previous close.

    Only detects outliers (reports indices); does not remove them.
    First bar (index 0) cannot be an outlier (no previous bar to compare).

    Assumes bars are already sorted by timestamp.

    Args:
        bars: Sorted bars
        max_pct_jump: Max allowed percentage change (default 10%). For example,
                     if max_pct_jump=0.10, a jump > 10% will be flagged.

    Returns:
        list[int]: Indices (in input bars list) of bars with outlier jumps
    """
    outliers = []

    if len(bars) < 2:
        return outliers  # Need at least 2 bars to detect jump

    for idx in range(1, len(bars)):
        prev_close = bars[idx - 1].close
        curr_close = bars[idx].close

        if prev_close == 0:
            # Skip division by zero (edge case)
            continue

        pct_change = abs(curr_close - prev_close) / prev_close

        if pct_change > max_pct_jump:
            outliers.append(idx)

    return outliers


def remove_invalid(bars: list[Bar]) -> tuple[list[Bar], list[ValidationIssue]]:
    """Remove bars with validation errors.

    Returns valid bars only, plus list of removed issues for logging.

    Args:
        bars: Bars to validate and filter

    Returns:
        tuple: (valid_bars, invalid_issues)
               - valid_bars: Bars without validation errors
               - invalid_issues: ValidationIssues for removed bars
    """
    issues = validate(bars)

    # Track which indices to keep
    invalid_indices = {issue.index for issue in issues}
    valid_bars = [bar for idx, bar in enumerate(bars) if idx not in invalid_indices]

    return valid_bars, issues
