"""Frozen rule-based MT5 DEMO candidate. Research-only, NEVER an approval.

This adapter translates a predeclared time-series momentum hypothesis into
the existing closed-bar engine. Any broker order still requires the existing
Founder authentication, independent risk gate and DEMO-send authorization.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import math
from collections.abc import Sequence

from src.backtest.spec import StrategySpec
from src.backtest.types import Signal
from src.execution.auto_engine import AutoTradeConfig
from src.execution.position_lifecycle import ExitMode
from src.execution.risk import IndependentRiskEngine, RiskLimits
from src.rule_engine.types import Bar
from src.strategies.time_series_momentum import TimeSeriesMomentumEvaluator


@dataclass(frozen=True)
class DemoTrendCandidate:
    """Frozen hypothesis; immutable defaults prevent silent performance retuning."""

    strategy_id: str = "CWS-DEMO-TF014-EURUSD-H4-V1"
    symbol: str = "EURUSD"
    timeframe: str = "H4"
    lookback_bars: int = 20
    stop_lookback_bars: int = 10
    trailing_lookback_bars: int = 20
    demo_volume: float = 0.01
    min_closed_bars: int = 60
    evidence_status: str = "RESEARCH_CANDIDATE"
    broker_orders_approved: bool = False

    def __post_init__(self) -> None:
        if (
            self.strategy_id != "CWS-DEMO-TF014-EURUSD-H4-V1"
            or self.symbol != "EURUSD"
            or self.timeframe != "H4"
            or self.lookback_bars != 20
            or self.stop_lookback_bars != 10
            or self.trailing_lookback_bars != 20
            or self.min_closed_bars != 60
            or self.demo_volume != .01
            or self.evidence_status != "RESEARCH_CANDIDATE"
            or self.broker_orders_approved is not False
        ):
            raise ValueError("DEMO_CANDIDATE_PARAMETERS_FROZEN")

    def strategy_spec(self) -> StrategySpec:
        return StrategySpec(
            strategy_id=self.strategy_id,
            risk_mode="SIGNAL_ONLY",
            provenance={
                "trend_following_principles": "VERIFIED_FROM_AUTHOR",
                "signal_translation": "IMPLEMENTATION_DERIVATION",
                "parameters_and_eurusd_h4": "UNVERIFIED",
                "broker_cost_and_forward": "NOT_VALIDATED",
            },
            signal_model="TIME_SERIES_MOMENTUM",
            lookback_bars=self.lookback_bars,
            stop_lookback_bars=self.stop_lookback_bars,
            entry_timing="CLOSE",
            exit_model="CHANNEL_TRAILING",
            exit_lookback_bars=self.trailing_lookback_bars,
            position_policy="ONE_OPEN",
            ambiguous_bar_policy="STOP_FIRST",
        )

    def auto_config(self) -> AutoTradeConfig:
        return AutoTradeConfig(
            strategy_id=self.strategy_id,
            symbol=self.symbol,
            demo_volume=self.demo_volume,
            exit_mode=ExitMode.TRAILING_ONLY,
            trailing_lookback=self.trailing_lookback_bars,
            max_pyramid_adds=0,
        )

    def risk_engine(self) -> IndependentRiskEngine:
        """Numbers are conservative proposal, not permission to set cloud gates."""
        return IndependentRiskEngine(
            RiskLimits(
                max_volume=self.demo_volume,
                max_open_positions=1,
                max_spread_points=20.0,
                max_daily_loss=100.0,
                max_total_volume_per_symbol=self.demo_volume,
                max_risk_per_trade_fraction=.0025,
                max_daily_loss_fraction=.01,
                required_account_currency="USD",
            )
        )

    def __call__(self, history: Sequence[Bar]) -> Signal | None:
        if len(history) < self.min_closed_bars:
            return None
        # Broker H4 source/timeframe must be verified by the trusted caller.
        recent = history[-self.min_closed_bars:]
        previous_ts: datetime | None = None
        for bar in recent:
            if bar.closed is not True:
                return None
            try:
                timestamp = datetime.fromisoformat(bar.timestamp)
            except (TypeError, ValueError):
                return None
            if timestamp.tzinfo is None or (
                previous_ts is not None and timestamp <= previous_ts
            ):
                return None
            if previous_ts is not None:
                elapsed = timestamp - previous_ts
                # The caller must independently verify the broker's H4 feed.
                # This additional guard rejects accidentally supplied M15/H1
                # candles and implausible/missing-history gaps; holiday/weekend
                # gaps are allowed up to four days.
                if not timedelta(hours=4) <= elapsed <= timedelta(days=4):
                    return None
            previous_ts = timestamp
            values = (bar.open, bar.high, bar.low, bar.close, bar.volume)
            if not all(
                isinstance(value, (float, int))
                and not isinstance(value, bool)
                and math.isfinite(value)
                for value in values
            ):
                return None
            if (
                min(bar.open, bar.high, bar.low, bar.close) <= 0
                or bar.volume < 0
                or bar.low > min(bar.open, bar.close)
                or bar.high < max(bar.open, bar.close)
                or bar.low > bar.high
            ):
                return None
        if recent[-1].volume == 0:
            return None
        signal = TimeSeriesMomentumEvaluator()(recent, self.strategy_spec())
        if signal is None:
            return None
        stop = signal.stop_price
        if not math.isfinite(stop) or stop <= 0:
            return None
        if signal.direction == "UP" and stop >= recent[-1].close:
            return None
        if signal.direction == "DOWN" and stop <= recent[-1].close:
            return None
        return signal
