from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
import tempfile

from src.execution.auto_engine import AutoTradeConfig, DemoAutoTradeEngine
from src.execution.coordinator import ExecutionCoordinator
from src.execution.mt5_adapter import ExecutionMode, MT5BrokerAdapter
from src.execution.position_controller import PositionActionCoordinator
from src.execution.position_lifecycle import ExitMode, PositionLifecycleManager
from src.execution.position_state import PositionStateStore
from src.execution.risk import IndependentRiskEngine, RiskContext, RiskLimits
from src.execution.safety import KillSwitchStore, SafetyGate, SafetySnapshot
from src.rule_engine.types import Bar


class Signal:
    def __init__(self, direction, stop_price):
        self.direction = direction
        self.stop_price = stop_price


class Terminal:
    TRADE_ACTION_DEAL = 1
    TRADE_ACTION_SLTP = 6
    ORDER_TYPE_BUY = 2
    ORDER_TYPE_SELL = 3
    POSITION_TYPE_BUY = 0
    POSITION_TYPE_SELL = 1

    def __init__(self):
        self.account = SimpleNamespace(trade_mode=0, trade_allowed=True, trade_expert=True)
        self.contract = SimpleNamespace(
            point=.00001, digits=5, volume_min=.01, volume_max=1.0,
            volume_step=.01, trade_stops_level=10, trade_mode=1
        )
        self.tick = SimpleNamespace(bid=1.1050, ask=1.1052)
        self.position_records = []
        self.sent = []

    def initialize(self): return True
    def shutdown(self): return None
    def account_info(self): return self.account
    def symbol_info(self, symbol): return self.contract
    def symbol_info_tick(self, symbol): return self.tick
    def positions_get(self, **kwargs): return tuple(self.position_records)
    def order_check(self, request): return SimpleNamespace(retcode=0, comment="ok")
    def order_send(self, request):
        self.sent.append(dict(request))
        return SimpleNamespace(retcode=10009, order=700, comment="ok")


@contextmanager
def dbs():
    paths = []
    try:
        for _ in range(3):
            handle = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
            path = Path(handle.name)
            handle.close()
            path.unlink(missing_ok=True)
            paths.append(path)
        yield paths
    finally:
        for path in paths:
            path.unlink(missing_ok=True)


def bars(n=25, last_low=1.1030, last_high=1.1070, last_close=1.1060):
    result = []
    for i in range(n - 1):
        result.append(Bar(str(i), 1.1, 1.1040, 1.1020, 1.1030, 100, True))
    result.append(Bar(str(n - 1), 1.1050, last_high, last_low, last_close, 100, True))
    return result


def snapshot(**changes):
    values = dict(
        connected=True, data_fresh=True, state_known=True,
        reconciled=True, risk_allowed=True, manual_pause=False
    )
    values.update(changes)
    return SafetySnapshot(**values)


def build(terminal, db, exit_mode=ExitMode.TRAILING_ONLY, signal=None):
    adapter = MT5BrokerAdapter(
        terminal, mode=ExecutionMode.DEMO,
        allow_order_send=True, ledger_path=db[0]
    )
    kill = KillSwitchStore(db[1])
    kill.deactivate("test")
    risk = IndependentRiskEngine(RiskLimits(.01, 1, 20, 100))
    entry = ExecutionCoordinator(adapter, SafetyGate(kill), risk_engine=risk)
    state = PositionStateStore(db[2])
    controller = PositionActionCoordinator(PositionLifecycleManager(adapter), state)
    engine = DemoAutoTradeEngine(
        config=AutoTradeConfig(
            "TF-X", "EURUSD", exit_mode=exit_mode, trailing_lookback=3
        ),
        adapter=adapter,
        entry=entry,
        positions=controller,
        state=state,
        signal_evaluator=lambda history: signal,
    )
    return engine, adapter, kill, state


def test_closed_bar_signal_enters_demo_with_stop_and_no_fixed_tp_for_trailing():
    terminal = Terminal()
    with dbs() as db:
        engine, adapter, kill, state = build(
            terminal, db, ExitMode.TRAILING_ONLY, Signal("UP", 1.09)
        )
        outcome = engine.on_closed_bar(
            bars(), bid=1.1050, ask=1.1052,
            snapshot=snapshot(), risk_context=RiskContext(0, 10, 0)
        )
        assert outcome.status == "FILLED"
        assert terminal.sent[0]["sl"] == 1.09
        assert "tp" not in terminal.sent[0]
        assert terminal.sent[0]["magic"] == 260926
        adapter.close()
        kill.close()
        state.close()


def test_manual_pause_blocks_new_entry():
    terminal = Terminal()
    with dbs() as db:
        engine, adapter, kill, state = build(
            terminal, db, ExitMode.TRAILING_ONLY, Signal("UP", 1.09)
        )
        outcome = engine.on_closed_bar(
            bars(), bid=1.1050, ask=1.1052,
            snapshot=snapshot(manual_pause=True), risk_context=RiskContext(0, 10, 0)
        )
        assert outcome.status == "GATE_BLOCKED"
        assert len(terminal.sent) == 0
        adapter.close()
        kill.close()
        state.close()


def test_existing_own_position_is_managed_instead_of_opening_second_position():
    terminal = Terminal()
    terminal.position_records = [
        SimpleNamespace(
            ticket=42, symbol="EURUSD", type=0, volume=.02,
            price_open=1.1, sl=1.09, tp=0.0, magic=260926, comment="AI"
        )
    ]
    with dbs() as db:
        engine, adapter, kill, state = build(
            terminal, db, ExitMode.TRAILING_ONLY, Signal("UP", 1.09)
        )
        outcome = engine.on_closed_bar(
            bars(), bid=1.1050, ask=1.1052,
            snapshot=snapshot(), risk_context=RiskContext(1, 10, 0)
        )
        assert outcome.status == "FILLED"
        assert len(terminal.sent) == 1
        assert terminal.sent[0]["action"] == terminal.TRADE_ACTION_SLTP
        adapter.close()
        kill.close()
        state.close()


def test_partial_then_trail_closes_half_and_removes_target():
    terminal = Terminal()
    terminal.position_records = [
        SimpleNamespace(
            ticket=42, symbol="EURUSD", type=0, volume=.02,
            price_open=1.1, sl=1.09, tp=1.11, magic=260926, comment="AI"
        )
    ]
    with dbs() as db:
        engine, adapter, kill, state = build(
            terminal, db, ExitMode.PARTIAL_THEN_TRAIL, None
        )
        outcome = engine.on_closed_bar(
            bars(last_high=1.115, last_low=1.103, last_close=1.112),
            bid=1.112, ask=1.1122,
            snapshot=snapshot(), risk_context=RiskContext(1, 10, 0)
        )
        assert outcome.status == "FILLED"
        assert terminal.sent[0]["action"] == terminal.TRADE_ACTION_DEAL
        assert terminal.sent[0]["volume"] == .01
        assert terminal.sent[1]["action"] == terminal.TRADE_ACTION_SLTP
        assert terminal.sent[1]["tp"] == 0.0
        assert state.get("42").partial_done
        adapter.close()
        kill.close()
        state.close()
