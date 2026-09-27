"""Autonomous DEMO engine: closed bar -> signal -> guarded entry/position action."""

from dataclasses import dataclass
import hashlib
from collections.abc import Callable, Sequence

from src.execution.coordinator import ExecutionCoordinator, ExecutionOutcome
from src.execution.mt5_adapter import MT5BrokerAdapter, MT5OrderRequest, MT5Position
from src.execution.position_controller import PositionActionCoordinator
from src.execution.position_lifecycle import ExitMode, LifecyclePlan, PositionLifecycleManager
from src.execution.position_policy import PositionAction, evaluate_position
from src.execution.position_state import PositionStateStore
from src.execution.risk import RiskContext
from src.execution.safety import SafetySnapshot
from src.rule_engine.types import Bar


@dataclass(frozen=True)
class AutoTradeConfig:
    strategy_id: str
    symbol: str
    magic: int = 260926
    demo_volume: float = 0.01
    reward_risk: float = 1.5
    exit_mode: ExitMode = ExitMode.TRAILING_ONLY
    trailing_lookback: int = 20
    partial_fraction: float = 0.5
    max_pyramid_adds: int = 0

    def __post_init__(self) -> None:
        if not self.strategy_id.strip() or not self.symbol.strip():
            raise ValueError("strategy_id and symbol are required")
        if not 0 < self.demo_volume <= 0.01:
            raise ValueError("DEMO volume must be in (0, 0.01]")
        if self.reward_risk <= 0:
            raise ValueError("reward_risk must be positive")


@dataclass(frozen=True)
class AutoTradeOutcome:
    status: str
    detail: str = ""


