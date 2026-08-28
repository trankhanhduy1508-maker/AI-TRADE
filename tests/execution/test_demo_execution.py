import json

import pytest

from src.execution.mt5_demo import DemoExecutionError, DemoExecutionJournal, ensure_demo_account


def test_live_account_is_rejected_before_any_order():
    with pytest.raises(DemoExecutionError, match="DEMO"):
        ensure_demo_account({"trade_mode": 2, "server": "Broker-Live"})


def test_demo_account_requires_trading_permissions():
    with pytest.raises(DemoExecutionError, match="trade permission"):
        ensure_demo_account({"trade_mode": 0, "trade_allowed": False, "trade_expert": True})


def test_journal_makes_retries_idempotent_and_reconciles():
    from pathlib import Path
    path = Path("execution-test-journal.jsonl")
    if path.exists():
        path.unlink()
    journal = DemoExecutionJournal(path)
    order_id = journal.prepare("EURUSD", "BUY", 0.01)
    assert journal.prepare("EURUSD", "BUY", 0.01) == order_id
    journal.record(order_id, "sent", {"order": 101})
    assert journal.match_remote(order_id, [{"comment": order_id, "ticket": 101}])
    journal.record(order_id, "closed", {"deal": 202})
    events = [json.loads(line)["event"] for line in path.read_text().splitlines()]
    assert events == ["prepared", "sent", "closed"]
    path.unlink()
