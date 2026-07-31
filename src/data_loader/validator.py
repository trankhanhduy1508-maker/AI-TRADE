"""Data validation for OHLCV bars.

Validates bars against data quality constraints (DATA_REQUIREMENTS.md section 10,
BACKTEST_ENGINE.md step 2). Returns list of issues found without raising exceptions.
"""

from dataclasses import dataclass
from src.rule_engine.types import Bar


@dataclass
class ValidationIssue:
    """Record of a single validation error found in a bar."""

    index: int          # Position in original list
    timestamp: str      # Bar's timestamp
    reason: str         # Human-readable description of the issue


def validate(bars: list[Bar]) -> list[ValidationIssue]:
    """Validate OHLCV bars and return all issues found.

    Checks constraints per DATA_REQUIREMENTS.md section 1:
    - H >= max(O, C)
    - L <= min(O, C)
    - H >= L
    - volume >= 0

    Args:
        bars: List of Bar objects to validate

    Returns:
        list[ValidationIssue]: List of validation issues (empty if all valid)
    """
    issues = []

    for idx, bar in enumerate(bars):
        # Check H >= max(O, C)
        if bar.high < max(bar.open, bar.close):
            issues.append(ValidationIssue(
                index=idx,
                timestamp=bar.timestamp,
                reason=f"High ({bar.high}) < max(Open, Close) = {max(bar.open, bar.close)}"
            ))

        # Check L <= min(O, C)
        if bar.low > min(bar.open, bar.close):
            issues.append(ValidationIssue(
                index=idx,
                timestamp=bar.timestamp,
                reason=f"Low ({bar.low}) > min(Open, Close) = {min(bar.open, bar.close)}"
            ))

        # Check H >= L
        if bar.high < bar.low:
            issues.append(ValidationIssue(
                index=idx,
                timestamp=bar.timestamp,
                reason=f"High ({bar.high}) < Low ({bar.low})"
            ))

        # Check volume >= 0
        if bar.volume < 0:
            issues.append(ValidationIssue(
                index=idx,
                timestamp=bar.timestamp,
                reason=f"Volume ({bar.volume}) is negative"
            ))

    return issues


def is_valid(bars: list[Bar]) -> bool:
    """Check if all bars are valid.

    Convenience helper for quick boolean check.

    Args:
        bars: List of Bar objects to validate

    Returns:
        bool: True if no issues found, False otherwise
    """
    return len(validate(bars)) == 0
