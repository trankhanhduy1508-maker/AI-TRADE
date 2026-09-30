"""Synthetic-only QA for METHOD LAB V2. No performance or market-edge claim."""
from dataclasses import replace
import math
import random
import unittest

from src.research.method_lab_v2 import (
    ATR_REFERENCE, BODY_ATR_MIN, BREAKOUT_BUFFER_ATR, CHANNEL,
    CLOSE_LOCATION_MIN, FEEDBACK_PAUSE, QUALITY_FAILURE_TRIGGER,
    SCORE_TRADE, SCORE_WATCH, SPEC_COMMIT,
    ClosedBar, MethodLabV2, Position, atr_series, classify_regime,
    decision_from_history, trail_window,
)

BASE = 1577836800
DAY = 86400


def bar(i, o, h, l, c, *, period=DAY, gap=False, closed=True, captured=None):
    ts = BASE + i*period
    return ClosedBar(ts, float(o), float(h), float(l), float(c), ts+period,
                     ts+period+1 if captured is None else captured, closed, gap)


def trend(n=330, *, drift=.10, period=DAY):
    out=[]
    prev=100.0
    for i in range(n):
        c=prev+drift
        out.append(bar(i, prev, max(prev,c)+.40, min(prev,c)-.40, c, period=period))
        prev=c
    return out


def breakout_after(history, *, period=DAY):
    i=len(history)
    prev=history[-1].close
    close=prev+2.0
    return bar(i, prev, close+.10, prev-.30, close, period=period)


def engine(*, tf='D1'):
    return MethodLabV2(symbol='SYNTHETIC', timeframe=tf, source_clock_verified=True)


class Smoke(unittest.TestCase):
    def test_locked_contract(self):
        self.assertEqual(SPEC_COMMIT, '2509ad559a69fd54aba04a27da4a6b3d7baa53b6')
        self.assertEqual(CHANNEL,55)
        self.assertEqual(BREAKOUT_BUFFER_ATR,.25)
        self.assertEqual(BODY_ATR_MIN,.50)
        self.assertEqual(CLOSE_LOCATION_MIN,.75)
        self.assertEqual(SCORE_TRADE,80)
        self.assertEqual(SCORE_WATCH,60)
        self.assertEqual(ATR_REFERENCE,100)
        self.assertEqual(QUALITY_FAILURE_TRIGGER,4)
        self.assertEqual(FEEDBACK_PAUSE,20)

    def test_regime_strong_up_compression_and_shock(self):
        bars=trend()
        atr=atr_series(bars)
        r=classify_regime(bars,atr)
        self.assertEqual(r.name,'TREND_STRONG_UP')
        flat=[]
        for i in range(330):
            flat.append(bar(i,100,100.1,99.9,100))
        r2=classify_regime(flat,[1.0]*100+[.5])
        self.assertEqual(r2.name,'COMPRESSION')
        r3=classify_regime(bars,[1.0]*100+[2.1])
        self.assertEqual(r3.name,'VOLATILITY_SHOCK')

    def test_score_trade_watch_abstain_and_bounds(self):
        bars=trend()
        bars.append(breakout_after(bars))
        d=decision_from_history(bars,atr_series(bars))
        self.assertEqual(d.action,'TRADE')
        self.assertGreaterEqual(d.score,80)
        self.assertLessEqual(d.score,100)
        watch=trend()
        prev=watch[-1].close
        watch.append(bar(len(watch),prev,prev+.7,prev-.2,prev+.5))
        w=decision_from_history(watch,atr_series(watch))
        self.assertEqual(w.action,'WATCH')
        self.assertGreaterEqual(w.score,60)
        self.assertLess(w.score,80)
        flat=[bar(i,100,100.2,99.8,100) for i in range(330)]
        a=decision_from_history(flat,[.4]*101)
        self.assertEqual(a.action,'ABSTAIN')
        self.assertGreaterEqual(a.score,0)
        self.assertLessEqual(a.score,100)

    def test_output_contract_never_claims_orders_or_net(self):
        m=engine()
        out=m.on_bar(trend(1)[0])
        self.assertEqual(out['orders_sent'],0)
        self.assertEqual(out['independent_forward_trades'],0)
        self.assertEqual(out['cost_status'],'NOT_EVALUATED')
        self.assertIsNone(out['account_currency_pnl'])
        self.assertEqual(out['edge_status'],'UNPROVEN')
        self.assertFalse(out['data_source_independently_verified'])


