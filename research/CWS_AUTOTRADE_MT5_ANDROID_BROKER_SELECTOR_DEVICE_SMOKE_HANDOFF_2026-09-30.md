# CWS AUTOTRADE — MT5 ANDROID BROKER SELECTOR + DEVICE SMOKE HANDOFF

**Ngày:** 2026-09-30  
**Repository:** `trankhanhduy1508-maker/AI-TRADE`  
**Nhánh duy nhất:** `codex/p0-covel-knowledge-audit`  
**HEAD tại thời điểm bàn giao:** `b4210648d68047370a87262458f24bae658349fb`

> Đây là handoff mới nhất và là SOURCE OF TRUTH cho phần APK MT5 login/cloud session/broker selector/device smoke.
> Không nghiên cứu lại toàn repo. Chỉ đọc các file được liệt kê dưới đây và tiếp tục từ trạng thái này.

---

## 1. Mục tiêu founder

Founder muốn APK Android CWS AutoTrade có UX giống MT5:

1. Khách **không phải gõ tên broker/server**.
2. Khách chọn broker/server từ danh sách.
3. Chỉ nhập:
   - Login
   - Password
4. Sau lần login thành công đầu tiên:
   - không phải nhập lại login/password ở những lần mở app sau;
   - APK tự restore session.
5. DEMO-only ở giai đoạn hiện tại.
6. Không giả PASS.
7. Không dừng ở compile-only; phải cố đưa device smoke tới PASS.
8. Không reboot/shutdown bất kỳ host nào.
9. Nếu FAIL -> sửa minimal diff -> chạy lại.

---

## 2. Kiến trúc hiện tại

Luồng:

`Android APK -> HTTPS -> Supabase Edge Function ai-trade-mt5-session -> MT5 cloud/WebTerminal protocol -> Broker MT5 DEMO`

**Windows không bắt buộc.**

MetaApi cloud adapter vẫn tồn tại trong repo nhưng runtime Supabase hiện không có `METAAPI_TOKEN` / `METAAPI_ACCOUNT_ID`, nên đường login hiện tại dùng MT5 cloud/WebTerminal protocol đã có trong project.

---

## 3. Android login/session đã làm

### File chính

`android/app/src/main/java/vn/cws/aitrade/Mt5ConnectActivity.java`

Đã có:

- dropdown/Spinner broker/server;
- Login;
- Password;
- Show/Hide password;
- auto-remember login;
- nút KẾT NỐI MT5;
- Disconnect;
- DEMO badge;
- account masked;
- balance/equity;
- AutoTrade vẫn fail-closed.

### Broker selector

Mới thêm:

`android/app/src/main/java/vn/cws/aitrade/NativeMt5BrokerOption.java`

APK không còn bắt khách gõ server text.

APK gọi:

`GET /mt5/brokers`

và dùng catalog từ backend.

Fallback bundled hiện có:

`MetaQuotes Ltd. · MetaQuotes-Demo`

Backend catalog hiện chỉ quảng bá broker/server **thực sự được hỗ trợ**.
Không nhét broker giả chỉ để dropdown dài.

---

## 4. Auto-login sau lần đầu

Mới thêm:

`android/app/src/main/java/vn/cws/aitrade/NativeMt5EncryptedSession.java`

Đặc điểm:

- chỉ lưu **opaque session token**;
- không lưu broker password;
- AES-GCM;
- Android Keystore;
- alias riêng:
  `vn.cws.aitrade.mt5.session.v1`;
- AAD riêng:
  `vn.cws.aitrade|mt5_session|v1`.

Flow:

1. login lần đầu thành công;
2. backend trả opaque session token;
3. APK mã hóa token bằng Android Keystore;
4. mở app sau đó -> `restoreSession()`;
5. gọi `GET /mt5/session/account`;
6. còn hợp lệ -> tự vào, không cần nhập password;
7. session hết hạn/revoke/token hỏng -> xóa local token và yêu cầu login lại;
8. Disconnect -> revoke server + xóa local token.

Backend remembered session:

- TTL 365 ngày;
- sliding renewal khi session được sử dụng thành công.

---

## 5. Supabase MT5 session backend

Function:

`ai-trade-mt5-session`

Project:

`oziktadfeenydvgobudr`

