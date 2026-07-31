"""Tests for CSV loader.

Tests csv_loader.load_csv() with various CSV formats and error cases.
"""

import pytest
from src.data_loader.csv_loader import load_csv
from src.rule_engine.types import Bar


class TestLoadCsv:
    """Test CSV loading functionality."""

    def test_load_clean_data(self):
        """Happy path: load valid CSV with proper format."""
        bars = load_csv("tests/data_loader/fixtures/clean_data.csv")

        assert len(bars) == 5
        assert all(isinstance(b, Bar) for b in bars)

        # Check first bar
        assert bars[0].timestamp == "2024-01-01 09:00:00"
        assert bars[0].open == 1.1000
        assert bars[0].high == 1.1050
        assert bars[0].low == 1.0980
        assert bars[0].close == 1.1030
        assert bars[0].volume == 1500000
        assert bars[0].closed is True

        # Check last bar
        assert bars[-1].timestamp == "2024-01-01 13:00:00"
        assert bars[-1].close == 1.1160

    def test_load_with_uppercase_headers(self):
        """Test case-insensitive header parsing."""
        # Create temp file with uppercase headers
        import tempfile
        import os

        content = """Timestamp,Open,High,Low,Close,Volume
2024-01-01 09:00:00,1.1000,1.1050,1.0980,1.1030,1500000
2024-01-01 10:00:00,1.1030,1.1080,1.1020,1.1070,1800000
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            bars = load_csv(temp_path)
            assert len(bars) == 2
            assert bars[0].timestamp == "2024-01-01 09:00:00"
            assert bars[0].open == 1.1000
        finally:
            os.unlink(temp_path)

    def test_load_duplicate_data(self):
        """Test loading data with duplicate timestamps (should all be loaded)."""
        bars = load_csv("tests/data_loader/fixtures/duplicate_data.csv")
        assert len(bars) == 5  # Loader doesn't dedupe, just loads

    def test_load_file_not_found(self):
        """Test error handling for missing file."""
        with pytest.raises(ValueError, match="file not found"):
            load_csv("tests/data_loader/fixtures/nonexistent.csv")

    def test_missing_required_column(self):
        """Test error when required columns are missing."""
        import tempfile
        import os

        # Missing 'Volume' column
        content = """timestamp,open,high,low,close
2024-01-01 09:00:00,1.1000,1.1050,1.0980,1.1030
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="missing required columns"):
                load_csv(temp_path)
        finally:
            os.unlink(temp_path)

    def test_empty_file(self):
        """Test error for empty CSV file."""
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("")  # Empty file
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="empty or has no header"):
                load_csv(temp_path)
        finally:
            os.unlink(temp_path)

    def test_header_only_no_data(self):
        """Test error for CSV with header but no data rows."""
        import tempfile
        import os

        content = "timestamp,open,high,low,close,volume\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="no data rows"):
                load_csv(temp_path)
        finally:
            os.unlink(temp_path)

    def test_invalid_float_conversion(self):
        """Test error when OHLCV values cannot be converted to float."""
        import tempfile
        import os

        content = """timestamp,open,high,low,close,volume
2024-01-01 09:00:00,invalid,1.1050,1.0980,1.1030,1500000
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Failed to parse"):
                load_csv(temp_path)
        finally:
            os.unlink(temp_path)
