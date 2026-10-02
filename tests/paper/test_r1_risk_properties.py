"""Deterministic synthetic property/fault tests. Not performance or broker QA."""
import random
import unittest
from src.paper.blind_r1_risk import risk_preflight
from tests.paper.test_r1_boolean_safety import fixture


class Smoke(unittest.TestCase):
    def test_never_sends_orders_in_paper_mode(self):
        for direction, stop in (("LONG", 95), ("SHORT", 105)):
            with self.subTest(direction=direction):
                out = risk_preflight(fixture(direction=direction,
                                             stop_price=stop,
                                             short_allowed=True))
                self.assertEqual(out["orders_sent"], 0)
                self.assertTrue(out["paper_only"])
                self.assertFalse(out["verified_real_world_inputs"])


class Runtime(unittest.TestCase):
    def test_1000_seeded_budget_and_lot_invariants(self):
        rng = random.Random(20260929)
        accepted = 0
        for _ in range(1000):
            equity = round(rng.uniform(500, 50000), 2)
            previous = equity * rng.uniform(0, 0.012)
            spread = round(rng.uniform(0.0, 0.9), 5)
            fee = round(rng.uniform(0.0, 1.0), 5)
            entry = round(rng.uniform(20.0, 250.0), 4)
            dist = round(rng.uniform(0.1, 15.0), 4)
            margin = round(rng.uniform(10.0, 1000.0), 4)
            available = round(rng.uniform(0.0, equity), 4)
            out = risk_preflight(fixture(
                current_equity_account=equity,
                existing_initial_risk_account=previous,
                entry_price=entry, stop_price=entry-dist,
                round_trip_spread_price=spread,
                round_trip_fee_per_lot_account=fee,
                margin_per_lot_account=margin,
                available_margin_account=available))
            self.assertEqual(out["orders_sent"], 0)
            self.assertTrue(out["paper_only"])
            self.assertFalse(out["verified_real_world_inputs"])
            if out["status"] == "REJECTED":
                self.assertEqual(out["units"], 0.0)
                continue
            accepted += 1
            self.assertEqual(out["status"], "ELIGIBLE_SYNTHETIC_PAPER_PREFLIGHT")
            self.assertGreater(out["units"], 0)
            self.assertAlmostEqual(out["units"] * 10, round(out["units"] * 10), places=6)
            self.assertLessEqual(out["per_position_risk_fraction"], 0.0025+1e-12)
            self.assertLessEqual(out["combined_nominal_risk_fraction"], 0.01+1e-12)
            self.assertLessEqual(out["reserved_margin_account"], available+1e-8)
        self.assertGreater(accepted, 300)

    def test_costs_and_existing_risk_never_increase_sizing(self):
        for fee in (0.1, 1.0, 10.0, 100.0):
            out = risk_preflight(fixture(round_trip_fee_per_lot_account=fee))
            self.assertEqual(out["orders_sent"], 0)
        baseline = risk_preflight(fixture())["units"]
        for more in (1.0, 10.0, 100.0):
            self.assertLessEqual(risk_preflight(fixture(
                round_trip_fee_per_lot_account=more))["units"], baseline)
        for existing in (0.0, 10.0, 40.0, 80.0, 99.0):
            units = risk_preflight(fixture(existing_initial_risk_account=existing))["units"]
            self.assertLessEqual(units, baseline)


class Fault(unittest.TestCase):
    def test_nonbool_audit_and_killswitch_rejected(self):
        fields = ("feed_audited", "execution_costs_audited", "contract_audited",
                  "fx_conversion_audited", "margin_audited",
                  "authorization_verified", "kill_switch_off",
                  "protective_stop_available")
        for name in fields:
            for bad in ("true", "false", 1, 0, None, []):
                with self.subTest(field=name, value=bad):
                    out = risk_preflight(fixture(**{name: bad}))
                    self.assertEqual(out["status"], "REJECTED")
                    self.assertEqual(out["orders_sent"], 0)

    def test_unapproved_short_never_eligible(self):
        for bad in ("false", "true", 1, 0, None, [], False):
            with self.subTest(short_allowed=bad):
                out = risk_preflight(fixture(
                    direction="SHORT", stop_price=105, short_allowed=bad))
                self.assertEqual(out["reason"], "SHORT_VEHICLE_NOT_VERIFIED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
