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
`64f64c368d1d7965d39bac9091a8fbb5c94f6145`

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
PC Commander clone đúng HEAD `64f64c3...`.
`python -m unittest discover -s tests/android -p test_mt5_session_source.py -v`
=> 10/10 PASS.

Java contract local không chạy vì host hiện không có Java/JDK; không gọi phần đó PASS từ local host.

### GitHub Android DEMO APK
Run: `36985196955`
Conclusion: SUCCESS.
Artifact: `CWS-AutoTrade-DEMO-debug`
Artifact ID: `11217700771`

APK SHA-256:
`c9e09f4c3e1fc4242ad96d3d37bbe8b942f73b76b5d2abf8be1bb3973186b7da`

### GitHub source-only QA
Run: `36985196954`
HEAD: `64f64c3...`
Conclusion: SUCCESS.

### GitHub device smoke
Run: `36985196986`
HEAD: `64f64c3...`
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
