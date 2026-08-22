"""Deterministic paper broker adapter for offline end-to-end validation."""

from dataclasses import dataclass
from pathlib import Path

from src.execution.mt5_adapter import (
    MT5OrderRequest,
    MT5OrderResult,
    OrderIntentLedger,
)


@dataclass(frozen=True)
class PaperExit:
    client_order_id: str
    symbol: str
    exit_price: float
    exit_reason: str
    timestamp: str


class PaperBrokerAdapter:
    """Fill at the declared price and retain transparent local positions."""

    def __init__(self, ledger_path: str | Path = ":memory:"):
        self._ledger = OrderIntentLedger(ledger_path)
        self._positions: dict[str, dict[str, object]] = {}
        self._closed: list[PaperExit] = []

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

    def closed_orders(self) -> tuple[PaperExit, ...]:
        return tuple(self._closed)

    def process_tick(
        self, symbol: str, *, bid: float, ask: float, timestamp: str
    ) -> PaperExit | None:
        """Mark positions and close the first hit using STOP_FIRST."""

        if bid <= 0 or ask <= 0 or bid > ask:
            raise ValueError("tick must have positive bid <= ask")
        for client_order_id, position in tuple(self._positions.items()):
            if position["symbol"] != symbol:
                continue
            direction = position["direction"]
            stop = position["stop_loss"]
            target = position["take_profit"]
            if direction == "UP":
                stop_hit = stop is not None and bid <= float(stop)
                target_hit = target is not None and ask >= float(target)
            else:
                stop_hit = stop is not None and ask >= float(stop)
                target_hit = target is not None and bid <= float(target)
            if stop_hit:
                exit_price, reason = float(stop), "STOP"
            elif target_hit:
                exit_price, reason = float(target), "TARGET"
            else:
                continue
            closed = PaperExit(client_order_id, symbol, exit_price, reason, timestamp)
            del self._positions[client_order_id]
            self._closed.append(closed)
            return closed
        return None

    def close(self) -> None:
        self._ledger.close()
