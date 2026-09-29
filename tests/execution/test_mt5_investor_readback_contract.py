"""Offline contract checks. No broker, OIDC, Vault or trading credentials."""
import unittest
from src.execution.mt5_investor_readback_contract import (
    InvestorReadbackBlocked, investor_lease, check_broker_readback,
)


def sample_lease():
    return {"ok": True, "status": "MT5_DEMO_LEASE", "purpose": "preflight",
            "credentialScope": "INVESTOR_READ_ONLY", "brokerOrdersAllowed": False,
            "liveMoneyLocked": True, "accountType": "DEMO", "login": 123456,
            "server": "MetaQuotes-Demo", "password": "investor-mock-only"}


def sample_account():
    return {"account_type": 1, "is_demo": True, "server": "MetaQuotes-Demo",
            "currency": "USD", "balance": 1000.0, "equity": 1003.0,
            "is_investor": True, "is_read_only": True}


def sample_positions():
    return [{"position_id": 456, "trade_symbol": "EURUSD",
             "trade_action": 0, "trade_volume": 1_000_000,
             "profit": 3.0, "sl": 1.0, "tp": 1.5}]


class InvestorContractTest(unittest.TestCase):
    def test_accept_investor_scope(self):
        login, server, _ = investor_lease(sample_lease())
        self.assertEqual((login, server), (123456, "MetaQuotes-Demo"))

    def test_reject_master_password_scope_and_order_permissions(self):
        for key, value in [
            ("credentialScope", "TRADING_MASTER"), ("brokerOrdersAllowed", True),
            ("purpose", "demo_forward"), ("accountType", "LIVE"),
            ("server", "Broker-Live"), ("liveMoneyLocked", False),
            ("login", 0), ("password", ""),
        ]:
            with self.subTest(key=key):
                value_lease = sample_lease()
                value_lease[key] = value
                with self.assertRaises(InvestorReadbackBlocked):
                    investor_lease(value_lease)

    def test_accept_complete_broker_readback_without_public_values(self):
        result = check_broker_readback(
            sample_account(), sample_positions(), login=123456,
            server="MetaQuotes-Demo")
        self.assertEqual(result, {
            "balanceRead": True, "equityRead": True, "positionsRead": True,
            "brokerOrders": False, "liveMoneyLocked": True,
        })
        self.assertNotIn("balance", result)
        self.assertNotIn("totalLot", result)

    def test_reject_live_or_missing_account_fields(self):
        for key, value in [
            ("account_type", 0), ("is_demo", False), ("server", "Other-Demo"),
            ("balance", None), ("equity", float("nan")), ("currency", ""),
        ]:
            with self.subTest(key=key):
                account = sample_account()
                account[key] = value
                with self.assertRaises(InvestorReadbackBlocked):
                    check_broker_readback(account, sample_positions(),
                                          login=123456, server="MetaQuotes-Demo")

    def test_broker_rights_fail_closed(self):
        for investor, read_only in [(False, False), (None, None),
                                    (False, None), (None, False)]:
            with self.subTest(investor=investor, read_only=read_only):
                account = sample_account()
                account["is_investor"] = investor
                account["is_read_only"] = read_only
                with self.assertRaisesRegex(
                    InvestorReadbackBlocked, "BROKER_INVESTOR_RIGHTS_MISSING"
                ):
                    check_broker_readback(account, [], login=123456,
                                          server="MetaQuotes-Demo")

    def test_reject_ambiguous_positions(self):
        for key, value in [
            ("position_id", 0), ("trade_symbol", ""), ("trade_action", 4),
            ("trade_volume", 0), ("profit", float("inf")), ("sl", -1),
        ]:
            with self.subTest(key=key):
                positions = sample_positions()
                positions[0][key] = value
                with self.assertRaises(InvestorReadbackBlocked):
                    check_broker_readback(sample_account(), positions,
                                          login=123456, server="MetaQuotes-Demo")
        with self.assertRaises(InvestorReadbackBlocked):
            check_broker_readback(sample_account(), None, login=123456,
                                  server="MetaQuotes-Demo")

    def test_empty_positions_is_valid(self):
        result = check_broker_readback(sample_account(), [], login=123456,
                                       server="MetaQuotes-Demo")
        self.assertTrue(result["positionsRead"])


if __name__ == "__main__":
    unittest.main()