class Runtime(unittest.TestCase):
    def test_engine_initializes_atr_and_generates_next_open_signal(self):
        m=engine()
        history=trend()
        for x in history:
            m.on_bar(x)
        self.assertGreaterEqual(len(m.atr_history),101)
        out=m.on_bar(breakout_after(history))
        self.assertEqual(out['action'],'TRADE')
        self.assertTrue(out['pending_next_open'])
        self.assertFalse(out['position_open'])
        self.assertGreaterEqual(out['score'],80)

    def test_next_open_and_monotonic_adaptive_stop(self):
        m=engine()
        history=trend()
        for x in history:
            m.on_bar(x)
        sig=m.on_bar(breakout_after(history))
        stop=m.pending[1]
        i=len(history)+1
        opened=m.on_bar(bar(i,history[-1].close+2.2,history[-1].close+2.8,
                            history[-1].close+1.8,history[-1].close+2.6))
        self.assertTrue(opened['position_open'])
        self.assertGreater(m.position.entry,stop)
        prior_stop=m.position.stop
        for j in range(i+1,i+45):
            c=m.bars[-1].close+.12
            m.on_bar(bar(j,c-.1,c+.5,c-.35,c))
            if m.position is None:
                break
            self.assertGreaterEqual(m.position.stop,prior_stop)
            prior_stop=m.position.stop
        self.assertIsNotNone(m.position)
        self.assertGreater(m.position.stop,m.position.initial_stop)

    def test_trail_window_mapping(self):
        self.assertEqual(trail_window('TREND_STRONG_UP',1),30)
        self.assertEqual(trail_window('TREND_WEAK_UP',1),20)
        self.assertEqual(trail_window('RANGE_OR_TRANSITION',1),10)
        self.assertEqual(trail_window('COMPRESSION',1),10)
        self.assertEqual(trail_window('VOLATILITY_SHOCK',1),5)
        self.assertIsNone(trail_window('UNKNOWN',1))
        self.assertEqual(trail_window('TREND_STRONG_DOWN',-1),30)

    def test_failure_feedback_uses_rolling_closed_tags_only(self):
        m=engine()
        m.position=Position(1,BASE,100,95,95,5,BASE,90,'TREND_STRONG_UP')
        self.assertEqual(len(m.feedback_tags),0)
        self.assertEqual(m.quality_quarantine_until,0)
        m.position=None
        m._apply_feedback(('WIN',),1)
        m._apply_feedback(('FAST_STOP','FAILED_BREAKOUT'),2)
        m._apply_feedback(('WIN',),3)
        self.assertEqual(m.quality_quarantine_until,0)
        m._apply_feedback(('FAST_STOP',),4)
        m._apply_feedback(('FAILED_BREAKOUT',),5)
        self.assertGreaterEqual(m.quality_quarantine_until,5+20+1)
        self.assertLessEqual(len(m.feedback_tags),8)

    def test_reversal_feedback_downgrades_trade_to_watch(self):
        m=engine()
        history=trend()
        for x in history:
            m.on_bar(x)
        for idx in (1,2,3):
            m._apply_feedback(('REGIME_REVERSAL',),idx)
        self.assertGreater(m.reversal_watch_until,0)
        m.reversal_watch_until=len(m.bars)+20
        out=m.on_bar(breakout_after(history))
        self.assertEqual(out['action'],'WATCH')
        self.assertEqual(out['decision_reason'],'REGIME_REVERSAL_WATCH_ONLY')
        self.assertFalse(out['pending_next_open'])

    def test_seeded_1200_bar_replay_is_deterministic(self):
        rng=random.Random(20260930)
        seq=[]
        prev=100.0
        for i in range(1200):
            drift=.04 if i<400 else (-.02 if i<700 else .06)
            c=max(1.0,prev+drift+rng.uniform(-.32,.32))
            seq.append(bar(i,prev,max(prev,c)+.15+rng.random()*.2,
                           min(prev,c)-.15-rng.random()*.2,c))
            prev=c
        a,b=engine(),engine()
        for x in seq:
            oa,ob=a.on_bar(x),b.on_bar(x)
            self.assertEqual(oa,ob)
            self.assertEqual(oa['orders_sent'],0)
        self.assertEqual(a.snapshot(),b.snapshot())
        self.assertEqual(len(a.bars),1200)

    def test_prefix_immunity(self):
        seq=trend(350)
        a,b=engine(),engine()
        for x in seq:
            self.assertEqual(a.on_bar(x),b.on_bar(x))
        snap=a.snapshot()
        for i in range(350,390):
            c=b.bars[-1].close+.2
            b.on_bar(bar(i,c-.1,c+.4,c-.3,c))
        self.assertEqual(a.snapshot(),snap)


