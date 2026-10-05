"""Synthetic-only regression: ensure paper preflight flags cannot bypass fail-closed gates."""
import unittest
from dataclasses import replace
from src.paper.blind_r1_risk import RiskInputs, risk_preflight


def fixture(**changes):
    fields = dict(symbol="EURUSD", mode="RESEARCH_PAPER_ONLY", direction="LONG",
                  product_type="FX", current_equity_account=10000.0,
                  existing_initial_risk_account=0.0, entry_price=100.0,
                  stop_price=95.0, contract_multiplier=1.0,
                  fx_quote_to_account=1.0, lot_step=0.1, min_lot=0.1,
                  max_lot=100.0, round_trip_fee_per_lot_account=0.1,
                  adverse_slippage_price_one_side=0.1,
                  round_trip_spread_price=0.2,
                  financing_buffer_per_lot_account=0.1,
                  margin_per_lot_account=100.0,
                  available_margin_account=10000.0,
                  quote_timestamp_utc=2000000000,
                  decision_timestamp_utc=2000000005,
                  provenance_id="SYNTHETIC_FIXTURE_ONLY",
                  feed_audited=True, execution_costs_audited=True,
                  contract_audited=True, fx_conversion_audited=True,
                  margin_audited=True, authorization_verified=True,
                  kill_switch_off=True, short_allowed=False,
                  protective_stop_available=True)
    fields.update(changes)
    return RiskInputs(**fields)


class Smoke(unittest.TestCase):
    def test_valid_fixture_is_only_a_synthetic_preflight(self):
        out = risk_preflight(fixture())
        self.assertEqual(out["status"], "ELIGIBLE_SYNTHETIC_PAPER_PREFLIGHT")
        self.assertEqual(out["orders_sent"], 0)
        self.assertFalse(out["verified_real_world_inputs"])

    def test_live_and_demo_send_remain_blocked(self):
        for mode in ("LIVE", "DEMO_SEND", "DEMO"):
            with self.subTest(mode=mode):
                self.assertEqual(risk_preflight(fixture(mode=mode))["reason"],
                                 "MODE_FORBIDDEN")


class Runtime(unittest.TestCase):
    def test_sizing_still_reserves_all_costs(self):
        out = risk_preflight(fixture())
        self.assertAlmostEqual(out["units"], 4.4)
        self.assertAlmostEqual(out["max_modelled_loss_account"], 24.64)
        self.assertLessEqual(out["per_position_risk_fraction"], 0.0025)

    def test_short_only_when_bool_true(self):
        out = risk_preflight(fixture(direction="SHORT", stop_price=105.0,
                                     short_allowed=True))
        self.assertEqual(out["status"], "ELIGIBLE_SYNTHETIC_PAPER_PREFLIGHT")
        self.assertEqual(out["orders_sent"], 0)

    def test_portfolio_cap_still_respected(self):
        out = risk_preflight(fixture(existing_initial_risk_account=99.0))
        self.assertAlmostEqual(out["units"], 0.1)
        self.assertLessEqual(out["combined_nominal_risk_fraction"], 0.01)


class Fault(unittest.TestCase):
    def test_every_truthy_string_audit_gate_is_rejected(self):
        fields = ("feed_audited", "execution_costs_audited",
                  "contract_audited", "fx_conversion_audited", "margin_audited",
                  "authorization_verified", "kill_switch_off",
                  "protective_stop_available")
        for field in fields:
            with self.subTest(field=field):
                out = risk_preflight(fixture(**{field: "false"}))
                self.assertEqual(out["reason"],
                                 "UNVERIFIED_SOURCE_COST_RISK_AUTH_OR_KILL_SWITCH")
                self.assertEqual(out["orders_sent"], 0)

    def test_integer_one_is_not_true_audit(self):
        out = risk_preflight(fixture(kill_switch_off=1))
        self.assertEqual(out["reason"],
                         "UNVERIFIED_SOURCE_COST_RISK_AUTH_OR_KILL_SWITCH")

    def test_string_false_cannot_enable_short(self):
        out = risk_preflight(fixture(direction="SHORT", stop_price=105.0,
                                     short_allowed="false"))
        self.assertEqual(out["reason"], "SHORT_VEHICLE_NOT_VERIFIED")

    def test_integer_one_cannot_enable_short(self):
        out = risk_preflight(fixture(direction="SHORT", stop_price=105.0,
                                     short_allowed=1))
        self.assertEqual(out["reason"], "SHORT_VEHICLE_NOT_VERIFIED")

    def test_real_boolean_false_blocks_kill_switch(self):
        self.assertEqual(risk_preflight(fixture(kill_switch_off=False))["status"],
                         "REJECTED")

    def test_missing_authorization_blocks(self):
        self.assertEqual(risk_preflight(fixture(authorization_verified=None))["status"],
                         "REJECTED")

    def test_nan_fee_blocks(self):
        self.assertEqual(risk_preflight(fixture(round_trip_fee_per_lot_account=float('nan')))["reason"],
                         "FEE_INVALID")

    def test_future_quote_blocks(self):
        self.assertEqual(risk_preflight(fixture(quote_timestamp_utc=2000000010))["reason"],
                         "QUOTE_STALE_OR_FUTURE")

    def test_missing_shortable_vehicle_blocks(self):
        self.assertEqual(risk_preflight(fixture(direction="SHORT", stop_price=105.0))["reason"],
                         "SHORT_VEHICLE_NOT_VERIFIED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
