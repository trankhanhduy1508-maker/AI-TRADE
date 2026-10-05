from types import SimpleNamespace
import unittest
from src.execution.mt5_session_bridge import BridgeErrorCode, Mt5SessionError, Mt5SessionService, ORDER_SEND_ENABLED

class FakeSecretStore:
    def __init__(self, fail=False): self.values={}; self.fail=fail
    def put(self,key,*,server,login,password):
        if self.fail: raise RuntimeError("secret-store-down")
        self.values[key]=(server,login,"sealed:"+str(len(password)))
    def delete(self,key): self.values.pop(key,None)

class FakeBridge:
    def __init__(self,*,login=12345678,server="Broker-Server-Demo",allowed=True,trade_mode=0):
        self.expected_password="mock-password-only"; self.expected_login=login; self.expected_server=server
        self.init_ok=True; self.timeout=False; self.order_send_calls=0
        self.info=SimpleNamespace(login=login,server=server,trade_mode=trade_mode,
            trade_allowed=allowed,trade_expert=allowed,balance=10000.0,equity=10001.0)
    def initialize(self):
        if self.timeout: raise TimeoutError()
        return self.init_ok
    def login(self,login,*,password,server):
        return login==self.expected_login and server==self.expected_server and password==self.expected_password
    def account_info(self): return self.info
    def shutdown(self): pass

def good(**patch):
    value={"server":"Broker-Server-Demo","login":12345678,"password":"mock-password-only","remember":False}
    value.update(patch); return value

class Smoke(unittest.TestCase):
    def test_master_connected_and_default_off(self):
        b=FakeBridge(); out=Mt5SessionService(lambda:b).connect(good())
        self.assertEqual(out["status"],"CONNECTED"); self.assertEqual(out["account"]["trade_mode"],"DEMO")
        self.assertEqual(out["account"]["trade_permission"],"TRADING_ALLOWED")
        self.assertEqual(out["auto_trade"],"OFF"); self.assertFalse(out["order_send_enabled"])
        self.assertEqual(out["orders_sent"],0); self.assertFalse(ORDER_SEND_ENABLED); self.assertEqual(b.order_send_calls,0)
    def test_investor_read_only(self):
        out=Mt5SessionService(lambda:FakeBridge(allowed=False)).connect(good())
        self.assertEqual(out["status"],"CONNECTED_READ_ONLY"); self.assertEqual(out["account"]["trade_permission"],"READ_ONLY")
    def test_invalid_password_fails_closed(self):
        with self.assertRaisesRegex(Mt5SessionError,"INVALID_LOGIN_OR_PASSWORD"): Mt5SessionService(FakeBridge).connect(good(password="wrong"))
    def test_wrong_server_fails_closed(self):
        with self.assertRaisesRegex(Mt5SessionError,"INVALID_LOGIN_OR_PASSWORD"): Mt5SessionService(FakeBridge).connect(good(server="Other-Demo"))
    def test_redaction_never_contains_password(self):
        self.assertNotIn("mock-password-only",Mt5SessionService.redact(Mt5SessionError(BridgeErrorCode.INVALID_LOGIN_OR_PASSWORD)))

