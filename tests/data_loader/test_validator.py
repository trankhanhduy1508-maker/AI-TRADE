"""Tests for data validation.

Tests validator.validate() and validator.is_valid() functions.
"""

import pytest
from src.rule_engine.types import Bar
from src.data_loader.validator import validate, is_valid, ValidationIssue


class TestValidate:
    """Test bar validation."""

    def test_valid_bars(self):
        """Test that valid bars return no issues."""
        bars = [
            Bar("2024-01-01 09:00:00", 1.1000, 1.1050, 1.0980, 1.1030, 1500000),
            Bar("2024-01-01 10:00:00", 1.1030, 1.1080, 1.1020, 1.1070, 1800000),
        ]
        issues = validate(bars)
        assert len(issues) == 0

    def test_high_less_than_open(self):
        """Test detection of high < open."""
        bars = [
            Bar("2024-01-01 09:00:00", 1.1000, 1.0950, 1.0980, 1.0990, 1500000),
        ]
        issues = validate(bars)
        # Multiple issues possible: high < max(O,C) and high < low
        assert len(issues) >= 1
        assert any("High" in issue.reason for issue in issues)

    def test_high_less_than_close(self):
        """Test detection of high < close."""
        bars = [
            Bar("2024-01-01 09:00:00", 1.1000, 1.1030, 1.0980, 1.1050, 1500000),
        ]
        issues = validate(bars)
        assert len(issues) == 1
        assert "High" in issues[0].reason

    def test_low_greater_than_open(self):
        """Test detection of low > open."""
        bars = [
            Bar("2024-01-01 09:00:00", 1.1000, 1.1050, 1.1010, 1.1030, 1500000),
        ]
        issues = validate(bars)
        assert len(issues) == 1
        assert "Low" in issues[0].reason

    def test_low_greater_than_close(self):
        """Test detection of low > close."""
        bars = [
            Bar("2024-01-01 09:00:00", 1.1000, 1.1050, 1.1040, 1.1030, 1500000),
        ]
        issues = validate(bars)
        assert len(issues) == 1
        assert "Low" in issues[0].reason

    def test_high_less_than_low(self):
        """Test detection of high < low (inverted range)."""
        bars = [
            Bar("2024-01-01 09:00:00", 1.1000, 1.0980, 1.1050, 1.1030, 1500000),
        ]
        issues = validate(bars)
        assert len(issues) >= 1  # Multiple violations possible
        assert any("High" in issue.reason for issue in issues)

    def test_negative_volume(self):
        """Test detection of negative volume."""
        bars = [
            Bar("2024-01-01 09:00:00", 1.1000, 1.1050, 1.0980, 1.1030, -1500000),
        ]
        issues = validate(bars)
        assert len(issues) == 1
        assert "negative" in issues[0].reason.lower()

    def test_zero_volume_valid(self):
        """Test that zero volume is allowed (gap/no trading)."""
        bars = [
            Bar("2024-01-01 09:00:00", 1.1000, 1.1050, 1.0980, 1.1030, 0),
        ]
        issues = validate(bars)
        assert len(issues) == 0

    def test_multiple_issues_per_bar(self):
        """Test bar with multiple validation errors."""
        bars = [
            Bar("2024-01-01 09:00:00", 1.1000, 1.0950, 1.1050, 1.1030, -1500000),
        ]
        issues = validate(bars)
        # Should report multiple issues: high < low, high < open, high < close, negative volume
        assert len(issues) >= 2

    def test_issue_contains_timestamp_and_index(self):
        """Test that issues contain correct index and timestamp."""
        bars = [
            Bar("2024-01-01 09:00:00", 1.1000, 1.1050, 1.0980, 1.1030, 1500000),
            Bar("2024-01-01 10:00:00", 1.1030, 1.0980, 1.1050, 1.1070, -100),
        ]
        issues = validate(bars)
        assert len(issues) >= 1
        assert issues[0].index == 1
        assert issues[0].timestamp == "2024-01-01 10:00:00"

    def test_empty_list(self):
        """Test that empty list returns no issues."""
        issues = validate([])
        assert len(issues) == 0


class TestIsValid:
    """Test is_valid() convenience function."""

    def test_is_valid_all_valid(self):
        """Test is_valid returns True for valid bars."""
        bars = [
            Bar("2024-01-01 09:00:00", 1.1000, 1.1050, 1.0980, 1.1030, 1500000),
        ]
        assert is_valid(bars) is True

    def test_is_valid_with_issues(self):
        """Test is_valid returns False when issues found."""
        bars = [
            Bar("2024-01-01 09:00:00", 1.1000, 1.1050, 1.0980, 1.1030, -1500000),
        ]
        assert is_valid(bars) is False

    def test_is_valid_empty_list(self):
        """Test is_valid returns True for empty list."""
        assert is_valid([]) is True
