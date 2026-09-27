"""Autonomous async execution engine for MetaApi-hosted MT5 DEMO accounts."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from collections.abc import Callable, Sequence

from src.execution.metaapi_cloud import MetaApiCloudAdapter
from src.execution.mt5_adapter import MT5OrderRequest, MT5Position
from src.execution.position_lifecycle import ExitMode, LifecyclePlan, PositionLifecycleManager
from src.execution.position_policy import PositionAction, evaluate_position
from src.execution.position_state import PositionStateStore
from src.execution.risk import IndependentRiskEngine, RiskContext
from src.execution.safety import SafetyGate, SafetySnapshot
from src.rule_engine.types import Bar


@dataclass(frozen=True)
class CloudAutoTradeConfig:
    strategy_id: str
    symbol: str
    magic: int = 260927
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
class CloudAutoTradeOutcome:
    status: str
    detail: str = ""


class CloudAutoTradeEngine:
    def __init__(
        self,
        *,
        config: CloudAutoTradeConfig,
        adapter: MetaApiCloudAdapter,
        gate: SafetyGate,
        risk_engine: IndependentRiskEngine,
        state: PositionStateStore,
        signal_evaluator: Callable[[Sequence[Bar]], object | None],
    ):
        self.config = config
        self.adapter = adapter
        self.gate = gate
        self.risk_engine = risk_engine
        self.state = state
        self.signal_evaluator = signal_evaluator
        self.plan = LifecyclePlan(
            exit_mode=config.exit_mode,
            partial_fraction=config.partial_fraction,
            max_pyramid_adds=config.max_pyramid_adds,
            trailing_lookback=config.trailing_lookback,
        )

    async def reconcile_owned_positions(self) -> tuple[MT5Position, ...]:
        ours = tuple(
            position
            for position in await self.adapter.positions(self.config.symbol)
            if position.magic == self.config.magic
        )
        self.state.reconcile_broker_positions(
            self.config.strategy_id,
            tuple((position.position_id, position.stop_loss) for position in ours),
        )
        return ours

    async def on_closed_bar(
        self,
        bars: Sequence[Bar],
        *,
        bid: float,
        ask: float,
        snapshot: SafetySnapshot,
        risk_context: RiskContext,
    ) -> CloudAutoTradeOutcome:
        if not bars or not bars[-1].closed:
            return CloudAutoTradeOutcome("NO_ACTION", "BAR_NOT_CLOSED")
        own = await self.reconcile_owned_positions()
        if len(own) > 1:
            return CloudAutoTradeOutcome("NO_ACTION", "MULTIPLE_OWN_POSITIONS")
        if own:
            return await self._manage(own[0], bars, snapshot, risk_context, bid, ask)

        signal = self.signal_evaluator(bars)
        if signal is None:
            return CloudAutoTradeOutcome("NO_ACTION", "NO_SIGNAL")
        direction = str(getattr(signal, "direction")).upper()
        stop = float(getattr(signal, "stop_price"))
        price = ask if direction == "UP" else bid
        target = self._target(direction, price, stop)
        order = MT5OrderRequest(
            self._intent_id("ENTRY", bars[-1].timestamp, direction),
            self.config.symbol,
            direction,
            self.config.demo_volume,
            price,
            stop,
            target,
            self.config.magic,
        )
        return await self._submit_guarded(order, snapshot, risk_context)

    async def _manage(
        self,
        position: MT5Position,
        bars: Sequence[Bar],
        snapshot: SafetySnapshot,
        risk_context: RiskContext,
        bid: float,
        ask: float,
    ) -> CloudAutoTradeOutcome:
        state = self.state.get(position.position_id)
        if state is None:
            state = self.state.ensure(
                position.position_id, self.config.strategy_id, position.stop_loss
            )
        instruction = evaluate_position(position, bars, self.plan, state)
        stamp = bars[-1].timestamp

        if instruction.action == PositionAction.HOLD:
            pyramid = await self._maybe_pyramid(
                position, bars, snapshot, risk_context, bid, ask, state.pyramid_adds
            )
            if pyramid is not None:
                return pyramid
            return CloudAutoTradeOutcome("HOLD", instruction.reason)

        reasons = self._risk_reduction_blockers(
            snapshot,
            require_fresh_data=instruction.action == PositionAction.TRAIL_STOP,
        )
        if reasons:
            return CloudAutoTradeOutcome("BLOCKED", ",".join(reasons))

        if instruction.action == PositionAction.TRAIL_STOP:
            result = await self.adapter.modify_position(
                position.position_id,
                client_order_id=self._intent_id("TRAIL", stamp, position.position_id),
                stop_loss=float(instruction.candidate_stop),
                take_profit=position.take_profit,
            )
            if result.status in {"FILLED", "PARTIAL"}:
                self.state.record_stop(position.position_id, float(instruction.candidate_stop))
            return CloudAutoTradeOutcome(result.status, instruction.reason)

        if instruction.action == PositionAction.PARTIAL_CLOSE:
            try:
                volume = await self.adapter.normalize_partial_volume(
                    position, float(instruction.partial_fraction)
                )
            except ValueError as exc:
                if str(exc) != "PARTIAL_VOLUME_NOT_REPRESENTABLE":
                    raise
                if position.stop_loss is None:
                    return CloudAutoTradeOutcome(
                        "BLOCKED", "PARTIAL_UNAVAILABLE_AND_NO_PROTECTIVE_STOP"
                    )
                fallback = await self.adapter.modify_position(
                    position.position_id,
                    client_order_id=self._intent_id(
                        "PARTIAL_FALLBACK_TRAIL", stamp, position.position_id
                    ),
                    stop_loss=float(position.stop_loss),
                    take_profit=None,
                )
                if fallback.status in {"FILLED", "PARTIAL"}:
                    self.state.mark_partial_done(position.position_id)
                return CloudAutoTradeOutcome(
                    fallback.status, "PARTIAL_UNAVAILABLE_SWITCHED_TO_TRAILING"
                )
            result = await self.adapter.close_position(
                position.position_id,
                client_order_id=self._intent_id("PARTIAL", stamp, position.position_id),
                volume=volume,
            )
            if result.status in {"FILLED", "PARTIAL"}:
                self.state.mark_partial_done(position.position_id)
                await self.adapter.modify_position(
                    position.position_id,
                    client_order_id=self._intent_id("DROP_TP", stamp, position.position_id),
                    stop_loss=float(position.stop_loss),
                    take_profit=None,
                )
            return CloudAutoTradeOutcome(result.status, instruction.reason)

        result = await self.adapter.close_position(
            position.position_id,
            client_order_id=self._intent_id("CLOSE", stamp, position.position_id),
        )
        if result.status in {"FILLED", "PARTIAL"}:
            self.state.mark_closed(position.position_id)
        return CloudAutoTradeOutcome(result.status, instruction.reason)

    async def _maybe_pyramid(
        self,
        position: MT5Position,
        bars: Sequence[Bar],
        snapshot: SafetySnapshot,
        risk_context: RiskContext,
        bid: float,
        ask: float,
        current_adds: int,
    ) -> CloudAutoTradeOutcome | None:
        if self.config.max_pyramid_adds <= 0:
            return None
        signal = self.signal_evaluator(bars)
        if signal is None or str(getattr(signal, "direction")).upper() != position.direction:
            return None
        market_price = bid if position.direction == "UP" else ask
        decision = PositionLifecycleManager.pyramid_decision(
            position,
            market_price=market_price,
            current_adds=current_adds,
            max_adds=self.config.max_pyramid_adds,
            independent_risk_allowed=snapshot.risk_allowed,
        )
        if not decision.allowed:
            return None

        stop = float(getattr(signal, "stop_price"))
        target = self._target(position.direction, market_price, stop)
        order = MT5OrderRequest(
            self._intent_id("PYRAMID", bars[-1].timestamp, str(current_adds + 1)),
            self.config.symbol,
            position.direction,
            self.config.demo_volume,
            market_price,
            stop,
            target,
            self.config.magic,
        )
        add_context = RiskContext(
            open_positions=risk_context.open_positions,
            spread_points=risk_context.spread_points,
            daily_loss=risk_context.daily_loss,
            current_symbol_volume=position.volume,
            increases_existing_position=True,
        )
        outcome = await self._submit_guarded(order, snapshot, add_context)
        if outcome.status in {"FILLED", "PARTIAL"}:
            self.state.record_pyramid_add(position.position_id)
        return outcome

    async def _submit_guarded(
        self,
        order: MT5OrderRequest,
        snapshot: SafetySnapshot,
        context: RiskContext,
    ) -> CloudAutoTradeOutcome:
        gate = self.gate.evaluate(snapshot)
        if not gate.allowed:
            return CloudAutoTradeOutcome("GATE_BLOCKED", ",".join(gate.reasons))
        decision = self.risk_engine.evaluate(order, context)
        if not decision.allowed:
            return CloudAutoTradeOutcome("RISK_BLOCKED", ",".join(decision.reasons))
        result = await self.adapter.submit(order)
        return CloudAutoTradeOutcome(result.status, order.client_order_id)

    @staticmethod
    def _risk_reduction_blockers(
        snapshot: SafetySnapshot, *, require_fresh_data: bool
    ) -> tuple[str, ...]:
        reasons: list[str] = []
        if not snapshot.connected:
            reasons.append("METAAPI_DISCONNECTED")
        if not snapshot.state_known:
            reasons.append("UNKNOWN_STATE")
        if not snapshot.reconciled:
            reasons.append("UNRECONCILED_POSITIONS")
        if require_fresh_data and not snapshot.data_fresh:
            reasons.append("STALE_DATA")
        return tuple(reasons)

    def _target(self, direction: str, entry: float, stop: float) -> float | None:
        if self.config.exit_mode == ExitMode.TRAILING_ONLY:
            return None
        risk = abs(entry - stop)
        if risk <= 0:
            raise ValueError("stop must differ from entry")
        return (
            entry + risk * self.config.reward_risk
            if direction == "UP"
            else entry - risk * self.config.reward_risk
        )

    def _intent_id(self, action: str, stamp: str, suffix: str) -> str:
        raw = f"{self.config.strategy_id}|{self.config.symbol}|{action}|{stamp}|{suffix}"
        return "AI" + hashlib.sha256(raw.encode()).hexdigest()[:20]
