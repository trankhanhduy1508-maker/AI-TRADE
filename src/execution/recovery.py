"""Fail-closed connection recovery and broker reconciliation contracts."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReconciliationResult:
    reconciled: bool
    missing_broker_positions: frozenset[str]
    unknown_broker_positions: frozenset[str]


def reconcile_positions(
    local_position_ids: set[str], broker_position_ids: set[str]
) -> ReconciliationResult:
    missing = frozenset(local_position_ids - broker_position_ids)
    unknown = frozenset(broker_position_ids - local_position_ids)
    return ReconciliationResult(
        reconciled=not missing and not unknown,
        missing_broker_positions=missing,
        unknown_broker_positions=unknown,
    )


class RecoveryState:
    def __init__(self):
        self.connected = False
        self.reconciled = False

    def connection_lost(self) -> None:
        self.connected = False
        self.reconciled = False

    def connection_restored(self, result: ReconciliationResult) -> None:
        self.connected = True
        self.reconciled = result.reconciled

    def can_open_new_risk(self) -> bool:
        return self.connected and self.reconciled
