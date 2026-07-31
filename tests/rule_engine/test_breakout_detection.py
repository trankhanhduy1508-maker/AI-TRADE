"""Test suite for RULE_003_BREAKOUT (breakout_detection.py)

Tests for breakout detection with body ratio validation.
"""

import pytest
from src.rule_engine.types import Bar
from src.rule_engine.breakout_detection import evaluate


class TestBreakoutDetection:
    """Test cases for breakout detection rule."""

    def test_breakout_true_up(self):
        """
        Test BREAKOUT_TRUE for UP direction with body ratio > 60%.

        Tham chiếu: RULE_003_BREAKOUT.md, mục 7 (Ví dụ BREAKOUT_TRUE)
        """
        # Swing High = 110, Swing Low = 100
        # Nến breakout: Open=109.5, High=111, Low=109, Close=110.8
        # Body ratio = (110.8 - 109.5) / (111 - 109) = 1.3 / 2 = 65% ✓

        bars = [
            Bar("2024-01-01", 100, 100, 95, 98, 1000),
            Bar("2024-01-02", 98, 101, 96, 99, 1000),
            Bar("2024-01-03", 99, 100, 97, 100, 1000),
            Bar("2024-01-04", 100, 102, 98, 100, 1000),
            Bar("2024-01-05", 100, 101, 98, 100, 1000),
            Bar("2024-01-06", 100, 101, 99, 100, 1000),
            Bar("2024-01-07", 100, 105, 100, 103, 1000),
            Bar("2024-01-08", 103, 104, 100, 102, 1000),
            Bar("2024-01-09", 102, 104, 100, 103, 1000),
            Bar("2024-01-10", 109.5, 111, 109, 110.8, 1000),  # Breakout bar
        ]

        result = evaluate(bars, structure_level=110, direction="UP", body_ratio_min=0.6)

        assert result.rule_id == "RULE_003"
        assert result.status == "BREAKOUT"
        assert result.score == 15
        assert result.max_score == 15
        assert result.reject is False
        assert result.detail["type"] == "true"

    def test_breakout_true_down(self):
        """Test BREAKOUT_TRUE for DOWN direction."""
        # Swing Low = 90, Swing High = 100
        # Nến breakout: Open=91, High=92, Low=89, Close=89.5
        # Body ratio = (91 - 89.5) / (92 - 89) = 1.5 / 3 = 50%

        bars = [
            Bar("2024-01-01", 100, 110, 95, 100, 1000),
            Bar("2024-01-02", 100, 109, 94, 100, 1000),
            Bar("2024-01-03", 100, 109, 94, 100, 1000),
            Bar("2024-01-04", 100, 108, 90, 100, 1000),
            Bar("2024-01-05", 100, 107, 91, 100, 1000),
            Bar("2024-01-06", 100, 107, 90, 100, 1000),
            Bar("2024-01-07", 100, 106, 85, 100, 1000),
            Bar("2024-01-08", 100, 105, 86, 100, 1000),
            Bar("2024-01-09", 100, 105, 86, 100, 1000),
            Bar("2024-01-10", 91, 92, 89, 89.5, 1000),  # Breakout bar (body 50%)
        ]

        result = evaluate(bars, structure_level=90, direction="DOWN", body_ratio_min=0.4)

        assert result.rule_id == "RULE_003"
        assert result.status == "BREAKOUT"
        assert result.score == 15
        assert result.reject is False

    def test_breakout_weak(self):
        """
        Test BREAKOUT_WEAK with body ratio between 40-60%.

        Tham chiếu: RULE_003_BREAKOUT.md, mục 7 (Ví dụ BREAKOUT_WEAK)
        """
        # Nến breakout: Close > 110 nhưng body ratio giữa 40-60%
        bars = [
            Bar("2024-01-01", 100, 100, 95, 98, 1000),
            Bar("2024-01-02", 98, 101, 96, 99, 1000),
            Bar("2024-01-03", 99, 100, 97, 100, 1000),
            Bar("2024-01-04", 100, 102, 98, 100, 1000),
            Bar("2024-01-05", 100, 101, 98, 100, 1000),
            Bar("2024-01-06", 100, 101, 99, 100, 1000),
            Bar("2024-01-07", 100, 105, 100, 103, 1000),
            Bar("2024-01-08", 103, 104, 100, 102, 1000),
            Bar("2024-01-09", 102, 104, 100, 103, 1000),
            Bar("2024-01-10", 109.5, 112, 109, 110.7, 1000),  # Weak breakout, body 52%
        ]

        result = evaluate(bars, structure_level=110, direction="UP", body_ratio_min=0.6)

        assert result.rule_id == "RULE_003"
        assert result.status == "WEAK"
        assert result.score in [5, 10]  # Body ratio between 40-60% can be 10
        assert result.reject is False

    def test_no_breakout_yet(self):
        """Test when price hasn't reached the structure level yet."""
        bars = [
            Bar("2024-01-01", 100, 100, 95, 98, 1000),
            Bar("2024-01-02", 98, 101, 96, 99, 1000),
            Bar("2024-01-03", 99, 100, 97, 100, 1000),
            Bar("2024-01-04", 100, 102, 98, 100, 1000),
            Bar("2024-01-05", 100, 101, 98, 100, 1000),
            Bar("2024-01-06", 100, 101, 99, 100, 1000),
            Bar("2024-01-07", 100, 105, 100, 103, 1000),
            Bar("2024-01-08", 103, 104, 100, 102, 1000),
            Bar("2024-01-09", 102, 104, 100, 103, 1000),
            Bar("2024-01-10", 109, 109.5, 108, 109.3, 1000),  # Close < 110
        ]

        result = evaluate(bars, structure_level=110, direction="UP", body_ratio_min=0.6)

        assert result.rule_id == "RULE_003"
        assert result.status == "WAIT"
        assert result.score == 0
        assert result.reject is False
        assert result.detail["type"] == "no_breakout"

    def test_doji_bar(self):
        """Test with a doji bar (open == close)."""
        bars = [
            Bar("2024-01-01", 100, 100, 95, 98, 1000),
            Bar("2024-01-02", 98, 101, 96, 99, 1000),
            Bar("2024-01-03", 99, 100, 97, 100, 1000),
            Bar("2024-01-04", 100, 102, 98, 100, 1000),
            Bar("2024-01-05", 100, 101, 98, 100, 1000),
            Bar("2024-01-06", 100, 101, 99, 100, 1000),
            Bar("2024-01-07", 100, 105, 100, 103, 1000),
            Bar("2024-01-08", 103, 104, 100, 102, 1000),
            Bar("2024-01-09", 102, 104, 100, 103, 1000),
            Bar("2024-01-10", 110.5, 111, 109, 110.5, 1000),  # Doji-like (close == open)
        ]

        result = evaluate(bars, structure_level=110, direction="UP", body_ratio_min=0.6)

        # Close > 110 so technically it breaks, but body ratio very low
        assert result.rule_id == "RULE_003"
        assert result.status in ["WEAK", "WAIT"]  # Could be very weak
        if result.status == "WEAK":
            assert result.score in [5, 10]

    def test_invalid_direction(self):
        """Test with invalid direction parameter."""
        bars = [
            Bar("2024-01-01", 100, 100, 95, 98, 1000),
            Bar("2024-01-02", 98, 101, 96, 99, 1000),
        ]

        result = evaluate(bars, structure_level=110, direction="INVALID", body_ratio_min=0.6)

        assert result.rule_id == "RULE_003"
        assert result.status == "WAIT"
        assert result.reject is False

    def test_empty_bars(self):
        """Test with empty bars list."""
        bars = []

        result = evaluate(bars, structure_level=110, direction="UP", body_ratio_min=0.6)

        assert result.rule_id == "RULE_003"
        assert result.status == "WAIT"
        assert result.reject is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
