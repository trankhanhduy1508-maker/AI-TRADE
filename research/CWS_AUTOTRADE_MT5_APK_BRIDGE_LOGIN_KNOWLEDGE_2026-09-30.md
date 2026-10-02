# CWS AutoTrade — Kinh nghiệm kiến trúc MT5 Login/Bridge cho APK
**Ngày:** 2026-09-30  
**Repo:** `trankhanhduy1508-maker/AI-TRADE`  
**Nhánh duy nhất:** `codex/p0-covel-knowledge-audit`  
**Parent HEAD:** `bd35c9126e487117157eeb742dcd3aefd5e0d261`

## 1. Kết luận kiến trúc

CWS AutoTrade APK có thể cung cấp trải nghiệm giống app giao dịch:

- chọn **Broker / MT5 Server**;
- nhập **Login (account number)**;
- nhập **Password**;
- nhấn **Kết nối MT5**;
- sau khi xác thực, hiển thị account/server/balance/equity/quyền giao dịch;
- AutoTrade chỉ được mở khi backend/bridge xác nhận tài khoản có quyền trade và mọi gate an toàn đạt.

Điểm quan trọng: APK **không nhúng MT5 desktop terminal** và không giả định có một REST endpoint MT5 công khai để APK tùy ý gửi lệnh trực tiếp.

Kiến trúc mục tiêu:

```
Android APK
    |
    | HTTPS/TLS
    v
CWS Auth / Session
    |
    v
CWS MT5 Bridge (Windows/VPS/host được phép)
    |
    +--> MetaTrader 5 terminal
    |        |
    |        v
    |     Broker MT5 Server
    |
    +--> CWS Trading Engine
    +--> Risk / Kill Switch / Audit
```

## 2. Vì sao cần MT5 Bridge

MetaQuotes Python Integration làm việc với **MetaTrader 5 terminal** qua interprocess communication. Tài liệu chính thức nêu:
- `initialize(..., login=..., password=..., server=...)` thiết lập kết nối với MT5 terminal và có thể khởi chạy terminal khi cần;
- `login(login, password=..., server=...)` kết nối tới trading account;
- `account_info()` đọc thông tin current account;
- `order_check(request)` chỉ kiểm tra request/funds, thành công không bảo đảm order cuối cùng sẽ được thực thi;
- `order_send(request)` thuộc lớp execution và chỉ được nối sau risk/auth/kill-switch gates.

Do đó luồng chuẩn cho APK là:
```
APK credentials -> HTTPS -> MT5 Bridge
MT5 Bridge -> initialize terminal
MT5 Bridge -> login(account, password, server)
MT5 Bridge -> account_info()
MT5 Bridge -> trả CWS session/token cho APK
```

APK sau login **không gửi password lặp lại cho mỗi quyết định giao dịch**.

## 3. Login form bắt buộc

Không chỉ Login + Password. Phải có ít nhất:

```
Server / Broker Server
Login / Account Number
Password
[Remember login] (optional)
[KẾT NỐI MT5]
```

MT5 Android chính thức cũng yêu cầu Login, Password và Server khi kết nối existing account. Broker/server cần được tìm hoặc nhập chính xác.

Có hai quyền password quan trọng:
- **Master / trading password:** có thể giao dịch;
- **Investor password:** chỉ xem account/prices, không thực hiện trade.

Nếu kết nối bằng investor password:
```
CONNECTED_READ_ONLY
AutoTrade = DISABLED
```

Không được đợi tới `order_send` mới phát hiện tài khoản read-only.

Một số server có thể bật **extended authentication/certificate** hoặc OTP. Kiến trúc phải trả trạng thái `ADDITIONAL_AUTH_REQUIRED` thay vì giả login/password luôn đủ.

## 4. API contract đề xuất cho APK

### POST /mt5/session/connect
Input:
```json
{
  "server": "Broker-Server-Demo",
  "login": 12345678,
  "password": "<sensitive>",
  "remember": false
}
```

Output thành công:
```json
{
  "status": "CONNECTED",
  "session_id": "<opaque-cws-session>",
  "account": {
    "login": 12345678,
    "server": "Broker-Server-Demo",
    "trade_mode": "DEMO",
    "trade_permission": "TRADING_ALLOWED | READ_ONLY",
    "balance": 10000.0,
    "equity": 10000.0
  }
}
```

Output lỗi phải có enum rõ ràng, ví dụ:
- `SERVER_NOT_FOUND`
- `INVALID_LOGIN_OR_PASSWORD`
- `INVESTOR_READ_ONLY`
- `ADDITIONAL_AUTH_REQUIRED`
- `TERMINAL_NOT_READY`
- `TIMEOUT`
- `BRIDGE_UNAVAILABLE`
- `ACCOUNT_INFO_UNAVAILABLE`

Không trả raw terminal error/password về log khách hàng.

### POST /mt5/session/disconnect
- xóa CWS session;
- disconnect/shutdown binding theo policy;
- xóa credential khỏi RAM/secret lease khi không remember.

### GET /mt5/session/account
- trả trạng thái account hiện tại;
- không cần password.

## 5. Quy tắc credential

