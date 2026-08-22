"""Safety-gated handoff from a validated decision to a broker adapter."""

from dataclasses import dataclass
from typing import Any

from src.execution.mt5_adapter import MT5OrderRequest, MT5OrderResult
from src.execution.safety import SafetyGate, SafetySnapshot


@dataclass(frozen=True)
class ExecutionOutcome:
    status: str
    reasons: tuple[str, ...] = ()
    broker_result: MT5OrderResult | None = None


class ExecutionCoordinator:
    """Never bypass the independent safety gate before adapter submission."""

    def __init__(self, adapter: Any, gate: SafetyGate):
        self._adapter = adapter
        self._gate = gate

    def submit(
        self, order: MT5OrderRequest, snapshot: SafetySnapshot
    ) -> ExecutionOutcome:
        decision = self._gate.evaluate(snapshot)
        if not decision.allowed:
            return ExecutionOutcome(status="GATE_BLOCKED", reasons=decision.reasons)
        result = self._adapter.submit(order)
        return ExecutionOutcome(status=result.status, broker_result=result)
