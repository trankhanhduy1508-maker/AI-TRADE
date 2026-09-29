from dataclasses import replace
from datetime import datetime, timedelta, timezone
import math

import pytest

from src.execution.demo_candidate import DemoTrendCandidate
from src.execution.mt5_adapter import MT5OrderRequest
from src.execution.risk import RiskContext
from src.rule_engine.types import Bar


def history(n=65, delta=.0001, *, volume=100):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    out = []
    for i in range(n):
        opened = 1.10 + i * delta
        closed = opened + delta / 2
        out.append(Bar(
            (start + timedelta(hours=4 * i)).isoformat(),
            opened, max(opened, closed) + .0002,
            min(opened, closed) - .0002,
            closed, volume, True,
        ))
    return out


def test_candidate_emits_deterministic_closed_bar_signal_with_protective_stop():
    profile = DemoTrendCandidate()
    first = profile(history())
    second = profile(history())
    assert first == second
    assert first is not None
    assert first.direction == "UP"
    assert math.isfinite(first.stop_price)
    assert 0 < first.stop_price < history()[-1].close


def test_candidate_does_not_trade_flat_incomplete_or_underwarmed_bars():
    profile = DemoTrendCandidate()
    assert profile(history(59)) is None
    assert profile(history(delta=0.0)) is None
    unclosed = history()
    unclosed[-1].closed = False
    assert profile(unclosed) is None


def test_candidate_rejects_out_of_order_nan_zero_volume_and_invalid_stop():
    profile = DemoTrendCandidate()
    out_of_order = history()
    out_of_order[-1].timestamp = out_of_order[-2].timestamp
    assert profile(out_of_order) is None
    nonfinite = history()
    nonfinite[-1].close = float("nan")
    assert profile(nonfinite) is None
    stale = history(volume=0)
    assert profile(stale) is None
    too_low = history()
    too_low[-3].low = -1.0
    assert profile(too_low) is None


def test_candidate_is_frozen_and_not_execution_approved():
    candidate = DemoTrendCandidate()
    assert candidate.evidence_status == "RESEARCH_CANDIDATE"
    assert candidate.broker_orders_approved is False
    assert candidate.auto_config().max_pyramid_adds == 0
    assert candidate.auto_config().demo_volume == .01
    with pytest.raises(ValueError, match="PARAMETERS_FROZEN"):
        replace(candidate, broker_orders_approved=True)
    with pytest.raises(ValueError, match="PARAMETERS_FROZEN"):
        replace(candidate, demo_volume=.05)


def test_candidate_risk_caps_single_position_stop_exposure_and_daily_loss():
    policy = DemoTrendCandidate().risk_engine()
    order = MT5OrderRequest("candidate", "EURUSD", "UP", .01, 1.11, 1.1090)
    context = RiskContext(
        open_positions=0, spread_points=10, daily_loss=0,
        account_equity=1000, tick_size=.00001,
        tick_value_per_lot=1.0, account_currency="USD",
    )
    assert policy.evaluate(order, context).allowed
    assert "MAX_OPEN_POSITIONS" in policy.evaluate(
        order, replace(context, open_positions=1)
    ).reasons
    assert "MAX_TRADE_STOP_RISK" in policy.evaluate(
        replace(order, stop_loss=1.10), context
    ).reasons
    assert "MAX_DAILY_LOSS_FRACTION" in policy.evaluate(
        order, replace(context, daily_loss=-10.0)
    ).reasons
    assert "BROKER_TICK_VALUE_REQUIRED" in policy.evaluate(
        order, replace(context, tick_size=None)
    ).reasons
