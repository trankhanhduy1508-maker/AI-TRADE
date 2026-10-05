import hashlib
import unittest
try:
    from src.research.pinned_continuous import run_bundle
except ImportError:
    run_bundle=None

class Provenance(unittest.TestCase):
    def test_h4_and_etf_source_schemas_are_accepted_with_provenance(self):
        self.assertTrue(callable(run_bundle))
        from datetime import datetime,timezone,timedelta
        for tf,fmt,header in [('H4','%Y-%m-%d %H:%M:%S','Date,open,high,low,close\n'),('D1','%Y-%m-%d','symbol,SPY,SPY,SPY,SPY\nfield,Open,High,Low,Close\nDate,,,,\n')]:
            start=datetime(2015,1,1,tzinfo=timezone.utc)
            raw=header+''.join((start+timedelta(hours=4*i) if tf=='H4' else start+timedelta(days=i)).strftime(fmt)+',100,101,99,100\n' for i in range(1000))
            b=raw.encode(); sha=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\x00'+b).hexdigest()
            entry=dict(cell='TEST_'+tf,symbol='SPY',raw=raw,git_blob_sha=sha,status='ELIGIBLE_HISTORICAL_REUSED',timeframe=tf,format='ETF_WIDE' if tf=='D1' else 'PROVIDER_OHLC')
            r=run_bundle([entry],as_of_utc=1700000000)
            self.assertEqual(r['completed_cells'],1)
            self.assertEqual(r['cells'][entry['cell']]['timeframe'],tf)

    def test_mismatched_source_hash_stops_before_results(self):
        self.assertTrue(callable(run_bundle))
        r=run_bundle([dict(cell='EURUSD_D1',symbol='EURUSD',raw='Date,open,high,low,close\n',git_blob_sha='0'*40,status='ELIGIBLE_HISTORICAL_REUSED')],as_of_utc=1700000000)
        self.assertEqual(r['cells']['EURUSD_D1']['status'],'SOURCE_HASH_MISMATCH')
        self.assertEqual(r['orders_sent'],0)

    def test_gap_rejection_preserved_without_reranking(self):
        self.assertTrue(callable(run_bundle))
        r=run_bundle([dict(cell='EURCHF_D1',symbol='EURCHF',raw='',git_blob_sha='0'*40,status='REJECTED_SOURCE_GAP')],as_of_utc=1700000000)
        self.assertEqual(r['cells']['EURCHF_D1']['status'],'REJECTED_SOURCE_GAP')

if __name__=='__main__':unittest.main()
