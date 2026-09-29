"""Offline fixture tests for OANDA's documented native H4/D candle schema.

These fixtures are NOT a provider response and NOT a forward trade.
"""
import hashlib
import json
import unittest
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlsplit
from zoneinfo import ZoneInfo

from src.data_loader.oanda_h4_adapter import (
    build_historical_read_url, parse_historical_page,
)


def start_time(*, year=2026, month=9, day=29, hour=17):
    return datetime(year,month,day,hour,tzinfo=ZoneInfo("America/New_York"))


def stamp(d):
    return d.astimezone(timezone.utc).isoformat().replace("+00:00","Z")


def candle(d=None, *, complete=True):
    d=d or start_time()
    return {
        "time":stamp(d),"complete":complete,"volume":123,
        "mid":{"o":"1.2000","h":"1.2100","l":"1.1900","c":"1.2050"},
        "bid":{"o":"1.1999","h":"1.2099","l":"1.1899","c":"1.2049"},
        "ask":{"o":"1.2001","h":"1.2101","l":"1.1901","c":"1.2051"},
    }


def parse(rows=None, *, granularity="H4", source="EUR_USD", url=None,
          retrieved=None):
    if rows is None:rows=[candle()]
    url=url or build_historical_read_url(source,granularity=granularity)
    body={"instrument":source,"granularity":granularity,"candles":rows}
    raw=json.dumps(body).encode()
    if retrieved is None:
        retrieved=int(start_time().timestamp())+3*86400
    return parse_historical_page(raw,instrument=source,
                                 granularity=granularity,
                                 retrieved_at_utc=retrieved,
                                 request_url=url)


class Smoke(unittest.TestCase):
    def test_get_only_practice_endpoint_and_native_h4(self):
        url=build_historical_read_url("EUR_USD")
        self.assertTrue(url.startswith("https://api-fxpractice.oanda.com/v3/instruments/EUR_USD/candles?"))
        q=parse_qs(urlsplit(url).query)
        self.assertEqual(q["granularity"],["H4"])
        self.assertEqual(q["price"],["MBA"])
        self.assertEqual(q["smooth"],["false"])
        self.assertEqual(q["dailyAlignment"],["17"])
        self.assertEqual(q["alignmentTimezone"],["America/New_York"])

    def test_reject_live_order_or_bad_instrument(self):
        for symbol in ("EUR/USD","../orders","eur_usd",""):
            with self.subTest(symbol=symbol):
                with self.assertRaises(ValueError):
                    build_historical_read_url(symbol)

    def test_reject_unsupported_tf_and_count(self):
        with self.assertRaises(ValueError):
            build_historical_read_url("EUR_USD",granularity="H1")
        with self.assertRaises(ValueError):
            build_historical_read_url("EUR_USD",count=5001)

    def test_provenance_never_claims_broker_costs(self):
        output=parse()
        self.assertEqual(output["accepted_completed_candles"],1)
        self.assertEqual(output["status"],
                         "PROVIDER_BYTES_PARSED_SOURCE_AND_LICENSE_NOT_AUDITED")
        self.assertFalse(output["verified_account_execution_costs"])
        self.assertEqual(output["broker_order_calls"],0)


