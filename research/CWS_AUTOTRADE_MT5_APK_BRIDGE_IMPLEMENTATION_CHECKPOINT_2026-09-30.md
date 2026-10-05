# CWS AUTOTRADE — MT5 APK LOGIN + BRIDGE DEMO-ONLY CHECKPOINT

**Ngày:** 2026-09-30  
**Repo:** `trankhanhduy1508-maker/AI-TRADE`  
**Nhánh duy nhất:** `codex/p0-covel-knowledge-audit`  
**HEAD đầu phiên:** `75fdb64f4a64eef9a0408a9e97c6ca80ae21124c`  
**HEAD trước checkpoint này:** `3942d623acccdb63b132c1473897e139c276770d`

## 1. Phạm vi đã triển khai

Đã thêm boundary MT5 session riêng, không sửa METHOD LAB V2/R0/R1/R2/R2b/V1/V2:

- `src/execution/mt5_session_bridge.py`
  - production abstraction cho `initialize`, `login`, `account_info`;
  - `RealMetaTrader5Bridge` import MetaTrader5 lazy để cloud/Linux không giả real-terminal PASS;
  - CWS opaque session token, expiry, revoke, bridge-generation fence;
  - mỗi session giữ bridge binding riêng để tránh lẫn account;
  - account/server/mode DEMO được kiểm tra lại;
  - master → `CONNECTED`; investor/read-only → `CONNECTED_READ_ONLY`;
  - AutoTrade luôn OFF trong phase này;
  - `ORDER_SEND_ENABLED = False`, không expose/call `order_send`.

- `src/execution/mt5_session_http.py`
  - `POST /mt5/session/connect`;
  - `GET /mt5/session/account`;
  - `POST /mt5/session/disconnect`;
  - response `Cache-Control: no-store`;
  - error body không echo password/raw terminal secret;
  - error enum có: SERVER_NOT_FOUND, INVALID_LOGIN_OR_PASSWORD, INVESTOR_READ_ONLY, ADDITIONAL_AUTH_REQUIRED, TERMINAL_NOT_READY, TIMEOUT, BRIDGE_UNAVAILABLE, ACCOUNT_INFO_UNAVAILABLE và các lỗi fail-closed session/account bổ sung.

- Android native:
  - `Mt5ConnectActivity.java`: Server, Login, Password, show/hide, Remember login, KẾT NỐI MT5, loading/error, account state, masked account, DEMO, Balance, Equity, AutoTrade OFF, Disconnect.
  - password bị xóa khỏi EditText sau submit;
  - APK không persist MT5 password vào SharedPreferences;
  - APK chỉ giữ opaque `sessionId` trong memory;
  - endpoint bridge lấy từ Gradle property `cwsMt5BridgeBaseUrl`, bắt buộc HTTPS và không hardcode credential;
  - `MainActivity` route nút MT5 sang màn hình mới;
  - manifest đăng ký activity mới.

## 2. Security / session

- Không credential thật trong source/test; chỉ mock string.
- `remember=false`: session service không gọi secret store.
- `remember=true`: bắt buộc đi qua `SecretStore`; mặc định `NullSecretStore` fail closed.
- Secret-store failure → `SECRET_STORE_FAILURE`.
- Disconnect revoke token; token cũ/replayed fail.
- Session expiry fail.
- Bridge restart xóa/fence session cũ.
- Wrong account/server từ terminal → fail closed.
- Multiple sessions có bridge binding tách riêng.
- Password không đưa vào METHOD LAB.
- `orders_sent = 0`.
- `order_send_enabled = false`.

## 3. Test 3 vòng

Môi trường test cục bộ của phiên không có mạng GitHub trực tiếp/Windows MT5 terminal. Code được chuẩn bị và chạy test cục bộ trước khi upload; sau upload đã read-back đúng bytes GitHub và kiểm tra lại các invariant source quan trọng.

### Smoke
`python -m unittest -q tests.execution.test_mt5_session_bridge.Smoke`

**5/5 PASS**
- valid fake DEMO master → CONNECTED;
- investor → CONNECTED_READ_ONLY;
- invalid password → fail closed;
- wrong server → fail closed;
- AutoTrade OFF + password redaction + orders_sent=0.

### Runtime
`python -m unittest -q tests.execution.test_mt5_session_bridge.Runtime tests.execution.test_mt5_session_http.HttpContract`

**11/11 PASS**
- connect → account_info → session;
- disconnect → revoke;
- reconnect;
- bridge restart;
- timeout;
- multiple session isolation;
- remember=false no secret-store write;
- remember=true secret-store path;
- ba HTTP route;
- bearer/session fail closed;
- error never enables execution.

### Fault
`python -m unittest -q tests.execution.test_mt5_session_bridge.Fault`

**9/9 PASS**
- wrong types;
- wrong account;
- stale/replayed token;
- server switch;
- terminal unavailable/network loss;
- non-DEMO account;
- malformed account_info;
- secret-store failure;
- session expiry.

### Android/source
- Pure Java contract: **12/12 PASS** bằng `javac` + `java`.
- Android source QA: **7/7 PASS**.
- `python -m compileall -q src tests`: **PASS**.
- Read-back exact GitHub bytes: **PASS** cho no-order_send, order_send hard false, required errors, 3 routes, UI fields, password clear/no local persistence, opaque session, response execution gates, manifest, MainActivity route và HTTPS external config.

## 4. Trạng thái MT5 thật và APK

`MOCK_MT5_BRIDGE = PASS`

`REAL_MT5_TERMINAL = NOT_TESTED`

Lý do: phiên này không có Windows MetaTrader 5 terminal thật. Không gọi mock là MT5 thật.

`DEMO_ORDER_SEND = DISABLED`

`orders_sent = 0`

APK **không được build/bàn giao trong checkpoint này**: repo hiện có release gate chủ động không build APK trước khi DEMO execution/release evidence hoàn tất, và phase này cố ý chưa bật order_send. Không phá gate cũ để tạo artifact giả hoàn thiện.

## 5. File thay đổi

- `src/execution/mt5_session_bridge.py`
- `src/execution/mt5_session_http.py`
- `tests/execution/test_mt5_session_bridge.py`
- `tests/execution/test_mt5_session_http.py`
- `android/app/src/main/java/vn/cws/aitrade/NativeMt5SessionContract.java`
- `android/app/src/main/java/vn/cws/aitrade/Mt5ConnectActivity.java`
- `android/qa/NativeMt5SessionContractCheck.java`
- `tests/android/test_mt5_session_source.py`
- `android/app/src/main/java/vn/cws/aitrade/MainActivity.java`
- `android/app/src/main/AndroidManifest.xml`
- `android/app/build.gradle`

## 6. Ranh giới chưa được tuyên bố PASS

- Chưa test Windows MT5 terminal thật.
- Chưa deploy HTTPS bridge host thật.
- Chưa Android SDK/device E2E cho activity mới.
- Chưa execution phase; không order_send kể cả DEMO.
- METHOD LAB V2 vẫn RESEARCH_ONLY / edge UNPROVEN.

**Kết luận:** cấu trúc APK login + CWS session + DEMO-only MT5 Bridge đã được triển khai và test bằng fake/contract; execution vẫn fail-closed và tách khỏi strategy.
