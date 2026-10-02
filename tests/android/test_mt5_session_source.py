from pathlib import Path
import unittest

ROOT=Path(__file__).parents[2]
ACT=(ROOT/"android/app/src/main/java/vn/cws/aitrade/Mt5ConnectActivity.java").read_text()
CONTRACT=(ROOT/"android/app/src/main/java/vn/cws/aitrade/NativeMt5SessionContract.java").read_text()
STORE=(ROOT/"android/app/src/main/java/vn/cws/aitrade/NativeMt5EncryptedSession.java").read_text()

class AndroidMt5Source(unittest.TestCase):
    def test_required_fields_and_controls(self):
        for term in ["Broker / MT5 Server","Login / Account Number","Password","Hiện mật khẩu","Tự động ghi nhớ đăng nhập (mã hóa)","KẾT NỐI MT5","Disconnect"]:
            self.assertIn(term,ACT)

    def test_broker_is_selected_not_typed(self):
        self.assertIn("Spinner",ACT)
        self.assertIn("NativeMt5BrokerOption",ACT)
        self.assertIn('request("GET","/mt5/brokers"',ACT)
        self.assertIn('"MetaQuotes Ltd.","MetaQuotes-Demo"',ACT)
        self.assertNotIn('server=input(form,"Broker / MT5 Server"',ACT)
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
        self.assertIn("encryptedSession.save(token)",ACT)
        self.assertIn("restoreSession()",ACT)
        self.assertIn('request("GET","/mt5/session/account"',ACT)

    def test_mt5_session_store_uses_keystore_not_password(self):
        self.assertIn("AndroidKeyStore",STORE)
        self.assertIn("AES/GCM/NoPadding",STORE)
        self.assertIn("vn.cws.aitrade|mt5_session|v1",STORE)
        self.assertNotIn('putString("password"',STORE)
        self.assertNotIn('FIELD = "password"',STORE)
        self.assertNotIn('savedPassword',STORE)
    def test_masking(self):
        self.assertIn("maskLogin",CONTRACT); self.assertIn("••••",CONTRACT)

    def test_backend_contract_and_client_trace_headers(self):
        self.assertIn("value.length() < 4", CONTRACT)
        self.assertIn("value.length() > 32", CONTRACT)
        self.assertIn('"X-CWS-Client","android-native-mt5"', ACT)
        self.assertIn('"X-CWS-Client-Version",BuildConfig.VERSION_NAME', ACT)
