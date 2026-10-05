"""All scenarios are SYNTHETIC; no real feed, account or profitability claim."""
from dataclasses import replace
import math
import unittest

from src.research.method_lab_v1 import (
    ClosedBar, Position, ResearchMethod, signal_from_closed_history,
    BREAKOUT_ATR_BUFFER, BODY_ATR_MIN, STOP_COOLDOWN_BARS,
    FEEDBACK_PAUSE_BARS, CHANNEL, SPEC_COMMIT,
)

BASE = 1577836800  # 2020-01-01 UTC
DAY = 86400


def candle(i, o, h, l, c, *, period=DAY, gap_verified=False,
           closed=True, ts=None, captured=None):
    ts = BASE + i * period if ts is None else ts
    return ClosedBar(ts, float(o), float(h), float(l), float(c),
                     ts + period, ts + period + 1 if captured is None else captured,
                     closed, gap_verified)


def rising(start=0, n=250, *, period=DAY):
    out = []
    last = 100.0 + .03 * start
    for i in range(start, start+n):
        c = 100.0 + .03 * (i+1)
        out.append(candle(i, last, max(last, c)+.4, min(last, c)-.4,
                          c, period=period))
        last = c
    return out


def breakout(i=250, *, period=DAY):
    previous = 100.0 + .03 * i
    close = previous + 2.5
    return candle(i, previous, close+.1, previous-.4, close, period=period)


def instrument(*, period='D1'):
    return ResearchMethod(symbol='SYNTHETIC_ONLY', timeframe=period,
                          source_clock_verified=True)


def primed(*, n=250):
    engine = instrument()
    for b in rising(n=n):
        engine.on_bar(b)
    return engine


class Smoke(unittest.TestCase):
    def test_constants_and_research_contract(self):
        self.assertEqual(CHANNEL, 55)
        self.assertEqual(BREAKOUT_ATR_BUFFER, .25)
        self.assertEqual(BODY_ATR_MIN, .5)
        self.assertEqual(STOP_COOLDOWN_BARS, 5)
        self.assertEqual(FEEDBACK_PAUSE_BARS, 20)
        self.assertEqual(SPEC_COMMIT, '750bb1a68c5b8fa90e116ae08feff5eb10f0d2d4')
        engine = instrument()
        output = engine.on_bar(rising(n=1)[0])
        self.assertEqual(output['orders_sent'], 0)
        self.assertEqual(output['cost_status'], 'NOT_EVALUATED')
        self.assertEqual(output['edge_status'], 'UNPROVEN')
        self.assertFalse(output['data_source_independently_verified'])
        self.assertEqual(output['signal_reason'], 'INDICATORS_NOT_READY')

    def test_strong_confirmed_breakout_only_next_open(self):
        engine = primed()
        signal = engine.on_bar(breakout())
        self.assertEqual(signal['signal_reason'], 'CONFIRMED_LONG')
        self.assertTrue(signal['pending_next_open'])
        self.assertFalse(signal['hypothetical_position'])
        self.assertEqual(signal['orders_sent'], 0)

    def test_wick_only_breakout_is_rejected(self):
        engine = primed()
        previous = 100 + .03*250
        b = candle(250, previous, previous+3, previous-.4, previous+.1)
        signal = engine.on_bar(b)
        self.assertEqual(signal['signal_reason'], 'BREAKOUT_NOT_CONFIRMED')
        self.assertFalse(signal['pending_next_open'])
        self.assertIn('LONG_CHANNEL_BUFFER', signal['failed_signal_checks'])
        self.assertIn('LONG_STRONG_BODY', signal['failed_signal_checks'])
        self.assertGreater(engine.snapshot()['diagnostic_counts']['LONG_CHANNEL_BUFFER'], 0)


class Runtime(unittest.TestCase):
    def test_entry_at_following_open_then_gap_worse(self):
        engine = primed()
        entry_signal = engine.on_bar(breakout())
        stop = engine.pending[1]
        entry = candle(251, 110.3, 110.8, 109.8, 110.5)
        opened = engine.on_bar(entry)
        self.assertTrue(opened['hypothetical_position'])
        self.assertFalse(opened['pending_next_open'])
        self.assertEqual(engine.position.entry_ts, entry.ts)
        self.assertAlmostEqual(engine.position.entry, entry.open)
        self.assertEqual(engine.position.initial_stop, stop)
        exit_bar = candle(252, stop-5, stop-4, stop-6, stop-5.5)
        closed = engine.on_bar(exit_bar)
        self.assertFalse(closed['hypothetical_position'])
        self.assertEqual(engine.closed_events[0]['exit_reason'], 'GAP_STOP')
        self.assertEqual(engine.closed_events[0]['exit_price'], exit_bar.open)
        self.assertLess(engine.closed_events[0]['gross_r'], -1)
        self.assertEqual(closed['signal_reason'], 'EXIT_BAR_NO_REENTRY')
        self.assertEqual(closed['closed_trade_count'], 1)

    def test_position_carries_across_arbitrary_fold_boundary(self):
        engine = primed()
        engine.on_bar(breakout())
        engine.on_bar(candle(251, 110.3, 110.8, 109.8, 110.5))
        self.assertIsNotNone(engine.position)
        for i in range(252, 505):
            c = 110.5 + .05*(i-251)
            engine.on_bar(candle(i, c-.05, c+.4, c-.35, c))
        self.assertIsNotNone(engine.position)
        self.assertEqual(engine.position.entry_ts, BASE+251*DAY)
        self.assertGreater(engine.position.stop, engine.position.initial_stop)
        self.assertEqual(len(engine.closed_events), 0)
        self.assertEqual(len(engine.bars), 505)

    def test_prefix_immune_to_any_future_bars(self):
        a = primed()
        b = primed()
        original = a.on_bar(breakout())
        self.assertEqual(original, b.on_bar(breakout()))
        prefix = a.snapshot()
        b.on_bar(candle(251, 100, 101, 99, 100))
        self.assertEqual(a.snapshot(), prefix)
        self.assertEqual(a.snapshot()['pending'], prefix['pending'])

    def test_quarantine_uses_only_closed_losses(self):
        engine = primed()
        engine.recent_closed_loss.extend([True, True, False, True])
        engine.on_bar(breakout())
        engine.on_bar(candle(251, 110.3, 110.8, 109.8, 110.5))
        exit_bar = candle(252, 100, 101, 99, 100)
        out = engine.on_bar(exit_bar)
        self.assertTrue(any(e['kind']=='QUARANTINE_FROM_CLOSED_LOSSES'
                            for e in out['events']))
        self.assertEqual(engine.quarantine_eligible_at, 252+21)
        self.assertEqual(engine.recent_closed_loss.count(True), 4)
        for i in range(253, 259):
            last = 100+.03*i
            out = engine.on_bar(candle(i, last, last+.5, last-.5, last+.1))
            self.assertEqual(out['signal_reason'], 'CLOSED_LOSS_QUARANTINE')
        self.assertEqual(out['orders_sent'], 0)

    def test_large_atr_shock_abstains(self):
        b = rising(n=220)
        b[-1] = breakout(219)
        x = signal_from_closed_history(b, [1.0]*100+[2.1])
        self.assertEqual(x.reason, 'VOLATILITY_SHOCK')

    def test_short_requires_explicit_permission(self):
        b = rising(n=220)
        x = signal_from_closed_history(b, [1.0]*101, short_allowed=False)
        self.assertEqual(x.direction, 0)
        self.assertEqual(x.reason, 'BREAKOUT_NOT_CONFIRMED')


