# QUY TẮC CHỐT — CWS AI TRADE: WEB APP TRƯỚC, AUTO TRADE ĐẠT GATE, APK RELEASE SAU
Ngày: 2026-09-28. Founder: Duy Trần. Canonical repo `trankhanhduy1508-maker/AI-TRADE`, **nhánh duy nhất** `codex/p0-covel-knowledge-audit`.

## Thứ tự bắt buộc, không đảo
1. **Web App trước:** sửa lỗi HTML bị Supabase Edge trả `text/plain`, phát hành static HTML qua host thực sự phục vụ `text/html`; kiểm chứng HTTP MIME, assets, Google OAuth Founder, mobile Chrome, offline/PWA, biểu đồ, danh mục thật, EPUB và tổng Lot/P&L. Supabase tiếp tục là backend/API, không coi Edge HTML là website.
2. **MT5 kết nối bảo mật:** Google Founder auth rồi liên kết account login + broker server + password qua server-side Vault; không nhúng password/token vào frontend, APK, query string, logs, GitHub, Drive hay chat. Chỉ hiện dữ liệu riêng sau xác thực; broker read-only phải kiểm chứng bằng phiên MT5 đang còn hiệu lực, không lấy `last_verified_at` cũ làm online hiện tại. Backend MT5 độc lập với điện thoại: app đóng/mất mạng không khiến cloud trader phụ thuộc thiết bị.
3. **Học, chiến lược, tự giao dịch:** kiểm kê dữ liệu nhiều năm **thực sự có quyền** theo từng nhà cung cấp, raw/hash/time-split; Masterbook chỉ cung cấp knowledge/giả thuyết, không mặc định là model weights. Train candidate; chứng minh OOS kín, walk-forward, cost/spread/slippage, stress, broker-symbol mapping, demo-forward. Model REJECTED / dữ liệu thiếu quyền **không thể promote**; không bịa backtest vài chục năm. Tín hiệu thiếu gate => `ABSTAIN`. Tự đặt lệnh DEMO chỉ khi model + broker + risk + kill-switch + The5ers (nếu applicable) + Founder approval đều PASS, trên engine server có log, reconcile/idempotency và nút dừng khẩn cấp. **Live-money LOCKED** cho tới một phê duyệt riêng tường minh, không ngầm bật qua login hay cập nhật app.
4. **Triple-check** nguồn/quyền/commit/hash → test/HTTP/mobile/broker runtime thật → đọc lại GitHub/Supabase/artifact/gates. Các mục chưa có evidence là `BLOCKED/PENDING`, không gọi DONE.
5. **APK CUỐI CÙNG:** chỉ tạo/phát hành sau khi **toàn bộ chức năng cam kết của Web App và DEMO auto-trade được xác minh và Founder nghiệm thu**, gồm thử nghiệm thiết bị. **Không xuất APK debug từng checkpoint, không tự build APK trên mỗi push, không gửi thêm APK thử khi chưa đủ gate.** Giữ một codebase web và cùng API backend; không xây 2 sản phẩm lệch nhau.

## Tự cập nhật Android, không cần gỡ cài lại
- Duy trì **cùng applicationId** `vn.cws.aitrade`, `versionCode` tăng nghiêm ngặt, và **cùng khóa ký release ổn định** do Founder sở hữu, lưu ngoài repo và bộ chứa artifact công khai. Không dùng khóa debug tự sinh mỗi CI: hai APK ký bằng khóa khác nhau không thể cập nhật tại chỗ.
- **Ưu tiên Google Play:** Play In-App Updates (flexible/immediate khi phù hợp), cập nhật và giữ dữ liệu theo quy trình Play. Không khẳng định tự cập nhật im lặng khi nền tảng yêu cầu người dùng xác nhận.
- Nếu phát hành ngoài Play: ứng dụng kiểm tra metadata bản phát hành qua **HTTPS endpoint chính thức**; xác minh ứng dụng, phiên bản cao hơn, chữ ký/phương tiện phân phối và SHA-256 trước khi bàn giao cho Android PackageInstaller; hệ điều hành/người dùng chấp thuận cập nhật theo quyền trên máy. Không lén cài APK, không bỏ qua cơ chế Android. Cần ký release ổn định và kiểm thử cập nhật trên máy thực.
- **Phân biệt hai loại cập nhật:** Web App/PWA tự nhận mã giao diện từ static host + service worker phiên bản; logic trading/risk trên backend qua quá trình triển khai có kiểm soát; APK native cần cập nhật chính thức khi có thay đổi package/WebView/permission hoặc bản bundle bắt buộc. Không nhúng khả năng tải và chạy JS không được ký/kiểm chứng.
- Update không tự thay model/chiến lược hay mở broker permission. Có rollback phiên bản được ký, nhật ký audit; kiểm thử upgrade giữ nguyên EPUB/vị thế/thiết lập trước khi phát hành.

## Các điều không được giả hoàn thành
- Supabase Edge trả mã HTML thô không được dùng làm link Web App.
- Tài khoản MT5 từng được xác minh không đồng nghĩa đang connected hoặc đủ quyền giao dịch.
- Backtest quá khứ/fixture không chứng minh model đã train hợp pháp, có khả năng giao dịch có lãi hoặc đủ OOS/WF.
- APK v0.3.0 debug trước đây là **artifact lịch sử** và **không phải bản auto-trade hay release**.
- Chưa có stable signing key, bằng chứng Android upgrade E2E và một kênh APK update đã triển khai thì ghi `BLOCKED`; không phát hành APK để che các blocker đó.

## Gate hiện tại khi ghi quyết định
Web hosting public có HTML MIME: **BLOCKED** (Render account trả lỗi/billing); Google Sites chưa publish; MT5 account DEMO trong Vault từng verified nhưng frontend chưa có authenticated session; hai model `REJECTED`, `risk_profile_approved=false`, `demo_send_enabled=false`, The5ers `BLOCKED_APPROVAL`; live-money `LOCKED`. Chỉ thực hiện các phần an toàn/độc lập, không mở lệnh.
