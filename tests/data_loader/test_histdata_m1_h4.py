"""HistData converter tests use synthetic EST-fixed CSV only, not market prices."""
import hashlib
import unittest
from datetime import datetime, timedelta, timezone

from src.data_loader.histdata_m1_h4 import (
    EST_FIXED, H4_SECONDS, MINUTES_PER_H4, derive_complete_h4,
)


def fixture(*, count=240, missing=(), hour=17, month=9, day=29):
    start=datetime(2026,month,day,hour,tzinfo=EST_FIXED)
    rows=[]
    for n in range(count):
        if n in missing: continue
        d=start+timedelta(minutes=n)
        base=1.1+n/1_000_000
        rows.append((d.strftime("%Y%m%d %H%M%S")+";"+
                    f"{base:.6f};{base+.0002:.6f};"+
                    f"{base-.0002:.6f};{base+.0001:.6f};0").encode())
    return b"\n".join(rows)+b"\n"


def now(data=None):
    return int(datetime(2026,9,30,tzinfo=timezone.utc).timestamp())+86400


class Smoke(unittest.TestCase):
    def test_expected_fixed_timezone_no_dst(self):
        self.assertEqual(EST_FIXED.utcoffset(None),timedelta(hours=-5))
        self.assertEqual(H4_SECONDS,14400)
        self.assertEqual(MINUTES_PER_H4,240)

    def test_one_full_h4_requires_240_minutes(self):
        raw=fixture()
        out=derive_complete_h4(raw,symbol="EURUSD",received_at_utc=now())
        self.assertEqual(out["h4_emitted"],1)
        self.assertEqual(out["h4_blocks_rejected"],0)
        self.assertEqual(out["bars"][0]["m1_count"],240)
        self.assertFalse(out["bars"][0]["native_h4"])
        self.assertEqual(out["raw_sha256"],hashlib.sha256(raw).hexdigest())

    def test_unsupported_source_symbol_rejected(self):
        with self.assertRaisesRegex(ValueError,"UNREGISTERED"):
            derive_complete_h4(fixture(),symbol="BTCUSD",received_at_utc=now())

    def test_bid_is_not_ask_or_mt5(self):
        out=derive_complete_h4(fixture(),symbol="XAUUSD",
                               received_at_utc=now())
        self.assertFalse(out["ask_or_spread_available"])
        self.assertFalse(out["source_native_mt5"])
        self.assertFalse(out["verified_after_cost_pnl_available"])
        self.assertEqual(out["input_provenance"],"UNVERIFIED_USER_SUPPLIED_BYTES")


class Runtime(unittest.TestCase):
    def test_synthetic_two_consecutive_h4_blocks(self):
        out=derive_complete_h4(fixture(count=480),symbol="EURGBP",
                               received_at_utc=now())
        self.assertEqual(out["h4_emitted"],2)
        self.assertEqual(out["h4_blocks_rejected"],0)
        self.assertEqual(out["bars"][1]["open_ts"]-out["bars"][0]["open_ts"],
                         14400)
        self.assertEqual(out["m1_observations"],480)

    def test_exact_source_bid_ohlc_rollup(self):
        out=derive_complete_h4(fixture(),symbol="USDJPY",
                               received_at_utc=now())
        b=out["bars"][0]
        self.assertEqual(b["open_bid"],"1.100000")
        self.assertEqual(b["high_bid"],"1.100439")
        self.assertEqual(b["low_bid"],"1.099800")
        self.assertEqual(b["close_bid"],"1.100339")

    def test_est_fixed_in_july_still_22_utc(self):
        start=datetime(2026,7,1,17,tzinfo=EST_FIXED)
        out=derive_complete_h4(fixture(month=7,day=1),
                               symbol="AUDUSD",received_at_utc=now())
        self.assertEqual(out["bars"][0]["open_ts"],
                         int(start.astimezone(timezone.utc).timestamp()))
        self.assertEqual(start.astimezone(timezone.utc).hour,22)

    def test_incomplete_first_and_complete_second(self):
        out=derive_complete_h4(fixture(count=480,missing=(100,)),
                               symbol="EURJPY",received_at_utc=now())
        self.assertEqual(out["h4_emitted"],1)
        self.assertEqual(out["h4_blocks_rejected"],1)
        self.assertEqual(out["h4_rejected_samples"][0]["missing_minutes"],1)


