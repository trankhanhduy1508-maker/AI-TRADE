import math
import pytest
from src.execution.risk import IndependentRiskEngine, RiskLimits, RiskContext
from src.execution.mt5_adapter import MT5OrderRequest


def engine(**changes):
    fields = dict(max_volume=.01, max_open_positions=1, max_spread_points=20,
                  max_daily_loss=100, max_risk_per_trade_fraction=.0025,
                  max_daily_loss_fraction=.01, max_portfolio_risk_fraction=.01,
                  max_drawdown_fraction=.05, max_consecutive_losses=5,
                  required_account_currency='USD')
    fields.update(changes)
    return IndependentRiskEngine(RiskLimits(**fields))


def context(**changes):
    fields = dict(open_positions=0, spread_points=10, daily_loss=0,
                  account_equity=10000, tick_size=.00001, tick_value_per_lot=1,
                  account_currency='USD', portfolio_open_risk=0,
                  peak_equity=10000, consecutive_losses=0)
    fields.update(changes)
    return RiskContext(**fields)


def order():
    return MT5OrderRequest(client_order_id='demo-test',symbol='EURUSD',direction='UP',
                           volume=.01,price=1.1,stop_loss=1.09,take_profit=None)


def test_bounded_demo_order_and_trailing_without_fixed_tp():
    assert engine().evaluate(order(),context()).allowed


def test_portfolio_includes_candidate_stop_risk_and_never_offsets_opposite_risk():
    assert 'MAX_PORTFOLIO_STOP_RISK' in engine().evaluate(order(),context(portfolio_open_risk=95)).reasons
    assert engine().evaluate(order(),context(portfolio_open_risk=80)).allowed
    assert 'PORTFOLIO_RISK_REQUIRED' in engine().evaluate(order(),context(portfolio_open_risk=-1)).reasons


def test_drawdown_and_loss_streak_stop_at_the_limit():
    assert 'MAX_DRAWDOWN' in engine().evaluate(order(),context(account_equity=9500)).reasons
    assert 'MAX_CONSECUTIVE_LOSSES' in engine().evaluate(order(),context(consecutive_losses=5)).reasons


@pytest.mark.parametrize('field,reason',[
    ('portfolio_open_risk','PORTFOLIO_RISK_REQUIRED'),
    ('peak_equity','PEAK_EQUITY_REQUIRED'),
    ('consecutive_losses','LOSS_STREAK_REQUIRED'),
])
def test_missing_or_invalid_broker_risk_state_blocks(field,reason):
    for value in (None, math.nan, math.inf, True):
        assert reason in engine().evaluate(order(),context(**{field:value})).reasons


def test_invalid_hard_limits_are_rejected():
    for field in ('max_portfolio_risk_fraction','max_drawdown_fraction'):
        for value in (True, 0, -.1, 1.01, math.nan):
            with pytest.raises(ValueError): engine(**{field:value})
    for value in (True, 0, -1, 1.5):
        with pytest.raises(ValueError): engine(max_consecutive_losses=value)


def test_portfolio_gate_also_requires_equity_and_stop_tick_metadata():
    e=engine(max_risk_per_trade_fraction=None,max_daily_loss_fraction=None)
    assert 'BROKER_EQUITY_REQUIRED' in e.evaluate(order(),context(account_equity=None)).reasons
    assert 'BROKER_TICK_VALUE_REQUIRED' in e.evaluate(order(),context(tick_size=None)).reasons
