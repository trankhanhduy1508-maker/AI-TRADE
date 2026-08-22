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
