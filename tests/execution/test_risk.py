from src.execution.mt5_adapter import MT5OrderRequest
from src.execution.risk import (
    IndependentRiskEngine,
    RiskContext,
    RiskLimits,
)


def _engine(**changes):
    values = {
        "max_volume": 0.01,
        "max_open_positions": 1,
        "max_spread_points": 20.0,
        "max_daily_loss": 100.0,
    }
    values.update(changes)
    return IndependentRiskEngine(RiskLimits(**values))


def _context(**changes):
    values = {
        "open_positions": 0,
        "spread_points": 10.0,
        "daily_loss": 0.0,
    }
    values.update(changes)
    return RiskContext(**values)


def _order(**changes):
    values = {
        "client_order_id": "risk-1",
        "symbol": "EURUSD",
        "direction": "UP",
        "volume": 0.01,
        "price": 1.1000,
        "stop_loss": 1.0900,
        "take_profit": 1.1200,
    }
    values.update(changes)
    return MT5OrderRequest(**values)


def test_independent_risk_engine_allows_only_valid_bounded_order():
    decision = _engine().evaluate(_order(), _context())

    assert decision.allowed
    assert decision.reasons == ()


def test_independent_risk_engine_blocks_volume_position_and_spread_limits():
    assert "MAX_VOLUME" in _engine().evaluate(
        _order(volume=0.02), _context()
    ).reasons
    assert "MAX_OPEN_POSITIONS" in _engine().evaluate(
        _order(), _context(open_positions=1)
    ).reasons
    assert "MAX_SPREAD" in _engine().evaluate(
        _order(), _context(spread_points=21.0)
    ).reasons


def test_independent_risk_engine_blocks_daily_loss_limit():
    decision = _engine(max_daily_loss=100.0).evaluate(
        _order(), _context(daily_loss=-100.0)
    )

    assert not decision.allowed
    assert "MAX_DAILY_LOSS" in decision.reasons


def test_independent_risk_engine_requires_directional_stop_and_target():
    assert "INVALID_STOPS" in _engine().evaluate(
        _order(stop_loss=1.1100), _context()
    ).reasons
    assert "INVALID_TARGET" in _engine().evaluate(
        _order(take_profit=1.0900), _context()
    ).reasons
    assert "MISSING_STOPS" in _engine().evaluate(
        _order(stop_loss=None, take_profit=None), _context()
    ).reasons


def test_independent_risk_engine_blocks_non_finite_market_context():
    decision = _engine().evaluate(_order(), _context(spread_points=float("nan")))

    assert not decision.allowed
    assert "INVALID_CONTEXT" in decision.reasons


def _fractional_engine():
    return IndependentRiskEngine(RiskLimits(
        max_volume=.01, max_open_positions=1, max_spread_points=20,
        max_daily_loss=100.0, max_total_volume_per_symbol=.01,
        max_risk_per_trade_fraction=.0025, max_daily_loss_fraction=.01,
        required_account_currency="USD",
    ))


def _broker_context(**changes):
    fields = {
        "open_positions": 0, "spread_points": 10.0, "daily_loss": 0.0,
        "account_equity": 10000.0, "tick_size": .00001,
        "tick_value_per_lot": 1.0, "account_currency": "USD",
    }
    fields.update(changes)
    return RiskContext(**fields)


def test_fractional_demo_risk_requires_verified_broker_equity_and_tick_value():
    engine = _fractional_engine()
    assert engine.evaluate(_order(), _broker_context()).allowed
    assert "BROKER_EQUITY_REQUIRED" in engine.evaluate(
        _order(), _broker_context(account_equity=None)
    ).reasons
    assert "BROKER_TICK_VALUE_REQUIRED" in engine.evaluate(
        _order(), _broker_context(tick_value_per_lot=None)
    ).reasons
    assert "ACCOUNT_CURRENCY_MISMATCH" in engine.evaluate(
        _order(), _broker_context(account_currency="EUR")
    ).reasons


def test_fractional_demo_risk_blocks_oversized_stop_loss_and_daily_loss():
    engine = _fractional_engine()
    assert "MAX_TRADE_STOP_RISK" in engine.evaluate(
        _order(stop_loss=1.00), _broker_context(account_equity=1000.0)
    ).reasons
    assert "MAX_DAILY_LOSS_FRACTION" in engine.evaluate(
        _order(stop_loss=1.099), _broker_context(account_equity=1000.0, daily_loss=-10.0)
    ).reasons
    assert "MAX_DAILY_LOSS" in engine.evaluate(
        _order(stop_loss=1.099), _broker_context(daily_loss=-100.0)
    ).reasons


def test_fractional_demo_risk_rejects_nan_and_nonpositive_tick_value():
    engine = _fractional_engine()
    for tick in (None, float("nan"), float("inf"), 0.0, -1.0):
        assert "BROKER_TICK_VALUE_REQUIRED" in engine.evaluate(
            _order(), _broker_context(tick_value_per_lot=tick)
        ).reasons


def test_fractional_demo_risk_policy_rejects_invalid_fraction_configuration():
    import pytest
    for amount in (-.01, 0.0, 1.01, float("nan"), float("inf"), True):
        with pytest.raises(ValueError):
            RiskLimits(.01, 1, 20, 100, max_risk_per_trade_fraction=amount)
