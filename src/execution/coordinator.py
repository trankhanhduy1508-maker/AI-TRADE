"""Safety-gated handoff from a validated decision to a broker adapter."""

from dataclasses import dataclass
from typing import Any

from src.execution.audit import AppendOnlyAuditLog, AuditEvent
from src.execution.mt5_adapter import MT5OrderRequest, MT5OrderResult
from src.execution.safety import SafetyGate, SafetySnapshot


@dataclass(frozen=True)
class ExecutionOutcome:
    status: str
    reasons: tuple[str, ...] = ()
    broker_result: MT5OrderResult | None = None


class ExecutionCoordinator:
    """Never bypass the independent safety gate before adapter submission."""

    def __init__(
        self,
        adapter: Any,
        gate: SafetyGate,
        audit_log: AppendOnlyAuditLog | None = None,
    ):
        self._adapter = adapter
        self._gate = gate
        self._audit_log = audit_log

    def submit(
        self, order: MT5OrderRequest, snapshot: SafetySnapshot
    ) -> ExecutionOutcome:
        decision = self._gate.evaluate(snapshot)
        if not decision.allowed:
            if self._audit_log is not None:
                self._audit_log.append(
                    AuditEvent(
                        "execution_blocked",
                        "REJECTED",
                        {"reasons": list(decision.reasons)},
                        client_order_id=order.client_order_id,
                    )
                )
            return ExecutionOutcome(status="GATE_BLOCKED", reasons=decision.reasons)
        result = self._adapter.submit(order)
        if self._audit_log is not None:
            self._audit_log.append(
                AuditEvent(
                    "order_submission",
                    result.status,
                    {
                        "retcode": result.retcode,
                        "broker_order_id": result.broker_order_id,
                    },
                    client_order_id=order.client_order_id,
                )
            )
        return ExecutionOutcome(status=result.status, broker_result=result)