class Fault(unittest.TestCase):
    def test_m1_missing_in_middle_does_not_forward_fill(self):
        out=derive_complete_h4(fixture(missing=(123,)),
                               symbol="EURUSD",received_at_utc=now())
        self.assertEqual(out["h4_emitted"],0)
        self.assertEqual(out["h4_blocks_rejected"],1)
        self.assertEqual(out["bars"],[])

    def test_duplicate_m1_timestamp_rejected(self):
        lines=fixture().splitlines()
        lines.insert(15,lines[14])
        with self.assertRaisesRegex(ValueError,"DUPLICATE_OR_UNSORTED"):
            derive_complete_h4(b"\n".join(lines),symbol="EURUSD",
                               received_at_utc=now())

    def test_reversed_source_rows_rejected(self):
        lines=fixture().splitlines()
        lines[12],lines[13]=lines[13],lines[12]
        with self.assertRaisesRegex(ValueError,"DUPLICATE_OR_UNSORTED"):
            derive_complete_h4(b"\n".join(lines),symbol="EURUSD",
                               received_at_utc=now())

    def test_incorrect_candle_ohlc_rejected(self):
        lines=fixture().splitlines()
        lines[25]=lines[25].split(b";")[0]+b";1.2;1.1;1.0;1.2;0"
        with self.assertRaisesRegex(ValueError,"INVALID_OHLC"):
            derive_complete_h4(b"\n".join(lines),symbol="EURUSD",
                               received_at_utc=now())

    def test_future_m1_rejected(self):
        raw=fixture()
        first=int(datetime(2026,9,29,17,tzinfo=EST_FIXED).timestamp())
        with self.assertRaisesRegex(ValueError,"UNCLOSED_OR_FUTURE"):
            derive_complete_h4(raw,symbol="EURUSD",
                               received_at_utc=first+30)

    def test_bad_decimal_nan_rejected(self):
        lines=fixture().splitlines()
        parts=lines[12].split(b";")
        parts[1]=b"NaN"
        lines[12]=b";".join(parts)
        with self.assertRaisesRegex(ValueError,"INVALID_OPEN_DECIMAL"):
            derive_complete_h4(b"\n".join(lines),symbol="EURUSD",
                               received_at_utc=now())

    def test_non_m1_second_timestamp_rejected(self):
        lines=fixture().splitlines()
        lines[12]=lines[12].replace(b"001200",b"001201",1)
        with self.assertRaisesRegex(ValueError,"NOT_M1_ALIGNED"):
            derive_complete_h4(b"\n".join(lines),symbol="EURUSD",
                               received_at_utc=now())

    def test_unaligned_session_drops_both_partial_buckets(self):
        out=derive_complete_h4(fixture(hour=18),symbol="EURUSD",
                               received_at_utc=now())
        self.assertEqual(out["h4_emitted"],0)
        self.assertEqual(out["h4_blocks_rejected"],2)

    def test_invalid_binary_rejected(self):
        with self.assertRaisesRegex(ValueError,"INVALID_BINARY"):
            derive_complete_h4(b"ab\x00cd",symbol="EURUSD",
                               received_at_utc=now())

    def test_no_source_observations_rejected(self):
        with self.assertRaisesRegex(ValueError,"NO_VALID"):
            derive_complete_h4(b"\n",symbol="EURUSD",
                               received_at_utc=now())

    def test_wrong_format_comma_rejected(self):
        with self.assertRaisesRegex(ValueError,"INVALID_HISTDATA"):
            derive_complete_h4(
                b"20260929 170000,1.1,1.2,1.0,1.1,0\n",
                symbol="EURUSD",received_at_utc=now())


if __name__=="__main__":
    unittest.main(verbosity=2)
