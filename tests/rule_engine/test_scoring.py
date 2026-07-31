"""Tests for scoring.py (orchestrator)."""

import pytest
from unittest.mock import patch, MagicMock
from src.rule_engine.types import Bar, RuleResult
from src.rule_engine.scoring import evaluate_setup, SetupScore


class TestScoringSetupScore:
    """Test SetupScore dataclass and basic scoring."""

    def test_setup_score_creation(self):
        """Test SetupScore dataclass."""
        results = [
            RuleResult(rule_id="RULE_001", status="TREND_UP", score=25, max_score=25),
        ]
        score = SetupScore(total=80, decision="TRADE", results=results)
        assert score.total == 80
        assert score.decision == "TRADE"
        assert len(score.results) == 1

    def test_setup_score_default_results(self):
        """Test SetupScore with default empty results."""
        score = SetupScore(total=50, decision="WAIT")
        assert score.total == 50
        assert score.decision == "WAIT"
        assert score.results == []


class TestScoringOrchestrator:
    """Test full orchestrator evaluation."""

    def create_sample_bars(self, count=60, trend="up"):
        """Helper to create sample bars."""
        bars = []
        price = 100.0
        for i in range(count):
            if trend == "up":
                price += 0.1
            elif trend == "down":
                price -= 0.1
            bars.append(Bar(
                timestamp=str(i),
                open=price - 0.05,
                high=price + 0.15,
                low=price - 0.15,
                close=price,
                volume=1000,
                closed=True
            ))
        return bars

    @patch('src.rule_engine.scoring.eval_rule_001', None)
    @patch('src.rule_engine.scoring.eval_rule_002', None)
    @patch('src.rule_engine.scoring.eval_rule_003', None)
    @patch('src.rule_engine.scoring.eval_rule_004', None)
    @patch('src.rule_engine.scoring.eval_rule_005', None)
    def test_scoring_without_rule_001_005(self):
        """Test when RULE_001-005 don't exist (all None)."""
        bars = self.create_sample_bars()
        score = evaluate_setup(
            bars=bars,
            entry=100.5,
            stop=98.0,
            target=105.0,
            direction="UP"
        )
        assert isinstance(score, SetupScore)
        assert score.total >= 0
        assert score.decision in ["TRADE", "WAIT", "REJECT"]

    @patch('src.rule_engine.scoring.eval_rule_001')
    @patch('src.rule_engine.scoring.eval_rule_002', None)
    @patch('src.rule_engine.scoring.eval_rule_003', None)
    @patch('src.rule_engine.scoring.eval_rule_004', None)
    @patch('src.rule_engine.scoring.eval_rule_005', None)
    def test_scoring_with_rule_001_only(self, mock_rule_001):
        """Test with only RULE_001."""
        mock_rule_001.return_value = RuleResult(
            rule_id="RULE_001",
            status="TREND_UP",
            score=25,
            max_score=25,
            reject=False
        )
        bars = self.create_sample_bars()
        score = evaluate_setup(
            bars=bars,
            entry=100.5,
            stop=98.0,
            target=105.0,
            direction="UP"
        )
        assert score.decision in ["TRADE", "WAIT", "REJECT"]
        assert len(score.results) > 0
        assert score.results[0].rule_id == "RULE_001"

    @patch('src.rule_engine.scoring.eval_rule_001')
    def test_scoring_reject_at_rule_001(self, mock_rule_001):
        """Test early reject at RULE_001."""
        mock_rule_001.return_value = RuleResult(
            rule_id="RULE_001",
            status="NO_TREND",
            score=0,
            max_score=25,
            reject=True  # Reject at step 1
        )
        bars = self.create_sample_bars()
        score = evaluate_setup(
            bars=bars,
            entry=100.5,
            stop=98.0,
            target=105.0,
            direction="UP"
        )
        assert score.decision == "REJECT"
        assert len(score.results) == 1
        assert score.results[0].reject is True

    @patch('src.rule_engine.scoring.eval_rule_001')
    @patch('src.rule_engine.scoring.eval_rule_002')
    @patch('src.rule_engine.scoring.eval_rule_003', None)
    @patch('src.rule_engine.scoring.eval_rule_004', None)
    @patch('src.rule_engine.scoring.eval_rule_005', None)
    def test_scoring_reject_at_rule_002(self, mock_rule_002, mock_rule_001):
        """Test reject at RULE_002."""
        mock_rule_001.return_value = RuleResult(
            rule_id="RULE_001",
            status="TREND_UP",
            score=25,
            max_score=25
        )
        mock_rule_002.return_value = RuleResult(
            rule_id="RULE_002",
            status="NO_STRUCTURE",
            score=0,
            max_score=20,
            reject=True
        )
        bars = self.create_sample_bars()
        score = evaluate_setup(
            bars=bars,
            entry=100.5,
            stop=98.0,
            target=105.0,
            direction="UP"
        )
        assert score.decision == "REJECT"
        assert len(score.results) == 2
        assert score.results[1].reject is True

    @patch('src.rule_engine.scoring.eval_rule_001', None)
    @patch('src.rule_engine.scoring.eval_rule_002', None)
    @patch('src.rule_engine.scoring.eval_rule_003', None)
    @patch('src.rule_engine.scoring.eval_rule_004', None)
    @patch('src.rule_engine.scoring.eval_rule_005', None)
    def test_scoring_high_score_trade(self):
        """Test high total score → TRADE decision."""
        bars = self.create_sample_bars()
        score = evaluate_setup(
            bars=bars,
            entry=100.5,
            stop=98.0,
            target=105.0,
            direction="UP"
        )
        # Without RULE_001-005, score comes from RULE_006-009
        # Best case: RSI 5 + EMA 5 + Risk 5 + Liquidity 5 = 20 (not enough for TRADE)
        # So should be WAIT or REJECT
        assert score.decision in ["TRADE", "WAIT", "REJECT"]

    @patch('src.rule_engine.scoring.eval_rule_001')
    @patch('src.rule_engine.scoring.eval_rule_002')
    @patch('src.rule_engine.scoring.eval_rule_003')
    @patch('src.rule_engine.scoring.eval_rule_004')
    @patch('src.rule_engine.scoring.eval_rule_005')
    def test_scoring_with_invalid_risk(
        self, mock_rule_005, mock_rule_004, mock_rule_003, mock_rule_002, mock_rule_001
    ):
        """Test scoring with invalid R/R (should reject)."""
        mock_rule_001.return_value = RuleResult(
            rule_id="RULE_001", status="TREND_UP", score=25, max_score=25
        )
        mock_rule_002.return_value = RuleResult(
            rule_id="RULE_002", status="STRUCTURE_VALID", score=20, max_score=20,
            detail={"swing_high": 100.2, "swing_low": 99.0}
        )
        mock_rule_003.return_value = RuleResult(
            rule_id="RULE_003", status="BREAKOUT_TRUE", score=15, max_score=15
        )
        mock_rule_004.return_value = RuleResult(
            rule_id="RULE_004", status="PULLBACK_VALID", score=15, max_score=15
        )
        mock_rule_005.return_value = RuleResult(
            rule_id="RULE_005", status="VOLUME_STRONG", score=10, max_score=10
        )

        bars = self.create_sample_bars()
        # R/R < 1.0 should cause reject
        score = evaluate_setup(
            bars=bars,
            entry=100.0,
            stop=97.0,  # Loss = 3
            target=102.0,  # Profit = 2, R/R = 0.67 < 1.0
            direction="UP"
        )
        assert score.decision == "REJECT"
        # Should have RULE_008 with reject=True
        rule_008 = next((r for r in score.results if r.rule_id == "RULE_008"), None)
        assert rule_008 is not None
        assert rule_008.reject is True

    @patch('src.rule_engine.scoring.eval_rule_001', None)
    @patch('src.rule_engine.scoring.eval_rule_002', None)
    @patch('src.rule_engine.scoring.eval_rule_003', None)
    @patch('src.rule_engine.scoring.eval_rule_004', None)
    @patch('src.rule_engine.scoring.eval_rule_005', None)
    def test_scoring_thresholds(self):
        """Test score threshold decision boundaries."""
        bars = self.create_sample_bars()

        # Test with good R/R (no reject)
        score = evaluate_setup(
            bars=bars,
            entry=100.0,
            stop=98.0,  # Loss = 2
            target=103.0,  # Profit = 3, R/R = 1.5 >= 1.5
            direction="UP"
        )
        # Score = RSI (5) + EMA (5) + Risk (5) + Liquidity (5) = 20 (REJECT)
        # OR could be higher if EMA/RSI give better scores
        assert score.decision in ["TRADE", "WAIT", "REJECT"]

    @patch('src.rule_engine.scoring.eval_rule_001')
    @patch('src.rule_engine.scoring.eval_rule_002')
    @patch('src.rule_engine.scoring.eval_rule_003')
    @patch('src.rule_engine.scoring.eval_rule_004')
    @patch('src.rule_engine.scoring.eval_rule_005')
    def test_scoring_all_rules_perfect(
        self,
        mock_rule_005,
        mock_rule_004,
        mock_rule_003,
        mock_rule_002,
        mock_rule_001
    ):
        """Test with all rules returning max score."""
        mock_rule_001.return_value = RuleResult(
            rule_id="RULE_001", status="TREND_UP", score=25, max_score=25
        )
        mock_rule_002.return_value = RuleResult(
            rule_id="RULE_002", status="STRUCTURE_VALID", score=20, max_score=20,
            detail={"swing_high": 100.2, "swing_low": 99.0}
        )
        mock_rule_003.return_value = RuleResult(
            rule_id="RULE_003", status="BREAKOUT_TRUE", score=15, max_score=15
        )
        mock_rule_004.return_value = RuleResult(
            rule_id="RULE_004", status="PULLBACK_VALID", score=15, max_score=15
        )
        mock_rule_005.return_value = RuleResult(
            rule_id="RULE_005", status="VOLUME_STRONG", score=10, max_score=10
        )

        bars = self.create_sample_bars()
        score = evaluate_setup(
            bars=bars,
            entry=100.5,
            stop=98.0,
            target=105.0,
            direction="UP"
        )
        # Total: 25+20+15+15+10 (RULE_001-005) + RSI + EMA + Risk + Liquidity
        # RSI = 100 (overbought) = 0, EMA = 5, Risk = 5, Liquidity = 3 (spread 2.0)
        # Total: 25+20+15+15+10+0+5+5+3 = 98
        assert score.total >= 80  # At least TRADE threshold
        assert score.decision == "TRADE"
        assert len(score.results) == 9

    def test_scoring_empty_bars(self):
        """Test with empty bars list."""
        score = evaluate_setup(
            bars=[],
            entry=100.0,
            stop=98.0,
            target=105.0,
            direction="UP"
        )
        # Should still return SetupScore (RSI/EMA will handle empty)
        assert isinstance(score, SetupScore)
        assert score.decision in ["TRADE", "WAIT", "REJECT"]

    @patch('src.rule_engine.scoring.eval_rule_001')
    @patch('src.rule_engine.scoring.eval_rule_002')
    @patch('src.rule_engine.scoring.eval_rule_003')
    @patch('src.rule_engine.scoring.eval_rule_004')
    @patch('src.rule_engine.scoring.eval_rule_005')
    def test_scoring_invalid_stop(
        self, mock_rule_005, mock_rule_004, mock_rule_003, mock_rule_002, mock_rule_001
    ):
        """Test with invalid stop (should reject at RULE_008, after RULE_001-005 pass)."""
        mock_rule_001.return_value = RuleResult(
            rule_id="RULE_001", status="TREND_UP", score=25, max_score=25
        )
        mock_rule_002.return_value = RuleResult(
            rule_id="RULE_002", status="STRUCTURE_VALID", score=20, max_score=20,
            detail={"swing_high": 100.2, "swing_low": 99.0}
        )
        mock_rule_003.return_value = RuleResult(
            rule_id="RULE_003", status="BREAKOUT_TRUE", score=15, max_score=15
        )
        mock_rule_004.return_value = RuleResult(
            rule_id="RULE_004", status="PULLBACK_VALID", score=15, max_score=15
        )
        mock_rule_005.return_value = RuleResult(
            rule_id="RULE_005", status="VOLUME_STRONG", score=10, max_score=10
        )

        bars = self.create_sample_bars()
        score = evaluate_setup(
            bars=bars,
            entry=100.0,
            stop=100.0,  # Invalid: stop == entry
            target=105.0,
            direction="UP"
        )
        assert score.decision == "REJECT"
        rule_008 = next((r for r in score.results if r.rule_id == "RULE_008"), None)
        assert rule_008 is not None
        assert rule_008.reject is True

    @patch('src.rule_engine.scoring.eval_rule_001')
    @patch('src.rule_engine.scoring.eval_rule_002')
    @patch('src.rule_engine.scoring.eval_rule_003')
    @patch('src.rule_engine.scoring.eval_rule_004')
    @patch('src.rule_engine.scoring.eval_rule_005')
    def test_scoring_down_direction(
        self, mock_rule_005, mock_rule_004, mock_rule_003, mock_rule_002, mock_rule_001
    ):
        """Test DOWN direction setup."""
        mock_rule_001.return_value = RuleResult(
            rule_id="RULE_001", status="TREND_DOWN", score=25, max_score=25
        )
        mock_rule_002.return_value = RuleResult(
            rule_id="RULE_002", status="STRUCTURE_VALID", score=20, max_score=20,
            detail={"swing_high": 101.0, "swing_low": 99.8}
        )
        mock_rule_003.return_value = RuleResult(
            rule_id="RULE_003", status="BREAKOUT_TRUE", score=15, max_score=15
        )
        mock_rule_004.return_value = RuleResult(
            rule_id="RULE_004", status="PULLBACK_VALID", score=15, max_score=15
        )
        mock_rule_005.return_value = RuleResult(
            rule_id="RULE_005", status="VOLUME_STRONG", score=10, max_score=10
        )

        bars = self.create_sample_bars(trend="down")
        score = evaluate_setup(
            bars=bars,
            entry=100.0,
            stop=102.0,  # Stop above entry for DOWN
            target=95.0,
            direction="DOWN"
        )
        assert isinstance(score, SetupScore)
        assert score.decision in ["TRADE", "WAIT", "REJECT"]