class Runtime(unittest.TestCase):
    def test_connect_account_disconnect_revoke(self):
        svc=Mt5SessionService(FakeBridge); token=svc.connect(good())["session_id"]
        self.assertEqual(svc.account(token)["account"]["login"],12345678); self.assertEqual(svc.disconnect(token)["status"],"DISCONNECTED")
        with self.assertRaisesRegex(Mt5SessionError,"SESSION_INVALID"): svc.account(token)
    def test_reconnect_creates_distinct_session(self):
        svc=Mt5SessionService(FakeBridge); self.assertNotEqual(svc.connect(good())["session_id"],svc.connect(good())["session_id"])
    def test_bridge_restart_invalidates_session(self):
        svc=Mt5SessionService(FakeBridge); token=svc.connect(good())["session_id"]; svc.bridge_restarted()
        with self.assertRaisesRegex(Mt5SessionError,"SESSION_INVALID"): svc.account(token)
    def test_timeout(self):
        b=FakeBridge(); b.timeout=True
        with self.assertRaisesRegex(Mt5SessionError,"TIMEOUT"): Mt5SessionService(lambda:b).connect(good())
    def test_multiple_session_isolation(self):
        bridges=[]
        def factory():
            b=FakeBridge(); bridges.append(b); return b
        svc=Mt5SessionService(factory); a=svc.connect(good()); b=svc.connect(good())
        bridges[0].info.login=99999999
        with self.assertRaisesRegex(Mt5SessionError,"ACCOUNT_IDENTITY_MISMATCH"): svc.account(a["session_id"])
        self.assertEqual(svc.account(b["session_id"])["account"]["login"],12345678)
    def test_remember_false_does_not_persist(self):
        store=FakeSecretStore(); Mt5SessionService(FakeBridge,secret_store=store).connect(good())
        self.assertEqual(store.values,{})
    def test_remember_true_routes_through_store(self):
        store=FakeSecretStore(); out=Mt5SessionService(FakeBridge,secret_store=store).connect(good(remember=True))
        self.assertIn(out["session_id"],store.values); self.assertNotIn("mock-password-only",repr(store.values))

class Fault(unittest.TestCase):
    def test_wrong_types(self):
        for patch in ({"login":"12345678"},{"remember":"false"},{"password":42},{"server":None}):
            with self.assertRaisesRegex(Mt5SessionError,"INVALID_REQUEST"): Mt5SessionService(FakeBridge).connect(good(**patch))
    def test_wrong_account_response(self):
        b=FakeBridge(); b.info.login=99999999
        with self.assertRaisesRegex(Mt5SessionError,"ACCOUNT_IDENTITY_MISMATCH"): Mt5SessionService(lambda:b).connect(good())
    def test_stale_replayed_revoked_token(self):
        svc=Mt5SessionService(FakeBridge); token=svc.connect(good())["session_id"]; svc.disconnect(token)
        for _ in range(2):
            with self.assertRaisesRegex(Mt5SessionError,"SESSION_INVALID"): svc.account(token)
    def test_server_switch(self):
        b=FakeBridge(); b.info.server="Switched-Demo"
        with self.assertRaisesRegex(Mt5SessionError,"ACCOUNT_IDENTITY_MISMATCH"): Mt5SessionService(lambda:b).connect(good())
    def test_terminal_unready_and_network_loss(self):
        b=FakeBridge(); b.init_ok=False
        with self.assertRaisesRegex(Mt5SessionError,"TERMINAL_NOT_READY"): Mt5SessionService(lambda:b).connect(good())
        class Broken(FakeBridge):
            def initialize(self): raise ConnectionError()
        with self.assertRaisesRegex(Mt5SessionError,"BRIDGE_UNAVAILABLE"): Mt5SessionService(Broken).connect(good())
    def test_non_demo_rejected(self):
        with self.assertRaisesRegex(Mt5SessionError,"DEMO_ACCOUNT_REQUIRED"): Mt5SessionService(lambda:FakeBridge(trade_mode=2)).connect(good())
    def test_malformed_account_info(self):
        b=FakeBridge(); b.info.balance=float("nan")
        with self.assertRaisesRegex(Mt5SessionError,"ACCOUNT_INFO_UNAVAILABLE"): Mt5SessionService(lambda:b).connect(good())
    def test_secret_store_failure(self):
        with self.assertRaisesRegex(Mt5SessionError,"SECRET_STORE_FAILURE"): Mt5SessionService(FakeBridge,secret_store=FakeSecretStore(fail=True)).connect(good(remember=True))
    def test_session_expiry(self):
        now=[1000.0]; svc=Mt5SessionService(FakeBridge,ttl_seconds=30,clock=lambda:now[0]); token=svc.connect(good())["session_id"]; now[0]=1031.0
        with self.assertRaisesRegex(Mt5SessionError,"SESSION_EXPIRED"): svc.account(token)
