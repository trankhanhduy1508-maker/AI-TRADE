"""Tests for RULE_007_EMA (ema_filter.py)."""

import pytest
from src.rule_engine.types import Bar
from src.rule_engine import ema_filter


class TestEMAFilter:
    """Test EMA calculation and bias scoring."""

    def test_no_data(self):
        """Test with empty bars list."""
        result = ema_filter.evaluate([], "UP", period=50)
        assert result.status == "NO_DATA"
        assert result.score == 0

    def test_insufficient_data(self):
        """Test when bars < period."""
        bars = [
            Bar(timestamp=str(i), open=100, high=101, low=99, close=100, volume=1000, closed=True)
            for i in range(30)
        ]
        # 30 bars < 50 period
        result = ema_filter.evaluate(bars, "UP", period=50)
        assert result.status == "INSUFFICIENT_DATA"
        assert result.score == 0

    def test_price_above_ema_up_aligned(self):
        """Test UP direction, price > EMA (aligned)."""
        # Tạo bars với price tren EMA
        bars = []
        price = 100.0
        for i in range(55):
            # Trending up → price sẽ trên EMA
            price += 0.1
            bars.append(Bar(
                timestamp=str(i),
                open=price - 0.05,
                high=price + 0.1,
                low=price - 0.1,
                close=price,
                volume=1000,
                closed=True
            ))

        result = ema_filter.evaluate(bars, "UP", period=50)
        assert result.rule_id == "RULE_007"
        assert result.max_score == 5
        # Price > EMA + cách xa > 0.5% → ALIGNED
        assert result.status == "ALIGNED"
        assert result.score == 5.0

    def test_price_below_ema_up_against(self):
        """Test UP direction, price < EMA (against)."""
        bars = []
        price = 100.0
        for i in range(55):
            # Trending down → price sẽ dưới EMA
            price -= 0.1
            bars.append(Bar(
                timestamp=str(i),
                open=price + 0.05,
                high=price + 0.1,
                low=price - 0.1,
                close=price,
                volume=1000,
                closed=True
            ))

        result = ema_filter.evaluate(bars, "UP", period=50)
        assert result.rule_id == "RULE_007"
        # Price < EMA + cách xa > 2% → AGAINST
        assert result.status == "AGAINST"
        assert result.score == 0.0

    def test_price_near_ema_neutral(self):
        """Test price very close to EMA (neutral)."""
        bars = []
        price = 100.0
        for i in range(55):
            bars.append(Bar(
                timestamp=str(i),
                open=price,
                high=price + 0.01,  # Very tight range
                low=price - 0.01,
                close=price,
                volume=1000,
                closed=True
            ))

        result = ema_filter.evaluate(bars, "UP", period=50)
        assert result.rule_id == "RULE_007"
        # Price gần EMA (no trend) → NEUTRAL
        assert result.status == "NEUTRAL"
        assert result.score == 3.0

    def test_price_below_ema_down_aligned(self):
        """Test DOWN direction, price < EMA (aligned)."""
        bars = []
        price = 100.0
        for i in range(55):
            price -= 0.1  # Downtrend
            bars.append(Bar(
                timestamp=str(i),
                open=price + 0.05,
                high=price + 0.1,
                low=price - 0.1,
                close=price,
                volume=1000,
                closed=True
            ))

        result = ema_filter.evaluate(bars, "DOWN", period=50)
        assert result.rule_id == "RULE_007"
        # Price < EMA + cách xa > 0.5% → ALIGNED (for DOWN)
        assert result.status == "ALIGNED"
        assert result.score == 5.0

    def test_price_above_ema_down_against(self):
        """Test DOWN direction, price > EMA (against)."""
        bars = []
        price = 100.0
        for i in range(55):
            price += 0.1  # Uptrend
            bars.append(Bar(
                timestamp=str(i),
                open=price - 0.05,
                high=price + 0.1,
                low=price - 0.1,
                close=price,
                volume=1000,
                closed=True
            ))

        result = ema_filter.evaluate(bars, "DOWN", period=50)
        assert result.rule_id == "RULE_007"
        # Price > EMA + cách xa → AGAINST (for DOWN)
        assert result.status == "AGAINST"
        assert result.score == 0.0

    def test_invalid_direction(self):
        """Test with invalid direction."""
        bars = [
            Bar(timestamp=str(i), open=100, high=101, low=99, close=100, volume=1000, closed=True)
            for i in range(55)
        ]
        result = ema_filter.evaluate(bars, "INVALID", period=50)
        assert result.status == "INVALID_DIRECTION"
        assert result.score == 0

    def test_ema_zero_handling(self):
        """Test when EMA calculation gives zero (edge case)."""
        # Xây dựng bars với giá 0 (không thực tế nhưng kiểm tra defensive)
        # Bây giờ kiểm tra nếu tất cả close = 0 thì EMA = 0
        bars = [
            Bar(timestamp=str(i), open=0, high=0, low=0, close=0, volume=1000, closed=True)
            for i in range(55)
        ]
        result = ema_filter.evaluate(bars, "UP", period=50)
        assert result.status == "INVALID_EMA"
        assert result.score == 0
