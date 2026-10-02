"""Synthetic-only tests. No Kraken or broker calls and no market observations."""
import hashlib
import json
import unittest
from src.data_loader.kraken_native_h4 import parse_kraken_spot_h4

T = 1_800_000_000 // 14_400 * 14_400


def row(start):
    return [start, "10", "12", "9", "11", "10.5", "3.4", 8]


def payload(rows=None, *, pair="BTC/USD", error=None):
    return json.dumps({"error": [] if error is None else error,
                       "result": {pair: rows if rows is not None else
                                  [row(T), row(T + 14_400)], "last": T + 14_400}}).encode()


def parse(raw=None, **kw):
    return parse_kraken_spot_h4(raw if raw is not None else payload(),
                                symbol=kw.pop("symbol", "BTCUSD"),
                                retrieved_at_utc=kw.pop("retrieved_at_utc", T + 14_401))


class Smoke(unittest.TestCase):
    def test_native_classification_no_fee_or_forward_claim(self):
        raw = payload()
        out = parse(raw)
        self.assertEqual(out["completed_h4"], 1)
        self.assertEqual(out["discarded_current_candle"], 1)
        self.assertTrue(out["bars"][0]["native_h4"])
        self.assertFalse(out["broker_mt5_equivalent"])
        self.assertFalse(out["venue_execution_costs_verified"])
        self.assertFalse(out["independent_forward"])
        self.assertEqual(out["raw_sha256"], hashlib.sha256(raw).hexdigest())

    def test_eth_pair(self):
        self.assertEqual(parse(payload(pair="ETH/USD"), symbol="ETHUSD")["venue_pair"], "ETH/USD")


class Runtime(unittest.TestCase):
    def test_two_closed_rows_last_open_row_is_dropped(self):
        out = parse(payload([row(T), row(T + 14_400), row(T + 28_800)]),
                    retrieved_at_utc=T + 28_801)
        self.assertEqual(out["completed_h4"], 2)
        self.assertEqual(out["bars"][1]["open_ts"], T + 14_400)

    def test_last_candle_dropped_even_when_clock_far_ahead(self):
        self.assertEqual(parse(retrieved_at_utc=T + 999_999)["completed_h4"], 1)


class Fault(unittest.TestCase):
    def test_missing_4h_row_rejected(self):
        with self.assertRaisesRegex(ValueError, "GAP_DUPLICATE"):
            parse(payload([row(T), row(T + 28_800), row(T + 43_200)]),
                  retrieved_at_utc=T + 43_201)

    def test_open_row_never_promoted_to_closed(self):
        with self.assertRaisesRegex(ValueError, "NO_COMPLETED"):
            parse(payload([row(T)]))

    def test_future_completed_row_rejected(self):
        with self.assertRaisesRegex(ValueError, "UNCLOSED_OR_FUTURE"):
            parse(retrieved_at_utc=T + 5)

    def test_foreign_pair_rejected(self):
        with self.assertRaisesRegex(ValueError, "PROVIDER_PAIR"):
            parse(payload(pair="ETH/USD"))

    def test_provider_error_rejected(self):
        with self.assertRaisesRegex(ValueError, "PROVIDER_RETURNED_ERROR"):
            parse(payload(error=["EQuery:Unknown asset pair"]))

    def test_invalid_ohlc_rejected(self):
        x = row(T)
        x[2] = "8"
        with self.assertRaisesRegex(ValueError, "INVALID_H4_OHLC"):
            parse(payload([x, row(T + 14_400)]))

    def test_duplicate_json_key_rejected(self):
        with self.assertRaisesRegex(ValueError, "DUPLICATE_JSON_KEY"):
            parse(b'{"error":[],"error":[],"result":{}}')

    def test_unregistered_pair_rejected(self):
        with self.assertRaisesRegex(ValueError, "UNREGISTERED_KRAKEN_PAIR"):
            parse(symbol="EURUSD")

    def test_unsorted_or_duplicate_rejected(self):
        with self.assertRaisesRegex(ValueError, "GAP_DUPLICATE"):
            parse(payload([row(T), row(T), row(T + 14_400)]))


if __name__ == "__main__":
    unittest.main()