Runtime đã deploy ít nhất tới version 4 trong phiên trước.

Routes:

- `GET /mt5/brokers`
- `POST /mt5/session/connect`
- `GET /mt5/session/account`
- `POST /mt5/session/disconnect`

Session table:

`ai_trade.mt5_app_sessions`

Đặc điểm:

- token random;
- DB chỉ lưu SHA-256 token;
- RLS enabled;
- anon/authenticated direct access revoked;
- expiry + revoke;
- remember sliding renewal;
- account snapshot columns đã thêm:
  - balance
  - equity
  - currency

---

## 6. First-time account bug và fix

Founder test tài khoản DEMO mới trong APK và nhận “kết nối thất bại”.

Log runtime lúc khoảng 15:21 local:

- Android gọi `/mt5/session/connect`;
- verifier MT5 nội bộ trả HTTP 200;
- `ai-trade-mt5-session` v2 trả HTTP 503.

Nguyên nhân:

verifier/binding flow cũ yêu cầu account phải tồn tại sẵn trong:

`ai_trade.mt5_demo_accounts`

trước khi cho login.

Điều này làm account DEMO mới bị reject trước khi hoàn thành flow session.

Backend đã được sửa để hỗ trợ first-time DEMO account bằng **temporary binding**, sau đó:

- nếu verification fail -> xóa binding tạm;
- nếu pass -> tạo opaque session;
- không persist password trong session table.

Commit quan trọng:

`0fa281123528ecc8a18bf58f877ea94e335a8ed9`

Sau đó session backend tiếp tục được mở rộng broker catalog.

---

## 7. Broker catalog runtime evidence

Endpoint thật:

`GET https://oziktadfeenydvgobudr.supabase.co/functions/v1/ai-trade-mt5-session/mt5/brokers`

Đã runtime PASS:

- HTTP 200
- status OK
- broker count = 1
- broker = `MetaQuotes Ltd.`
- server = `MetaQuotes-Demo`

---

## 8. APK artifact gần nhất đã build PASS

Bản broker-selector trước khi device-smoke workflow được thêm:

GitHub HEAD tương ứng:

`a832535b17d610827f7319b0d452cfc3d1dc0689`

Artifact:

`CWS-AutoTrade-DEMO-broker-selector.apk`

SHA-256:

`c158495deaddad7fb85265f1aa1ad349ccbb7f956314d15bfe82dfcbc204e70f`

Đã PASS:

- source tests;
- Java debug/release compile;
- lint;
- APK assemble;
- artifact upload;
- MT5 Demo Protocol Probe.

**Nhưng chưa được gọi device E2E PASS.**

---

## 9. Device smoke mới được thêm

Workflow:

`.github/workflows/cws-autotrade-android-device-smoke.yml`

Mục tiêu:

1. build debug APK;
2. boot Android emulator;
3. install APK;
4. start:
   `vn.cws.aitrade/.Mt5ConnectActivity`;
5. UI dump;
6. assert:
   - Broker / MT5 Server;
   - MetaQuotes Ltd. · MetaQuotes-Demo;
   - Login / Account Number;
   - Password;
   - KẾT NỐI MT5;
7. force-stop app;
8. relaunch;
9. kiểm app không crash;
10. capture logcat;
11. fail nếu có FATAL EXCEPTION cho package.

### Lỗi emulator đã gặp

#### Round 1

FAIL tại boot:

`adb: command not found`

Fix:

dùng absolute path:

`$ANDROID_HOME/platform-tools/adb`

Commit:

`7b2e85914dc0dba7e48530cec0bc1362ae016a37`

#### Round 2

Emulator vẫn fail/timeout ở boot.
Workflow từng dùng:

`-accel off`

x86_64 software emulation quá chậm.

Fix mới:

- nếu có `/dev/kvm`, chmod và dùng acceleration;
- fallback `-accel off`;
- boot timeout rõ;
- nếu fail thì dump `/tmp/emulator.log`.

Commit:

`229d81a77d9f0148733b5f69116857c483115f63`

### Zombie workflow problem

Một run cũ bị kẹt ở step logcat sau boot failure và giữ concurrency lock.

Fix:

- logcat có `timeout 20`;
- concurrency group chuyển từ branch sang commit SHA.

Commits:

`c36fe988acb1610ff10217cb715aab57c05b8514`

