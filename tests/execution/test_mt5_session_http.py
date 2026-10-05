import json
import unittest
from types import SimpleNamespace
from src.execution.mt5_session_bridge import Mt5SessionService
from src.execution.mt5_session_http import handle_request

class Bridge:
    def initialize(self): return True
    def login(self,login,*,password,server): return password=="mock-password-only"
    def account_info(self): return SimpleNamespace(login=12345678,server="Broker-Server-Demo",trade_mode=0,trade_allowed=True,trade_expert=True,balance=10000,equity=10001)
    def shutdown(self): pass

class HttpContract(unittest.TestCase):
    def setUp(self): self.svc=Mt5SessionService(Bridge)
    def connect(self):
        code,h,b=handle_request(self.svc,method="POST",path="/mt5/session/connect",body=json.dumps({"server":"Broker-Server-Demo","login":12345678,"password":"mock-password-only","remember":False}))
        self.assertEqual(code,200); self.assertEqual(h["cache-control"],"no-store"); return b
    def test_three_routes(self):
        out=self.connect(); token=out["session_id"]
        code,_,acct=handle_request(self.svc,method="GET",path="/mt5/session/account",headers={"Authorization":"Bearer "+token})
        self.assertEqual(code,200); self.assertEqual(acct["account"]["login"],12345678)
        code,_,disc=handle_request(self.svc,method="POST",path="/mt5/session/disconnect",headers={"Authorization":"Bearer "+token})
        self.assertEqual(code,200); self.assertEqual(disc["status"],"DISCONNECTED")
    def test_no_token_fails_closed(self):
        code,_,body=handle_request(self.svc,method="GET",path="/mt5/session/account")
        self.assertEqual(code,401); self.assertEqual(body["status"],"SESSION_INVALID")
    def test_malformed_json_no_secret_echo(self):
        code,_,body=handle_request(self.svc,method="POST",path="/mt5/session/connect",body='{"password":"mock-password-only"')
        self.assertEqual(code,400); self.assertNotIn("mock-password-only",repr(body))
    def test_error_never_enables_execution(self):
        code,_,body=handle_request(self.svc,method="POST",path="/mt5/session/connect",body=json.dumps({"server":"Broker-Server-Demo","login":12345678,"password":"wrong","remember":False}))
        self.assertEqual(code,401); self.assertFalse(body["order_send_enabled"]); self.assertEqual(body["orders_sent"],0)
