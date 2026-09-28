"""Fake-terminal contract tests, NOT an MT5 broker integration test."""
from dataclasses import replace
from datetime import timezone
from types import SimpleNamespace as NS

import pytest

from src.execution.demo_readback import read_demo_snapshot


class FakeTerminal:
    POSITION_TYPE_BUY = 0
    POSITION_TYPE_SELL = 1

    def __init__(self):
        self.connected = True
        self.account = NS(
            login=123456, server="MetaQuotes-Demo", trade_mode=0,
            currency="USD", balance=1000.0, equity=1012.5,
            trade_allowed=True, trade_expert=True,
        )
        self.rows = [
            NS(ticket=1, symbol="EURUSD", type=0, volume=0.01,
               profit=15.0, sl=1.07, tp=1.12),
            NS(ticket=2, symbol="EURUSD", type=1, volume=0.02,
               profit=-2.5, sl=0.0, tp=0.0),
        ]
        self.send_calls = 0

    def terminal_info(self):
        return NS(connected=self.connected)

    def account_info(self):
        return self.account

    def positions_get(self):
        return self.rows

    def order_send(self, *_args, **_kwargs):
        self.send_calls += 1
        raise AssertionError("readback must not send orders")


def snapshot(terminal):
    return read_demo_snapshot(
        terminal, expected_login="123456", expected_server="MetaQuotes-Demo"
    )


def test_fresh_readback_contains_equity_and_each_position_without_total_lot_kpi():
    terminal = FakeTerminal()
    result = snapshot(terminal)
    assert (result.login, result.server, result.currency) == (
        "123456", "MetaQuotes-Demo", "USD"
    )
    assert (result.balance, result.equity) == (1000.0, 1012.5)
    assert (result.gross_profit, result.gross_loss, result.net_pnl) == (15.0, -2.5, 12.5)
    assert result.symbols_with_positions == 1
    assert [(p.side, p.lot) for p in result.positions] == [("BUY", 0.01), ("SELL", 0.02)]
    assert result.positions[1].stop_loss is None
    assert result.as_of.tzinfo == timezone.utc
    assert result.source == "MT5_TERMINAL"
    assert not hasattr(result, "total_lot")
    assert terminal.send_calls == 0


@pytest.mark.parametrize("change,message", [
    (lambda t: setattr(t.account, "trade_mode", 2), "LIVE_OR_NON_DEMO_ACCOUNT_BLOCKED"),
    (lambda t: setattr(t.account, "server", "Other-Demo"), "ACCOUNT_IDENTITY_MISMATCH"),
    (lambda t: setattr(t.account, "login", 654321), "ACCOUNT_IDENTITY_MISMATCH"),
    (lambda t: setattr(t.account, "equity", float("nan")), "INVALID_EQUITY"),
    (lambda t: setattr(t.account, "balance", None), "INVALID_BALANCE"),
    (lambda t: setattr(t, "rows", None), "POSITIONS_READ_FAILED"),
    (lambda t: setattr(t.rows[0], "profit", float("inf")), "INVALID_POSITION_PNL"),
    (lambda t: setattr(t.rows[0], "volume", 0.0), "INVALID_POSITION_LOT"),
    (lambda t: setattr(t.rows[0], "type", 8), "INVALID_POSITION_SIDE"),
])
def test_invalid_or_partial_broker_state_fails_closed(change, message):
    terminal = FakeTerminal()
    change(terminal)
    with pytest.raises(RuntimeError, match=message):
        snapshot(terminal)
    assert terminal.send_calls == 0


def test_investor_mode_is_read_only_not_permission_to_trade():
    terminal = FakeTerminal()
    terminal.account.trade_allowed = False
    result = snapshot(terminal)
    assert result.trade_allowed is False
    assert result.positions
    assert terminal.send_calls == 0


def test_missing_account_fails_closed():
    terminal = FakeTerminal()
    terminal.account = None
    with pytest.raises(RuntimeError, match="ACCOUNT_READ_FAILED"):
        snapshot(terminal)


@pytest.mark.parametrize("disconnect", [
    lambda t: setattr(t, "connected", False),
    lambda t: setattr(t, "terminal_info", None),
    lambda t: setattr(t, "terminal_info", lambda: None),
    lambda t: setattr(t, "terminal_info", lambda: NS(connected=None)),
])
def test_no_broker_connection_never_returns_cached_account_data(disconnect):
    terminal = FakeTerminal()
    disconnect(terminal)
    with pytest.raises(RuntimeError, match="TERMINAL_INFO_UNAVAILABLE|BROKER_DISCONNECTED"):
        snapshot(terminal)
    assert terminal.send_calls == 0