class Fault(unittest.TestCase):
    def test_bad_types_and_short_permission_fail_closed(self):
        for bad in ('true','false',1,0,None):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ValueError,'AUDIT_FLAGS_MUST_BE_BOOLEAN'):
                    MethodLabV2(symbol='S',timeframe='D1',source_clock_verified=bad)
                with self.assertRaisesRegex(ValueError,'SHORT_FLAG_MUST_BE_BOOLEAN'):
                    decision_from_history([],[],short_allowed=bad)

    def test_duplicate_nan_future_unclosed_are_atomic(self):
        m=engine()
        for x in trend(250):
            m.on_bar(x)
        state=m.snapshot()
        valid=bar(250,120,121,119,120.5)
        cases=(replace(valid,ts=m.bars[-1].ts,close_at_utc=m.bars[-1].ts+DAY),
               replace(valid,low=float('nan')),
               replace(valid,captured_at_utc=valid.close_at_utc-1),
               replace(valid,captured_at_utc=9999999999),
               replace(valid,source_confirmed_closed=False))
        for bad in cases:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                m.on_bar(bad)
            self.assertEqual(m.snapshot(),state)

    def test_calendar_gap_requires_both_external_flags(self):
        m=engine()
        m.on_bar(trend(1)[0])
        with self.assertRaisesRegex(ValueError,'CALENDAR_GAP_UNVERIFIED'):
            m.on_bar(bar(2,100,101,99,100.5,gap=True))
        m2=MethodLabV2(symbol='S',timeframe='D1',source_clock_verified=True,
                       calendar_audited=True)
        m2.on_bar(trend(1)[0])
        accepted=m2.on_bar(bar(2,100,101,99,100.5,gap=True))
        self.assertEqual(accepted['bar_index'],1)
        self.assertFalse(accepted['data_source_independently_verified'])

    def test_future_suffix_cannot_change_prior_decision_function(self):
        prefix=trend()
        prefix.append(breakout_after(prefix))
        decision=decision_from_history(prefix,atr_series(prefix))
        mutated=list(prefix)
        for i in range(len(prefix),len(prefix)+50):
            mutated.append(bar(i,100,1000000,.001,999999))
        same=decision_from_history(mutated[:len(prefix)],atr_series(mutated[:len(prefix)]))
        self.assertEqual(decision,same)

    def test_score_never_scales_risk_or_exceeds_bounds(self):
        rng=random.Random(9)
        for _ in range(100):
            bars=trend()
            p=bars[-1].close
            c=p+rng.uniform(-2,3)
            o=p+rng.uniform(-.5,.5)
            hi=max(o,c)+rng.uniform(.05,.8)
            lo=min(o,c)-rng.uniform(.05,.8)
            bars.append(bar(len(bars),o,hi,lo,c))
            d=decision_from_history(bars,atr_series(bars))
            self.assertTrue(0<=d.score<=100)
            if d.action!='TRADE':
                self.assertIsNone(d.stop)

    def test_no_broker_network_or_cost_imports(self):
        import ast, pathlib
        path=pathlib.Path(__file__).parents[2]/'src/research/method_lab_v2.py'
        tree=ast.parse(path.read_text())
        names=set()
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):
                names.update(a.name.split('.')[0] for a in node.names)
            elif isinstance(node,ast.ImportFrom) and node.module:
                names.add(node.module.split('.')[0])
        banned={'requests','httpx','socket','subprocess','MetaTrader5','ccxt','ib_insync'}
        self.assertFalse(names & banned)


if __name__=='__main__':
    unittest.main(verbosity=2)