class Runtime(unittest.TestCase):
    def test_native_h4_bid_ask_mid_and_source_hash(self):
        output=parse()
        b=output["candles"][0]
        self.assertEqual(b["close_ts"]-b["open_ts"],14400)
        self.assertEqual(b["bid"]["o"],1.1999)
        self.assertEqual(b["ask"]["c"],1.2051)
        self.assertEqual(b["mid"]["c"],1.2050)
        self.assertEqual(len(b["source_record_sha256"]),64)
        self.assertEqual(b["source_id"],"EUR_USD:H4:"+str(b["open_ts"]))

    def test_true_native_d1_boundary_during_dst_change(self):
        # NY 17:00 around DST spring-forward is an exchange-local
        # daily alignment, not a fixed UTC wall-clock time.
        d=start_time(year=2026,month=3,day=7)
        output=parse([candle(d)],granularity="D",
                     retrieved=int(d.timestamp())+2*86400)
        b=output["candles"][0]
        self.assertEqual(b["close_ts"]-b["open_ts"],23*3600)

    def test_weekend_gap_is_flagged_not_synthesized(self):
        d=start_time(year=2026,month=9,day=25)
        rows=[candle(d),candle(d+timedelta(days=3))]
        output=parse(rows)
        self.assertEqual(len(output["candles"]),2)
        self.assertEqual(len(output["gaps_needing_market_calendar_review"]),1)
        self.assertFalse(output["gaps_needing_market_calendar_review"][0]["calendar_verified"])

    def test_explicit_unclosed_bar_rejected_from_acceptance(self):
        d=start_time()
        output=parse([candle(d),candle(d+timedelta(hours=4),complete=False)])
        self.assertEqual(output["accepted_completed_candles"],1)
        self.assertEqual(output["rejected_unclosed"],1)


class Fault(unittest.TestCase):
    def test_disallow_wrong_returned_instrument(self):
        url=build_historical_read_url("EUR_USD")
        raw=json.dumps({"instrument":"GBP_USD","granularity":"H4",
                        "candles":[candle()]}).encode()
        with self.assertRaisesRegex(ValueError,"MISMATCH"):
            parse_historical_page(raw,instrument="EUR_USD",granularity="H4",
                                  retrieved_at_utc=int(start_time().timestamp())+14400,
                                  request_url=url)

    def test_refuse_incomplete_price_component(self):
        c=candle()
        del c["ask"]
        with self.assertRaisesRegex(ValueError,"MISSING_PROVIDER_PRICE_COMPONENT"):
            parse([c])

    def test_crossed_bid_ask_fail_closed(self):
        c=candle()
        c["ask"]["o"]="1.1901"  # valid ask OHLC, but ask.open < bid.open
        with self.assertRaisesRegex(ValueError,"CROSSED"):
            parse([c])

    def test_reject_duplicate_bar(self):
        with self.assertRaisesRegex(ValueError,"DUPLICATE_OR_UNSORTED"):
            parse([candle(),candle()])

    def test_reject_future_complete_candle(self):
        with self.assertRaisesRegex(ValueError,"SOURCE_CLOSE_FUTURE"):
            parse(retrieved=int(start_time().timestamp())+100)

    def test_wrong_request_price_or_alignment(self):
        url=build_historical_read_url("EUR_USD").replace("price=MBA","price=M")
        with self.assertRaisesRegex(ValueError,"ALIGNMENT_OR_PRICE"):
            parse(url=url)

    def test_reject_invalid_candle_timestamp(self):
        c=candle()
        c["time"]="2026-09-29T12:00:00.000000001Z"
        with self.assertRaisesRegex(ValueError,"SUBSECOND"):
            parse([c])

    def test_reject_time_not_ny_aligned(self):
        c=candle(start_time(hour=18))
        with self.assertRaisesRegex(ValueError,"H4_NOT_EXPECTED"):
            parse([c])

    def test_reject_broker_live_host_even_on_read_path(self):
        url=build_historical_read_url("EUR_USD").replace(
            "api-fxpractice","api-fxtrade")
        with self.assertRaisesRegex(ValueError,"NOT_APPROVED"):
            parse(url=url)

    def test_reject_nonfinite_market_value(self):
        c=candle()
        c["mid"]["c"]="NaN"
        with self.assertRaisesRegex(ValueError,"INVALID_mid_OHLC"):
            parse([c])

    def test_reject_bool_volume(self):
        c=candle()
        c["volume"]=True
        with self.assertRaisesRegex(ValueError,"INVALID_TICK_VOLUME"):
            parse([c])


if __name__=="__main__":
    unittest.main(verbosity=2)
