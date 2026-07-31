"""Tests for RULE_008_RISK (risk_validation.py)."""

import pytest
from src.rule_engine import risk_validation


class TestRiskValidation:
    """Test Risk/Reward and Stop Loss validation."""

    def test_stop_equals_entry(self):
        """Test when stop == entry (invalid)."""
        result = risk_validation.evaluate(
            entry=100.0,
            stop=100.0,
            target=105.0,
            direction="UP"
        )
        assert result.rule_id == "RULE_008"
        assert result.status == "INVALID_STOP"
        assert result.score == 0
        assert result.reject is True

    def test_stop_above_entry_for_up(self):
        """Test UP direction with stop > entry (invalid)."""
        result = risk_validation.evaluate(
            entry=100.0,
            stop=101.0,  # Above entry
            target=105.0,
            direction="UP"
        )
        assert result.status == "INVALID_STOP"
        assert result.reject is True

    def test_stop_below_entry_for_down(self):
        """Test DOWN direction with stop < entry (invalid)."""
        result = risk_validation.evaluate(
            entry=100.0,
            stop=99.0,  # Below entry
            target=95.0,
            direction="DOWN"
        )
        assert result.status == "INVALID_STOP"
        assert result.reject is True

    def test_no_target(self):
        """Test when target is None (cannot calculate R/R)."""
        result = risk_validation.evaluate(
            entry=100.0,
            stop=98.0,
            target=None,
            direction="UP"
        )
        assert result.rule_id == "RULE_008"
        assert result.status == "NO_TARGET"
        assert result.score == 0.0
        assert result.reject is False  # No target is not a reject

    def test_rr_acceptable_up(self):
        """Test UP direction with R/R >= 1.5 (acceptable)."""
        # Entry=100, Stop=98 (loss=2), Target=103 (profit=3)
        # R/R = 3/2 = 1.5
        result = risk_validation.evaluate(
            entry=100.0,
            stop=98.0,
            target=103.0,
            direction="UP",
            rr_min=1.5
        )
        assert result.rule_id == "RULE_008"
        assert result.status == "ACCEPTABLE"
        assert result.score == 5.0
        assert result.reject is False

    def test_rr_fair_up(self):
        """Test UP direction with 1.0 <= R/R < 1.5 (fair)."""
        # Entry=100, Stop=98 (loss=2), Target=101 (profit=1)
        # R/R = 1/2 = 0.5, wait that's < 1.0
        # Let's make it 1.2: Entry=100, Stop=98 (loss=2), Target=102.4 (profit=2.4)
        # R/R = 2.4/2 = 1.2
        result = risk_validation.evaluate(
            entry=100.0,
            stop=98.0,
            target=102.4,
            direction="UP",
            rr_min=1.5
        )
        assert result.status == "FAIR"
        assert result.score == 3.0
        assert result.reject is False

    def test_rr_unacceptable_up(self):
        """Test UP direction with R/R < 1.0 (unacceptable + reject)."""
        # Entry=100, Stop=97 (loss=3), Target=102 (profit=2)
        # R/R = 2/3 = 0.67 < 1.0
        result = risk_validation.evaluate(
            entry=100.0,
            stop=97.0,
            target=102.0,
            direction="UP",
            rr_min=1.5
        )
        assert result.status == "UNACCEPTABLE"
        assert result.score == 0.0
        assert result.reject is True  # R/R < 1.0 → REJECT

    def test_rr_acceptable_down(self):
        """Test DOWN direction with R/R >= 1.5 (acceptable)."""
        # Entry=100, Stop=102 (loss=2), Target=97 (profit=3)
        # R/R = 3/2 = 1.5
        result = risk_validation.evaluate(
            entry=100.0,
            stop=102.0,
            target=97.0,
            direction="DOWN",
            rr_min=1.5
        )
        assert result.status == "ACCEPTABLE"
        assert result.score == 5.0
        assert result.reject is False

    def test_rr_unacceptable_down(self):
        """Test DOWN direction with R/R < 1.0 (reject)."""
        # Entry=100, Stop=103 (loss=3), Target=98 (profit=2)
        # R/R = 2/3 = 0.67 < 1.0
        result = risk_validation.evaluate(
            entry=100.0,
            stop=103.0,
            target=98.0,
            direction="DOWN",
            rr_min=1.5
        )
        assert result.status == "UNACCEPTABLE"
        assert result.reject is True

    def test_custom_rr_min(self):
        """Test with custom R/R minimum."""
        # Entry=100, Stop=98 (loss=2), Target=104 (profit=4)
        # R/R = 4/2 = 2.0, >= 2.0 → ACCEPTABLE
        result = risk_validation.evaluate(
            entry=100.0,
            stop=98.0,
            target=104.0,
            direction="UP",
            rr_min=2.0
        )
        assert result.status == "ACCEPTABLE"
        assert result.score == 5.0

    def test_rr_boundary_1_0(self):
        """Test R/R exactly at 1.0 (fair, not acceptable)."""
        # Entry=100, Stop=98 (loss=2), Target=102 (profit=2)
        # R/R = 2/2 = 1.0
        result = risk_validation.evaluate(
            entry=100.0,
            stop=98.0,
            target=102.0,
            direction="UP",
            rr_min=1.5
        )
        assert result.status == "FAIR"
        assert result.score == 3.0
        assert result.reject is False

    def test_rr_boundary_rr_min(self):
        """Test R/R exactly at rr_min threshold."""
        # Entry=100, Stop=98 (loss=2), Target=103 (profit=3)
        # R/R = 3/2 = 1.5, exactly at rr_min
        result = risk_validation.evaluate(
            entry=100.0,
            stop=98.0,
            target=103.0,
            direction="UP",
            rr_min=1.5
        )
        assert result.status == "ACCEPTABLE"
        assert result.score == 5.0
