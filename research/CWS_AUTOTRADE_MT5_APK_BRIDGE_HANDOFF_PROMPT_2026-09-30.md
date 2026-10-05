@GitHub

TIẾP TỤC CWS AUTOTRADE — APK MT5 LOGIN + MT5 BRIDGE, DEMO-ONLY.

Repository:
trankhanhduy1508-maker/AI-TRADE

Nhánh duy nhất:
codex/p0-covel-knowledge-audit

HEAD tham chiếu lúc bàn giao:
4cebc07fb46f29dc7034e0eb848ad63b81a506a2

ĐỌC TRƯỚC, THEO THỨ TỰ:
1. research/CWS_METHOD_LAB_V2_IMPLEMENTATION_QA_CHECKPOINT_2026-09-30.md
2. research/CWS_AUTOTRADE_MT5_APK_BRIDGE_LOGIN_KNOWLEDGE_2026-09-30.md

Sau đó kiểm tra HEAD mới nhất.
Nếu HEAD đã đổi thì dùng HEAD mới nhất nhưng KHÔNG nghiên cứu lại toàn repository.
Chỉ đọc thêm các file Android/API/MT5/Auth/Risk mà hai checkpoint hoặc code hiện tại dẫn trực tiếp.

==================================================
MỤC TIÊU
==================================================

Xây cấu trúc CWS AutoTrade APK cho phép user kết nối tài khoản MT5 DEMO bằng:

- Broker / MT5 Server
- Login / Account Number
- Password
- Remember login (optional)
- nút KẾT NỐI MT5

Sau khi kết nối:
- xác minh đúng account + server;
- đọc account_info;
- phân biệt TRADING_ALLOWED và READ_ONLY / investor password;
- hiển thị Demo badge, account, server, balance, equity;
- AutoTrade mặc định OFF;
- chỉ tạo CWS session/token sau login;
- APK không gửi password lặp lại cho từng quyết định.

Kiến trúc:
Android APK
→ HTTPS/TLS
→ CWS Auth/Session
→ CWS MT5 Bridge
→ MetaTrader 5 Terminal
→ Broker MT5 Server

METHOD LAB V2 / Strategy:
→ chỉ tạo decision intent
→ Risk/Auth/Kill Switch
→ MT5 Execution Adapter
→ order_check
→ order_send CHƯA BẬT trong nhiệm vụ này.

==================================================
NGUYÊN TẮC BẮT BUỘC
==================================================

1. DEMO-ONLY.
2. KHÔNG gửi order thật.
3. KHÔNG bật order_send, kể cả DEMO, trừ khi nhiệm vụ sau Founder giao riêng execution phase.
4. Không hỏi password/PAT qua chat.
5. Không commit hoặc log credential thật.
6. Không hardcode password.
7. Không lưu plaintext password trong DB/Supabase.
8. Trading Engine không được biết password.
9. Nếu remember=false, credential chỉ sống tối thiểu để connect/session.
10. Nếu remember=true, thiết kế secret storage mã hóa; APK chỉ giữ opaque session.
11. Investor password → CONNECTED_READ_ONLY; AutoTrade disabled.
12. Certificate/OTP/extended-auth → ADDITIONAL_AUTH_REQUIRED, không giả login thành công.
13. Login + Password chưa đủ: phải có MT5 Server.
14. Không đụng Main/Production.
15. Không sửa R0/R1/R2/R2b/V1/V2 trừ bug integration bắt buộc và phải có regression evidence.
16. Không nghiên cứu chi phí trong nhiệm vụ này.
17. Không fake PASS.

==================================================
NHIỆM VỤ 1 — GROUND CODE HIỆN CÓ
==================================================

- Kiểm tra HEAD.
- Tìm Android project/APK code hiện có.
- Tìm backend/API/Auth hiện có.
- Tìm MT5 adapter/MetaTrader5 Python integration hiện có.
- Tìm risk/kill-switch/session code liên quan.
- Không duyệt toàn repo nếu không cần.
- Báo trong evidence file các path thực tế đã dùng.

Nếu Android skeleton chưa có:
- tạo cấu trúc tối thiểu phù hợp repo hiện tại;
- không dựng lại cả sản phẩm.

==================================================
NHIỆM VỤ 2 — SPEC LOGIN CONTRACT
==================================================

Tạo API contract tối thiểu:

POST /mt5/session/connect

Input:
{
  "server": "Broker-Server-Demo",
  "login": 12345678,
  "password": "<sensitive>",
  "remember": false
}

Success:
{
  "status": "CONNECTED",
  "session_id": "<opaque>",
  "account": {
    "login": 12345678,
    "server": "Broker-Server-Demo",
    "trade_mode": "DEMO",
    "trade_permission": "TRADING_ALLOWED",
    "balance": 10000.0,
    "equity": 10000.0
  }
}

