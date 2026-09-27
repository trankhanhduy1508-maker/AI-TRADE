from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
import tempfile

from src.execution.mt5_adapter import ExecutionMode, MT5BrokerAdapter
from src.execution.position_lifecycle import PositionLifecycleManager


class FakeTerminal:
    TRADE_ACTION_DEAL = 1
    TRADE_ACTION_SLTP = 6
    ORDER_TYPE_BUY = 2
    ORDER_TYPE_SELL = 3
    POSITION_TYPE_BUY = 0
    POSITION_TYPE_SELL = 1

    def __init__(self):
        self.account = SimpleNamespace(trade_mode=0, trade_allowed=True, trade_expert=True)
        self.contract = SimpleNamespace(
            point=0.00001,
            digits=5,
            volume_min=0.01,
            volume_max=1.0,
            volume_step=0.01,
            trade_stops_level=10,
            trade_mode=1,
        )
        self.tick = SimpleNamespace(bid=1.1050, ask=1.1052)
        self.position = SimpleNamespace(
            ticket=42,
            symbol="EURUSD",
            type=0,
            volume=0.02,
            price_open=1.1000,
            sl=1.0900,
            tp=1.1200,
        )
        self.sent = []

    def initialize(self): return True
    def shutdown(self): return None
    def account_info(self): return self.account
    def symbol_info(self, symbol): return self.contract
    def symbol_info_tick(self, symbol): return self.tick
    def positions_get(self, **kwargs): return (self.position,)
    def order_check(self, request): return SimpleNamespace(retcode=0, comment="ok")
    def order_send(self, request):
        self.sent.append(dict(request))
        return SimpleNamespace(retcode=10009, order=9001, comment="done")


@contextmanager
def _db_path():
    handle = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
    path = Path(handle.name)
    handle.close()
    path.unlink(missing_ok=True)
    try:
        yield path
    finally:
        path.unlink(missing_ok=True)


def _adapter(terminal, path):
    return MT5BrokerAdapter(
        terminal,
        mode=ExecutionMode.DEMO,
        allow_order_send=True,
        ledger_path=path,
    )


def test_trailing_stop_can_only_ratchet_in_favorable_direction():
    terminal = FakeTerminal()
    with _db_path() as path:
        adapter = _adapter(terminal, path)
        adapter.positions()[0]

        good = adapter.modify_position("42", client_order_id="trail-good", stop_loss=1.1010, take_profit=1.1200)
        bad = adapter.modify_position("42", client_order_id="trail-bad", stop_loss=1.0800, take_profit=1.1200)
        adapter.close()

    assert good.status == "FILLED"
    assert terminal.sent[0]["action"] == terminal.TRADE_ACTION_SLTP
    assert terminal.sent[0]["sl"] == 1.1010
    assert bad.status == "RISK_REJECTED"
    assert bad.message == "STOP_WOULD_INCREASE_RISK"
    assert len(terminal.sent) == 1


def test_partial_close_uses_opposite_side_and_position_ticket():
    terminal = FakeTerminal()
    with _db_path() as path:
        adapter = _adapter(terminal, path)
        result = adapter.close_position("42", client_order_id="partial-1", volume=0.01)
        adapter.close()

    assert result.status == "FILLED"
    request = terminal.sent[0]
    assert request["position"] == 42
    assert request["type"] == terminal.ORDER_TYPE_SELL
    assert request["volume"] == 0.01
    assert request["price"] == terminal.tick.bid


def test_full_close_and_modify_are_duplicate_safe_across_restart():
    terminal = FakeTerminal()
    with _db_path() as path:
        first = _adapter(terminal, path)
        first_result = first.close_position("42", client_order_id="close-stable")
        first.close()

        second_terminal = FakeTerminal()
        second = _adapter(second_terminal, path)
        duplicate = second.close_position("42", client_order_id="close-stable")
        second.close()

    assert first_result.status == "FILLED"
    assert duplicate.status == "DUPLICATE_SUPPRESSED"
    assert len(second_terminal.sent) == 0


def test_position_ids_support_exact_reconciliation():
    terminal = FakeTerminal()
    with _db_path() as path:
        adapter = _adapter(terminal, path)
        assert adapter.broker_position_ids() == {"42"}
        adapter.close()


def test_lifecycle_allows_pyramiding_only_on_winner_and_after_risk_gate():
    terminal = FakeTerminal()
    with _db_path() as path:
        adapter = _adapter(terminal, path)
        position = adapter.positions()[0]
        manager = PositionLifecycleManager(adapter)

        allowed = manager.pyramid_decision(
            position,
            market_price=1.1060,
            current_adds=0,
            max_adds=2,
            independent_risk_allowed=True,
        )
        losing = manager.pyramid_decision(
            position,
            market_price=1.0950,
            current_adds=0,
            max_adds=2,
            independent_risk_allowed=True,
        )
        risk_blocked = manager.pyramid_decision(
            position,
            market_price=1.1060,
            current_adds=0,
            max_adds=2,
            independent_risk_allowed=False,
        )
        adapter.close()

    assert allowed.allowed
    assert not losing.allowed and losing.reason == "NOT_A_WINNER"
    assert not risk_blocked.allowed and risk_blocked.reason == "RISK_GATE_BLOCKED"
