from pathlib import Path
import re


EA_PATH = Path(__file__).parents[2] / "mql5" / "Experts" / "AITradeTrendFollowingEA.mq5"
TESTER_CONFIG_PATH = (
    Path(__file__).parents[2]
    / "mql5"
    / "tester"
    / "AITradeTrendFollowingEA_FAIL_CLOSED.ini"
)


def _source() -> str:
    return EA_PATH.read_text(encoding="utf-8")


def test_native_ea_exists_and_is_demo_locked_by_default() -> None:
    source = _source()

    assert re.search(r"input\s+bool\s+EnableDemoTrading\s*=\s*false\s*;", source)
    assert "ACCOUNT_TRADE_MODE_DEMO" in source
    assert "ACCOUNT_TRADE_MODE_REAL" not in source


def test_native_ea_requires_terminal_and_safety_gates_before_trade_calls() -> None:
    source = _source()

    assert "TERMINAL_CONNECTED" in source
    assert "TERMINAL_TRADE_ALLOWED" in source
    assert "SafetyGateAllowsTrading" in source
    assert "if(!SafetyGateAllowsTrading())" in source
    assert "trade.Buy" in source
    assert "trade.Sell" in source


def test_native_ea_uses_closed_bar_breakout_and_fixed_demo_lot() -> None:
    source = _source()

    assert "CopyRates" in source
    assert "rates[1].close" in source
    assert "DemoLots" in source
    assert re.search(r"input\s+double\s+DemoLots\s*=\s*0\.01\s*;", source)
    assert "OrderSend" not in source


def test_native_ea_has_independent_fail_closed_kill_switch_pause_and_audit() -> None:
    source = _source()

    assert "KillSwitchActive" in source
    assert "EntriesPaused" in source
    assert "FileIsExist" in source
    assert "AITrade\\\\kill_switch.flag" in source
    assert "AITrade\\\\entries_paused.flag" in source
    assert "DISARMED" in source
    assert "RESUMED" in source
    assert "AppendAudit" in source
    assert "AITrade\\\\native_audit.csv" in source
    assert "FILE_COMMON" in source


def test_native_ea_blocks_new_orders_when_audit_sink_is_unavailable() -> None:
    source = _source()

    assert "AuditWritable" in source
    assert "if(!AuditWritable())" in source


def test_native_ea_reserves_signal_bar_persistently_before_submit() -> None:
    source = _source()

    assert "SignalReservationKey" in source
    assert "GlobalVariableCheck" in source
    assert "GlobalVariableSet" in source
    assert "ReserveSignal" in source
    assert "if(!ReserveSignal(rates[1].time))" in source


def test_tester_smoke_config_is_fail_closed() -> None:
    config = TESTER_CONFIG_PATH.read_text(encoding="utf-8")

    assert "Expert=AITradeTrendFollowingEA" in config
    assert "Login=1" in config
    assert "Synthetic tester profile" in config
    assert "AllowLiveTrading=0" in config
    assert "UseRemote=0" in config
    assert "UseCloud=0" in config
    assert "ShutdownTerminal" not in config