`b4210648d68047370a87262458f24bae658349fb`

---

## 10. Trạng thái workflow tại thời điểm handoff

HEAD:

`b4210648d68047370a87262458f24bae658349fb`

MT5 Demo Protocol Probe trên HEAD:

**PASS**

Run:

`36697406326`

Device smoke trên HEAD:

Run:

`36697401100`

Status tại thời điểm handoff:

**IN_PROGRESS**

Job:

`109828544049`

Lưu ý:
trước đó có nhiều run cũ cancelled/failure do sửa workflow emulator.
Không dùng kết quả cũ để kết luận cho HEAD hiện tại.

---

## 11. Tài khoản DEMO founder đã cung cấp

Founder đã gửi screenshot tài khoản MetaQuotes-Demo và cho phép test tự do vì là DEMO.

Không ghi password vào source/handoff.

Tool orchestration có lớp bảo vệ credential nên không thể tự chuyển password nhìn thấy trong screenshot qua Supabase/GitHub tool calls.

Do đó:

- có thể test UI/device smoke không credential;
- có thể đọc log runtime sau khi Founder bấm connect;
- không được fake credential E2E PASS.

Nếu Founder tự nhập credential trong APK, xem ngay Supabase logs và fix tiếp nếu fail.

---

## 12. AutoTrade hiện tại

**Không được gọi là AutoTrade execution PASS.**

Hiện:

- `order_send_enabled = false`
- `orders_sent = 0`
- AutoTrade UI fail-closed.

Repo chưa có WebTerminal broker order primitive được xác minh đủ để bật execution.
Runtime MetaApi order lane cũ lại thiếu provider token.

Không bật cờ runtime chỉ để làm nút sáng.

---

## 13. Quy tắc tiếp tục cho chat mới

1. Đọc file handoff này trước.
2. Verify branch HEAD.
3. Không nghiên cứu lại toàn repo.
4. Ưu tiên tiếp tục **device smoke** cho tới PASS.
5. Nếu device smoke FAIL:
   - đọc đúng job log;
   - minimal diff;
   - rerun;
   - không đổi mục tiêu.
6. Sau device smoke PASS:
   - lấy artifact/evidence;
   - kiểm UI dump;
   - kiểm logcat không crash.
7. Sau đó founder sẽ test credential DEMO trên điện thoại thật.
8. Nếu login fail:
   - xem Supabase function logs đúng timestamp;
   - phân biệt APK/network/backend/verifier;
   - tự fix.
9. Không fake PASS.
10. Không reboot/shutdown.
11. Không dùng credential thật trong source/test.
12. DEMO-only.
13. Không bật live-money execution.

---

## 14. File cần đọc tiếp

Theo thứ tự:

1. `research/CWS_AUTOTRADE_MT5_ANDROID_BROKER_SELECTOR_DEVICE_SMOKE_HANDOFF_2026-09-30.md`
2. `research/CWS_AUTOTRADE_MT5_CLOUD_SESSION_RUNTIME_CHECKPOINT_2026-09-30.md`
3. `research/CWS_AUTOTRADE_MT5_CLOUD_NO_WINDOWS_CORRECTION_2026-09-30.md`
4. `android/app/src/main/java/vn/cws/aitrade/Mt5ConnectActivity.java`
5. `android/app/src/main/java/vn/cws/aitrade/NativeMt5EncryptedSession.java`
6. `android/app/src/main/java/vn/cws/aitrade/NativeMt5BrokerOption.java`
7. `supabase/functions/ai-trade-mt5-session/index.ts`
8. `.github/workflows/cws-autotrade-android-device-smoke.yml`

---

## 15. Trạng thái chuẩn để chat mới dùng

`WINDOWS_REQUIRED = FALSE`

`BROKER_CATALOG_RUNTIME = PASS`

`APK_BROKER_SELECTOR_BUILD = PASS`

`APK_AUTO_RESTORE_SESSION_SOURCE = PASS`

`MT5_DEMO_PROTOCOL_PROBE = PASS`

`DEVICE_SMOKE = IN_PROGRESS`

`FOUNDER_REAL_ANDROID_CREDENTIAL_E2E = NOT_YET_PASS`

`AUTOTRADE_ORDER_EXECUTION = DISABLED`

`orders_sent = 0`
