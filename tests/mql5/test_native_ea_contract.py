from pathlib import Path
import re


EA_PATH = Path(__file__).parents[2] / "mql5" / "Experts" / "AITradeTrendFollowingEA.mq5"


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