Tuyệt đối không:
- hardcode password vào APK;
- commit password/login thật lên GitHub;
- log password;
- lưu plaintext trong Supabase/database;
- gửi password lại ở mỗi trade request;
- đưa password vào crash report/analytics.

Nếu `remember=false`:
- credential chỉ tồn tại trong request và memory cần thiết cho connect;
- xóa/reference-release sau khi tạo session.

Nếu `remember=true`:
- mã hóa at rest bằng secret/key-management riêng;
- APK chỉ giữ token/session opaque;
- log phải redact;
- cần revoke/delete credential.

Trading Engine không cần biết password. Chia trách nhiệm:

```
Credential Service / MT5 Bridge -> biết credential tối thiểu
Trading Engine              -> nhận market/account state, không nhận password
APK                          -> nhận session token, không nhận secret backend
```

## 6. Luồng Demo-first cho CWS

Giai đoạn đầu **chỉ MT5 DEMO**:

1. APK nhập Server/Login/Password.
2. Backend kiểm tra input và TLS/session.
3. MT5 Bridge `initialize`.
4. `login`.
5. `account_info`.
6. Xác nhận:
   - account đúng;
   - server đúng;
   - DEMO;
   - trade permission;
   - connection healthy.
7. Trả CONNECTED hoặc CONNECTED_READ_ONLY.
8. AutoTrade mặc định **OFF**.
9. Khi bật AutoTrade:
   - kill switch;
   - authorization;
   - METHOD LAB / strategy;
   - portfolio/risk preflight;
   - `order_check`;
   - sau này mới `order_send` trong demo execution phase được founder bật rõ ràng.

Không cho login thành công đồng nghĩa AutoTrade tự ON.

## 7. Kiến trúc Android tối thiểu

Màn hình 1 — MT5 Connect:
- Server search/input
- Login numeric
- Password
- Show/hide password
- Remember login
- Connect

Màn hình 2 — Account:
- Connected / disconnected / read-only
- Broker/server
- Account number masked một phần
- Demo badge
- Balance/equity
- AutoTrade OFF/ON
- Disconnect

Màn hình 3 — AutoTrade status:
- Engine status
- Kill switch
- Last decision
- Position
- Read-only audit/history

Không hiển thị password sau connect.

## 8. Acceptance tests bắt buộc

Smoke:
- valid demo master credential -> CONNECTED;
- valid investor credential -> CONNECTED_READ_ONLY;
- invalid password -> fail closed;
- wrong server -> fail closed;
- no password stored when remember=false.

Runtime:
- bridge restart không biến session cũ thành trade-enabled giả;
- account_info phải khớp login/server trước khi enable;
- disconnect revoke session;
- multiple APK sessions không làm lẫn account;
- login timeout không treo UI vô hạn;
- password redaction trong logs.

Fault:
- string/integer sai kiểu;
- replay session token;
- wrong account returned by terminal;
- server switch;
- bridge/terminal crash;
- network loss;
- certificate/OTP required;
- investor password;
- stale account state;
- kill switch false;
- terminal reports trading disabled;
- secret-storage failure.

Không fake PASS. Test DEMO-send chỉ được thực hiện khi execution phase được giao riêng.

## 9. Quan hệ với METHOD LAB V2

METHOD LAB V2 hiện vẫn `RESEARCH_ONLY`, `orders_sent=0`, `edge_status=UNPROVEN`.

Kiến trúc phải giữ ranh giới:
```
METHOD LAB V2
   -> decision intent
Risk/Auth/Kill Switch
   -> allowed/blocked
MT5 Execution Adapter
   -> order_check
   -> order_send (future DEMO execution phase only)
```

Không để strategy code gọi MT5 credential hoặc `order_send` trực tiếp.

## 10. Nguồn chính thức đã xác minh ngày 2026-09-30

- MetaTrader 5 Android Account Connection:
  https://www.metatrader5.com/en/mobile-trading/android/help/settings_accounts/account_connect
- MetaTrader 5 Python Integration:
  https://www.mql5.com/en/docs/python_metatrader5
- Python initialize:
  https://www.mql5.com/en/docs/python_metatrader5/mt5initialize_py
- Python login:
  https://www.mql5.com/en/docs/python_metatrader5/mt5login_py
- account_info:
  https://www.mql5.com/en/docs/python_metatrader5/mt5accountinfo_py
- order_check:
  https://www.mql5.com/en/docs/python_metatrader5/mt5ordercheck_py

## 11. Quyết định bàn giao

Bước tiếp theo cho chat mới:
1. đọc checkpoint METHOD LAB V2;
2. đọc file này;
3. kiểm tra HEAD mới nhất;
4. khảo sát code Android/API/MT5 hiện có trong repo, không nghiên cứu lại toàn repo;
5. viết spec DEMO-only MT5 Bridge;
6. triển khai login contract + bridge abstraction + secure session;
7. mock/fake MT5 adapter trước nếu môi trường không có Windows terminal;
8. tách rõ mock PASS và real-terminal PASS;
9. không `order_send` thật cho tới khi founder giao execution phase;
10. Smoke -> Runtime -> Fault, lưu evidence và checkpoint.

**Không dùng password thật trong source/test.**