Read only:
{
  "status": "CONNECTED_READ_ONLY",
  ...
}

Các error enum tối thiểu:
SERVER_NOT_FOUND
INVALID_LOGIN_OR_PASSWORD
INVESTOR_READ_ONLY
ADDITIONAL_AUTH_REQUIRED
TERMINAL_NOT_READY
TIMEOUT
BRIDGE_UNAVAILABLE
ACCOUNT_INFO_UNAVAILABLE

Thêm:
POST /mt5/session/disconnect
GET /mt5/session/account

Không trả raw password hoặc terminal secret trong response/log.

==================================================
NHIỆM VỤ 3 — MT5 BRIDGE ABSTRACTION
==================================================

Tạo interface/adapter sao cho production Windows bridge có thể dùng:

mt5.initialize(...)
mt5.login(login, password=..., server=...)
mt5.account_info()

Nhưng nếu cloud hiện tại không có Windows MT5 terminal:
- KHÔNG giả real-terminal PASS;
- implement interface + Fake/Mock adapter;
- test integration contract bằng fake;
- ghi rõ REAL_MT5_TERMINAL = NOT_TESTED;
- không biến mock thành production evidence.

Production adapter phải tách khỏi APK và Trading Engine.

==================================================
NHIỆM VỤ 4 — APK/UI
==================================================

Màn hình MT5 Connect:
- Server
- Login
- Password
- Show/hide password
- Remember login
- KẾT NỐI MT5
- loading / timeout / lỗi rõ ràng

Màn hình Account:
- Connected / Disconnected / Read-only
- Broker/server
- masked account number
- DEMO badge
- Balance
- Equity
- AutoTrade OFF mặc định
- Disconnect

Password không hiển thị lại sau connect.

Nếu project Android hiện dùng Compose/XML/Flutter/React Native thì giữ stack hiện tại, KHÔNG đổi framework tùy hứng.

==================================================
NHIỆM VỤ 5 — SECURITY / SESSION
==================================================

- Redact password khỏi logs.
- Session token opaque.
- Session expiry/revoke.
- Disconnect revoke session.
- Không để session cũ thành trade-enabled sau bridge restart.
- Không lẫn account giữa hai session.
- Protect remember credential bằng abstraction secret store.
- Không đưa password vào analytics/crash report.
- Test replay/stale token.
- Test wrong-account response từ terminal.

==================================================
NHIỆM VỤ 6 — RISK BOUNDARY
==================================================

Giữ flow:

METHOD LAB V2 decision intent
→ Authorization
→ Kill Switch
→ Risk Preflight
→ MT5 adapter

Trong nhiệm vụ này:
orders_sent = 0
order_send_enabled = false

Có thể chuẩn bị order_check interface nhưng không execute trade.

==================================================
NHIỆM VỤ 7 — TEST 3 VÒNG
==================================================

SMOKE:
- form validation;
- fake valid DEMO master -> CONNECTED;
- fake investor -> CONNECTED_READ_ONLY;
- invalid password/server -> fail closed;
- password không xuất hiện trong logs;
- AutoTrade default OFF.

RUNTIME:
- connect -> account_info -> session;
- disconnect -> revoke;
- reconnect;
- bridge restart;
- multiple sessions/account isolation;
- timeout;
- remember=false không persist secret;
- remember=true chỉ đi qua encrypted secret-store abstraction;
- UI state đúng với backend.

FAULT:
- wrong types;
- wrong account returned;
- stale/replayed token;
- server switch;
- terminal crash;
- network loss;
- OTP/certificate required;
- investor password;
- account trading disabled;
- kill switch false;
- secret store failure;
- session expiry;
- backend trả malformed data.

Test FAIL -> tự sửa minimal diff -> chạy lại.
Không dừng chỉ để báo cáo checkpoint.

==================================================
NHIỆM VỤ 8 — BÀN GIAO
==================================================

Khi hoàn thành:
- lưu checkpoint tiếng Việt;
- ghi rõ commit/HEAD;
- liệt kê file thay đổi;
- ghi test Smoke/Runtime/Fault;
- phân biệt:
  MOCK/Fake Bridge PASS
  REAL MT5 TERMINAL PASS hoặc NOT_TESTED
  DEMO order_send = DISABLED
- không nói “APK hoàn chỉnh kết nối MT5 thật” nếu chưa chạy real Windows MT5 terminal.
- nếu build được APK thì lưu artifact/path và hash;
- nếu chưa build được do Android toolchain thật sự thiếu, sửa môi trường nếu có thể; chỉ ghi blocker sau khi đã thử cách hợp lý.

LÀM LIÊN TỤC ĐẾN KHI HOÀN THÀNH PHẦN CÓ THỂ THỰC HIỆN TRONG PHIÊN.
Không hỏi lại các quyết định kỹ thuật đã được prompt này chốt.
