"""Native MetaTrader5 Python IPC adapter, restricted to DEMO accounts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .mt5_demo import DemoExecutionJournal, ensure_demo_account


class MT5DemoAdapter:
    def __init__(self, mt5_module: Any, journal_path: str | Path = "demo-execution.jsonl"):
        self.mt5 = mt5_module
        self.journal = DemoExecutionJournal(journal_path)
        self.account: dict[str, Any] | None = None

    def connect(self) -> dict[str, Any]:
        if not self.mt5.initialize():
            raise RuntimeError(f"MT5 initialize failed: {self.mt5.last_error()}")
        try:
            self.account = ensure_demo_account(self.mt5.account_info())
        except Exception:
            self.mt5.shutdown()
            raise
        return self.account

    def open_minimal(self, symbol: str, volume: float = 0.01) -> dict[str, Any]:
        if self.account is None:
            raise RuntimeError("connect() must succeed before trading")
        info = self.mt5.symbol_info(symbol)
        if info is None or not getattr(info, "visible", False):
            if not self.mt5.symbol_select(symbol, True):
                raise RuntimeError(f"cannot select symbol {symbol}")
        tick = self.mt5.symbol_info_tick(symbol)
        if tick is None:
            raise RuntimeError(f"no tick for {symbol}")
        order_id = self.journal.prepare(symbol, "BUY", volume)
        existing = self.mt5.positions_get(symbol=symbol) or []
        history = self.mt5.history_orders_get(symbol=symbol) or []
        if self.journal.match_remote(order_id, [getattr(x, "_asdict", lambda: {})() for x in (*existing, *history)]):
            raise RuntimeError("idempotency key already reconciled")
        request = {
            "action": self.mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": self.mt5.ORDER_TYPE_BUY,
            "price": tick.ask,
            "deviation": 20,
            "magic": 260828,
            "comment": order_id,
            "type_time": self.mt5.ORDER_TIME_GTC,
            "type_filling": self.mt5.ORDER_FILLING_RETURN,
        }
        check = self.mt5.order_check(request)
        if check is None or check.retcode != self.mt5.TRADE_RETCODE_DONE:
            raise RuntimeError(f"order_check rejected: {check}")
        self.journal.record(order_id, "checked", {"symbol": symbol})
        result = self.mt5.order_send(request)
        if result is None or result.retcode != self.mt5.TRADE_RETCODE_DONE:
            raise RuntimeError(f"order_send rejected: {result}")
        payload = {"order": result.order, "deal": result.deal, "price": result.price}
        self.journal.record(order_id, "sent", payload)
        return payload

    def close(self) -> None:
        self.mt5.shutdown()