class DemoAutoTradeEngine:
    """DEMO-only autonomous orchestration. LIVE unlocking is outside this class."""

    def __init__(
        self,
        *,
        config: AutoTradeConfig,
        adapter: MT5BrokerAdapter,
        entry: ExecutionCoordinator,
        positions: PositionActionCoordinator,
        state: PositionStateStore,
        signal_evaluator: Callable[[Sequence[Bar]], object | None],
    ):
        self.config = config
        self.adapter = adapter
        self.entry = entry
        self.positions = positions
        self.state = state
        self.signal_evaluator = signal_evaluator
        self.plan = LifecyclePlan(
            exit_mode=config.exit_mode,
            partial_fraction=config.partial_fraction,
            max_pyramid_adds=config.max_pyramid_adds,
            trailing_lookback=config.trailing_lookback,
        )

    def on_closed_bar(
        self,
        bars: Sequence[Bar],
        *,
        bid: float,
        ask: float,
        snapshot: SafetySnapshot,
        risk_context: RiskContext,
    ) -> AutoTradeOutcome:
        if not bars or not bars[-1].closed:
            return AutoTradeOutcome("NO_ACTION", "BAR_NOT_CLOSED")

        ours = tuple(
            position
            for position in self.adapter.positions(self.config.symbol)
            if position.magic == self.config.magic
        )
        if len(ours) > 1:
            return AutoTradeOutcome("NO_ACTION", "MULTIPLE_OWN_POSITIONS")
        if ours:
            return self._manage(ours[0], bars, snapshot, risk_context, bid, ask)

        signal = self.signal_evaluator(bars)
        if signal is None:
            return AutoTradeOutcome("NO_ACTION", "NO_SIGNAL")
        direction = str(getattr(signal, "direction")).upper()
        stop = float(getattr(signal, "stop_price"))
        price = ask if direction == "UP" else bid
        target = self._target(direction, price, stop)
        client_id = self._intent_id("ENTRY", bars[-1].timestamp, direction)
        order = MT5OrderRequest(
            client_id,
            self.config.symbol,
            direction,
            self.config.demo_volume,
            price,
            stop_loss=stop,
            take_profit=target,
            magic=self.config.magic,
        )
        result: ExecutionOutcome = self.entry.submit(order, snapshot, risk_context)
        return AutoTradeOutcome(result.status, client_id)

    def reconcile_owned_positions(self) -> tuple[MT5Position, ...]:
        ours = tuple(
            position
            for position in self.adapter.positions(self.config.symbol)
            if position.magic == self.config.magic
        )
        self.state.reconcile_broker_positions(
            self.config.strategy_id,
            tuple((position.position_id, position.stop_loss) for position in ours),
        )
        return ours

    def _manage(
        self,
        position: MT5Position,
        bars: Sequence[Bar],
        snapshot: SafetySnapshot,
        risk_context: RiskContext,
        bid: float,
        ask: float,
    ) -> AutoTradeOutcome:
        state = self.state.get(position.position_id)
        if state is None:
            self.positions.register(position, self.config.strategy_id)
            state = self.state.get(position.position_id)
            assert state is not None
        instruction = evaluate_position(position, bars, self.plan, state)
        action = instruction.action
        stamp = bars[-1].timestamp
        if action == PositionAction.HOLD:
            pyramid = self._maybe_pyramid(
                position, bars, snapshot, risk_context, bid, ask, state
            )
            if pyramid is not None:
                return pyramid
            return AutoTradeOutcome("HOLD", instruction.reason)
        if action == PositionAction.TRAIL_STOP:
            result = self.positions.trail(
                position,
                snapshot=snapshot,
                client_order_id=self._intent_id("TRAIL", stamp, position.position_id),
                candidate_stop=float(instruction.candidate_stop),
            )
            return AutoTradeOutcome(result.status, instruction.reason)
        if action == PositionAction.PARTIAL_CLOSE:
            try:
                result = self.positions.partial_close(
                    position,
                    snapshot=snapshot,
                    client_order_id=self._intent_id("PARTIAL", stamp, position.position_id),
                    fraction=float(instruction.partial_fraction),
                )
            except ValueError as exc:
                if str(exc) != "PARTIAL_VOLUME_NOT_REPRESENTABLE":
                    raise
                if position.stop_loss is None:
                    return AutoTradeOutcome("BLOCKED", "PARTIAL_UNAVAILABLE_AND_NO_PROTECTIVE_STOP")
                fallback = self.adapter.modify_position(
                    position.position_id,
                    client_order_id=self._intent_id("PARTIAL_FALLBACK_TRAIL", stamp, position.position_id),
                    stop_loss=float(position.stop_loss),
                    take_profit=None,
                )
                if fallback.status in {"FILLED", "PARTIAL"}:
                    self.state.mark_partial_done(position.position_id)
                return AutoTradeOutcome(fallback.status, "PARTIAL_UNAVAILABLE_SWITCHED_TO_TRAILING")
            if result.status in {"FILLED", "PARTIAL"}:
                self.adapter.modify_position(
                    position.position_id,
                    client_order_id=self._intent_id("DROP_TP", stamp, position.position_id),
                    stop_loss=float(position.stop_loss),
                    take_profit=None,
                )
            return AutoTradeOutcome(result.status, instruction.reason)
        result = self.positions.full_close(
            position,
            snapshot=snapshot,
            client_order_id=self._intent_id("CLOSE", stamp, position.position_id),
        )
        return AutoTradeOutcome(result.status, instruction.reason)

    def _maybe_pyramid(
        self,
        position: MT5Position,
        bars: Sequence[Bar],
        snapshot: SafetySnapshot,
        risk_context: RiskContext,
        bid: float,
        ask: float,
        state,
    ) -> AutoTradeOutcome | None:
        if self.config.max_pyramid_adds <= 0:
            return None
        signal = self.signal_evaluator(bars)
        if signal is None or str(getattr(signal, "direction")).upper() != position.direction:
            return None
        market_price = bid if position.direction == "UP" else ask
        decision = PositionLifecycleManager.pyramid_decision(
            position,
            market_price=market_price,
            current_adds=state.pyramid_adds,
            max_adds=self.config.max_pyramid_adds,
            independent_risk_allowed=snapshot.risk_allowed,
        )
        if not decision.allowed:
            return None
        stop = float(getattr(signal, "stop_price"))
        target = self._target(position.direction, market_price, stop)
        client_id = self._intent_id(
            "PYRAMID", bars[-1].timestamp, str(state.pyramid_adds + 1)
        )
        context = RiskContext(
            open_positions=risk_context.open_positions,
            spread_points=risk_context.spread_points,
            daily_loss=risk_context.daily_loss,
            current_symbol_volume=position.volume,
            increases_existing_position=True,
        )
        order = MT5OrderRequest(
            client_id,
            self.config.symbol,
            position.direction,
            self.config.demo_volume,
            market_price,
            stop_loss=stop,
            take_profit=target,
            magic=self.config.magic,
        )
        result = self.entry.submit(order, snapshot, context)
        if result.status in {"FILLED", "PARTIAL"}:
            self.state.record_pyramid_add(position.position_id)
        return AutoTradeOutcome(result.status, decision.reason)

    def _target(self, direction: str, entry: float, stop: float) -> float | None:
        if self.config.exit_mode == ExitMode.TRAILING_ONLY:
            return None
        risk = abs(entry - stop)
        if risk <= 0:
            raise ValueError("stop must differ from entry")
        if direction == "UP":
            return entry + risk * self.config.reward_risk
        return entry - risk * self.config.reward_risk

    def _intent_id(self, action: str, stamp: str, suffix: str) -> str:
        raw = f"{self.config.strategy_id}|{self.config.symbol}|{action}|{stamp}|{suffix}"
        return "AI-" + hashlib.sha256(raw.encode()).hexdigest()[:24]
