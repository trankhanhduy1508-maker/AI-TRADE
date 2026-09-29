"""Synthetic-only smoke, runtime and fault tests for metadata journal."""
import json
import tempfile
import unittest
from pathlib import Path
from src.paper.r1_source_receipt import (
    _record, verify_source_receipts, FORWARD_START_UTC,
)

BAR = FORWARD_START_UTC - 14400


def info(**overrides):
    v = {"source": "KRAKEN_SPOT_NATIVE_H4", "symbol": "BTCUSD",
         "source_kind": "NATIVE_H4_KRAKEN_SPOT", "first_open_ts": BAR - 14400,
         "last_close_ts": BAR, "completed_h4": 1, "rejected_h4": 0}
    v.update(overrides)
    return v


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "private_receipts.jsonl"

    def record(self, raw=b"SYNTHETIC-NOT-MARKET-DATA", **changes):
        return _record(self.path, source_bytes=raw, metadata=info(**changes),
                       captured_at_utc=FORWARD_START_UTC - 1)


class Smoke(Base):
    def test_creates_metadata_without_raw_or_paper_fills(self):
        result = self.record()
        self.assertEqual(result["status"], "METADATA_RECEIPT_UNVERIFIED")
        self.assertFalse(result["raw_bytes_persisted"])
        self.assertEqual(result["paper_fills_created"], 0)
        self.assertEqual(result["orders_sent"], 0)
        data = self.path.read_bytes()
        self.assertNotIn(b"SYNTHETIC-NOT-MARKET-DATA", data)
        self.assertEqual(verify_source_receipts(self.path)["records"], 1)

    def test_first_record_never_promotes_provenance(self):
        self.record()
        self.assertIn('"evidence_class":"SOURCE_ONLY_UNVERIFIED"',
                      self.path.read_text())


class Runtime(Base):
    def test_sequential_multi_source_and_reload(self):
        self.record()
        _record(self.path, source_bytes=b"SECOND_SOURCE", metadata=info(
            source="BITSTAMP_PUBLIC_OHLC", symbol="ETHUSD",
            source_kind="NATIVE_H4_BITSTAMP_SPOT"),
            captured_at_utc=FORWARD_START_UTC - 1)
        self.assertEqual(verify_source_receipts(self.path)["records"], 2)
        entries = [json.loads(x) for x in self.path.read_text().splitlines()]
        self.assertEqual(entries[1]["prev_hash"], entries[0]["record_hash"])

    def test_derived_is_not_native(self):
        _record(self.path, source_bytes=b"M1_FIXTURE", metadata=info(
            source="HISTDATA_GENERIC_ASCII_M1_BID", symbol="EURUSD",
            source_kind="DERIVED_H4_BID_ONLY", first_open_ts=BAR - 60),
            captured_at_utc=FORWARD_START_UTC - 1)
        self.assertEqual(verify_source_receipts(self.path)["records"], 1)


class Fault(Base):
    def test_duplicate_rejected(self):
        self.record()
        with self.assertRaisesRegex(ValueError, "DUPLICATE_OR_NONCHRONOLOGICAL"):
            self.record()

    def test_tampered_data_rejected(self):
        self.record()
        self.path.write_text(self.path.read_text().replace("BTCUSD", "ETHUSD"))
        with self.assertRaisesRegex(ValueError, "CORRUPT_RECEIPT_LINE"):
            verify_source_receipts(self.path)

    def test_bad_source_kind_blocked(self):
        with self.assertRaisesRegex(ValueError, "NATIVE_DERIVED"):
            self.record(source_kind="DERIVED_H4_BID_ONLY")

    def test_future_close_rejected(self):
        with self.assertRaisesRegex(ValueError, "INVALID_RECEIPT_TIME"):
            self.record(last_close_ts=FORWARD_START_UTC + 14400)

    def test_undocumented_provider_blocked(self):
        with self.assertRaisesRegex(ValueError, "UNREGISTERED_PROVIDER"):
            self.record(source="UNAUTHORIZED_API")

    def test_no_raw_bytes_rejected(self):
        with self.assertRaisesRegex(ValueError, "BAD_RECEIPT_INPUT"):
            self.record(raw=b"")

    def test_broken_hash_chain_blocks_append(self):
        self.record()
        self.path.write_text(self.path.read_text().replace('"seq":1', '"seq":8'))
        with self.assertRaisesRegex(ValueError, "CORRUPT_RECEIPT_LINE"):
            self.record()

    def test_counterfeit_licence_not_accepted(self):
        from src.paper.r1_source_receipt import _check_event
        self.record()
        event = json.loads(self.path.read_text())["event"]
        event["data_rights"] = "VERIFIED"
        with self.assertRaisesRegex(ValueError, "UNAUTHORIZED_EVIDENCE_PROMOTION"):
            _check_event(event)

    def test_boolean_number_rejected(self):
        with self.assertRaisesRegex(ValueError, "INVALID_RECEIPT_NUMBER"):
            self.record(completed_h4=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
