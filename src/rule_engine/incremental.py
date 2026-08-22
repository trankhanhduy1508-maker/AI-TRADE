"""Point-in-time incremental features for the existing rule engine.

The original trend and structure rules rescan every historical bar whenever a
new prefix is evaluated. This module confirms each candidate swing exactly
once, after its right-hand confirmation window is available, and preserves the
same strict-comparison semantics without changing the public rule outputs.
"""

from dataclasses import dataclass
from collections.abc import Sequence

from src.rule_engine.types import Bar, RuleResult


@dataclass(frozen=True)
class CachedRuleFeatures:
    """Features that can be reused by one closed-bar scoring decision."""

    trend_result: RuleResult
    swing_levels: tuple[float | None, float | None]


class PointInTimeRuleCache:
    """Incrementally cache confirmed swings for append-only bar prefixes.

    ``update`` expects the same append-only closed-bar prefixes produced by the
    backtest engine. A candidate at index ``i`` is processed only when bars
    through ``i + n`` have arrived, so no future bar is exposed early.
    """

    def __init__(self, n: int = 2):
        if n < 1:
            raise ValueError("swing confirmation n must be positive")
        self.n = n
        self._bars: list[Bar] = []
        self._high_values: list[float] = []
        self._low_values: list[float] = []
        self._hh_count = 0
        self._hl_count = 0
        self._lh_count = 0
        self._ll_count = 0

    def update(self, history: Sequence[Bar]) -> CachedRuleFeatures:
        """Consume newly appended bars and return current point-in-time features."""

        if len(history) < len(self._bars):
            raise ValueError("rule cache history cannot move backwards")
        if self._bars and history[len(self._bars) - 1] != self._bars[-1]:
            raise ValueError("rule cache history must remain append-only")

        for index in range(len(self._bars), len(history)):
            self._bars.append(history[index])
            candidate_index = index - self.n
            if candidate_index < self.n:
                continue
            self._confirm_candidate(candidate_index)

        return CachedRuleFeatures(
            trend_result=self._trend_result(),
            swing_levels=(
                self._high_values[-1] if self._high_values else None,
                self._low_values[-1] if self._low_values else None,
            ),
        )

    def _confirm_candidate(self, index: int) -> None:
        candidate = self._bars[index]
        left = self._bars[index - self.n : index]
        right = self._bars[index + 1 : index + self.n + 1]

        is_high = all(candidate.high > bar.high for bar in left) and all(
            candidate.high > bar.high for bar in right
        )
        if is_high:
            if self._high_values:
                previous = self._high_values[-1]
                self._hh_count += previous < candidate.high
                self._lh_count += previous > candidate.high
            self._high_values.append(candidate.high)

        is_low = all(candidate.low < bar.low for bar in left) and all(
            candidate.low < bar.low for bar in right
        )
        if is_low:
            if self._low_values:
                previous = self._low_values[-1]
                self._hl_count += previous < candidate.low
                self._ll_count += previous > candidate.low
            self._low_values.append(candidate.low)

    def _trend_result(self) -> RuleResult:
        if len(self._bars) < 2 * self.n + 1:
            return RuleResult(
                rule_id="RULE_001",
                status="TREND_NEUTRAL",
                score=0,
                max_score=25,
                reject=True,
                detail={"reason": "Insufficient bars for swing detection"},
            )

        if len(self._high_values) < 2 and len(self._low_values) < 2:
            return RuleResult(
                rule_id="RULE_001",
                status="TREND_NEUTRAL",
                score=0,
                max_score=25,
                reject=True,
                detail={
                    "hh_hl_pairs": 0,
                    "lh_ll_pairs": 0,
                    "reason": "Insufficient trend pairs",
                },
            )

        if self._hh_count > 0 and self._hl_count > 0:
            hh_hl_pairs = min(self._hh_count, self._hl_count)
        else:
            hh_hl_pairs = max(self._hh_count, self._hl_count)
        if self._lh_count > 0 and self._ll_count > 0:
            lh_ll_pairs = min(self._lh_count, self._ll_count)
        else:
            lh_ll_pairs = max(self._lh_count, self._ll_count)

        if hh_hl_pairs >= 2:
            return RuleResult(
                rule_id="RULE_001",
                status="TREND_UP",
                score=25 if hh_hl_pairs >= 3 else 21,
                max_score=25,
                reject=False,
                detail={
                    "hh_hl_pairs": hh_hl_pairs,
                    "lh_ll_pairs": lh_ll_pairs,
                },
            )
        if lh_ll_pairs >= 2:
            return RuleResult(
                rule_id="RULE_001",
                status="TREND_DOWN",
                score=25 if lh_ll_pairs >= 3 else 21,
                max_score=25,
                reject=False,
                detail={
                    "hh_hl_pairs": hh_hl_pairs,
                    "lh_ll_pairs": lh_ll_pairs,
                },
            )
        return RuleResult(
            rule_id="RULE_001",
            status="TREND_NEUTRAL",
            score=0,
            max_score=25,
            reject=True,
            detail={
                "hh_hl_pairs": hh_hl_pairs,
                "lh_ll_pairs": lh_ll_pairs,
                "reason": "Insufficient trend pairs",
            },
        )
