from __future__ import annotations
import unittest
from src.execution.mt5_cloud_metaapi import MetaApiCloudBridge, MetaApiConfig
from src.execution.mt5_session_bridge import Mt5SessionError

class Transport:
    def __init__(self, responses):
        self.responses=list(responses); self.calls=[]
    def request(self, method, url, *, headers, body=None, timeout=20.0):
        self.calls.append((method,url,headers,body))
        if not self.responses: raise AssertionError("unexpected request")
        return self.responses.pop(0)

def cfg():
    return MetaApiConfig(token="t"*40, poll_interval_seconds=0.05, connect_timeout_seconds=3)

def demo_info(**patch):
    value={"platform":"mt5","server":"Broker-Server-Demo","login":12345678,
           "balance":10000.0,"equity":10001.0,"tradeAllowed":True,
           "investorMode":False,"type":"ACCOUNT_TRADE_MODE_DEMO"}
    value.update(patch); return value

class Smoke(unittest.TestCase):
    def test_cloud_master_connects_without_windows_terminal(self):
        t=Transport([(201,{"id":"cloud-account-1"}),(200,demo_info()),(200,demo_info())])
        b=MetaApiCloudBridge(cfg(),transport=t,sleeper=lambda _:None)
        self.assertTrue(b.initialize()); self.assertTrue(b.login(12345678,password="mock-password-only",server="Broker-Server-Demo"))
        info=b.account_info()
        self.assertEqual(info.login,12345678); self.assertTrue(info.trade_allowed)
        self.assertFalse(any("order" in call[1].lower() for call in t.calls))
    def test_investor_is_read_only(self):
        t=Transport([(201,{"id":"cloud-account-2"}),(200,demo_info(investorMode=True,tradeAllowed=True))])
        b=MetaApiCloudBridge(cfg(),transport=t,sleeper=lambda _:None); b.initialize(); b.login(12345678,password="mock-password-only",server="Broker-Server-Demo")
        self.assertFalse(b._last_info.trade_allowed)
    def test_server_not_found_mapping(self):
        t=Transport([(400,{"details":{"code":"E_SRV_NOT_FOUND"}})])
        b=MetaApiCloudBridge(cfg(),transport=t,sleeper=lambda _:None); b.initialize()
        with self.assertRaisesRegex(Mt5SessionError,"SERVER_NOT_FOUND"): b.login(12345678,password="x",server="Missing-Demo")
    def test_invalid_credentials_mapping(self):
        t=Transport([(400,{"details":"E_AUTH","message":"failed to authenticate"})])
        b=MetaApiCloudBridge(cfg(),transport=t,sleeper=lambda _:None); b.initialize()
        with self.assertRaisesRegex(Mt5SessionError,"INVALID_LOGIN_OR_PASSWORD"): b.login(12345678,password="x",server="Broker-Server-Demo")

class Runtime(unittest.TestCase):
    def test_account_read_refreshes_cloud_state(self):
        t=Transport([(201,{"id":"cloud-account-3"}),(200,demo_info()),(200,demo_info(equity=10005.0))])
        b=MetaApiCloudBridge(cfg(),transport=t,sleeper=lambda _:None); b.initialize(); b.login(12345678,password="x",server="Broker-Server-Demo")
        self.assertEqual(b.account_info().equity,10005.0)
    def test_shutdown_deletes_ephemeral_provider_account(self):
        t=Transport([(201,{"id":"cloud-account-4"}),(200,demo_info()),(204,None)])
        b=MetaApiCloudBridge(cfg(),transport=t,sleeper=lambda _:None); b.initialize(); b.login(12345678,password="x",server="Broker-Server-Demo"); b.shutdown()
        self.assertEqual(t.calls[-1][0],"DELETE"); self.assertIn("cloud-account-4",t.calls[-1][1])
    def test_provider_token_never_in_body(self):
        t=Transport([(201,{"id":"cloud-account-5"}),(200,demo_info())])
        b=MetaApiCloudBridge(cfg(),transport=t,sleeper=lambda _:None); b.initialize(); b.login(12345678,password="x",server="Broker-Server-Demo")
        self.assertTrue(all((call[3] is None or cfg().token not in repr(call[3])) for call in t.calls))
        self.assertTrue(all(call[2].get("auth-token")==cfg().token for call in t.calls))

class Fault(unittest.TestCase):
    def test_real_account_rejected_and_cleaned(self):
        t=Transport([(201,{"id":"cloud-account-6"}),(200,demo_info(type="ACCOUNT_TRADE_MODE_REAL")),(204,None)])
        b=MetaApiCloudBridge(cfg(),transport=t,sleeper=lambda _:None); b.initialize()
        with self.assertRaisesRegex(Mt5SessionError,"DEMO_ACCOUNT_REQUIRED"): b.login(12345678,password="x",server="Broker-Server-Demo")
        self.assertEqual(t.calls[-1][0],"DELETE")
    def test_wrong_account_rejected(self):
        t=Transport([(201,{"id":"cloud-account-7"}),(200,demo_info(login=99999999)),(204,None)])
        b=MetaApiCloudBridge(cfg(),transport=t,sleeper=lambda _:None); b.initialize()
        with self.assertRaisesRegex(Mt5SessionError,"ACCOUNT_IDENTITY_MISMATCH"): b.login(12345678,password="x",server="Broker-Server-Demo")
    def test_wrong_server_rejected(self):
        t=Transport([(201,{"id":"cloud-account-8"}),(200,demo_info(server="Switched-Demo")),(204,None)])
        b=MetaApiCloudBridge(cfg(),transport=t,sleeper=lambda _:None); b.initialize()
        with self.assertRaisesRegex(Mt5SessionError,"ACCOUNT_IDENTITY_MISMATCH"): b.login(12345678,password="x",server="Broker-Server-Demo")
    def test_missing_backend_token_fails_closed(self):
        bad=MetaApiConfig(token="")
        with self.assertRaisesRegex(Mt5SessionError,"BRIDGE_UNAVAILABLE"): MetaApiCloudBridge(bad,transport=Transport([])).initialize()
    def test_no_order_execution_surface(self):
        self.assertFalse(hasattr(MetaApiCloudBridge,"order_send"))
