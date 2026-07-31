"""Tests for data cleaning.

Tests sort_and_dedupe(), detect_outliers(), and remove_invalid() functions.
"""

import pytest
from src.rule_engine.types import Bar
from src.data_loader.cleaner import sort_and_dedupe, detect_outliers, remove_invalid


class TestSortAndDedupe:
    """Test sorting and deduplication."""

    def test_sort_unsorted_data(self):
        """Test that bars are sorted by timestamp."""
        bars = [
            Bar("2024-01-01 11:00:00", 1.1070, 1.1120, 1.1050, 1.1100, 2000000),
            Bar("2024-01-01 09:00:00", 1.1000, 1.1050, 1.0980, 1.1030, 1500000),
            Bar("2024-01-01 10:00:00", 1.1030, 1.1080, 1.1020, 1.1070, 1800000),
        ]
        sorted_bars, n_dupes = sort_and_dedupe(bars)

        assert len(sorted_bars) == 3
        assert n_dupes == 0
        assert sorted_bars[0].timestamp == "2024-01-01 09:00:00"
        assert sorted_bars[1].timestamp == "2024-01-01 10:00:00"
        assert sorted_bars[2].timestamp == "2024-01-01 11:00:00"

    def test_remove_duplicate_timestamps(self):
        """Test that duplicate timestamps are removed (keeping first occurrence)."""
        bars = [
            Bar("2024-01-01 09:00:00", 1.1000, 1.1050, 1.0980, 1.1030, 1500000),
            Bar("2024-01-01 09:00:00", 1.1000, 1.1055, 1.0975, 1.1035, 1600000),  # dup
            Bar("2024-01-01 10:00:00", 1.1030, 1.1080, 1.1020, 1.1070, 1800000),
        ]
        sorted_bars, n_dupes = sort_and_dedupe(bars)

        assert len(sorted_bars) == 2
        assert n_dupes == 1
        # Should keep first 09:00 bar
        assert sorted_bars[0].close == 1.1030

    def test_multiple_duplicates(self):
        """Test handling multiple duplicate timestamps."""
        bars = [
            Bar("2024-01-01 09:00:00", 1.1000, 1.1050, 1.0980, 1.1030, 1500000),
            Bar("2024-01-01 09:00:00", 1.1000, 1.1055, 1.0975, 1.1035, 1600000),
            Bar("2024-01-01 09:00:00", 1.1000, 1.1060, 1.0970, 1.1040, 1700000),
            Bar("2024-01-01 10:00:00", 1.1030, 1.1080, 1.1020, 1.1070, 1800000),
        ]
        sorted_bars, n_dupes = sort_and_dedupe(bars)

        assert len(sorted_bars) == 2
        assert n_dupes == 2
        # Should keep first 09:00 bar (1.1030 close)
        assert sorted_bars[0].close == 1.1030

    def test_already_sorted_no_dupes(self):
        """Test that already sorted data with no dupes returns correct counts."""
        bars = [
            Bar("2024-01-01 09:00:00", 1.1000, 1.1050, 1.0980, 1.1030, 1500000),
            Bar("2024-01-01 10:00:00", 1.1030, 1.1080, 1.1020, 1.1070, 1800000),
        ]
        sorted_bars, n_dupes = sort_and_dedupe(bars)

        assert len(sorted_bars) == 2
        assert n_dupes == 0
        assert sorted_bars[0].timestamp == "2024-01-01 09:00:00"

    def test_empty_list(self):
        """Test empty list handling."""
        sorted_bars, n_dupes = sort_and_dedupe([])
        assert len(sorted_bars) == 0
        assert n_dupes == 0


