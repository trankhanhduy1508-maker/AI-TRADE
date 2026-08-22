from types import SimpleNamespace
from contextlib import contextmanager
from pathlib import Path
import tempfile

import pytest

from src.execution.mt5_adapter import (
    ExecutionMode,
    MT5BrokerAdapter,
    MT5OrderRequest,
    TradingDisabledError,
)


class FakeTerminal:
    TRADE_ACTION_DEAL = 1
    ORDER_TYPE_BUY = 2
    ORDER_TYPE_SELL = 3

    def __init__(self, *, check_retcode=0, send_retcode=10009):
        self.check_retcode = check_retcode
        self.send_retcode = send_retcode
        self.initialize_calls = 0
        self.check_calls = 0
        self.send_calls = 0
        self.contract = SimpleNamespace(
            point=0.00001,
            digits=5,
            volume_min=0.01,
            volume_max=1.0,
            volume_step=0.01,
            trade_stops_level=10,
            trade_mode=1,
        )
        self.account = SimpleNamespace(
            trade_mode=0,
            trade_allowed=True,
            trade_expert=True,
        )

    def initialize(self, **kwargs):
        self.initialize_calls += 1
        return True

    def shutdown(self):
        return None

    def order_check(self, request):
        self.check_calls += 1
        return SimpleNamespace(retcode=self.check_retcode, comment="check")

    def symbol_info(self, symbol):
        return self.contract

    def account_info(self):
        return self.account

    def order_send(self, request):
        self.send_calls += 1
        return SimpleNamespace(
            retcode=self.send_retcode,
            order=987,
            price=request["price"],
            volume=request["volume"],
            comment="sent",
        )


def _request(client_order_id="intent-1"):
    return MT5OrderRequest(
        client_order_id=client_order_id,
        symbol="EURUSD",
        direction="UP",
        volume=0.01,
        price=1.1,
        stop_loss=1.09,
        take_profit=1.12,
    )


@contextmanager
def _ledger_path():
    handle = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
    path = Path(handle.name)
    handle.close()
    path.unlink(missing_ok=True)
    try:
        yield path
    finally:
        path.unlink(missing_ok=True)


def test_disabled_adapter_never_initializes_or_sends():
    terminal = FakeTerminal()
    with _ledger_path() as db_path:
        adapter = MT5BrokerAdapter(terminal, ledger_path=db_path)

        with pytest.raises(TradingDisabledError):
            adapter.submit(_request())
        adapter.close()

    assert terminal.initialize_calls == 0
    assert terminal.send_calls == 0


def test_live_mode_is_locked_even_when_send_flag_is_requested():
    terminal = FakeTerminal()
    with _ledger_path() as db_path:
        adapter = MT5BrokerAdapter(
            terminal,
            mode=ExecutionMode.LIVE,
            allow_order_send=True,
            ledger_path=db_path,
        )

        with pytest.raises(TradingDisabledError, match="LIVE"):
            adapter.submit(_request())
        adapter.close()

    assert terminal.initialize_calls == 0


def test_order_check_must_pass_before_order_send():
    terminal = FakeTerminal(check_retcode=10016)
    with _ledger_path() as db_path:
        adapter = MT5BrokerAdapter(
            terminal,
            mode=ExecutionMode.DEMO,
            allow_order_send=True,
            ledger_path=db_path,
        )

        result = adapter.submit(_request())
        adapter.close()

    assert result.status == "CHECK_REJECTED"
    assert terminal.check_calls == 1
    assert terminal.send_calls == 0


def test_success_is_persistently_duplicate_safe():
    with _ledger_path() as db_path:
        first_terminal = FakeTerminal()
        first = MT5BrokerAdapter(
            first_terminal,
            mode=ExecutionMode.DEMO,
            allow_order_send=True,
            ledger_path=db_path,
        )

        first_result = first.submit(_request("stable-intent"))

        second_terminal = FakeTerminal()
        second = MT5BrokerAdapter(
            second_terminal,
            mode=ExecutionMode.DEMO,
            allow_order_send=True,
            ledger_path=db_path,
        )
        second_result = second.submit(_request("stable-intent"))
        first.close()
        second.close()

    assert first_result.status == "FILLED"
    assert second_result.status == "DUPLICATE_SUPPRESSED"
    assert first_terminal.send_calls == 1
    assert second_terminal.send_calls == 0


