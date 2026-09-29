from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
import tempfile

from src.execution.audit import AppendOnlyAuditLog
from src.execution.mt5_adapter import ExecutionMode, MT5BrokerAdapter
from src.execution.position_controller import PositionActionCoordinator
from src.execution.position_lifecycle import PositionLifecycleManager
from src.execution.position_state import PositionStateStore
from src.execution.safety import SafetySnapshot


class Terminal:
    TRADE_ACTION_DEAL = 1
    TRADE_ACTION_SLTP = 6
    ORDER_TYPE_BUY = 2
    ORDER_TYPE_SELL = 3
    POSITION_TYPE_BUY = 0
    POSITION_TYPE_SELL = 1

    def __init__(self):
        self.account = SimpleNamespace(
            login=123456, server="MetaQuotes-Demo",
            trade_mode=0, trade_allowed=True, trade_expert=True)
        self.contract = SimpleNamespace(
            point=.00001, digits=5, volume_min=.01, volume_max=1.0,
            volume_step=.01, trade_stops_level=10, trade_mode=1
        )
        self.tick = SimpleNamespace(bid=1.1050, ask=1.1052)
        self.position = SimpleNamespace(
            ticket=42, symbol="EURUSD", type=0, volume=.02,
            price_open=1.1, sl=1.09, tp=1.12
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
        return SimpleNamespace(retcode=10009, order=99, comment="ok")


@contextmanager
def paths():
    names = []
    try:
        for _ in range(3):
            handle = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
            path = Path(handle.name)
            handle.close()
            path.unlink(missing_ok=True)
            names.append(path)
        yield names
    finally:
        for path in names:
            path.unlink(missing_ok=True)


def snapshot(**changes):
    values = dict(
        connected=True, data_fresh=True, state_known=True,
        reconciled=True, risk_allowed=True, manual_pause=False
    )
    values.update(changes)
    return SafetySnapshot(**values)


def test_read_only_positions_do_not_require_order_send_permission():
    terminal = Terminal()
    with paths() as db:
        adapter = MT5BrokerAdapter(
            terminal, mode=ExecutionMode.DEMO,
            allow_order_send=False, ledger_path=db[0]
        )
        assert adapter.broker_position_ids() == {"42"}
        adapter.close()


def test_position_state_survives_restart_and_prevents_second_partial():
    terminal = Terminal()
    with paths() as db:
        adapter = MT5BrokerAdapter(
            terminal, mode=ExecutionMode.DEMO,
            allow_order_send=True, ledger_path=db[0]
        )
        position = adapter.positions()[0]
        state = PositionStateStore(db[1])
        audit = AppendOnlyAuditLog(db[2])
        coordinator = PositionActionCoordinator(PositionLifecycleManager(adapter), state, audit)
        coordinator.register(position, "TF-004")

        first = coordinator.partial_close(
            position, snapshot=snapshot(),
            client_order_id="partial-once", fraction=.5
        )
        state.close()

        reopened = PositionStateStore(db[1])
        second_coordinator = PositionActionCoordinator(
            PositionLifecycleManager(adapter), reopened, audit
        )
        second = second_coordinator.partial_close(
            position, snapshot=snapshot(),
            client_order_id="partial-again", fraction=.5
        )

        assert first.status == "FILLED"
        assert second.status == "BLOCKED"
        assert second.reasons == ("PARTIAL_ALREADY_DONE",)
        reopened.close()
        audit.close()
        adapter.close()


def test_manual_pause_or_risk_block_do_not_prevent_risk_reducing_close():
    terminal = Terminal()
    with paths() as db:
        adapter = MT5BrokerAdapter(
            terminal, mode=ExecutionMode.DEMO,
            allow_order_send=True, ledger_path=db[0]
        )
        position = adapter.positions()[0]
        state = PositionStateStore(db[1])
        state.ensure(position.position_id, "TF-004", position.stop_loss)
        coordinator = PositionActionCoordinator(PositionLifecycleManager(adapter), state)

        outcome = coordinator.full_close(
            position,
            snapshot=snapshot(risk_allowed=False, manual_pause=True),
            client_order_id="emergency-close",
        )

        assert outcome.status == "FILLED"
        assert state.get("42").status == "CLOSED"
        state.close()
        adapter.close()


def test_trailing_requires_fresh_reconciled_state():
    terminal = Terminal()
    with paths() as db:
        adapter = MT5BrokerAdapter(
            terminal, mode=ExecutionMode.DEMO,
            allow_order_send=True, ledger_path=db[0]
        )
        position = adapter.positions()[0]
        state = PositionStateStore(db[1])
        state.ensure(position.position_id, "TF-004", position.stop_loss)
        coordinator = PositionActionCoordinator(PositionLifecycleManager(adapter), state)

        stale = coordinator.trail(
            position,
            snapshot=snapshot(data_fresh=False),
            client_order_id="stale-trail",
            candidate_stop=1.101,
        )

        assert stale.status == "BLOCKED"
        assert stale.reasons == ("STALE_DATA",)
        assert len(terminal.sent) == 0
        state.close()
        adapter.close()


def test_reconcile_uses_broker_snapshot_as_source_of_truth():
    with paths() as db:
        state = PositionStateStore(db[1])
        state.ensure("old", "TF-004", 1.0)
        state.reconcile_broker_positions("TF-004", (("new", 1.1),))
        assert state.get("old").status == "CLOSED"
        assert state.get("new").status == "OPEN"
        state.close()
