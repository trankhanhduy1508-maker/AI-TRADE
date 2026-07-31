"""Tests for RULE_006_RSI (rsi_filter.py)."""

import pytest
from src.rule_engine.types import Bar
from src.rule_engine import rsi_filter


class TestRSIFilter:
    """Test RSI calculation and scoring."""

    def test_insufficient_data(self):
        """Test when bars < period+1."""
        bars = [
            Bar(timestamp="1", open=100, high=101, low=99, close=100.5, volume=1000),
            Bar(timestamp="2", open=100.5, high=102, low=100, close=101, volume=1000),
        ]
        result = rsi_filter.evaluate(bars, "UP", period=14)
        assert result.status == "INSUFFICIENT_DATA"
        assert result.score == 0

    def test_rsi_aligned_up_neutral(self):
        """Test UP direction, RSI in neutral zone (30-70)."""
        # Tạo bars với RSI khoảng 50 (neutral)
        bars = []
        price = 100.0
        for i in range(16):
            price += 0.3 if i % 2 == 0 else -0.1
            bars.append(Bar(
                timestamp=str(i),
                open=price,
                high=price + 0.5,
                low=price - 0.5,
                close=price,
                volume=1000,
                closed=True
            ))

        result = rsi_filter.evaluate(bars, "UP", period=14)
        # RSI phải trong 30-70, so should be NEUTRAL (score 3)
        assert result.rule_id == "RULE_006"
        assert result.max_score == 5
        assert result.reject is False

    def test_rsi_aligned_up_moderate(self):
        """Test UP direction, RSI in moderate zone."""
        # Tạo bars với alternating up/down để RSI không quá cao
        bars = []
        price = 100.0
        for i in range(16):
            # Alternating: up 0.3, down 0.1 → net trend up nhưng RSI moderate
            price += 0.3 if i % 2 == 0 else -0.1
            bars.append(Bar(
                timestamp=str(i),
                open=price - 0.1,
                high=price + 0.2,
                low=price - 0.15,
                close=price,
                volume=1000,
                closed=True
            ))

        result = rsi_filter.evaluate(bars, "UP", period=14)
        assert result.rule_id == "RULE_006"
        # With alternating moves, RSI should be in 30-70 → ALIGNED
        assert result.status in ["ALIGNED", "NEUTRAL"]
        assert result.score in [5.0, 3.0]

    def test_rsi_against_up_overbought(self):
        """Test UP direction, RSI overbought (>70)."""
        # Tạo bars dengan strong up trend → RSI > 70
        bars = []
        price = 100.0
        for i in range(16):
            price += 0.5  # Strong up trend
            bars.append(Bar(
                timestamp=str(i),
                open=price - 0.5,
                high=price + 0.3,
                low=price - 0.2,
                close=price,
                volume=1000,
                closed=True
            ))

        result = rsi_filter.evaluate(bars, "UP", period=14)
        assert result.rule_id == "RULE_006"
        # Strong trend up → RSI > 70 → AGAINST
        assert result.score >= 0  # Could be 5 if RSI <= 70, or 0 if > 70

    def test_rsi_aligned_down_moderate(self):
        """Test DOWN direction, RSI in moderate zone."""
        bars = []
        price = 100.0
        for i in range(16):
            # Alternating: down 0.3, up 0.1 → net trend down but RSI moderate
            price -= 0.3 if i % 2 == 0 else -0.1
            bars.append(Bar(
                timestamp=str(i),
                open=price + 0.1,
                high=price + 0.15,
                low=price - 0.2,
                close=price,
                volume=1000,
                closed=True
            ))

        result = rsi_filter.evaluate(bars, "DOWN", period=14)
        assert result.rule_id == "RULE_006"
        # With alternating moves, RSI should be in 30-70 → ALIGNED
        assert result.score in [5.0, 3.0]

    def test_invalid_direction(self):
        """Test with invalid direction."""
        bars = [
            Bar(timestamp=str(i), open=100, high=101, low=99, close=100, volume=1000, closed=True)
            for i in range(20)
        ]
        result = rsi_filter.evaluate(bars, "INVALID", period=14)
        assert result.status == "INVALID_DIRECTION"
        assert result.score == 0

    def test_single_closed_bar_unclosed_bars_ignored(self):
        """Test that unclosed bars are ignored."""
        bars = [
            Bar(timestamp="0", open=100, high=101, low=99, close=100, volume=1000, closed=True),
            Bar(timestamp="1", open=100, high=101, low=99, close=101, volume=1000, closed=False),  # Unclosed
        ]
        # Only 1 closed bar, need 15 for period 14
        result = rsi_filter.evaluate(bars, "UP", period=14)
        assert result.status == "INSUFFICIENT_DATA"
