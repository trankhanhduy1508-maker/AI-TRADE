"""Deterministic synthetic stress for method-state invariants; not performance QA."""
import random
import unittest
from dataclasses import replace
from src.research.method_lab_v1 import ClosedBar, ResearchMethod
from tests.research.test_method_lab_v1 import BASE, DAY, candle, rising, breakout


class Smoke(unittest.TestCase):
    def test_h4_uses_same_causal_rule_and_zero_orders(self):
        m = ResearchMethod(symbol='SYN_H4', timeframe='H4', source_clock_verified=True)
        for b in rising(n=250, period=14400):
            o = m.on_bar(b)
            self.assertEqual(o['orders_sent'], 0)
        out = m.on_bar(breakout(period=14400))
        self.assertEqual(out['signal_reason'], 'CONFIRMED_LONG')
        self.assertTrue(out['pending_next_open'])


class Runtime(unittest.TestCase):
    def test_seeded_1000_bar_stream_is_deterministic_and_stop_never_loosens(self):
        rng = random.Random(20260929)
        bars, prev = [], 100.0
        for i in range(1000):
            close = max(.01, prev + .045 + rng.uniform(-.4, .4))
            high = max(prev, close) + .2 + rng.random()*.2
            low = min(prev, close) - .2 - rng.random()*.2
            bars.append(candle(i, prev, high, low, close))
            prev = close
        a = ResearchMethod(symbol='SYN', timeframe='D1', source_clock_verified=True)
        b = ResearchMethod(symbol='SYN', timeframe='D1', source_clock_verified=True)
        prev_state = None
        for x in bars:
            left, right = a.on_bar(x), b.on_bar(x)
            self.assertEqual(left, right)
            self.assertEqual(left['orders_sent'], 0)
            self.assertEqual(left['edge_status'], 'UNPROVEN')
            self.assertEqual(left['cost_status'], 'NOT_EVALUATED')
            now = a.snapshot()['position']
            if now is not None and prev_state is not None and now['entry_ts']==prev_state['entry_ts']:
                self.assertGreaterEqual(now['stop'], prev_state['stop'])
            prev_state = now
        self.assertEqual(a.snapshot(), b.snapshot())
        self.assertEqual(len(a.bars), 1000)
        self.assertLessEqual(len(a._atr_history), 101)

    def test_closed_loss_quarantine_never_uses_open_trade_marks(self):
        m = ResearchMethod(symbol='SYN', timeframe='D1', source_clock_verified=True)
        for bar in rising(n=250):
            m.on_bar(bar)
        m.on_bar(breakout())
        m.on_bar(candle(251, 110.3, 110.8, 109.8, 110.5))
        self.assertTrue(m.position is not None)
        self.assertEqual(len(m.recent_closed_loss), 0)
        self.assertEqual(m.quarantine_eligible_at, 0)


class Fault(unittest.TestCase):
    def test_200_invalid_mutations_are_atomic(self):
        m = ResearchMethod(symbol='SYN', timeframe='D1', source_clock_verified=True)
        for bar in rising(n=250):
            m.on_bar(bar)
        state=m.snapshot()
        for i in range(200):
            valid=candle(250, 108, 109, 107, 108.5)
            bad=(replace(valid, ts=m.bars[-1].ts),
                 replace(valid, high=1.0),
                 replace(valid, low=float('nan')),
                 replace(valid, captured_at_utc=valid.close_at_utc-1))[i%4]
            with self.assertRaises(ValueError):
                m.on_bar(bad)
            self.assertEqual(m.snapshot(),state)

    def test_unapproved_session_gap_never_backfills(self):
        m=ResearchMethod(symbol='SYN', timeframe='H4', source_clock_verified=True)
        m.on_bar(rising(n=1, period=14400)[0])
        s=m.snapshot()
        with self.assertRaisesRegex(ValueError,'CALENDAR_GAP_UNVERIFIED'):
            m.on_bar(candle(2,100,102,99,101,period=14400,gap_verified=True))
        self.assertEqual(m.snapshot(),s)


if __name__ == '__main__':
    unittest.main(verbosity=2)
