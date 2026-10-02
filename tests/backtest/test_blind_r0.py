"""Blind R0 regression: no TF-004/TF-014 results, no broker calls."""
import math
import unittest

from src.backtest.blind_r0 import (
    ATR_MULTIPLIER, CHANNEL, PREREG_SHA, TRAIL, Bar, Costs,
    block_bootstrap, simulate, validate_bars,
)


def fixture():
    bars = []
    for i in range(220):
        close = 100 + .1*i
        bars.append(Bar(i*86400, close, close+1, close-1, close, 100))
    bars[205] = Bar(205*86400, 190, 191, 189, 190, 100)
    bars[206] = Bar(206*86400, 195, 196, 190, 194, 100)
    bars[207] = Bar(207*86400, 165, 166, 160, 164, 100)
    return bars


class SmokeContract(unittest.TestCase):
    def test_fixed_prereg(self):
        self.assertEqual(CHANNEL, 55)
        self.assertEqual(TRAIL, 20)
        self.assertEqual(ATR_MULTIPLIER, 2.5)
        self.assertEqual(PREREG_SHA, "9041d3de3122abfb41ef8ab2f0fca12f114307cf")

    def test_bars_reject_future_timestamp(self):
        b = fixture()
        b[10] = Bar(b[9].ts, 99, 100, 98, 99)
        with self.assertRaises(ValueError):
            validate_bars(b)

    def test_bars_reject_bad_ohlc(self):
        b = fixture()
        b[10] = Bar(b[10].ts, 99, 98, 97, 99)
        with self.assertRaises(ValueError):
            validate_bars(b)

    def test_costs_reject_nan(self):
        with self.assertRaises(ValueError):
            Costs(slippage_price=float("nan"))


class RuntimeExecution(unittest.TestCase):
    def test_signal_close_cannot_execute_same_bar(self):
        result = simulate(fixture(), begin=200, end=206)
        self.assertEqual(result["trade_count"], 0)
        self.assertIsNone(result["open_position_marked"])

    def test_next_open_and_gap_at_worse_open(self):
        result = simulate(fixture(), begin=200, end=208)
        self.assertEqual(result["trade_count"], 1)
        t = result["trades"][0]
        self.assertEqual(t["entry_ts"], 206*86400)
        self.assertEqual(t["entry_price"], 195)
        self.assertEqual(t["exit_ts"], 207*86400)
        self.assertEqual(t["exit_reason"], "GAP_STOP")
        self.assertEqual(t["exit_price"], 165)
        self.assertEqual(t["gross_pnl_price"], -30)

    def test_open_position_is_marked_without_forced_close(self):
        result = simulate(fixture(), begin=200, end=207)
        self.assertEqual(result["trade_count"], 0)
        p = result["open_position_marked"]
        self.assertIsNotNone(p)
        self.assertEqual(p["entry_price"], 195)
        self.assertLess(p["unrealized_pnl_r"], 0)
        self.assertAlmostEqual(result["ending_marked_equity_r"],
                               p["unrealized_pnl_r"])

    def test_costs_accounted_and_stress_is_monotone(self):
        fees = Costs(spread_price=.1, commission_price=.2,
                     slippage_price=.3, provenance="ASSUMED_COST")
        one = simulate(fixture(), begin=200, end=208, costs=fees)
        two = simulate(fixture(), begin=200, end=208,
                       costs=fees, cost_multiplier=2)
        self.assertEqual(one["trade_count"], 1)
        self.assertAlmostEqual(one["trades"][0]["cost_price"], 0.9)
        self.assertAlmostEqual(two["trades"][0]["cost_price"], 1.8)
        self.assertLess(two["net_pnl_price"], one["net_pnl_price"])
        self.assertEqual(one["cost_provenance"], "ASSUMED_COST")
        self.assertIsNone(one["account_currency_pnl"])

    def test_stop_can_trigger_on_entry_bar(self):
        b = fixture()
        b[206] = Bar(206*86400, 190, 192, 100, 120, 100)
        result = simulate(b, begin=200, end=207)
        self.assertEqual(result["trade_count"], 1)
        self.assertEqual(result["trades"][0]["exit_reason"], "ENTRY_BAR_STOP")
        self.assertEqual(result["trades"][0]["holding_bars"], 0)

    def test_short_disallowed_without_executable_instrument(self):
        b = fixture()
        b[205] = Bar(205*86400, 80, 81, 79, 80, 100)
        b[206] = Bar(206*86400, 79, 80, 74, 75, 100)
        yes = simulate(b, begin=200, end=207, allow_short=True)
        no = simulate(b, begin=200, end=207, allow_short=False)
        self.assertIsNotNone(yes["open_position_marked"])
        self.assertEqual(yes["open_position_marked"]["direction"], -1)
        self.assertIsNone(no["open_position_marked"])


class FaultIsolation(unittest.TestCase):
    def test_no_future_bar_leak_into_previous_result(self):
        b = fixture()
        before = simulate(b, begin=200, end=207)
        b[207] = Bar(207*86400, 999, 1000, 998, 999, 100)
        after = simulate(b, begin=200, end=207)
        self.assertEqual(before, after)

    def test_no_fabricated_return_when_empty(self):
        b = fixture()
        out = simulate(b, begin=200, end=205)
        self.assertIsNone(out["profit_factor"])
        self.assertIsNone(out["expectancy_r"])
        self.assertEqual(out["trade_count"], 0)

    def test_invalid_split_rejected(self):
        with self.assertRaises(ValueError):
            simulate(fixture(), begin=210, end=210)

    def test_bootstrap_seed_is_deterministic(self):
        ts = [{"pnl_r": x} for x in (-1.0, .3, .4, 2.0, -.6)]
        a = block_bootstrap(ts, n=100)
        self.assertEqual(a, block_bootstrap(ts, n=100))
        self.assertEqual(a["seed"], 20260929)
        self.assertTrue(math.isfinite(a["total_r_median"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
