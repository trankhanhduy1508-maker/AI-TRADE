"""Synthetic input tests, never read real market data or make a claim about it."""
import tempfile
import unittest
from pathlib import Path
from src.research.r2_csv import load_normalized_ohlc


class Base(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.p=Path(self.temp.name)/'synthetic.csv'


class Smoke(Base):
    def test_normalized_csv_is_read_without_network(self):
        self.p.write_text('open_ts_utc,open,high,low,close\n1420070400,1,2,.5,1.5\n')
        bars, sha=load_normalized_ohlc(self.p)
        self.assertEqual(len(bars),1)
        self.assertEqual(bars[0].ts,1420070400)
        self.assertEqual(len(sha),64)


class Runtime(Base):
    def test_bom_and_two_rows(self):
        self.p.write_bytes(b'\xef\xbb\xbfopen_ts_utc,open,high,low,close\n1420070400,1,2,.5,1.5\n1420156800,2,3,1,2\n')
        bars,_=load_normalized_ohlc(self.p)
        self.assertEqual(len(bars),2)


class Fault(Base):
    def test_date_only_is_not_invented_utc(self):
        self.p.write_text('open_ts_utc,open,high,low,close\n2026-01-01,1,2,.5,1.5\n')
        with self.assertRaisesRegex(ValueError,'UTC_EPOCH_REQUIRED'):
            load_normalized_ohlc(self.p)

    def test_close_only_is_not_fabricated_ohlc(self):
        self.p.write_text('Date,Close\n2026-01-01,100\n')
        with self.assertRaisesRegex(ValueError,'REQUIRES_NORMALIZED'):
            load_normalized_ohlc(self.p)

    def test_extra_column_rejected(self):
        self.p.write_text('open_ts_utc,open,high,low,close\n1420070400,1,2,.5,1.5,secret\n')
        with self.assertRaisesRegex(ValueError,'UNEXPECTED_CSV_FIELD'):
            load_normalized_ohlc(self.p)

    def test_binary_rejected(self):
        self.p.write_bytes(b'\x00')
        with self.assertRaisesRegex(ValueError,'INVALID_RAW_CSV'):
            load_normalized_ohlc(self.p)


if __name__=='__main__': unittest.main()
