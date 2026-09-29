"""No broker. Deterministic synthetic paper sizing regression only."""
import unittest
from dataclasses import replace

from src.paper.blind_r1_risk import (
    MAX_COMBINED_INITIAL_RISK, MAX_RISK_PER_POSITION,
    RiskInputs, risk_preflight,
)


def fixture(**kwargs):
    defaults={
        "symbol":"EURUSD","mode":"RESEARCH_PAPER_ONLY",
        "direction":"LONG","product_type":"FX",
        "current_equity_account":10000.0,
        "existing_initial_risk_account":0.0,
        "entry_price":100.0,"stop_price":95.0,
        "contract_multiplier":1.0,"fx_quote_to_account":1.0,
        "lot_step":0.1,"min_lot":0.1,"max_lot":100.0,
        "round_trip_fee_per_lot_account":0.1,
        "adverse_slippage_price_one_side":0.1,
        "round_trip_spread_price":0.2,
        "financing_buffer_per_lot_account":0.1,
        "margin_per_lot_account":100.0,
        "available_margin_account":10000.0,
        "quote_timestamp_utc":2000000000,
        "decision_timestamp_utc":2000000005,
        "provenance_id":"FIXTURE-NOT-REAL-BROKER-ATTESTATION",
        "feed_audited":True,"execution_costs_audited":True,
        "contract_audited":True,"fx_conversion_audited":True,
        "margin_audited":True,"authorization_verified":True,
        "kill_switch_off":True,"short_allowed":False,
        "protective_stop_available":True,
    }
    defaults.update(kwargs)
    return RiskInputs(**defaults)


class Smoke(unittest.TestCase):
    def test_frozen_risk_limits(self):
        self.assertEqual(str(MAX_RISK_PER_POSITION),"0.0025")
        self.assertEqual(str(MAX_COMBINED_INITIAL_RISK),"0.01")

    def test_no_live_or_demo_send(self):
        for mode in ("LIVE","DEMO_SEND","DEMO","",None):
            with self.subTest(mode=mode):
                x=risk_preflight(fixture(mode=mode))
                self.assertEqual(x["status"],"REJECTED")
                self.assertEqual(x["reason"],"MODE_FORBIDDEN")
                self.assertEqual(x["orders_sent"],0)

    def test_missing_any_audit_gate(self):
        for field in ("feed_audited","execution_costs_audited",
                      "contract_audited","fx_conversion_audited",
                      "margin_audited","authorization_verified",
                      "kill_switch_off","protective_stop_available"):
            with self.subTest(field=field):
                x=risk_preflight(fixture(**{field:False}))
                self.assertEqual(x["status"],"REJECTED")

    def test_nontradable_index_rejected(self):
        x=risk_preflight(fixture(product_type="CASH_INDEX"))
        self.assertEqual(x["reason"],"PRODUCT_NOT_EXECUTABLE")


class Runtime(unittest.TestCase):
    def test_round_down_risk_includes_fee_spread_slip_finance(self):
        out=risk_preflight(fixture())
        self.assertEqual(out["status"],"ELIGIBLE_SYNTHETIC_PAPER_PREFLIGHT")
        self.assertAlmostEqual(out["units"],4.4)
        self.assertAlmostEqual(out["max_modelled_loss_account"],24.64)
        self.assertLessEqual(out["per_position_risk_fraction"],.0025)
        self.assertLessEqual(out["combined_nominal_risk_fraction"],.01)
        self.assertTrue(out["paper_only"])
        self.assertFalse(out["verified_real_world_inputs"])
        self.assertEqual(out["orders_sent"],0)

    def test_combined_portfolio_budget_is_respected(self):
        out=risk_preflight(fixture(existing_initial_risk_account=99.0))
        self.assertEqual(out["status"],"ELIGIBLE_SYNTHETIC_PAPER_PREFLIGHT")
        self.assertAlmostEqual(out["units"],.1)
        self.assertLessEqual(out["combined_nominal_risk_fraction"],.01)

    def test_margin_limits_before_risk_cap(self):
        out=risk_preflight(fixture(available_margin_account=220.0))
        self.assertEqual(out["units"],2.2)
        self.assertAlmostEqual(out["reserved_margin_account"],220.0)

    def test_short_valid_only_with_verified_short_vehicle(self):
        out=risk_preflight(fixture(direction="SHORT",stop_price=105.0,
                                   short_allowed=True))
        self.assertEqual(out["status"],"ELIGIBLE_SYNTHETIC_PAPER_PREFLIGHT")
        self.assertEqual(out["direction"],"SHORT")

    def test_price_gap_loss_can_exceed_initial_stop(self):
        out=risk_preflight(fixture())
        self.assertIn("EXCEED_STOP_BUDGET",out["gap_tail_risk"])


class Fault(unittest.TestCase):
    def test_kill_switch_never_fails_open(self):
        self.assertEqual(risk_preflight(fixture(kill_switch_off=False))["status"],
                         "REJECTED")

    def test_stale_or_future_quotes(self):
        for t in (2000000006,1999999960):
            with self.subTest(t=t):
                x=risk_preflight(fixture(quote_timestamp_utc=t))
                self.assertEqual(x["reason"],"QUOTE_STALE_OR_FUTURE")

    def test_invalid_long_stop(self):
        self.assertEqual(risk_preflight(fixture(stop_price=100))["reason"],
                         "INVALID_LONG_STOP")

    def test_nonborrowable_short(self):
        self.assertEqual(risk_preflight(fixture(direction="SHORT",
                            stop_price=105.0))["reason"],
                         "SHORT_VEHICLE_NOT_VERIFIED")

    def test_minimum_lot_too_risky(self):
        out=risk_preflight(fixture(min_lot=5.0,max_lot=100.0))
        self.assertEqual(out["reason"],"MIN_LOT_EXCEEDS_RISK_OR_MARGIN_BUDGET")

    def test_missing_margin(self):
        out=risk_preflight(fixture(margin_per_lot_account=0))
        self.assertEqual(out["reason"],"MARGIN_INVALID")

    def test_nan_cost_is_rejected(self):
        out=risk_preflight(fixture(round_trip_fee_per_lot_account=float("nan")))
        self.assertEqual(out["reason"],"FEE_INVALID")

    def test_total_cap_already_reached(self):
        out=risk_preflight(fixture(existing_initial_risk_account=100))
        self.assertEqual(out["reason"],"PORTFOLIO_RISK_CAP_REACHED")

    def test_invalid_fractional_min_step(self):
        out=risk_preflight(fixture(min_lot=.15))
        self.assertEqual(out["reason"],"INVALID_LOT_GRANULARITY")

    def test_zero_available_margin(self):
        out=risk_preflight(fixture(available_margin_account=0))
        self.assertEqual(out["reason"],"MIN_LOT_EXCEEDS_RISK_OR_MARGIN_BUDGET")


if __name__=="__main__":
    unittest.main(verbosity=2)
