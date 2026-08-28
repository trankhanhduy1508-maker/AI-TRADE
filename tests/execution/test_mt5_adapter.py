from types import SimpleNamespace

import pytest

from src.execution.mt5_adapter import MT5DemoAdapter


class FakeMT5:
    TRADE_ACTION_DEAL = 1
    ORDER_TYPE_BUY = 0
    ORDER_TIME_GTC = 0
    ORDER_FILLING_RETURN = 0
    TRADE_RETCODE_DONE = 10009

    def __init__(self):
        self.sent = []

    def initialize(self):
        return True

    def account_info(self):
        return SimpleNamespace(login=7, server="Demo", trade_mode=0, trade_allowed=True, trade_expert=True)

    def symbol_select(self, symbol, visible):
        return True

    def symbol_info(self, symbol):
        return SimpleNamespace(visible=True, point=0.00001)

    def symbol_info_tick(self, symbol):
        return SimpleNamespace(ask=1.1, bid=1.0999)

    def order_check(self, request):
        return SimpleNamespace(retcode=self.TRADE_RETCODE_DONE)

    def order_send(self, request):
        self.sent.append(request)
        return SimpleNamespace(retcode=self.TRADE_RETCODE_DONE, order=11, deal=12, price=request["price"])

    def positions_get(self, **kwargs):
        return []

    def history_orders_get(self, **kwargs):
        return []

    def history_deals_get(self, **kwargs):
        return []

    def shutdown(self):
        pass


def test_adapter_refuses_non_demo_before_order():
    fake = FakeMT5()
    fake.account_info = lambda: SimpleNamespace(login=7, server="Live", trade_mode=2, trade_allowed=True, trade_expert=True)
    with pytest.raises(RuntimeError, match="DEMO"):
        MT5DemoAdapter(fake).connect()


def test_adapter_orders_only_after_check_and_returns_ticket():
    fake = FakeMT5()
    from pathlib import Path
    path = Path("adapter-test-journal.jsonl")
    if path.exists():
        path.unlink()
    adapter = MT5DemoAdapter(fake, journal_path=path)
    adapter.connect()
    result = adapter.open_minimal("EURUSD", 0.01)
    assert result["order"] == 11
    assert len(fake.sent) == 1
    path.unlink()
