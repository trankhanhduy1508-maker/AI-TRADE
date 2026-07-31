"""Test suite for RULE_005_VOLUME (volume_confirmation.py)

Tests for volume confirmation based on SMA comparison.
"""

import pytest
from src.rule_engine.types import Bar
from src.rule_engine.volume_confirmation import evaluate


class TestVolumeConfirmation:
    """Test cases for volume confirmation rule."""

    def test_volume_strong(self):
        """
        Test VOLUME_STRONG when current volume > 150% SMA20.

        Tham chiếu: RULE_005_VOLUME.md, mục 7 (Ví dụ VOLUME_STRONG)
        """
        # SMA20 volume = 1M
        # Nến breakout volume = 1.8M (180% SMA20)

        bars = [
            Bar("2024-01-01", 100, 100, 95, 98, 1000000),
            Bar("2024-01-02", 98, 101, 96, 99, 1000000),
            Bar("2024-01-03", 99, 100, 97, 100, 1000000),
            Bar("2024-01-04", 100, 102, 98, 100, 1000000),
            Bar("2024-01-05", 100, 101, 98, 100, 1000000),
            Bar("2024-01-06", 100, 101, 99, 100, 1000000),
            Bar("2024-01-07", 100, 105, 100, 103, 1000000),
            Bar("2024-01-08", 103, 104, 100, 102, 1000000),
            Bar("2024-01-09", 102, 104, 100, 103, 1000000),
            Bar("2024-01-10", 103, 105, 100, 104, 1000000),
            Bar("2024-01-11", 104, 106, 103, 105, 1000000),
            Bar("2024-01-12", 105, 107, 104, 106, 1000000),
            Bar("2024-01-13", 106, 108, 105, 107, 1000000),
            Bar("2024-01-14", 107, 109, 106, 108, 1000000),
            Bar("2024-01-15", 108, 110, 107, 109, 1000000),
            Bar("2024-01-16", 109, 111, 108, 110, 1000000),
            Bar("2024-01-17", 110, 112, 109, 111, 1000000),
            Bar("2024-01-18", 111, 113, 110, 112, 1000000),
            Bar("2024-01-19", 112, 114, 111, 113, 1000000),
            Bar("2024-01-20", 113, 115, 112, 114, 1000000),
            Bar("2024-01-21", 114, 116, 113, 115, 1000000),  # SMA20 = 1000000
            Bar("2024-01-22", 115, 117, 114, 116, 1800000),  # Volume = 1.8M (180%)
        ]

        result = evaluate(bars, sma_period=20)

        assert result.rule_id == "RULE_005"
        assert result.status == "STRONG"
        assert result.score == 10
        assert result.max_score == 10
        assert result.reject is False
        assert result.detail["volume_ratio"] >= 1.5

    def test_volume_normal(self):
        """Test VOLUME_NORMAL when volume is 100-150% SMA20."""
        bars = [
            Bar(f"2024-01-{i:02d}", 100, 100, 95, 98, 1000000)
            for i in range(1, 21)
        ]
        # Add one more bar with volume at 125% SMA
        bars.append(Bar("2024-01-21", 100, 100, 95, 98, 1250000))

        result = evaluate(bars, sma_period=20)

        assert result.rule_id == "RULE_005"
        assert result.status == "NORMAL"
        assert result.score == 7
        assert result.reject is False
        assert 1.0 <= result.detail["volume_ratio"] < 1.5

    def test_volume_weak(self):
        """Test VOLUME_WEAK when volume is 80-100% SMA20."""
        bars = [
            Bar(f"2024-01-{i:02d}", 100, 100, 95, 98, 1000000)
            for i in range(1, 21)
        ]
        # Add one more bar with volume at 90% SMA
        bars.append(Bar("2024-01-21", 100, 100, 95, 98, 900000))

        result = evaluate(bars, sma_period=20)

        assert result.rule_id == "RULE_005"
        assert result.status == "WEAK"
        assert result.score == 5
        assert result.reject is False
        assert 0.8 <= result.detail["volume_ratio"] < 1.0

    def test_volume_poor(self):
        """
        Test VOLUME_POOR when volume < 80% SMA20.

        Tham chiếu: RULE_005_VOLUME.md, mục 7 (Ví dụ VOLUME_POOR)
        """
        # SMA20 volume = 1M
        # Nến breakout volume = 0.7M (70% SMA20)

        bars = [
            Bar(f"2024-01-{i:02d}", 100, 100, 95, 98, 1000000)
            for i in range(1, 21)
        ]
        # Add one more bar with volume at 70% SMA
        bars.append(Bar("2024-01-21", 100, 100, 95, 98, 700000))

        result = evaluate(bars, sma_period=20)

        assert result.rule_id == "RULE_005"
        assert result.status == "WEAK"
        assert result.score == 0
        assert result.reject is False
        assert result.detail["volume_ratio"] < 0.8

    def test_insufficient_bars_for_sma(self):
        """Test with insufficient bars to calculate SMA."""
        bars = [
            Bar(f"2024-01-{i:02d}", 100, 100, 95, 98, 1000000)
            for i in range(1, 10)
        ]

        result = evaluate(bars, sma_period=20)

        assert result.rule_id == "RULE_005"
        assert result.status == "WEAK"
        assert result.score == 0
        assert result.reject is False
        assert "Insufficient" in result.detail.get("reason", "")

    def test_empty_bars(self):
        """Test with empty bars list."""
        bars = []

        result = evaluate(bars, sma_period=20)

        assert result.rule_id == "RULE_005"
        assert result.status == "WEAK"
        assert result.score == 0
        assert result.reject is False

    def test_volume_ratio_calculation(self):
        """Test that volume ratio is calculated correctly."""
        # Create bars with known SMA
        bars = [
            Bar(f"2024-01-{i:02d}", 100, 100, 95, 98, 1000)
            for i in range(1, 21)
        ]
        # Add bar with 1600 volume (160% of 1000, > 150%)
        bars.append(Bar("2024-01-21", 100, 100, 95, 98, 1600))

        result = evaluate(bars, sma_period=20)

        assert result.status == "STRONG"  # 160% is > 150%, should be STRONG
        assert result.score == 10
        assert abs(result.detail["volume_ratio"] - 1.6) < 0.01

    def test_custom_sma_period(self):
        """Test with custom SMA period."""
        bars = [
            Bar(f"2024-01-{i:02d}", 100, 100, 95, 98, 1000000)
            for i in range(1, 11)
        ]
        # Add bar with high volume
        bars.append(Bar("2024-01-11", 100, 100, 95, 98, 1800000))

        result = evaluate(bars, sma_period=10)

        assert result.rule_id == "RULE_005"
        assert result.status == "STRONG"
        assert result.score == 10
        assert result.detail["sma_period"] == 10

    def test_zero_sma_volume(self):
        """Test when SMA volume is zero (edge case)."""
        bars = [
            Bar(f"2024-01-{i:02d}", 100, 100, 95, 98, 0)
            for i in range(1, 21)
        ]
        bars.append(Bar("2024-01-21", 100, 100, 95, 98, 1000))

        result = evaluate(bars, sma_period=20)

        assert result.rule_id == "RULE_005"
        assert result.status == "WEAK"
        assert result.score == 0
        assert result.reject is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
