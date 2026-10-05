"""Synthetic kiểm tra lifecycle, không là kết quả thị trường."""
import unittest
from dataclasses import replace
from src.research.r2_walkforward import Bar, CANDIDATES
try:
    from src.research.continuous_replay import replay
except ImportError:
    replay=None

def bars(n=600):
    # 200 bar warmup; monotonic breakout then long winner.
    return [Bar(1400000000+i*86400,100+i*.2,100+i*.2+.1,100+i*.2-.1,100+i*.2+.05) for i in range(n)]

class Lifecycle(unittest.TestCase):
    def test_replay_is_implemented(self):
        self.assertTrue(callable(replay),'continuous replay must exist')

    def test_flat_selection_does_not_discard_existing_winner(self):
        self.assertTrue(callable(replay))
        result=replay(bars(),begin=200,end=600,selections={200:CANDIDATES[0],450:None},cost=0.,short=False)
        self.assertEqual(result['closed_trades'],0)
        self.assertTrue(result['open_position_at_boundary'])
        self.assertEqual(result['position']['entry_index'],201)
        self.assertEqual(result['position']['candidate'],'R0_REFERENCE')
        self.assertGreater(result['unrealized_r'],0.)

    def test_pending_entry_survives_selection_boundary(self):
        self.assertTrue(callable(replay))
        result=replay(bars(),begin=200,end=210,selections={200:CANDIDATES[0],201:None},cost=0.,short=False)
        self.assertEqual(result['position']['entry_index'],201)

    def test_gap_fill_uses_worse_open(self):
        self.assertTrue(callable(replay))
        data=bars(220)
        data[210]=replace(data[210],open=120.,high=120.1,low=119.9,close=120.)
        result=replay(data,begin=200,end=211,selections={200:CANDIDATES[0]},cost=0.,short=False)
        self.assertEqual(result['closed_trades'],1)
        self.assertEqual(result['gap_stops'],1)
        self.assertEqual(result['trades'][0]['exit_price'],120.)

    def test_future_changes_leave_prior_marks_unchanged(self):
        self.assertTrue(callable(replay))
        data=bars()
        changed=data[:]
        changed[500:]=[replace(b,open=1.,high=10000.,low=.1,close=1.) for b in changed[500:]]
        kw=dict(begin=200,end=500,selections={200:CANDIDATES[0],450:None},cost=.1,short=False)
        self.assertEqual(replay(data,**kw),replay(changed,**kw))

    def test_cost_stress_preserves_lifecycle_and_reduces_marks(self):
        self.assertTrue(callable(replay))
        kw=dict(begin=200,end=600,selections={200:CANDIDATES[0]},short=False)
        a=replay(bars(),cost=0.,**kw); b=replay(bars(),cost=.1,**kw)
        self.assertEqual(a['position'],b['position'])
        self.assertLess(b['unrealized_r'],a['unrealized_r'])
        self.assertEqual(a['orders_sent'],0)

    def test_unknown_candidate_rejected(self):
        self.assertTrue(callable(replay))
        with self.assertRaisesRegex(ValueError,'UNKNOWN_CANDIDATE'):
            replay(bars(),begin=200,end=600,selections={200:('NEW',1,1,1)},cost=0.,short=False)

if __name__=='__main__':unittest.main()
