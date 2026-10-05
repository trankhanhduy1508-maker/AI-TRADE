import unittest
from dataclasses import replace
from tests.research.test_r2_walkforward import fixture, source, START, DAY
try:
    from src.research.continuous_walkforward import run_continuous
except ImportError:
    run_continuous=None

class Walkforward(unittest.TestCase):
    def test_report_exposes_baseline_and_no_promotion(self):
        self.assertTrue(callable(run_continuous))
        data=fixture(1000)
        r=run_continuous(data,study=source(),as_of_utc=START+1000*DAY)
        self.assertEqual(r['orders_sent'],0)
        self.assertEqual(r['promotion'],'NOT_APPROVED')
        self.assertEqual(set(r['lanes']),{'R2_FROZEN_SELECTION','R0_FIXED','FLAT'})
        self.assertEqual(r['completed_evaluation_bars'],500)
        self.assertEqual(r['r3_nested_selection_implemented'],False)

    def test_unclosed_future_suffix_does_not_change_report(self):
        self.assertTrue(callable(run_continuous))
        data=fixture(1250); other=data[:]
        for i in range(1000,1250):
            other[i]=replace(other[i],open=1.,high=10000.,low=.01,close=1.)
        kw=dict(study=source(),as_of_utc=START+1000*DAY)
        self.assertEqual(run_continuous(data,**kw),run_continuous(other,**kw))

if __name__=='__main__':unittest.main()
