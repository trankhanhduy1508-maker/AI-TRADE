"""Synthetic-only, never real market PnL or independently new OOS."""
import hashlib
import math
import unittest
from dataclasses import replace
from src.research.r2_walkforward import Bar, Study, _play, run_walkforward, CANDIDATES

DAY = 86400
START = 1420070400


def fixture(n=1750, *, interval=DAY):
    result = []
    last = 100.0
    for i in range(n):
        p = 100 + i*.009 + 7*math.sin(i/11) + 1.2*math.sin(i/2.5)
        o = last
        result.append(Bar(START+i*interval, o, max(o,p)+1,
                          min(o,p)-1, p))
        last = p
    return result


def source(tf='D1', kind='NATIVE_D1', **changes):
    data = dict(symbol='SYNTHETIC', timeframe=tf, source_kind=kind,
                source_sha256=hashlib.sha256(b'R2-SYNTHETIC-FIXTURE').hexdigest(),
                exposure='SYNTHETIC_FIXTURE', session='24_7',
                allow_short=False, assumed_round_trip_cost_price=0.0)
    data.update(changes)
    return Study(**data)


class Smoke(unittest.TestCase):
    def test_frozen_candidate_and_step(self):
        self.assertEqual(tuple(x[0] for x in CANDIDATES),
                         ('R0_REFERENCE','R2_FAST','R2_SLOW'))
        out = run_walkforward(fixture(1000), study=source(),
                              as_of_utc=START+1000*DAY)
        self.assertEqual(out['episode_count'], 2)
        self.assertEqual(out['independent_forward_trades'], 0)
        self.assertEqual(out['edge_status'], 'UNPROVEN')
        self.assertEqual(out['orders_sent'], 0)

    def test_h4_derived_is_properly_classified(self):
        b = fixture(1000, interval=14400)
        out = run_walkforward(b, study=source('H4','DERIVED_H4_BID_ONLY'),
                              as_of_utc=START+1000*14400)
        self.assertEqual(out['source_kind'], 'DERIVED_H4_BID_ONLY')
        self.assertEqual(out['fee_status'], 'GROSS_ONLY')


class Runtime(unittest.TestCase):
    def test_repeated_folds_use_only_past(self):
        data=fixture()
        out=run_walkforward(data,study=source(),as_of_utc=START+len(data)*DAY)
        self.assertEqual(out['episode_count'],5)
        self.assertEqual([e['decision_bar_index'] for e in out['episodes']],
                         [500,750,1000,1250,1500])
        self.assertTrue(all(e['training_bar_count']<=1000 for e in out['episodes']))
        self.assertTrue(all(e['status']=='SYNTHETIC_TEST_ONLY' for e in out['episodes']))

    def test_future_suffixed_prices_do_not_change_prior_folds(self):
        original=fixture(1750)
        altered=list(original)
        for i in range(1500,1750):
            b=altered[i]
            altered[i]=Bar(b.ts, b.open, 1000000.0, .0001, 999999.0)
        cutoff=START+1500*DAY
        a=run_walkforward(original,study=source(),as_of_utc=cutoff)
        b=run_walkforward(altered,study=source(),as_of_utc=cutoff)
        self.assertEqual(a,b)
        self.assertEqual(a['ignored_unclosed_or_future_bars'],250)

    def test_replay_is_bitwise_deterministic(self):
        b=fixture(1250)
        a=run_walkforward(b,study=source(),as_of_utc=START+1250*DAY)
        self.assertEqual(a,run_walkforward(b,study=source(),as_of_utc=START+1250*DAY))

    def test_costs_are_modeled_never_verified(self):
        b=fixture(1000)
        x=run_walkforward(b,study=source(assumed_round_trip_cost_price=.15),
                          as_of_utc=START+1000*DAY)
        self.assertEqual(x['fee_status'],'MODELED_ONLY')
        self.assertIsNone(x['account_currency_pnl'])
        for e in x['episodes']:
            if e['selected'] != 'FLAT':
                self.assertLessEqual(e['modeled_cost_stress']['2x']['realized_r'],
                                     e['realized_r']+1e-12)
                self.assertLessEqual(e['modeled_cost_stress']['3x']['realized_r'],
                                     e['modeled_cost_stress']['2x']['realized_r']+1e-12)


class Fault(unittest.TestCase):
    def test_single_price_series_does_not_become_ohlc(self):
        with self.assertRaisesRegex(ValueError,'UNREGISTERED_SOURCE_KIND'):
            run_walkforward(fixture(1000), study=source(kind='SINGLE_PRICE_D1'),
                            as_of_utc=START+1000*DAY)

    def test_unverified_future_label_rejected(self):
        with self.assertRaisesRegex(ValueError,'FORWARD_CLAIM_FORBIDDEN'):
            run_walkforward(fixture(1000),study=source(exposure='INDEPENDENT_FORWARD'),
                            as_of_utc=START+1000*DAY)

    def test_bad_ohlc_is_rejected(self):
        b=fixture(1000)
        b[700]=Bar(b[700].ts,1,2,3,1)
        with self.assertRaisesRegex(ValueError,'INVALID_OHLC'):
            run_walkforward(b,study=source(),as_of_utc=START+1000*DAY)

    def test_duplicate_or_unsorted_rejected(self):
        b=fixture(1000)
        b[700]=replace(b[700],ts=b[699].ts)
        with self.assertRaisesRegex(ValueError,'DUPLICATE_UNSORTED'):
            run_walkforward(b,study=source(),as_of_utc=START+1000*DAY)

    def test_24_7_gap_rejected(self):
        b=fixture(1000)
        del b[700]
        with self.assertRaisesRegex(ValueError,'UNVERIFIED_GAP'):
            run_walkforward(b,study=source(),as_of_utc=START+1000*DAY)

    def test_short_flag_requires_boolean(self):
        with self.assertRaisesRegex(ValueError,'SHORT_VEHICLE_NOT_VERIFIED'):
            run_walkforward(fixture(1000),study=source(allow_short='false'),
                            as_of_utc=START+1000*DAY)

    def test_stop_gaps_execute_at_worse_open(self):
        # First 250 bars provide real indicator warmup, not a claim of real prices.
        b=fixture(251)
        for i in range(200,210):
            b[i]=Bar(b[i].ts,100.0,101.0,99.0,100.0)
        b[210]=Bar(b[210].ts,100.0,151.0,99.0,150.0)
        b[211]=Bar(b[211].ts,155.0,159.0,151.0,156.0)
        b[212]=Bar(b[212].ts,1.0,2.0,.5,1.0)
        out=_play(b,200,250,CANDIDATES[0],short=False,cost=0)
        self.assertGreaterEqual(out['gap_stops'],1)

    def test_invalid_cost_rejected(self):
        with self.assertRaisesRegex(ValueError,'INVALID_COST_SCENARIO'):
            run_walkforward(fixture(1000),study=source(assumed_round_trip_cost_price=float('nan')),
                            as_of_utc=START+1000*DAY)

    def test_unclosed_suffix_not_backfilled(self):
        x=run_walkforward(fixture(1000),study=source(),as_of_utc=START+900*DAY)
        self.assertEqual(x['completed_input_bars'],900)
        self.assertEqual(x['ignored_unclosed_or_future_bars'],100)

    def test_wrong_tf_rejected(self):
        with self.assertRaisesRegex(ValueError,'SOURCE_TIMEFRAME_MISMATCH'):
            run_walkforward(fixture(1000),study=source('H4','NATIVE_D1'),
                            as_of_utc=START+1000*DAY)


if __name__ == '__main__':
    unittest.main(verbosity=2)
