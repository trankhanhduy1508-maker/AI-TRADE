"""Safety-aware broker position actions and persistent lifecycle bookkeeping."""

from dataclasses import dataclass

from src.execution.audit import AppendOnlyAuditLog, AuditEvent
from src.execution.mt5_adapter import MT5OrderResult, MT5Position
from src.execution.position_lifecycle import PositionLifecycleManager
from src.execution.position_state import PositionStateStore
from src.execution.safety import SafetySnapshot


@dataclass(frozen=True)
class PositionActionOutcome:
    status: str
    reasons: tuple[str, ...] = ()
    broker_result: MT5OrderResult | None = None


class PositionActionCoordinator:
    """Allow risk reduction under kill/manual pause, but never on unknown state."""

    def __init__(
        self,
        lifecycle: PositionLifecycleManager,
        state: PositionStateStore,
        audit_log: AppendOnlyAuditLog | None = None,
    ):
        self._lifecycle = lifecycle
        self._state = state
        self._audit = audit_log

    @staticmethod
    def _reduction_reasons(snapshot: SafetySnapshot, *, require_fresh_data: bool) -> tuple[str, ...]:
        reasons: list[str] = []
        if not snapshot.connected:
            reasons.append("MT5_DISCONNECTED")
        if not snapshot.state_known:
            reasons.append("UNKNOWN_STATE")
        if not snapshot.reconciled:
            reasons.append("UNRECONCILED_POSITIONS")
        if require_fresh_data and not snapshot.data_fresh:
            reasons.append("STALE_DATA")
        return tuple(reasons)

    def register(self, position: MT5Position, strategy_id: str) -> None:
        self._state.ensure(position.position_id, strategy_id, position.stop_loss)

    def trail(
        self,
        position: MT5Position,
        *,
        snapshot: SafetySnapshot,
        client_order_id: str,
        candidate_stop: float,
    ) -> PositionActionOutcome:
        reasons = self._reduction_reasons(snapshot, require_fresh_data=True)
        if reasons:
            return self._blocked("trail_blocked", client_order_id, reasons)
        result = self._lifecycle.trail_stop(
            position,
            client_order_id=client_order_id,
            candidate_stop=candidate_stop,
        )
        if result.status in {"FILLED", "PARTIAL"}:
            self._state.record_stop(position.position_id, candidate_stop)
        return self._record("trail_stop", client_order_id, result)

    def partial_close(
        self,
        position: MT5Position,
        *,
        snapshot: SafetySnapshot,
        client_order_id: str,
        fraction: float,
    ) -> PositionActionOutcome:
        reasons = self._reduction_reasons(snapshot, require_fresh_data=False)
        if reasons:
            return self._blocked("partial_close_blocked", client_order_id, reasons)
        state = self._state.get(position.position_id)
        if state is None:
            return self._blocked("partial_close_blocked", client_order_id, ("POSITION_STATE_MISSING",))
        if state.partial_done:
            return self._blocked("partial_close_blocked", client_order_id, ("PARTIAL_ALREADY_DONE",))
        result = self._lifecycle.partial_close(
            position,
            client_order_id=client_order_id,
            fraction=fraction,
        )
        if result.status in {"FILLED", "PARTIAL"}:
            self._state.mark_partial_done(position.position_id)
        return self._record("partial_close", client_order_id, result)

    def full_close(
        self,
        position: MT5Position,
        *,
        snapshot: SafetySnapshot,
        client_order_id: str,
    ) -> PositionActionOutcome:
        reasons = self._reduction_reasons(snapshot, require_fresh_data=False)
        if reasons:
            return self._blocked("full_close_blocked", client_order_id, reasons)
        result = self._lifecycle.full_close(position, client_order_id=client_order_id)
        if result.status in {"FILLED", "PARTIAL"}:
            self._state.mark_closed(position.position_id)
        return self._record("full_close", client_order_id, result)

    def _blocked(self, event_type: str, client_order_id: str, reasons: tuple[str, ...]) -> PositionActionOutcome:
        if self._audit is not None:
            self._audit.append(AuditEvent(event_type, "REJECTED", {"reasons": list(reasons)}, client_order_id))
        return PositionActionOutcome("BLOCKED", reasons)

    def _record(self, event_type: str, client_order_id: str, result: MT5OrderResult) -> PositionActionOutcome:
        if self._audit is not None:
            self._audit.append(
                AuditEvent(
                    event_type,
                    result.status,
                    {"retcode": result.retcode, "broker_order_id": result.broker_order_id},
                    client_order_id,
                )
            )
        return PositionActionOutcome(result.status, broker_result=result)
