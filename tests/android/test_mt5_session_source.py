from pathlib import Path
import unittest

ROOT=Path(__file__).parents[2]
ACT=(ROOT/"android/app/src/main/java/vn/cws/aitrade/Mt5ConnectActivity.java").read_text()
CONTRACT=(ROOT/"android/app/src/main/java/vn/cws/aitrade/NativeMt5SessionContract.java").read_text()

class AndroidMt5Source(unittest.TestCase):
    def test_required_fields_and_controls(self):
        for term in ["Broker / MT5 Server","Login / Account Number","Password","Hiện mật khẩu","Remember login","KẾT NỐI MT5","Disconnect"]:
            self.assertIn(term,ACT)
    def test_demo_and_autotrade_off_are_visible(self):
        self.assertIn("DEMO",ACT); self.assertIn("AutoTrade: OFF",ACT)
    def test_password_cleared_and_not_persisted_locally(self):
        self.assertIn('password.setText("")',ACT)
        self.assertNotIn('putString("password"',ACT)
        self.assertNotIn("SharedPreferences",ACT)
    def test_https_and_no_redirects(self):
        self.assertIn('startsWith("https://")',ACT)
        self.assertIn("setInstanceFollowRedirects(false)",ACT)
    def test_response_fails_closed_on_order_flags(self):
        self.assertIn('reply.optBoolean("order_send_enabled",true)',ACT)
        self.assertIn('reply.optInt("orders_sent",-1)!=0',ACT)
    def test_opaque_session_only(self):
        self.assertIn("sessionId=token",ACT)
        self.assertNotIn("String savedPassword",ACT)
    def test_masking(self):
        self.assertIn("maskLogin",CONTRACT); self.assertIn("••••",CONTRACT)