class Fault(unittest.TestCase):
    def test_no_unverified_clock(self):
        engine = ResearchMethod(symbol='SYN', timeframe='D1')
        with self.assertRaisesRegex(ValueError, 'SOURCE_CLOCK_UNVERIFIED'):
            engine.on_bar(rising(n=1)[0])
        self.assertEqual(len(engine.bars), 0)

    def test_duplicate_and_unsorted_fail_without_state_change(self):
        engine = primed()
        snap = engine.snapshot()
        with self.assertRaisesRegex(ValueError, 'BAR_DUPLICATE_OR_REORDERED'):
            engine.on_bar(engine.bars[-1])
        self.assertEqual(engine.snapshot(), snap)

    def test_missing_bar_requires_verified_calendar(self):
        engine = primed()
        snap = engine.snapshot()
        bar = candle(251, 108, 109, 107, 108.5)
        with self.assertRaisesRegex(ValueError, 'CALENDAR_GAP_UNVERIFIED'):
            engine.on_bar(bar)
        self.assertEqual(engine.snapshot(), snap)

    def test_attested_gap_only_with_boolean_flags(self):
        engine = ResearchMethod(symbol='SYN', timeframe='D1',
                                source_clock_verified=True, calendar_audited=True)
        engine.on_bar(rising(n=1)[0])
        with self.assertRaisesRegex(ValueError, 'CALENDAR_GAP_UNVERIFIED'):
            engine.on_bar(candle(2, 100, 102, 99, 101, gap_verified=False))
        accepted = engine.on_bar(candle(2, 100, 102, 99, 101, gap_verified=True))
        self.assertEqual(accepted['bar_index'], 1)
        self.assertFalse(accepted['data_source_independently_verified'])

    def test_string_flags_never_authorized(self):
        for bad in ('true', 'false', 1, 0, None):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ValueError, 'AUDIT_FLAGS_MUST_BE_BOOLEAN'):
                    ResearchMethod(symbol='SYN', timeframe='D1',
                                   source_clock_verified=bad)
                with self.assertRaisesRegex(ValueError, 'SHORT_FLAG_MUST_BE_BOOLEAN'):
                    signal_from_closed_history([], [], short_allowed=bad)

    def test_bad_ohlc_and_nan_atomic(self):
        for bad in (float('nan'), float('inf'), -1.0):
            engine = primed()
            snap = engine.snapshot()
            with self.subTest(bad=bad), self.assertRaisesRegex(ValueError, 'OHLC_INVALID'):
                engine.on_bar(candle(250, 108, 109, 107, bad))
            self.assertEqual(engine.snapshot(), snap)

    def test_unclosed_or_future_capture_rejected(self):
        engine = instrument()
        b = rising(n=1)[0]
        for bad in (replace(b, source_confirmed_closed=False),
                    replace(b, captured_at_utc=b.close_at_utc-1),
                    replace(b, captured_at_utc=9999999999)):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                engine.on_bar(bad)
        self.assertEqual(len(engine.bars), 0)

    def test_invalid_pending_gap_does_not_open_position(self):
        engine = primed()
        engine.on_bar(breakout())
        stop = engine.pending[1]
        out = engine.on_bar(candle(251, stop-1, stop, stop-3, stop-2))
        self.assertFalse(out['hypothetical_position'])
        self.assertFalse(out['pending_next_open'])
        self.assertEqual(out['signal_reason'], 'PENDING_REJECT_BAR_NO_REENTRY')
        self.assertTrue(any(e['kind']=='PENDING_REJECT_GAP_INVALID_STOP'
                            for e in out['events']))
        self.assertEqual(out['orders_sent'], 0)

    def test_no_independent_forward_claim(self):
        with self.assertRaisesRegex(ValueError, 'INDEPENDENT_FORWARD_CLAIM_FORBIDDEN'):
            ResearchMethod(symbol='SYN', timeframe='D1', exposure='INDEPENDENT_FORWARD',
                           source_clock_verified=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
