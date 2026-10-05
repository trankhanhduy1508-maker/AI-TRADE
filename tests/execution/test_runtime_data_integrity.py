"""Dữ liệu broker hỏng phải chặn trước signal; fake broker, không gửi lệnh."""
import unittest
from types import SimpleNamespace
from datetime import datetime, timezone
from src.execution.mt5_runtime import closed_bars, daily_pnl, runtime_snapshot, RuntimeMarketState

class DataIntegrity(unittest.TestCase):
    def test_risk_permission_requires_explicit_approval(self):
        now=datetime.now(timezone.utc)
        market=RuntimeMarketState((),1.,1.1,1.,0.,now)
        snapshot=runtime_snapshot(market=market,now=now,reconciled=True,max_tick_age_seconds=120)
        self.assertFalse(snapshot.risk_allowed)

    def broker(self, **changes):
        row=dict(time=1700000000,open=1.,high=2.,low=.5,close=1.5,tick_volume=3.)
        row.update(changes)
        return SimpleNamespace(copy_rates_from_pos=lambda *a:[row],last_error=lambda:(0,''))

    def test_invalid_prices_are_rejected(self):
        for changes in ({'close':float('nan')},{'open':0.},{'high':1.},{'low':1.6},{'tick_volume':-1.}):
            with self.subTest(changes=changes), self.assertRaisesRegex(RuntimeError,'BROKER_BAR_INVALID'):
                closed_bars(self.broker(**changes),'EURUSD',15,2)

    def test_invalid_bar_timestamp_is_rejected(self):
        for stamp in (0,-1,1700000000.5):
            with self.subTest(stamp=stamp), self.assertRaisesRegex(RuntimeError,'BROKER_BAR_INVALID'):
                closed_bars(self.broker(time=stamp),'EURUSD',15,2)

    def test_nonfinite_deal_cost_is_rejected(self):
        broker=SimpleNamespace(history_deals_get=lambda *a:[SimpleNamespace(magic=1,profit=2.,commission=float('nan'))])
        with self.assertRaisesRegex(RuntimeError,'BROKER_DAILY_PNL_INVALID'):
            daily_pnl(broker,magic=1)

    def test_invalid_freshness_limit_is_rejected(self):
        now=datetime.now(timezone.utc)
        market=RuntimeMarketState((),1.,1.1,1.,0.,now)
        for limit in (float('inf'),float('nan'),-1,True):
            with self.subTest(limit=limit),self.assertRaisesRegex(ValueError,'INVALID_TICK_AGE_LIMIT'):
                runtime_snapshot(market=market,now=now,reconciled=True,max_tick_age_seconds=limit)

if __name__=='__main__':unittest.main()
