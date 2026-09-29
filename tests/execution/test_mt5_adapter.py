from types import SimpleNamespace
from contextlib import contextmanager
from pathlib import Path
import tempfile

import pytest

from src.execution.mt5_adapter import (
    ExecutionMode,
    MT5BrokerAdapter,
    MT5OrderRequest,
    OrderIntentLedger,
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
            login=123456,
            server="MetaQuotes-Demo",
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

    def terminal_info(self):
        return SimpleNamespace(connected=True)

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


@pytest.mark.parametrize("ledger_path", [":memory:", ""])
def test_order_capable_demo_requires_a_persistent_ledger(ledger_path):
    terminal = FakeTerminal()
    with pytest.raises(TradingDisabledError, match="PERSISTENT_ORDER_LEDGER_REQUIRED"):
        MT5BrokerAdapter(
            terminal, mode=ExecutionMode.DEMO,
            allow_order_send=True, ledger_path=ledger_path,
        )
    assert terminal.initialize_calls == 0
    assert terminal.send_calls == 0


def test_readonly_demo_can_use_in_memory_ledger_without_order_access():
    terminal = FakeTerminal()
    adapter = MT5BrokerAdapter(
        terminal, mode=ExecutionMode.DEMO,
        allow_order_send=False,
    )
    with pytest.raises(TradingDisabledError, match="order submission is disabled"):
        adapter.submit(_request("readonly-no-send"))
    adapter.close()
    assert terminal.send_calls == 0


def test_investor_readonly_demo_can_read_but_never_mutate():
    terminal = FakeTerminal()
    terminal.account.trade_allowed = False
    terminal.account.trade_expert = False
    terminal.account.currency = "USD"
    terminal.account.balance = 1500.0
    terminal.account.equity = 1507.0
    terminal.positions_get = lambda **kwargs: ()
    adapter = MT5BrokerAdapter(
        terminal, mode=ExecutionMode.DEMO, allow_order_send=False,
    )
    assert adapter.positions() == ()
    fresh = adapter.account_snapshot(
        expected_login="123456", expected_server="MetaQuotes-Demo",
    )
    assert (fresh.balance, fresh.equity) == (1500.0, 1507.0)
    assert fresh.trade_allowed is False
    with pytest.raises(TradingDisabledError, match="order submission is disabled"):
        adapter.submit(_request("investor-no-order"))
    assert terminal.send_calls == 0
    adapter.close()


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


@pytest.mark.parametrize("attribute,value", [
    ("login", None),
    ("login", 0),
    ("login", ""),
    ("login", "012345"),
    ("server", None),
    ("server", ""),
    ("server", "   "),
])
def test_demo_missing_identity_never_reads_or_sends(attribute, value):
    terminal = FakeTerminal()
    setattr(terminal.account, attribute, value)
    with _ledger_path() as db_path:
        adapter = MT5BrokerAdapter(
            terminal, mode=ExecutionMode.DEMO,
            allow_order_send=True, ledger_path=db_path,
        )
        with pytest.raises(TradingDisabledError, match="identity required"):
            adapter.submit(_request("missing-demo-identity"))
        adapter.close()
    assert terminal.check_calls == 0
    assert terminal.send_calls == 0


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


def test_sqlite_intent_claim_is_atomic_across_two_connections():
    with _ledger_path() as db_path:
        first = OrderIntentLedger(db_path)
        second = OrderIntentLedger(db_path)
        assert first.claim("cross-worker-claim")
        assert not second.claim("cross-worker-claim")
        assert second.get("cross-worker-claim") == ("SUBMITTING", None, None)
        first.close()
        second.close()
        restarted = OrderIntentLedger(db_path)
        assert not restarted.claim("cross-worker-claim")
        assert restarted.get("cross-worker-claim")[0] == "SUBMITTING"
        restarted.close()


def test_stale_duplicate_precheck_cannot_submit_same_intent_twice():
    with _ledger_path() as db_path:
        first_terminal = FakeTerminal()
        second_terminal = FakeTerminal()
        first = MT5BrokerAdapter(
            first_terminal, mode=ExecutionMode.DEMO,
            allow_order_send=True, ledger_path=db_path,
        )
        second = MT5BrokerAdapter(
            second_terminal, mode=ExecutionMode.DEMO,
            allow_order_send=True, ledger_path=db_path,
        )
        assert first.submit(_request("simulated-race")).status == "FILLED"
        # Model both workers observing an absent intent before the atomic
        # reservation. The second must still lose the INSERT-on-conflict.
        original = second._duplicate_result
        checks = 0

        def stale_first_check(client_order_id):
            nonlocal checks
            checks += 1
            if checks == 1:
                return None
            return original(client_order_id)

        second._duplicate_result = stale_first_check
        outcome = second.submit(_request("simulated-race"))
        assert outcome.status == "DUPLICATE_SUPPRESSED"
        assert checks == 2
        assert first_terminal.send_calls == 1
        assert second_terminal.send_calls == 0
        first.close()
        second.close()


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


@pytest.mark.parametrize("mutate_account", [
    lambda a: setattr(a, "trade_mode", 2),
    lambda a: setattr(a, "trade_allowed", False),
    lambda a: setattr(a, "login", 654321),
    lambda a: setattr(a, "server", "Different-Demo"),
    lambda a: setattr(a, "server", None),
    lambda a: setattr(a, "login", None),
])
def test_broker_switch_after_order_check_blocks_order_send(mutate_account):
    terminal = FakeTerminal()
    original = terminal.order_check

    def switching_check(request):
        result = original(request)
        mutate_account(terminal.account)
        return result

    terminal.order_check = switching_check
    with _ledger_path() as db_path:
        adapter = MT5BrokerAdapter(
            terminal, mode=ExecutionMode.DEMO,
            allow_order_send=True, ledger_path=db_path,
        )
        with pytest.raises(TradingDisabledError):
            adapter.submit(_request("session-switch"))
        adapter.close()
    assert terminal.check_calls == 1
    assert terminal.send_calls == 0


def test_adapter_account_snapshot_requires_exact_demo_identity():
    terminal = FakeTerminal()
    terminal.account.currency = "USD"
    terminal.account.balance = 1000.0
    terminal.account.equity = 1002.5
    terminal.positions_get = lambda: ()
    with _ledger_path() as db_path:
        adapter = MT5BrokerAdapter(
            terminal, mode=ExecutionMode.DEMO,
            allow_order_send=False, ledger_path=db_path,
        )
        snapshot = adapter.account_snapshot(
            expected_login="123456", expected_server="MetaQuotes-Demo"
        )
        assert (snapshot.balance, snapshot.equity) == (1000.0, 1002.5)
        with pytest.raises(RuntimeError, match="ACCOUNT_IDENTITY_MISMATCH"):
            adapter.account_snapshot(
                expected_login="123456", expected_server="Wrong-Demo"
            )
        adapter.close()
    assert terminal.check_calls == 0
    assert terminal.send_calls == 0


def test_positions_read_is_blocked_after_switch_to_live_account():
    terminal = FakeTerminal()
    terminal.positions_get = lambda **kwargs: (_ for _ in ()).throw(
        AssertionError("LIVE account positions must never be accessed")
    )
    with _ledger_path() as db_path:
        adapter = MT5BrokerAdapter(
            terminal, mode=ExecutionMode.DEMO,
            allow_order_send=False, ledger_path=db_path,
        )
        assert adapter.connect()
        terminal.account.trade_mode = 2
        with pytest.raises(TradingDisabledError, match="DEMO"):
            adapter.positions()
        adapter.close()
    assert terminal.send_calls == 0


@pytest.mark.parametrize("stop_loss", [None, float("nan"), float("inf"), -float("inf"), 0.0, -1.0])
def test_direct_adapter_requires_finite_positive_protective_stop_before_broker_calls(stop_loss):
    """Direct adapter callers cannot bypass protective SL through a missing/invalid value."""
    terminal = FakeTerminal()
    with _ledger_path() as db_path:
        adapter = MT5BrokerAdapter(
            terminal, mode=ExecutionMode.DEMO,
            allow_order_send=True, ledger_path=db_path,
        )
        order = MT5OrderRequest(
            client_order_id="direct-no-protective-stop",
            symbol="EURUSD", direction="UP", volume=0.01,
            price=1.1, stop_loss=stop_loss,
        )
        result = adapter.submit(order)
        assert result.status == "RISK_REJECTED"
        assert result.message == "PROTECTIVE_STOP_REQUIRED"
        assert terminal.check_calls == 0
        assert terminal.send_calls == 0
        assert adapter._ledger.get(order.client_order_id) is None
        adapter.close()


@pytest.mark.parametrize("target", [float("nan"), float("inf"), -float("inf"), 0.0, -1.0])
def test_direct_adapter_rejects_invalid_target_before_broker_calls(target):
    terminal = FakeTerminal()
    with _ledger_path() as db_path:
        adapter = MT5BrokerAdapter(
            terminal, mode=ExecutionMode.DEMO,
            allow_order_send=True, ledger_path=db_path,
        )
        order = MT5OrderRequest(
            client_order_id="direct-invalid-target",
            symbol="EURUSD", direction="UP", volume=0.01,
            price=1.1, stop_loss=1.09, take_profit=target,
        )
        result = adapter.submit(order)
        assert result.status == "CONTRACT_REJECTED"
        assert result.message == "TARGET_INVALID"
        assert terminal.check_calls == 0
        assert terminal.send_calls == 0
        assert adapter._ledger.get(order.client_order_id) is None
        adapter.close()


@pytest.mark.parametrize("stop_loss", [None, float("nan"), float("inf"), -float("inf"), 0.0, -1.0, False])
def test_modify_position_rejects_missing_or_invalid_stop_before_broker_calls(stop_loss):
    terminal = FakeTerminal()
    with _ledger_path() as db_path:
        adapter = MT5BrokerAdapter(
            terminal, mode=ExecutionMode.DEMO,
            allow_order_send=True, ledger_path=db_path,
        )
        result = adapter.modify_position(
            "42", client_order_id="invalid-sl-modification",
            stop_loss=stop_loss,
        )
        assert (result.status, result.message) == (
            "RISK_REJECTED", "PROTECTIVE_STOP_REQUIRED"
        )
        assert terminal.initialize_calls == 0
        assert terminal.check_calls == 0
        assert terminal.send_calls == 0
        assert adapter._ledger.get("invalid-sl-modification") is None
        adapter.close()


@pytest.mark.parametrize("take_profit", [float("nan"), float("inf"), -float("inf"), 0.0, -1.0, False])
def test_modify_position_rejects_invalid_target_before_broker_calls(take_profit):
    terminal = FakeTerminal()
    with _ledger_path() as db_path:
        adapter = MT5BrokerAdapter(
            terminal, mode=ExecutionMode.DEMO,
            allow_order_send=True, ledger_path=db_path,
        )
        result = adapter.modify_position(
            "42", client_order_id="invalid-tp-modification",
            stop_loss=1.09, take_profit=take_profit,
        )
        assert (result.status, result.message) == (
            "CONTRACT_REJECTED", "TARGET_INVALID"
        )
        assert terminal.initialize_calls == 0
        assert terminal.check_calls == 0
        assert terminal.send_calls == 0
        assert adapter._ledger.get("invalid-tp-modification") is None
        adapter.close()


def test_positions_read_fails_closed_when_account_switches_during_broker_call():
    terminal = FakeTerminal()

    def switched_positions(**kwargs):
        terminal.account.trade_mode = 2
        return ()

    terminal.positions_get = switched_positions
    adapter = MT5BrokerAdapter(
        terminal, mode=ExecutionMode.DEMO, allow_order_send=False,
    )
    with pytest.raises(TradingDisabledError, match="DEMO account"):
        adapter.positions()
    assert terminal.send_calls == 0
    adapter.close()
