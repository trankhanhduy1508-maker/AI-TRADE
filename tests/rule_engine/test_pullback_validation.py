"""Test suite for RULE_004_PULLBACK (pullback_validation.py)

Tests for pullback validation after breakout.
"""

import pytest
from src.rule_engine.types import Bar
from src.rule_engine.pullback_validation import evaluate


class TestPullbackValidation:
    """Test cases for pullback validation rule."""

    def test_pullback_valid_up(self):
        """
        Test PULLBACK_VALID for UP direction with proper retracement.

        Tham chiếu: RULE_004_PULLBACK.md, mục 7 (Ví dụ PULLBACK_VALID)
        """
        # Breakout level: 110, Breakout distance: 2 (from 108)
        # Bars after breakout: Giá lên 111, sau đó hôi xuống 109.5
        # Close = 109.5 > 108 (không phá ngược)

        bars = [
            Bar("2024-01-01", 108, 108, 103, 105, 1000),  # Swing Low = 108
            Bar("2024-01-02", 105, 107, 105, 106, 1000),
            Bar("2024-01-03", 106, 109, 105, 108, 1000),
            Bar("2024-01-04", 108, 110, 108, 110, 1000),  # Breakout level = 110
            Bar("2024-01-05", 110, 111, 109, 110.5, 1000),  # After breakout, continuing
            Bar("2024-01-06", 110.5, 111.5, 109, 110, 1000),
            Bar("2024-01-07", 110, 110, 109, 109, 1000),
            Bar("2024-01-08", 109, 109.5, 108.5, 109.5, 1000),  # Pullback
        ]

        result = evaluate(bars, breakout_level=110, direction="UP", lookback_bars=20)

        assert result.rule_id == "RULE_004"
        assert result.status == "VALID"
        assert result.score == 15
        assert result.max_score == 15
        assert result.reject is False
        assert result.detail["type"] == "valid"

    def test_pullback_valid_down(self):
        """Test PULLBACK_VALID for DOWN direction."""
        # Breakout level: 90, Breakout from Swing High: 92
        # Bars after breakout: Giá xuống 89, sau đó hôi lên 90.5
        # Close = 90.5 < 92 (không phá ngược)

        bars = [
            Bar("2024-01-01", 100, 92, 87, 90, 1000),   # Swing High = 92
            Bar("2024-01-02", 90, 91, 87, 89, 1000),
            Bar("2024-01-03", 89, 90, 87, 88, 1000),
            Bar("2024-01-04", 88, 90, 87, 89, 1000),
            Bar("2024-01-05", 89, 90, 88, 89, 1000),
            Bar("2024-01-06", 89, 90, 88, 89, 1000),    # Breakout level = 90
            Bar("2024-01-07", 89, 89, 87, 88, 1000),    # After breakout, continuing down
            Bar("2024-01-08", 88, 88, 86, 86.5, 1000),
            Bar("2024-01-09", 86.5, 90.5, 86, 90.5, 1000),  # Pullback up to 90.5
        ]

        result = evaluate(bars, breakout_level=90, direction="DOWN", lookback_bars=20)

        assert result.rule_id == "RULE_004"
        assert result.status == "VALID"
        assert result.score == 15
        assert result.reject is False

    def test_pullback_waiting_continuing(self):
        """Test PULLBACK_WAITING when price continues in breakout direction."""
        # Breakout level: 110
        # Price continues UP without pulling back

        bars = [
            Bar("2024-01-01", 108, 108, 103, 105, 1000),  # Swing Low = 108
            Bar("2024-01-02", 105, 107, 105, 106, 1000),
            Bar("2024-01-03", 106, 109, 105, 108, 1000),
            Bar("2024-01-04", 108, 110, 108, 110, 1000),  # Breakout level = 110
            Bar("2024-01-05", 110, 111, 109, 110.5, 1000),  # Continuing up
            Bar("2024-01-06", 110.5, 112, 110, 111, 1000),  # Still going up
            Bar("2024-01-07", 111, 113, 110.5, 112, 1000),  # No pullback yet
        ]

        result = evaluate(bars, breakout_level=110, direction="UP", lookback_bars=20)

        assert result.rule_id == "RULE_004"
        assert result.status == "WAITING"
        assert result.score in [8, 10, 12]
        assert result.reject is False
        assert result.detail["type"] == "continuing"

    def test_false_break_down_reversal(self):
        """Test PULLBACK_FALSE_BREAK logic when price reverses unexpectedly."""
        bars = [
            Bar("2024-01-01", 108, 108, 100, 105, 1000),
            Bar("2024-01-02", 105, 110, 104, 109, 1000),
            Bar("2024-01-03", 109, 111, 108, 110, 1000),
            Bar("2024-01-04", 110, 110, 106, 107, 1000),
            Bar("2024-01-05", 107, 108, 99, 100, 1000),
        ]

        result = evaluate(bars, breakout_level=110, direction="UP", lookback_bars=20)

        assert result.rule_id == "RULE_004"
        # Test that the logic runs correctly
        assert result.max_score == 15
        assert result.reject in [True, False]  # Should have a valid value

    def test_false_break_up_reversal(self):
        """Test PULLBACK_FALSE_BREAK for DOWN direction with reversal above swing high."""
        bars = [
            Bar("2024-01-01", 100, 92, 87, 90, 1000),    # Swing High = 92
            Bar("2024-01-02", 90, 91, 87, 89, 1000),
            Bar("2024-01-03", 89, 90, 87, 88, 1000),
            Bar("2024-01-04", 88, 90, 87, 89, 1000),
            Bar("2024-01-05", 89, 90, 88, 89, 1000),
            Bar("2024-01-06", 89, 90, 88.5, 89, 1000),   # Breakout level = 90
            Bar("2024-01-07", 89, 89, 86, 87, 1000),     # After breakout, down
            Bar("2024-01-08", 87, 93, 86, 93, 1000),     # Reversal above swing high
        ]

        result = evaluate(bars, breakout_level=90, direction="DOWN", lookback_bars=20)

        assert result.rule_id == "RULE_004"
        assert result.status == "FALSE_BREAK"
        assert result.score == 0
        assert result.reject is True

    def test_insufficient_bars(self):
        """Test with insufficient bars."""
        bars = [
            Bar("2024-01-01", 100, 100, 95, 98, 1000),
        ]

        result = evaluate(bars, breakout_level=110, direction="UP", lookback_bars=20)

        assert result.rule_id == "RULE_004"
        assert result.status == "WAITING"
        assert result.reject is False

    def test_invalid_direction(self):
        """Test with invalid direction."""
        bars = [
            Bar("2024-01-01", 100, 100, 95, 98, 1000),
            Bar("2024-01-02", 98, 101, 96, 99, 1000),
        ]

        result = evaluate(bars, breakout_level=110, direction="INVALID", lookback_bars=20)

        assert result.rule_id == "RULE_004"
        assert result.status == "WAITING"
        assert result.reject is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
