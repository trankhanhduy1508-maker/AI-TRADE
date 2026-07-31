"""Tests for end-to-end data loading pipeline.

Tests load_and_clean() function with various scenarios.
"""

import pytest
from src.data_loader.pipeline import load_and_clean
from src.rule_engine.types import Bar


class TestLoadAndClean:
    """Test complete load_and_clean pipeline."""

    def test_clean_data_pipeline(self):
        """Test happy path with clean data."""
        result = load_and_clean("tests/data_loader/fixtures/clean_data.csv")

        assert "bars" in result
        assert "n_duplicates_removed" in result
        assert "invalid_removed" in result
        assert "outlier_indices" in result

        assert len(result["bars"]) == 5
        assert result["n_duplicates_removed"] == 0
        assert len(result["invalid_removed"]) == 0
        assert len(result["outlier_indices"]) == 0

    def test_duplicate_data_pipeline(self):
        """Test pipeline with duplicate timestamps."""
        result = load_and_clean("tests/data_loader/fixtures/duplicate_data.csv")

        assert result["n_duplicates_removed"] == 2
        assert len(result["bars"]) == 3  # 5 input, 2 dupes removed

    def test_invalid_data_pipeline(self):
        """Test pipeline with invalid bars."""
        result = load_and_clean("tests/data_loader/fixtures/invalid_data.csv")

        # Should detect invalid bars
        assert len(result["invalid_removed"]) >= 1
        # Valid bars count should be less than input
        assert len(result["bars"]) < 4

    def test_outlier_data_pipeline(self):
        """Test pipeline with outlier bars."""
        result = load_and_clean("tests/data_loader/fixtures/outlier_data.csv")

        # Should detect outliers in final bars list
        # Input has bars 2 and 3 with normal close values
        # But bar 3 (index 2 in final list) has ~10.76% jump from bar 2
        # Outliers are detected after sort/dedupe/remove_invalid

        assert len(result["bars"]) >= 2
        # Should flag at least the 11:00 bar as outlier (10.76% jump)
        assert len(result["outlier_indices"]) >= 1

    def test_output_dict_structure(self):
        """Test that output dict has correct structure and types."""
        result = load_and_clean("tests/data_loader/fixtures/clean_data.csv")

        assert isinstance(result, dict)
        assert isinstance(result["bars"], list)
        assert isinstance(result["n_duplicates_removed"], int)
        assert isinstance(result["invalid_removed"], list)
        assert isinstance(result["outlier_indices"], list)

        # All bars should be Bar instances
        assert all(isinstance(b, result["bars"][0].__class__) for b in result["bars"])

    def test_custom_outlier_threshold(self):
        """Test pipeline with custom outlier detection threshold."""
        # Default threshold (10%)
        result_default = load_and_clean(
            "tests/data_loader/fixtures/outlier_data.csv",
            max_pct_jump=0.10
        )

        # Stricter threshold (5%)
        result_strict = load_and_clean(
            "tests/data_loader/fixtures/outlier_data.csv",
            max_pct_jump=0.05
        )

        # Stricter threshold should detect more outliers or equal
        assert len(result_strict["outlier_indices"]) >= len(result_default["outlier_indices"])

    def test_file_not_found(self):
        """Test error handling for missing file."""
        with pytest.raises(ValueError):
            load_and_clean("tests/data_loader/fixtures/nonexistent.csv")

    def test_sorted_output_by_timestamp(self):
        """Test that output bars are sorted by timestamp."""
        result = load_and_clean("tests/data_loader/fixtures/clean_data.csv")
        bars = result["bars"]

        # Check timestamp ordering
        for i in range(len(bars) - 1):
            assert bars[i].timestamp <= bars[i + 1].timestamp

    def test_no_duplicate_timestamps_in_output(self):
        """Test that output has no duplicate timestamps."""
        result = load_and_clean("tests/data_loader/fixtures/duplicate_data.csv")
        bars = result["bars"]

        timestamps = [b.timestamp for b in bars]
        assert len(timestamps) == len(set(timestamps))  # No duplicates

    def test_all_output_bars_are_closed(self):
        """Test that all output bars are marked as closed."""
        result = load_and_clean("tests/data_loader/fixtures/clean_data.csv")

        assert all(b.closed for b in result["bars"])

    def test_outlier_indices_refer_to_final_bars(self):
        """Test that outlier indices reference final bars list, not original."""
        result = load_and_clean("tests/data_loader/fixtures/outlier_data.csv")

        # All outlier indices should be within bounds of final bars list
        for idx in result["outlier_indices"]:
            assert 0 <= idx < len(result["bars"])
