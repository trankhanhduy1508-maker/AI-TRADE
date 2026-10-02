# CWS AI TRADE — APK-first product spec: cập nhật/rollback, tự học, can thiệp, biểu đồ

Ngày 2026-09-28. **Tình trạng:** hướng APK và update/rollback được Founder yêu cầu; phương án UX đóng lệnh và TradingView là **đề xuất**, chưa là lệnh thay đổi broker execution.

## Trải nghiệm khách hàng được định hướng

Mở app → Google login → liên kết đúng broker/server/tài khoản qua backend auth/Vault → màn hình tổng hợp 16 thị trường theo universe (chỉ số vị thế có thật khi xác thực) → trang EA có trạng thái `ABSTAIN`/`PAPER`/`DEMO`/`LIVE LOCKED`, chiến lược/model version và mức rủi ro đã duyệt → quản lý cập nhật/phiên bản → xem bằng chứng AI học. Nếu chưa đủ gate, nút Bật Auto Trade phải disabled, hiển thị lý do, tuyệt đối không có “demo PASS” giả.

### Nâng cấp APK và khôi phục
Màn hình `Cập nhật & khôi phục` hiển thị bản app đang cài, build SHA và phiên bản được ký, ngày phát hành, ghi chú/tương thích dữ liệu, nút kiểm tra cập nhật. Stable channel opt-in; security-critical update có cảnh báo riêng. Luôn hiển thị phiên bản model/strategy/knowledge **độc lập** so với APK. Khi version hiện hành có lỗi, khách có thể quay về *một bản model/strategy đã được duyệt và tương thích* (chỉ khi Risk Engine cho phép) hoặc ngay lập tức `PAUSE_NEW_ORDERS`; giao diện rollback đã được kiểm integrity nếu có. Native APK recovery phải là bản mới có `versionCode` tăng, mang nội dung cũ đã kiểm và được cùng signing identity ký. Không hứa silent native downgrade. Trước/sau update: export/backup đã mã hóa và kiểm migrations, login, vault reference, subscription, existing positions, kill-switch và dữ liệu học; app không tự thay đổi vị thế đang mở.

### Quá trình tự học
Trang `Kho tri thức` hiển thị danh sách nguồn đã có, phân biệt sách nguyên bản (quyền riêng), distilled lessons, market dataset, backtest report, unapproved candidate và approved model; hiển thị provenance, hash, phạm vi giấy phép, coverage thực tế và trạng thái từng bước. Nhận tài liệu xong không tự tuyên bố đã train; tác vụ nhỏ/khả năng offline index có thể chạy trên điện thoại sau consent, training nặng chạy trên worker CWS khi được cấp tài nguyên; kết quả phải qua OOS/WF/paper/demo gate. Không tự promote từ REJECTED.

### Kiểm soát lệnh (đề xuất để Founder chốt)
Mặc định `AUTO_DISCIPLINED` không đặt biểu đồ và nút BUY/SELL vào giữa màn hình. Nút `Tạm dừng lệnh mới` và `Dừng khẩn cấp` luôn dễ tìm. Đề xuất `Đóng lệnh`/ `Đóng tất cả` cho chủ tài khoản có quyền, bảo đảm phản hồi chính xác từ broker trước khi hiện thành công, partial fills/timeout/retries idempotent; đóng tay sẽ freeze reentry và journal `MANUAL_OVERRIDE` để model không mở lại ngay. Nếu khách đóng bằng ứng dụng MT5 khác, reconciliation phải phát hiện và không lập tức đảo chiều. Emergency không phụ thuộc vào thông báo AI và không bắt khách chờ cooldown. Logic/điều kiện thay đổi execution cần phê duyệt Founder trước khi triển khai.

### Biểu đồ (đề xuất)
Không bắt khách dùng TradingView. Tab `Biểu đồ nâng cao` mở khi khách muốn, host widget theo điều khoản và quyền phân phối; view-only, không cho phép CWS dùng chart widget làm nguồn huấn luyện hoặc giá khớp lệnh. Dashboard chính ưu tiên vị thế thực, tổng Lot/P&L, trạng thái EA/risk và nhật ký quyết định.

## Định nghĩa DONE
Không có APK bàn giao nếu chưa có DEMO execution qua gate thật; Android cài và nâng cấp tại chỗ theo cùng khóa ký; model/strategy recovery và native recovery được thử bằng phiên bản cao hơn mà vẫn giữ dữ liệu; có kiểm thử tình huống app đóng/mất mạng/broker timeout/đóng lệnh bên ngoài; mọi lệnh phải có audit và reconciled broker confirmation. Không có lời hứa lợi nhuận từ backtest lịch sử. Live-money duy trì LOCKED.

## Yêu cầu xác thực MT5 được Founder nhấn mạnh (2026-09-28)

**CWS AutoTrade APK phải kết nối MT5 từ màn hình đăng nhập với đủ 3 trường**: `Login` (số tài khoản), `Password` (mật khẩu), `Server` (máy chủ đúng của broker). Khi khách đăng nhập, APK chuyển thông tin qua HTTPS đến API đã xác thực người dùng; backend dùng adapter được hỗ trợ để **đăng nhập broker thật**, kiểm tra account ID/server/account mode và trả readback vừa xác minh gồm balance, equity, danh sách vị thế và thời gian kiểm tra. Chỉ chuyển sang `CONNECTED` sau xác nhận broker runtime; lỗi đăng nhập, server không hỗ trợ hoặc hết phiên => `DISCONNECTED` hoặc `BLOCKED`. Tuyệt đối không lấy so khớp password trong Vault hay `last_verified_at` cũ thay cho broker session hiện tại.

**Bảo vệ credential**: không lưu mật khẩu hoặc service-role token trong APK, HTML, GitHub, log hay file xuất; chỉ xử lý qua API có quyền chủ tài khoản, TLS, rate limit, audit không có bí mật và Vault khi có consent hợp lệ. Tài khoản của khách A không được đọc hoặc sử dụng tài khoản của khách B. Quyền đóng lệnh thủ công, dừng khẩn cấp và đối chiếu vị thế phải gắn đúng chủ tài khoản, không có quyền quản trị chéo.

**Hạn chế hiện tại (không được gọi DONE)**: API `ai-trade-founder-mt5` hiện chỉ chấp nhận `MetaQuotes-Demo` **đã liên kết trước** và chỉ kiểm broker DEMO theo yêu cầu; giao diện đăng nhập OAuth hiện yêu cầu origin GitHub Pages nên chưa có kênh callback Google native APK đã xác minh. API verifier hiện trả balance nhưng chưa có equity/vị thế được xác minh; chưa có generic broker adapter cho mọi server. Những phần đó phải được bổ sung và kiểm thử trên tài khoản DEMO được phép, sau đó thử Android Google login → submit 3 trường → account/positions readback → disconnect/reconnect → fail-closed mới đủ PASS. Không bật auto-trade và tuyệt đối không mở live-money chỉ vì login thành công.
