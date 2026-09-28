"""Offline compatibility tests; no broker access and no DEMO orders."""
import sys
from types import ModuleType
import pytest

from scripts.run_metaapi_demo_autotrade import main


def test_obsolete_demo_send_flag_is_blocked_before_import(monkeypatch):
    monkeypatch.delenv("METAAPI_TOKEN", raising=False)
    assert main(["--enable-demo-send"]) == 78


def test_unsupported_old_transport_flags_fail_explicitly():
    with pytest.raises(SystemExit) as error:
        main(["--bars", "250"])
    assert error.value.code == 2


def test_read_only_alias_preserves_supported_runtime_options(monkeypatch):
    fake = ModuleType("scripts.run_metaapi_cloud_autotrade")

    async def current():
        import os
        assert os.environ["AI_TRADE_SYMBOL"] == "EURUSD"
        assert os.environ["AI_TRADE_TIMEFRAME"] == "15m"
        assert os.environ["AI_TRADE_POLL_SECONDS"] == "20.0"
        assert os.environ["AI_TRADE_ONCE"] == "YES"
        assert os.environ["AI_TRADE_ENABLE_DEMO_SEND"] == "NO"
        return 0

    fake.main = current
    monkeypatch.setitem(sys.modules, fake.__name__, fake)
    monkeypatch.setenv("AI_TRADE_ENABLE_DEMO_SEND", "YES")
    assert main(["--symbol", "EURUSD", "--timeframe", "15m",
                 "--poll-seconds", "20", "--once"]) == 0
