"""Deterministic paper broker adapter for offline end-to-end validation."""

from pathlib import Path

from src.execution.mt5_adapter import (
    MT5OrderRequest,
    MT5OrderResult,
    OrderIntentLedger,
)


class PaperBrokerAdapter:
    """Fill at the declared price and retain transparent local positions."""

    def __init__(self, ledger_path: str | Path = ":memory:"):
        self._ledger = OrderIntentLedger(ledger_path)
        self._positions: dict[str, dict[str, object]] = {}

    def submit(self, order: MT5OrderRequest) -> MT5OrderResult:
        existing = self._ledger.get(order.client_order_id)
        if existing is not None:
            status, broker_order_id, retcode = existing
            return MT5OrderResult(
                order.client_order_id,
                "DUPLICATE_SUPPRESSED",
                broker_order_id,
                retcode,
                f"existing paper intent status={status}",
            )

        broker_order_id = f"paper:{order.client_order_id}"
        self._ledger.record(order.client_order_id, "SUBMITTING")
        self._positions[order.client_order_id] = {
            "position_id": broker_order_id,
            "symbol": order.symbol,
            "direction": order.direction.upper(),
            "volume": order.volume,
            "entry_price": order.price,
            "stop_loss": order.stop_loss,
            "take_profit": order.take_profit,
        }
        self._ledger.record(order.client_order_id, "FILLED", broker_order_id, 10009)
        return MT5OrderResult(
            order.client_order_id,
            "FILLED",
            broker_order_id,
            10009,
            "deterministic paper fill",
        )

    def open_orders(self) -> tuple[dict[str, object], ...]:
        return tuple(self._positions.values())

    def close(self) -> None:
        self._ledger.close()