class TestDetectOutliers:
    """Test outlier detection."""

    def test_normal_price_movement(self):
        """Test that small price changes are not flagged as outliers."""
        bars = [
            Bar("2024-01-01 09:00:00", 1.1000, 1.1050, 1.0980, 1.1030, 1500000),
            Bar("2024-01-01 10:00:00", 1.1030, 1.1080, 1.1020, 1.1070, 1800000),
        ]
        outliers = detect_outliers(bars, max_pct_jump=0.10)
        assert len(outliers) == 0

    def test_detect_large_jump(self):
        """Test detection of price jump > threshold."""
        bars = [
            Bar("2024-01-01 09:00:00", 1.1000, 1.1050, 1.0980, 1.1030, 1500000),
            # 1.2220 vs 1.1030 = (1.2220-1.1030)/1.1030 = 10.76% jump
            Bar("2024-01-01 10:00:00", 1.2200, 1.2250, 1.2100, 1.2220, 2000000),
        ]
        outliers = detect_outliers(bars, max_pct_jump=0.10)
        assert len(outliers) == 1
        assert outliers[0] == 1

    def test_outlier_detection_at_threshold(self):
        """Test behavior exactly at threshold boundary."""
        bars = [
            Bar("2024-01-01 09:00:00", 1.1000, 1.1050, 1.0980, 1.1030, 1500000),
            # Exactly at 10% jump: (1.21330 - 1.1030) / 1.1030 = 9.99% (just under 10%)
            Bar("2024-01-01 10:00:00", 1.2130, 1.2180, 1.2100, 1.21329, 2000000),
        ]
        outliers = detect_outliers(bars, max_pct_jump=0.10)
        # Should not flag (just under threshold, not exceeding)
        assert len(outliers) == 0

    def test_first_bar_cannot_be_outlier(self):
        """Test that first bar cannot be flagged as outlier."""
        bars = [
            Bar("2024-01-01 09:00:00", 1.1000, 1.1050, 1.0980, 1.1030, 1500000),
        ]
        outliers = detect_outliers(bars, max_pct_jump=0.10)
        assert len(outliers) == 0

    def test_multiple_outliers(self):
        """Test detection of multiple outlier bars."""
        bars = [
            Bar("2024-01-01 09:00:00", 1.1000, 1.1050, 1.0980, 1.1030, 1500000),
            Bar("2024-01-01 10:00:00", 1.2200, 1.2250, 1.2100, 1.2220, 2000000),  # outlier
            Bar("2024-01-01 11:00:00", 1.0500, 1.0550, 1.0450, 1.0520, 1800000),  # outlier
        ]
        outliers = detect_outliers(bars, max_pct_jump=0.10)
        assert len(outliers) == 2
        assert 1 in outliers
        assert 2 in outliers

    def test_custom_threshold(self):
        """Test outlier detection with custom percentage threshold."""
        bars = [
            Bar("2024-01-01 09:00:00", 1.1000, 1.1050, 1.0980, 1.1030, 1500000),
            # 5% jump
            Bar("2024-01-01 10:00:00", 1.1580, 1.1630, 1.1530, 1.1580, 2000000),
        ]
        # Should detect with 0.04 (4%) threshold
        outliers = detect_outliers(bars, max_pct_jump=0.04)
        assert len(outliers) == 1

        # Should not detect with 0.06 (6%) threshold
        outliers = detect_outliers(bars, max_pct_jump=0.06)
        assert len(outliers) == 0

    def test_empty_list(self):
        """Test empty list returns no outliers."""
        outliers = detect_outliers([])
        assert len(outliers) == 0

    def test_single_bar(self):
        """Test single bar returns no outliers."""
        bars = [Bar("2024-01-01 09:00:00", 1.1000, 1.1050, 1.0980, 1.1030, 1500000)]
        outliers = detect_outliers(bars)
        assert len(outliers) == 0

    def test_zero_previous_close(self):
        """Test handling of zero previous close (avoids division by zero)."""
        bars = [
            Bar("2024-01-01 09:00:00", 0.0, 0.0, 0.0, 0.0, 0),
            Bar("2024-01-01 10:00:00", 1.1030, 1.1080, 1.1020, 1.1070, 1800000),
        ]
        # Should not crash, just skip comparison for that bar
        outliers = detect_outliers(bars, max_pct_jump=0.10)
        assert isinstance(outliers, list)


class TestRemoveInvalid:
    """Test removal of invalid bars."""

    def test_remove_invalid_bars(self):
        """Test removal of bars with validation errors."""
        bars = [
            Bar("2024-01-01 09:00:00", 1.1000, 1.1050, 1.0980, 1.1030, 1500000),  # valid
            Bar("2024-01-01 10:00:00", 1.1030, 1.0980, 1.1050, 1.1070, 1800000),  # invalid (high < low)
            Bar("2024-01-01 11:00:00", 1.1070, 1.1120, 1.1050, 1.1100, 2000000),  # valid
        ]
        valid_bars, issues = remove_invalid(bars)

        assert len(valid_bars) == 2
        assert len(issues) >= 1
        assert valid_bars[0].timestamp == "2024-01-01 09:00:00"
        assert valid_bars[1].timestamp == "2024-01-01 11:00:00"

    def test_all_valid_bars(self):
        """Test when all bars are valid."""
        bars = [
            Bar("2024-01-01 09:00:00", 1.1000, 1.1050, 1.0980, 1.1030, 1500000),
            Bar("2024-01-01 10:00:00", 1.1030, 1.1080, 1.1020, 1.1070, 1800000),
        ]
        valid_bars, issues = remove_invalid(bars)

        assert len(valid_bars) == 2
        assert len(issues) == 0

    def test_all_invalid_bars(self):
        """Test when all bars are invalid."""
        bars = [
            Bar("2024-01-01 09:00:00", 1.1000, 1.1050, 1.0980, 1.1030, -1500000),
            Bar("2024-01-01 10:00:00", 1.1030, 1.0980, 1.1050, 1.1070, -1800000),
        ]
        valid_bars, issues = remove_invalid(bars)

        assert len(valid_bars) == 0
        assert len(issues) >= 2

    def test_issue_contains_correct_indices(self):
        """Test that issues reference correct original bar indices."""
        bars = [
            Bar("2024-01-01 09:00:00", 1.1000, 1.1050, 1.0980, 1.1030, 1500000),
            Bar("2024-01-01 10:00:00", 1.1030, 1.0980, 1.1050, 1.1070, 1800000),  # invalid
        ]
        valid_bars, issues = remove_invalid(bars)

        assert len(issues) >= 1
        assert issues[0].index == 1

    def test_empty_list(self):
        """Test empty list."""
        valid_bars, issues = remove_invalid([])
        assert len(valid_bars) == 0
        assert len(issues) == 0
