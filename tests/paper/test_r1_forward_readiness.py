"""Synthetic-only forward cut-off, timestamp, cost and kill-switch tests."""
import unittest
from src.paper.r1_forward_readiness import (
    FORWARD_START_UTC, assess_forward_quote,
)

Z = FORWARD_START_UTC


def fixture(**changes):
    e = {"symbol": "EURUSD", "timeframe": "H4", "provider": "BROKER_READ_ONLY",
         "source_bar_id": "test-closed-bar-1", "bar_close_ts": Z,
         "bar_retrieved_ts": Z + 2, "quote_source_ts": Z + 4,
         "quote_received_ts": Z + 5, "decision_ts": Z + 6,
         "quote_raw_sha256": "a" * 64, "cost_evidence_sha256": "b" * 64,
         "bid": 1.1, "ask": 1.1002, "authorization_verified": True,
         "kill_switch_off": True, "costs_audited": True,
         "data_rights_approved": True}
    e.update(changes)
    return e


def inspect(**changes):
    return assess_forward_quote(fixture(**changes), now_utc=Z + 8)


class Smoke(unittest.TestCase):
    def test_paper_is_never_implicitly_activated(self):
        out = inspect()
        self.assertEqual(out["status"], "TIMING_INTEGRITY_ONLY_AWAITING_INDEPENDENT_AUDIT")
        self.assertEqual(out["paper_fills_created"], 0)
        self.assertEqual(out["orders_sent"], 0)
        self.assertFalse(out["forward_evidence_verified"])


class Runtime(unittest.TestCase):
    def test_bid_ask_spread_from_synthetic_fixture(self):
        self.assertAlmostEqual(inspect()["spread_price_observed"], .0002)

    def test_cutoff_bar_not_before_registration(self):
        self.assertEqual(inspect(bar_close_ts=Z - 1)["status"], "REJECTED")


class Fault(unittest.TestCase):
    def test_kill_switch_blocks(self):
        self.assertEqual(inspect(kill_switch_off=False)["reason"],
                         "AUTH_COST_RIGHTS_OR_KILL_SWITCH_BLOCKED")

    def test_no_fee_audit_blocks(self):
        self.assertEqual(inspect(costs_audited=False)["status"], "REJECTED")

    def test_no_authorization_blocks(self):
        self.assertEqual(inspect(authorization_verified=False)["status"], "REJECTED")

    def test_no_data_rights_blocks(self):
        self.assertEqual(inspect(data_rights_approved=False)["status"], "REJECTED")

    def test_missing_fee_evidence_blocks(self):
        self.assertEqual(inspect(cost_evidence_sha256="0" * 64)["reason"],
                         "MISSING_SOURCE_OR_COST_HASH")

    def test_future_quote_blocks(self):
        self.assertEqual(inspect(quote_source_ts=Z + 99)["status"], "REJECTED")

    def test_delayed_quote_is_not_next_open(self):
        e = fixture(bar_retrieved_ts=Z + 32, quote_source_ts=Z + 35,
                    quote_received_ts=Z + 36, decision_ts=Z + 37)
        self.assertEqual(assess_forward_quote(e, now_utc=Z + 40)["reason"],
                         "NOT_CONTEMPORANEOUS_NEXT_OPEN_QUOTE")

    def test_quote_before_bar_ingestion_blocks(self):
        self.assertEqual(inspect(bar_retrieved_ts=Z + 7)["status"], "REJECTED")

    def test_crossed_bid_ask_blocks(self):
        self.assertEqual(inspect(ask=1.09)["reason"], "INVALID_OR_CROSSED_BID_ASK")

    def test_nan_blocks(self):
        self.assertEqual(inspect(bid=float("nan"))["status"], "REJECTED")

    def test_broker_source_required(self):
        self.assertEqual(inspect(provider="HISTDATA")["status"], "REJECTED")

    def test_unexpected_fields_block(self):
        e = fixture(secret="NOT_ALLOWED")
        self.assertEqual(assess_forward_quote(e, now_utc=Z + 8)["reason"],
                         "SCHEMA_MISMATCH")


if __name__ == "__main__":
    unittest.main()
