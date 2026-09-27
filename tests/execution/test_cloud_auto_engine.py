import asyncio
from contextlib import contextmanager
from pathlib import Path
import tempfile

from src.execution.cloud_auto_engine import (
    CloudAutoTradeConfig,
    CloudAutoTradeEngine,
)
from src.execution.mt5_adapter import MT5OrderResult, MT5Position
from src.execution.position_lifecycle import ExitMode
from src.execution.position_state import PositionStateStore
from src.execution.risk import IndependentRiskEngine, RiskContext, RiskLimits
from src.execution.safety import KillSwitchStore, SafetyGate, SafetySnapshot
from src.rule_engine.types import Bar


class Signal:
    direction = "UP"
    stop_price = 1.09


class FakeCloudAdapter:
    def __init__(self, position=None, partial_representable=True):
        self.position = position
        self.partial_representable = partial_representable
        self.submit_calls = []
        self.modify_calls = []
        self.close_calls = []

    async def positions(self, symbol=None):
        if self.position is None:
            return ()
        if symbol is not None and self.position.symbol != symbol:
            return ()
        return (self.position,)

    async def submit(self, order):
        self.submit_calls.append(order)
        return MT5OrderResult(order.client_order_id, "FILLED", "42", 10009)

    async def normalize_partial_volume(self, position, fraction):
        if not self.partial_representable:
            raise ValueError("PARTIAL_VOLUME_NOT_REPRESENTABLE")
        return 0.01

    async def modify_position(self, position_id, **kwargs):
        self.modify_calls.append((position_id, kwargs))
        return MT5OrderResult(kwargs["client_order_id"], "FILLED", position_id, 10009)

    async def close_position(self, position_id, **kwargs):
        self.close_calls.append((position_id, kwargs))
        return MT5OrderResult(kwargs["client_order_id"], "FILLED", position_id, 10009)


@contextmanager
def stores():
    paths = []
    try:
        for _ in range(2):
            h = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
            path = Path(h.name)
            h.close()
            path.unlink(missing_ok=True)
            paths.append(path)
        kill = KillSwitchStore(paths[0])
        kill.deactivate("test")
        state = PositionStateStore(paths[1])
        yield kill, state
        state.close()
        kill.close()
    finally:
        for path in paths:
            path.unlink(missing_ok=True)


def snapshot(**changes):
    values = dict(
        connected=True,
        data_fresh=True,
        state_known=True,
        reconciled=True,
        risk_allowed=True,
        manual_pause=False,
    )
    values.update(changes)
    return SafetySnapshot(**values)


def bars(target_hit=False):
    out = []
    for i in range(25):
        out.append(Bar(str(i), 1.10, 1.106, 1.099, 1.104, 100, True))
    if target_hit:
        out[-1] = Bar("24", 1.105, 1.121, 1.103, 1.115, 100, True)
    return out


def risk_context(open_positions=0, volume=0.0):
    return RiskContext(
        open_positions=open_positions,
        spread_points=5,
        daily_loss=0,
        current_symbol_volume=volume,
    )


def run(coro):
    return asyncio.run(coro)


def build(adapter, kill, state, exit_mode=ExitMode.TRAILING_ONLY):
    return CloudAutoTradeEngine(
        config=CloudAutoTradeConfig(
            "TF-CLOUD",
            "EURUSD",
            exit_mode=exit_mode,
            trailing_lookback=20,
        ),
        adapter=adapter,
        gate=SafetyGate(kill),
        risk_engine=IndependentRiskEngine(
            RiskLimits(.01, 1, 30, 10, max_total_volume_per_symbol=.01)
        ),
        state=state,
        signal_evaluator=lambda history: Signal(),
    )


def test_cloud_entry_is_blocked_by_manual_pause_before_broker_call():
    with stores() as (kill, state):
        adapter = FakeCloudAdapter()
        engine = build(adapter, kill, state)
        result = run(
            engine.on_closed_bar(
                bars(),
                bid=1.1050,
                ask=1.1052,
                snapshot=snapshot(manual_pause=True),
                risk_context=risk_context(),
            )
        )
        assert result.status == "GATE_BLOCKED"
        assert adapter.submit_calls == []


def test_unrepresentable_partial_switches_to_trailing_instead_of_crashing():
    position = MT5Position(
        "42", "EURUSD", "UP", .01, 1.10, 1.09, 1.11, 260927, "AI"
    )
    with stores() as (kill, state):
        adapter = FakeCloudAdapter(position, partial_representable=False)
        engine = build(adapter, kill, state, ExitMode.PARTIAL_THEN_TRAIL)
        result = run(
            engine.on_closed_bar(
                bars(target_hit=True),
                bid=1.115,
                ask=1.1152,
                snapshot=snapshot(),
                risk_context=risk_context(1, .01),
            )
        )
        assert result.status == "FILLED"
        assert result.detail == "PARTIAL_UNAVAILABLE_SWITCHED_TO_TRAILING"
        assert adapter.close_calls == []
        assert len(adapter.modify_calls) == 1
        assert adapter.modify_calls[0][1]["take_profit"] is None
        assert state.get("42").partial_done


def test_cloud_broker_snapshot_closes_stale_local_position_state():
    with stores() as (kill, state):
        state.ensure("old", "TF-CLOUD", 1.0)
        adapter = FakeCloudAdapter()
        engine = build(adapter, kill, state)
        assert run(engine.reconcile_owned_positions()) == ()
        assert state.get("old").status == "CLOSED"
