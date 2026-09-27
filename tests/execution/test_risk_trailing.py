from src.execution.mt5_adapter import MT5OrderRequest
from src.execution.risk import IndependentRiskEngine, RiskContext, RiskLimits


def test_trailing_only_can_omit_fixed_take_profit_but_not_stop_loss():
    engine = IndependentRiskEngine(RiskLimits(0.01, 1, 20.0, 100.0))
    context = RiskContext(open_positions=0, spread_points=10.0, daily_loss=0.0)
    trailing = MT5OrderRequest(
        "trail", "EURUSD", "UP", 0.01, 1.1, stop_loss=1.09, take_profit=None
    )
    unprotected = MT5OrderRequest(
        "unsafe", "EURUSD", "UP", 0.01, 1.1, stop_loss=None, take_profit=None
    )

    assert engine.evaluate(trailing, context).allowed
    rejected = engine.evaluate(unprotected, context)
    assert not rejected.allowed
    assert "MISSING_STOPS" in rejected.reasons
