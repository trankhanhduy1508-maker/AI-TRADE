# CWS AUTOTRADE — ANDROID MT5 RECOVERY CHECKPOINT — 2026-10-02

## Kết luận chính
Không xây lại từ đầu. Backend MT5 hiện tại hoạt động; điểm cần sửa là Android/device/build cũ.

## Evidence backend
Supabase project: `oziktadfeenydvgobudr`.

Internal selftest `ai-trade-mt5-session-selftest` đã chạy lại bằng credential DEMO trong Vault và trả:
- `REAL_DEMO_SESSION_E2E_PASS`
- connect HTTP 200 / CONNECTED
- account HTTP 200 / CONNECTED
- disconnect HTTP 200 / DISCONNECTED
- tradeMode DEMO
- tradePermission TRADING_ALLOWED
- orderSendEnabled false
- ordersSent 0
- credentialExposed false
- sessionTokenExposed false

=> Backend MT5 session không phải blocker hiện tại.

## Sửa Android
HEAD source dùng để build APK:
`a35999c8c62e6bc2632f301aa755bec1f4182845`

Các sửa:
1. Password contract: 4–32 ký tự, đồng bộ backend.
2. Không xóa encrypted session cũ trước khi input mới qua validation.
3. Request thêm:
   - `X-CWS-Client: android-native-mt5`
   - `X-CWS-Client-Version: BuildConfig.VERSION_NAME`
4. Error mapping rõ hơn:
   - NETWORK_TIMEOUT
   - NETWORK_DNS_FAILED
   - BRIDGE_UNAVAILABLE
5. Version:
   - versionCode = 4
   - versionName = `0.4.0-demo`

## Test
### Local source QA
PC Commander clone đúng HEAD `a35999c8...`.
`python -m unittest discover -s tests/android -p test_mt5_session_source.py -v`
=> 10/10 PASS.

Java contract local không chạy vì host hiện không có Java/JDK; không gọi phần đó PASS từ local host.

### GitHub Android DEMO APK
Run: `36985873836`
Conclusion: SUCCESS.
Artifact: `CWS-AutoTrade-DEMO-debug`
Artifact ID: `11217836696`

APK SHA-256:
`ff20a195d4acb3ca809d1075798727105aea098441c87550d2f440e71a979601`

### GitHub source-only QA
Run: `36985873853`
HEAD: `a35999c8...`
Conclusion: SUCCESS.

### GitHub device smoke
Run: `36985874034`
HEAD: `a35999c8...`
Conclusion: SUCCESS.

## Ranh giới PASS
PASS:
- Backend REAL DEMO session E2E.
- Android source QA.
- APK build.
- Emulator/device smoke.

CHƯA PASS:
- Founder physical Android + real credential E2E trên APK v0.4.0-demo.
- AutoTrade DEMO order execution.

## AutoTrade
AutoTrade vẫn fail-closed:
- live money LOCKED;
- order_send chưa unlock;
- approval/risk/demo-send gates chưa PASS;
- không bật execution chỉ để nút Android sáng.

Thiết kế VNext:
`research/CWS_AUTOTRADE_ANDROID_MT5_VNEXT_2026-10-02.md`

Render governance:
`docs/CWS_RENDER_MINIMAL_USAGE_POLICY_2026-10-02.md`


## Readiness VNext bổ sung
Supabase `ai-trade-mt5-session` version 6 đã deploy.

`GET /mt5/brokers` hiện trả:
- `control_plane = SERVER_AUTHORITATIVE`
- `render_required = false`
- `demo_autotrade_ready = false`
- blockers:
  - `RUNTIME_DISABLED`
  - `DEMO_SEND_DISABLED`
  - `RISK_NOT_APPROVED`
  - `PROVIDER_NOT_READY`

Android HEAD `a35999c8...` hiển thị blocker này trực tiếp và refresh readiness khi resume.
