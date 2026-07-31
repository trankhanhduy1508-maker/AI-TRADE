"""Tests for RULE_009_LIQUIDITY (liquidity_check.py)."""

import pytest
from src.rule_engine import liquidity_check


class TestLiquidityCheck:
    """Test liquidity evaluation based on spread and depth."""

    def test_liquidity_good(self):
        """Test good liquidity (spread < 2 pip, depth ok)."""
        result = liquidity_check.evaluate(spread_pips=1.0, depth_ok=True)
        assert result.rule_id == "RULE_009"
        assert result.status == "GOOD"
        assert result.score == 5.0
        assert result.reject is False

    def test_liquidity_good_boundary_low(self):
        """Test liquidity at boundary (spread exactly 2 pip)."""
        result = liquidity_check.evaluate(spread_pips=2.0, depth_ok=True)
        # >= 2 is in FAIR range
        assert result.status == "FAIR"
        assert result.score == 3.0

    def test_liquidity_good_tight_spread(self):
        """Test very tight spread."""
        result = liquidity_check.evaluate(spread_pips=0.5, depth_ok=True)
        assert result.status == "GOOD"
        assert result.score == 5.0

    def test_liquidity_fair(self):
        """Test fair liquidity (spread 2-5 pip, depth ok)."""
        result = liquidity_check.evaluate(spread_pips=3.0, depth_ok=True)
        assert result.rule_id == "RULE_009"
        assert result.status == "FAIR"
        assert result.score == 3.0
        assert result.reject is False

    def test_liquidity_fair_boundary_high(self):
        """Test liquidity at boundary (spread exactly 5 pip)."""
        result = liquidity_check.evaluate(spread_pips=5.0, depth_ok=True)
        # >= 5 and <= 5, so FAIR
        assert result.status == "FAIR"
        assert result.score == 3.0

    def test_liquidity_poor_wide_spread(self):
        """Test poor liquidity (spread > 5 pip)."""
        result = liquidity_check.evaluate(spread_pips=6.0, depth_ok=True)
        assert result.rule_id == "RULE_009"
        assert result.status == "POOR"
        assert result.score == 0.0
        assert result.reject is False  # Liquidity không reject cứng

    def test_liquidity_poor_depth_not_ok(self):
        """Test poor liquidity (depth not ok)."""
        result = liquidity_check.evaluate(spread_pips=2.0, depth_ok=False)
        assert result.status == "POOR"
        assert result.score == 0.0
        assert result.reject is False

    def test_liquidity_poor_both_conditions(self):
        """Test poor liquidity (both spread wide and depth bad)."""
        result = liquidity_check.evaluate(spread_pips=10.0, depth_ok=False)
        assert result.status == "POOR"
        assert result.score == 0.0
        assert result.reject is False

    def test_liquidity_very_wide_spread(self):
        """Test extremely wide spread."""
        result = liquidity_check.evaluate(spread_pips=50.0, depth_ok=True)
        assert result.status == "POOR"
        assert result.score == 0.0

    def test_liquidity_detail_output(self):
        """Test that detail dict contains spread and depth info."""
        result = liquidity_check.evaluate(spread_pips=1.5, depth_ok=True)
        assert "spread_pips" in result.detail
        assert "depth_ok" in result.detail
        assert result.detail["spread_pips"] == 1.5
        assert result.detail["depth_ok"] is True
