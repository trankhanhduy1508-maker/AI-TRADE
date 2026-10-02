# CWS AUTOTRADE — MT5 DIRECT ANDROID RECOVERY — 2026-10-02

## Kết luận gốc

Không yêu cầu Founder nhập lại MT5 credential để chẩn đoán lỗi cloud nữa.

Bằng chứng runtime với credential DEMO do Founder cho phép sử dụng:
- Android -> Supabase verifier: broker trả login code 3.
- Server diagnostic chỉ ghi metadata an toàn:
  - login_digits = 10
  - password_length = 8
  - verification_attempts = 3
- Không ghi Login thật, password, token hoặc broker secret vào repo/log.

Cùng credential đó được test trực tiếp trên PC Commander:
1. Python/pymt5 direct + URL + SHA1 CID: LOGIN_CODE=0.
2. Python/pymt5 direct + empty URL + SHA1 CID: LOGIN_CODE=0.
3. Python/pymt5 init + URL + SHA1 CID: LOGIN_CODE=0.
4. Python/pymt5 init + empty URL + random CID: LOGIN_CODE=0.
5. Node 24 + ws 8.18.3 + WebCrypto, byte layout tương đương verifier CWS:
   BOOT code=0, body=98; LOGIN_CODE=0, body=168.

=> Credential hợp lệ và protocol payload hoạt động.
=> Lỗi còn lại là khác biệt môi trường/egress của đường Supabase cloud đối với account DEMO mới.
Không tiếp tục bắt Founder gõ lại password để sửa handshake.

## Sửa kiến trúc

Android v0.6.0-demo-direct:
- file: `NativeMt5DirectClient.java`
- kết nối trực tiếp `wss://web.metatrader.app/terminal`
- bootstrap cmd=0
- login cmd=28
- account readback cmd=3
- AES/CBC/PKCS5Padding, IV zero, key exchange theo protocol đã pin
- xác minh bắt buộc server = `MetaQuotes-Demo`
- password chỉ dùng trong RAM của APK cho direct login
- password KHÔNG gửi qua Supabase ở luồng login mới
- password KHÔNG persist vào SharedPreferences/Keystore/repo/log
- AutoTrade vẫn OFF
- live money vẫn LOCKED

Supabase app-session cũ chỉ còn dùng cho legacy session restore đã có.
Direct login mới không giả lập cloud session và không gọi order-send.

## Runtime evidence đúng HEAD

HEAD Android direct:
`949d9bae07cfbb0b3b03e4eb1a4ec0933c18b2fc`

PASS:
- MT5 Demo Protocol Probe: run 36993597889
- Android source-only QA: run 36993594745
- Android DEMO APK: run 36993594339
- Android device smoke: run 36993594344
- emulator install: PASS
- emulator launch/relaunch: PASS
- logcat fatal-crash gate: PASS

APK artifact:
- artifact id: `11220253706`
- artifact name: `CWS-AutoTrade-DEMO-debug`
- APK SHA-256:
  `ca9d63a41ed1ef3333ca27f1b637440b52e1415c8fa5d5220137dea708549e07`

## Boundary

Đã PASS:
- user DEMO credential qua direct protocol trên PC nhiều biến thể;
- byte-equivalent Node/WebCrypto direct test;
- Android Java compile/lint;
- APK build;
- emulator device smoke.

Chưa gọi PASS:
- physical Android direct broker login bằng APK v0.6.0-demo-direct.
Không fake PASS cho bước này khi chưa có runtime evidence từ chính điện thoại.

## Render

Không thay đổi quyết định:
- Render không lưu file/state;
- Render không làm trading brain;
- không thêm Render service để giải quyết lỗi login này;
- direct Android login giúp tránh đưa thêm workload vào Render.
