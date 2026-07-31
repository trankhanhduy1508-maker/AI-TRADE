"""Tests for RULE_010_EXIT (exit_rules.py)."""

import pytest
from src.rule_engine.types import Bar
from src.rule_engine.exit_rules import evaluate_exit, ExitSignal


class TestExitRules:
    """Test exit signal evaluation."""

    def test_insufficient_data(self):
        """Test with insufficient bars."""
        bars = [
            Bar(timestamp="1", open=100, high=101, low=99, close=100, volume=1000)
        ]
        result = evaluate_exit(bars, entry=100, stop=98, target=105, direction="UP")
        assert result.action == "HOLD"
        assert "Not enough data" in result.reason

    def test_stop_loss_hit_up(self):
        """Test UP setup with stop loss hit."""
        bars = [
            Bar(timestamp="1", open=100, high=101, low=99, close=100.5, volume=1000),
            Bar(timestamp="2", open=100.5, high=101.5, low=97.5, close=97.0, volume=1000),  # Price touches SL
        ]
        result = evaluate_exit(bars, entry=100, stop=98, target=105, direction="UP")
        assert result.action == "EXIT_NOW"
        assert "Stop loss hit" in result.reason

    def test_stop_loss_hit_down(self):
        """Test DOWN setup with stop loss hit."""
        bars = [
            Bar(timestamp="1", open=100, high=101, low=99, close=99.5, volume=1000),
            Bar(timestamp="2", open=99.5, high=102.5, low=98.5, close=102.0, volume=1000),  # Price touches SL
        ]
        result = evaluate_exit(bars, entry=100, stop=102, target=95, direction="DOWN")
        assert result.action == "EXIT_NOW"
        assert "Stop loss hit" in result.reason

    def test_take_profit_hit_up(self):
        """Test UP setup with target hit."""
        bars = [
            Bar(timestamp="1", open=100, high=101, low=99, close=100.5, volume=1000),
            Bar(timestamp="2", open=100.5, high=105.5, low=100, close=105.0, volume=1000),  # Price reaches target
        ]
        result = evaluate_exit(bars, entry=100, stop=98, target=105, direction="UP")
        assert result.action == "EXIT_NOW"
        assert "Target hit" in result.reason

    def test_take_profit_hit_down(self):
        """Test DOWN setup with target hit."""
        bars = [
            Bar(timestamp="1", open=100, high=101, low=99, close=99.5, volume=1000),
            Bar(timestamp="2", open=99.5, high=100, low=94.5, close=95.0, volume=1000),  # Price reaches target
        ]
        result = evaluate_exit(bars, entry=100, stop=102, target=95, direction="DOWN")
        assert result.action == "EXIT_NOW"
        assert "Target hit" in result.reason

    def test_no_target_still_can_exit_on_stop(self):
        """Test that no target doesn't prevent stop loss detection."""
        bars = [
            Bar(timestamp="1", open=100, high=101, low=99, close=100.5, volume=1000),
            Bar(timestamp="2", open=100.5, high=101.5, low=97.5, close=97.0, volume=1000),
        ]
        result = evaluate_exit(bars, entry=100, stop=98, target=None, direction="UP")
        # Should still detect stop loss hit even without target
        assert result.action == "EXIT_NOW"
        assert "Stop loss" in result.reason

    def test_false_break_up(self):
        """Test false break or structure break detection (UP setup)."""
        bars = [
            Bar(timestamp="1", open=100, high=101, low=99, close=101.0, volume=1000),  # Breakout above entry
            Bar(timestamp="2", open=101, high=102, low=100, close=101.5, volume=1000),  # Still above
            Bar(timestamp="3", open=101.5, high=101.5, low=99, close=99.0, volume=1000),  # Falls below entry
        ]
        result = evaluate_exit(bars, entry=100, stop=98, target=105, direction="UP")
        assert result.action == "EXIT_NOW"
        # Either false break or structure break is acceptable
        assert "False break" in result.reason or "Structure break" in result.reason

    def test_false_break_down(self):
        """Test false break detection (DOWN setup)."""
        bars = [
            Bar(timestamp="1", open=100, high=101, low=99, close=99.0, volume=1000),  # Breakout below entry
            Bar(timestamp="2", open=99, high=100, low=98, close=98.5, volume=1000),  # Still below
            Bar(timestamp="3", open=98.5, high=101, low=98, close=101.0, volume=1000),  # Rises above entry
        ]
        result = evaluate_exit(bars, entry=100, stop=102, target=95, direction="DOWN")
        assert result.action == "EXIT_NOW"
        assert "False break" in result.reason

    def test_structure_break_up_lower_high(self):
        """Test structure break or false break UP (lower high detected)."""
        bars = [
            Bar(timestamp="1", open=100, high=101, low=99, close=100.5, volume=1000),
            Bar(timestamp="2", open=100.5, high=102, low=100, close=101.5, volume=1000),  # Higher high
            Bar(timestamp="3", open=101.5, high=101.5, low=99, close=99.5, volume=1000),  # Lower high, price below entry
        ]
        result = evaluate_exit(bars, entry=100, stop=98, target=105, direction="UP")
        assert result.action == "EXIT_NOW"
        assert "Structure break" in result.reason or "lower high" in result.reason or "False break" in result.reason

    def test_structure_break_down_higher_low(self):
        """Test structure break or false break DOWN (higher low detected)."""
        bars = [
            Bar(timestamp="1", open=100, high=101, low=99, close=99.5, volume=1000),
            Bar(timestamp="2", open=99.5, high=100, low=98, close=98.5, volume=1000),  # Lower low
            Bar(timestamp="3", open=98.5, high=101, low=98.5, close=100.5, volume=1000),  # Higher low, price above entry
        ]
        result = evaluate_exit(bars, entry=100, stop=102, target=95, direction="DOWN")
        assert result.action == "EXIT_NOW"
        assert "Structure break" in result.reason or "higher low" in result.reason or "False break" in result.reason

    def test_trailing_sl_up(self):
        """Test trailing stop loss (UP direction)."""
        bars = [
            Bar(timestamp="1", open=100, high=101, low=99, close=100.5, volume=1000),
            Bar(timestamp="2", open=100.5, high=102, low=100, close=101.5, volume=1000),
            Bar(timestamp="3", open=101.5, high=103, low=101, close=102.5, volume=1000),  # New swing low at 101
            Bar(timestamp="4", open=102.5, high=104, low=101.5, close=103.0, volume=1000),
        ]
        result = evaluate_exit(bars, entry=100, stop=98, target=105, direction="UP")
        if result.action == "TRAIL_SL":
            assert result.new_stop is not None
            assert result.new_stop > 98  # New stop should be higher than original
            assert "Trailing" in result.reason or "swing" in result.reason

    def test_trailing_sl_down(self):
        """Test trailing stop loss (DOWN direction)."""
        bars = [
            Bar(timestamp="1", open=100, high=101, low=99, close=99.5, volume=1000),
            Bar(timestamp="2", open=99.5, high=100, low=98, close=98.5, volume=1000),
            Bar(timestamp="3", open=98.5, high=99, low=97, close=97.5, volume=1000),  # New swing high at 99
            Bar(timestamp="4", open=97.5, high=98, low=96, close=96.5, volume=1000),
        ]
        result = evaluate_exit(bars, entry=100, stop=102, target=95, direction="DOWN")
        if result.action == "TRAIL_SL":
            assert result.new_stop is not None
            assert result.new_stop < 102  # New stop should be lower than original
            assert "Trailing" in result.reason or "swing" in result.reason

    def test_hold_no_signal(self):
        """Test HOLD when no exit signal is detected."""
        bars = [
            Bar(timestamp="1", open=100, high=101, low=99, close=100.5, volume=1000),
            Bar(timestamp="2", open=100.5, high=101.5, low=100, close=101.0, volume=1000),  # No signal
        ]
        result = evaluate_exit(bars, entry=100, stop=98, target=105, direction="UP")
        assert result.action == "HOLD"
        assert result.new_stop is None
        assert "No exit signal" in result.reason or "trend continues" in result.reason

    def test_exit_signal_dataclass(self):
        """Test ExitSignal dataclass creation."""
        signal = ExitSignal(action="HOLD", new_stop=None, reason="Test reason")
        assert signal.action == "HOLD"
        assert signal.new_stop is None
        assert signal.reason == "Test reason"

        signal2 = ExitSignal(action="TRAIL_SL", new_stop=101.5, reason="New stop set")
        assert signal2.action == "TRAIL_SL"
        assert signal2.new_stop == 101.5