def test_contract_preflight_rejects_volume_step_before_order_check():
    terminal = FakeTerminal()
    with _ledger_path() as db_path:
        adapter = MT5BrokerAdapter(
            terminal,
            mode=ExecutionMode.DEMO,
            allow_order_send=True,
            ledger_path=db_path,
        )

        order = MT5OrderRequest(
            client_order_id="bad-volume-step",
            symbol="EURUSD",
            direction="UP",
            volume=0.015,
            price=1.1,
            stop_loss=1.09,
            take_profit=1.12,
        )
        result = adapter.submit(order)
        adapter.close()

    assert result.status == "CONTRACT_REJECTED"
    assert "VOLUME_STEP" in result.message
    assert terminal.check_calls == 0
    assert terminal.send_calls == 0


def test_contract_preflight_rejects_missing_symbol_metadata_fail_closed():
    terminal = FakeTerminal()
    terminal.contract = None
    with _ledger_path() as db_path:
        adapter = MT5BrokerAdapter(
            terminal,
            mode=ExecutionMode.DEMO,
            allow_order_send=True,
            ledger_path=db_path,
        )

        result = adapter.submit(_request("missing-contract"))
        adapter.close()

    assert result.status == "CONTRACT_REJECTED"
    assert "SYMBOL_INFO_MISSING" in result.message
    assert terminal.check_calls == 0
    assert terminal.send_calls == 0


def test_contract_preflight_rejects_broker_minimum_stop_distance():
    terminal = FakeTerminal()
    with _ledger_path() as db_path:
        adapter = MT5BrokerAdapter(
            terminal,
            mode=ExecutionMode.DEMO,
            allow_order_send=True,
            ledger_path=db_path,
        )

        order = MT5OrderRequest(
            client_order_id="bad-stop-distance",
            symbol="EURUSD",
            direction="UP",
            volume=0.01,
            price=1.1,
            stop_loss=1.09995,
            take_profit=1.12,
        )
        result = adapter.submit(order)
        adapter.close()

    assert result.status == "CONTRACT_REJECTED"
    assert "STOP_DISTANCE" in result.message
    assert terminal.check_calls == 0
    assert terminal.send_calls == 0


def test_demo_mode_rejects_real_account_before_order_check():
    terminal = FakeTerminal()
    terminal.account.trade_mode = 2
    with _ledger_path() as db_path:
        adapter = MT5BrokerAdapter(
            terminal,
            mode=ExecutionMode.DEMO,
            allow_order_send=True,
            ledger_path=db_path,
        )

        with pytest.raises(TradingDisabledError, match="DEMO account"):
            adapter.submit(_request("real-account"))
        adapter.close()

    assert terminal.check_calls == 0
    assert terminal.send_calls == 0


def test_demo_mode_fails_closed_when_account_trading_is_disabled():
    terminal = FakeTerminal()
    terminal.account.trade_allowed = False
    with _ledger_path() as db_path:
        adapter = MT5BrokerAdapter(
            terminal,
            mode=ExecutionMode.DEMO,
            allow_order_send=True,
            ledger_path=db_path,
        )

        with pytest.raises(TradingDisabledError, match="trading disabled"):
            adapter.submit(_request("trading-disabled"))
        adapter.close()

    assert terminal.check_calls == 0
    assert terminal.send_calls == 0


def test_demo_mode_fails_closed_when_account_context_is_unavailable():
    terminal = FakeTerminal()
    terminal.account_info = None
    with _ledger_path() as db_path:
        adapter = MT5BrokerAdapter(
            terminal,
            mode=ExecutionMode.DEMO,
            allow_order_send=True,
            ledger_path=db_path,
        )

        with pytest.raises(ConnectionError, match="initialization failed"):
            adapter.submit(_request("missing-account-context"))
        adapter.close()

    assert terminal.check_calls == 0
    assert terminal.send_calls == 0


def test_contract_preflight_rejects_stop_at_entry_even_without_broker_minimum():
    terminal = FakeTerminal()
    terminal.contract.trade_stops_level = 0
    with _ledger_path() as db_path:
        adapter = MT5BrokerAdapter(
            terminal,
            mode=ExecutionMode.DEMO,
            allow_order_send=True,
            ledger_path=db_path,
        )

        order = MT5OrderRequest(
            client_order_id="stop-at-entry",
            symbol="EURUSD",
            direction="UP",
            volume=0.01,
            price=1.1,
            stop_loss=1.1,
            take_profit=1.12,
        )
        result = adapter.submit(order)
        adapter.close()

    assert result.status == "CONTRACT_REJECTED"
    assert result.message == "STOP_DISTANCE_INVALID"
    assert terminal.check_calls == 0
    assert terminal.send_calls == 0
