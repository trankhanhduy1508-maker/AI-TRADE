# CWS AUTOTRADE — MT5 ANDROID CLIPBOARD FIX — 2026-10-02

## Kết luận gốc
Không phải credential DEMO sai.

Credential DEMO do Founder cung cấp đã được test trực tiếp trên PC qua pinned `cloudQuant/pymt5@e7b5a8d...` và MetaQuotes WebTerminal protocol.

Kết quả matrix 4/4:
- DIRECT + web.metatrader.app + SHA1 client-id: LOGIN_CODE=0
- DIRECT + empty URL + SHA1 client-id: LOGIN_CODE=0
- INIT + web.metatrader.app + SHA1 client-id: LOGIN_CODE=0
- INIT + empty URL + random client-id: LOGIN_CODE=0

Sau đó cùng credential được đưa qua toàn bộ CWS backend:
- POST /mt5/session/connect -> 200 CONNECTED
- GET /mt5/session/account -> 200 CONNECTED
- GET /mt5/session/account lần 2 -> 200 CONNECTED
- trade_mode = DEMO
- trade_permission = TRADING_ALLOWED
- POST /mt5/session/disconnect -> 200 DISCONNECTED
- order_send_enabled = false
- orders_sent = 0

Không ghi Login/password thật vào tài liệu này.

## Root cause thực tế
Lần nhập tay trên APK Android gửi đúng độ dài:
- login_digits = 10
- password_length = 8
nhưng broker trả login code 3 sau 3 lần retry.

Vì exact credential từ Founder đã PASS khi đưa trực tiếp qua PC và CWS backend, root cause còn lại là manual entry trên Android có thể khác ký tự dù độ dài giống nhau.

Không tiếp tục bắt Founder gõ lại bằng tay.

## Sửa Android
HEAD:
`f9934031564079836bdaa88f0b580fb3638c310f`

Thay đổi:
- thêm nút `DÁN TỪ MT5`;
- parser chỉ lấy Login + Password + MetaQuotes-Demo từ clipboard;
- bỏ qua Investor password;
- clipboard chỉ xử lý trong RAM;
- không ghi credential vào SharedPreferences/file/GitHub/log;
- nếu connect fail, password không bị xóa ngay để người dùng có thể đối chiếu;
- password vẫn bị xóa sau connect thành công, disconnect hoặc onDestroy;
- versionCode = 5;
- versionName = 0.5.0-demo.

## Backend
- ai-trade-mt5-session v8
  - retry verifier tối đa 3 lần;
  - audit diagnostic chỉ chứa metadata an toàn.
- ai-trade-mt5-demo-validate v5
  - aligned pinned MetaQuotes WebTerminal direct-login flow.

Selftest sau deploy:
- REAL_DEMO_SESSION_E2E_PASS
- tradeMode DEMO
- tradePermission TRADING_ALLOWED
- orderSendEnabled false
- ordersSent 0
- credentialExposed false
- sessionTokenExposed false

## Gate evidence cho HEAD f9934031
- Local Android source unittest: 10/10 PASS.
- GitHub Android DEMO APK run 36992239724: SUCCESS.
- GitHub source-only QA run 36992239765: SUCCESS.
- GitHub Android device smoke run 36992239775: SUCCESS.
- MT5 Demo Protocol Probe run 36992244610: SUCCESS.
- Device smoke kiểm install + launch + nút DÁN TỪ MT5 + relaunch + logcat.

Artifact:
- GitHub artifact ID: 11219724409
- APK SHA-256:
  `67c7fd155d0d3cf03a2276cddda4194e7fa6f0085c88c09c9c17add5a5539920`

## Security
- DEMO only.
- Live money locked.
- order_send_enabled = false.
- orders_sent = 0.
- Không lưu password vào APK persistence.
- Không đưa credential vào GitHub.

## Bước test vật lý tiếp theo
Trên MT5 Android:
1. dùng biểu tượng Copy của tài khoản DEMO;
2. mở CWS AutoTrade v0.5.0-demo;
3. bấm `DÁN TỪ MT5`;
4. bấm `KẾT NỐI MT5`.

Không gõ tay lại Login/password.
