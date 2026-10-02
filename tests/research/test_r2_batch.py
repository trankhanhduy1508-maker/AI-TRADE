"""Batch tests: missing sources and tiny fixtures, never market data."""
import math
import tempfile
import unittest
from pathlib import Path
from src.research.r2_batch import run_batch

START=1420070400


def entry(**changes):
    x={"cell":"SYNTHETIC_D1","symbol":"SYNTHETIC","timeframe":"D1",
       "source_kind":"NATIVE_D1","csv_path":None,
       "research_rights_confirmed":False,"session":"24_7",
       "allow_short":False,"assumed_round_trip_cost_price":0.0}
    x.update(changes)
    return x


class Smoke(unittest.TestCase):
    def test_source_not_available_is_explicit(self):
        x=run_batch([entry()],as_of_utc=START+1000*86400)
        self.assertEqual(x['cells']['SYNTHETIC_D1']['status'],
                         'RESEARCH_RIGHTS_NOT_CONFIRMED')
        self.assertEqual(x['orders_sent'],0)


class Runtime(unittest.TestCase):
    def test_real_parser_synthetic_csv_is_historical_not_forward(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'synthetic.csv'
            prev=100.
            with p.open('w') as f:
                f.write('open_ts_utc,open,high,low,close\n')
                for i in range(1000):
                    c=100+.01*i+7*math.sin(i/11)
                    f.write(f'{START+i*86400},{prev},{max(prev,c)+1},{min(prev,c)-1},{c}\n')
                    prev=c
            x=run_batch([entry(csv_path=str(p),research_rights_confirmed=True)],
                        as_of_utc=START+1000*86400)
            c=x['cells']['SYNTHETIC_D1']
            self.assertEqual(c['status'],'HISTORICAL_REUSED_DESCRIPTIVE_ONLY')
            self.assertEqual(c['episode_count'],2)
            self.assertEqual(c['independent_forward_trades'],0)
            self.assertFalse(c['research_rights_independently_verified'])
            self.assertIsNone(c['account_currency_pnl'])
            self.assertNotIn('100.0,101.0,99.0',str(x))


class Fault(unittest.TestCase):
    def test_future_clock_rejected_even_when_data_missing(self):
        with self.assertRaisesRegex(ValueError,'INVALID_AS_OF_CLOCK'):
            run_batch([entry()],as_of_utc=9999999999)

    def test_duplicate_cells_rejected(self):
        with self.assertRaisesRegex(ValueError,'DUPLICATE_OR_EMPTY_CELL'):
            run_batch([entry(),entry()],as_of_utc=START+1000*86400)

    def test_no_rights_never_attempts_missing_file(self):
        x=run_batch([entry(csv_path='/nonexistent/raw.csv')],
                    as_of_utc=START+1000*86400)
        self.assertEqual(x['cells']['SYNTHETIC_D1']['status'],
                         'RESEARCH_RIGHTS_NOT_CONFIRMED')

    def test_no_source_is_not_backtest(self):
        x=run_batch([entry(research_rights_confirmed=True)],
                    as_of_utc=START+1000*86400)
        self.assertEqual(x['cells_with_historical_exploratory_results'],0)

    def test_invalid_schema_rejected(self):
        with self.assertRaisesRegex(ValueError,'INVALID_CATALOG_SCHEMA'):
            run_batch([entry(unapproved_field='yes')],
                      as_of_utc=START+1000*86400)


if __name__=='__main__': unittest.main()
