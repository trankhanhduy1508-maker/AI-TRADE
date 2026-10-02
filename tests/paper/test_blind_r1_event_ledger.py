"""R1 provenance Smoke/Runtime/Fault, synthetic bars ONLY, not forward evidence."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.paper.blind_r1_event_ledger import (
    FORWARD_START_UTC, GENESIS, _append, append_actual_observation,
    validate_observation, verify_ledger,
)

H4 = 14400
NOW = FORWARD_START_UTC + 10*86400


def event(index=0, **overrides):
    o=FORWARD_START_UTC+index*H4
    e={
        "schema_version":1,"kind":"BAR_CLOSED",
        "symbol":"BTCUSD","timeframe":"H4",
        "provider":"BITSTAMP_PUBLIC_OHLC",
        "provider_url":"https://www.bitstamp.net/api/v2/ohlc/btcusd/?step=14400&limit=1000&exclude_current_candle=true",
        "source_bar_id":f"synthetic-fixture-{index}",
        "open_ts":o,"close_ts":o+H4,"retrieved_ts":o+H4+60,
        "closed":True,"open":100.0,"high":110.0,
        "low":90.0,"close":105.0,"volume":5.0,
        "raw_sha256":hashlib.sha256(f"fixture-{index}".encode()).hexdigest(),
        "instrument_type":"BITSTAMP_USD_SPOT",
    }
    e.update(overrides)
    return e


class Smoke(unittest.TestCase):
    def test_forward_epoch(self):
        import datetime
        self.assertEqual(
            datetime.datetime.fromtimestamp(
                FORWARD_START_UTC,datetime.timezone.utc).isoformat(),
            "2026-09-30T00:00:00+00:00")

    def test_fixture_format(self):
        validate_observation(event(),now_utc=NOW)

    def test_unclosed_rejected(self):
        with self.assertRaisesRegex(ValueError,"UNCLOSED"):
            validate_observation(event(closed=False),now_utc=NOW)

    def test_older_history_not_forward(self):
        with self.assertRaisesRegex(ValueError,"NOT_NEW"):
            validate_observation(event(
                close_ts=FORWARD_START_UTC-1,
                open_ts=FORWARD_START_UTC-H4-1,
                retrieved_ts=FORWARD_START_UTC+60),now_utc=NOW)

    def test_yahoo_h4_is_not_native(self):
        with self.assertRaisesRegex(ValueError,"UNSUPPORTED_YAHOO_SOURCE_TF"):
            validate_observation(event(
                provider="YAHOO_FINANCE_CHART",
                provider_url="https://query2.finance.yahoo.com/v8/finance/chart/BTC-USD"),
                now_utc=NOW)

    def test_unregistered_market_rejected(self):
        with self.assertRaisesRegex(ValueError,"NOT_PREREGISTERED_INSTRUMENT"):
            validate_observation(event(symbol="CUSTOM_ASSET"),now_utc=NOW)


class Runtime(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/"paper_events.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def test_append_chain_and_no_paper_order(self):
        a=_append(self.path,event(0),now_utc=NOW)
        b=_append(self.path,event(1),now_utc=NOW)
        self.assertEqual(a["status"],"APPENDED_QUARANTINED")
        self.assertEqual(b["seq"],2)
        self.assertEqual(a["paper_orders_created"],0)
        s=verify_ledger(self.path)
        self.assertEqual(s["records"],2)
        self.assertEqual(s["last_record_hash"],b["last_record_hash"])
        self.assertEqual(s["source_audit"],"NOT_VERIFIED")

    def test_identical_source_bar_id_is_idempotent(self):
        a=_append(self.path,event(0),now_utc=NOW)
        b=_append(self.path,event(0),now_utc=NOW)
        self.assertEqual(b["status"],"DUPLICATE_NO_WRITE")
        self.assertEqual(verify_ledger(self.path)["records"],1)
        self.assertEqual(a["last_record_hash"],b["last_record_hash"])

    def test_yahoo_daily_is_labelled_not_executable(self):
        daily=event(
            provider="YAHOO_FINANCE_CHART",
            symbol="S&P 500",timeframe="D1",
            provider_url="https://query2.finance.yahoo.com/v8/finance/chart/%5EGSPC",
            instrument_type="YAHOO_NONTRADEABLE_INDEX",
            close_ts=FORWARD_START_UTC+86400,
            retrieved_ts=FORWARD_START_UTC+86400+60)
        a=_append(self.path,daily,now_utc=NOW)
        self.assertEqual(a["forward_independence"],"NOT_VERIFIED")
        self.assertEqual(a["paper_orders_created"],0)


class Fault(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/"paper_events.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def test_future_bar_rejected_even_if_claimed_closed(self):
        with self.assertRaisesRegex(ValueError,"NOT_NEW"):
            _append(self.path,event(0),now_utc=FORWARD_START_UTC+H4-1)
        self.assertFalse(self.path.exists())

    def test_actual_ingest_uses_clock_not_caller_claim(self):
        with patch("src.paper.blind_r1_event_ledger.time.time",
                   return_value=FORWARD_START_UTC+H4-5):
            with self.assertRaisesRegex(ValueError,"NOT_NEW"):
                append_actual_observation(self.path,event(0))
        self.assertFalse(self.path.exists())

    def test_missing_4h_interval_fails_closed(self):
        _append(self.path,event(0),now_utc=NOW)
        with self.assertRaisesRegex(ValueError,"BITSTAMP_MISSING"):
            _append(self.path,event(2),now_utc=NOW)
        self.assertEqual(verify_ledger(self.path)["records"],1)

    def test_conflicting_same_source_id_rejected(self):
        _append(self.path,event(0),now_utc=NOW)
        with self.assertRaisesRegex(ValueError,"CONFLICTING_DUPLICATE_ID"):
            _append(self.path,event(0,close=104.0),now_utc=NOW)

    def test_corrupt_historical_line_rejected_not_recovered(self):
        _append(self.path,event(0),now_utc=NOW)
        e=json.loads(self.path.read_text())
        e["event"]["close"]=999.0
        self.path.write_text(json.dumps(e)+"\n")
        with self.assertRaisesRegex(ValueError,"CORRUPTED_LEDGER"):
            _append(self.path,event(1),now_utc=NOW)

    def test_raw_source_hash_required(self):
        with self.assertRaisesRegex(ValueError,"MISSING_RAW_SOURCE_HASH"):
            _append(self.path,event(raw_sha256=GENESIS),now_utc=NOW)

    def test_invalid_ohlc_rejected(self):
        with self.assertRaisesRegex(ValueError,"INVALID_OHLCV"):
            _append(self.path,event(high=99.0),now_utc=NOW)

    def test_no_duplicate_interval_under_different_id(self):
        _append(self.path,event(0),now_utc=NOW)
        with self.assertRaisesRegex(ValueError,"OUT_OF_ORDER_BAR"):
            _append(self.path,event(0,source_bar_id="alternate-id"),
                    now_utc=NOW)

    def test_bad_event_cannot_promote_source_verification(self):
        with self.assertRaisesRegex(ValueError,"SCHEMA_MISMATCH"):
            _append(self.path,event(provenance_status="VERIFIED"),
                    now_utc=NOW)

    def test_bitstamp_wrong_market_url_cannot_be_accepted(self):
        with self.assertRaisesRegex(ValueError,"INVALID_BITSTAMP_SOURCE_URL"):
            _append(self.path,event(
                provider_url="https://www.bitstamp.net/api/v2/ohlc/ethusd/?step=14400&limit=1000&exclude_current_candle=true"),
                now_utc=NOW)

    def test_bitstamp_wrong_interval_url_rejected(self):
        with self.assertRaisesRegex(ValueError,"BITSTAMP_SOURCE_QUERY_NOT_REGISTERED"):
            _append(self.path,event(
                provider_url="https://www.bitstamp.net/api/v2/ohlc/btcusd/?step=86400&limit=1000&exclude_current_candle=true"),
                now_utc=NOW)

    def test_bitstamp_unclosed_query_rejected(self):
        with self.assertRaisesRegex(ValueError,"BITSTAMP_SOURCE_QUERY_NOT_REGISTERED"):
            _append(self.path,event(
                provider_url="https://www.bitstamp.net/api/v2/ohlc/btcusd/?step=14400&limit=1000&exclude_current_candle=false"),
                now_utc=NOW)



if __name__=="__main__":
    unittest.main(verbosity=2)
