# QUY TẮC CHỐT — CWS AI TRADE: APK-FIRST, AI HỌC LIÊN TỤC, CẬP NHẬT VÀ ROLLBACK

Ngày: 2026-09-28. Founder Duy Trần. Repository: `trankhanhduy1508-maker/AI-TRADE`; nhánh duy nhất `codex/p0-covel-knowledge-audit`.

## 1. Quyết định mới (thay thế quy tắc Web App first cùng ngày)

**Tập trung phát triển mã nguồn APK Android trước**: UX/đăng nhập/broker readback/portfolio/tổng lãi lỗ/cơ chế học/update/rollback/kiểm soát khách hàng và demo auto-trade. Web App và Google Sites là **kênh phụ**, không còn là điều kiện buộc phải triển khai trước APK. Giữ tận dụng mã first-party và API độc lập, không tạo hai execution engines khác nhau.

**Không đóng gói, gửi hoặc yêu cầu Founder cài APK debug theo checkpoint.** Sau khi toàn bộ chức năng DEMO auto-trade và an toàn, đăng nhập thật, nâng cấp tại chỗ, rollback, migration, E2E trên Android đạt bằng chứng thì mới phát hành một APK release có kênh cập nhật. Chỉ cho phép build QA nội bộ khi đã qua gate DEMO auto-trade và Founder chấp thuận chuẩn bị release; không coi build thành công là sản phẩm xong.

Không sửa Main/Stable, không dùng PC Founder, AppDeploy, không tạo thêm provider trả phí/khác chỉ để lách quota. Plugin/connector và công cụ cloud trước, mã nguồn độc lập/kiểm thử tại chỗ sau. Không tự đổi nhánh hoặc đổi production.

## 2. Android app: tính tự chủ có giới hạn thật

APK là giao diện chính, local cache và kho nghiên cứu được phép; khách hàng chủ động cài, cập nhật và chọn hành động. APK không nhúng token DB service role hoặc mật khẩu MT5. Android/MT5 Mobile không chạy EA MQL5 như MT5 desktop; không xây hệ thống rủi ro phụ thuộc vào điện thoại phải mở màn hình hoặc chạy nền liên tục. Nhiệm vụ thực thi được cấp quyền chạy ở broker/MT5 compatible runtime độc lập, theo trạng thái server-authoritative. Mất kết nối: ngừng cấp tín hiệu/lệnh mới theo gate; lệnh tồn tại được broker quản lý theo điều kiện đã cấu hình; reconcilation khi nối lại. Nếu có standalone/local engine trong tương lai, kiểm tra API broker và Android background limitations riêng trước khi công bố.

**Live-money LOCKED** cho đến phê duyệt riêng, không mở qua đăng nhập, bản cập nhật hay tải sách.

## 3. Auto-update & rollback cho người dùng, giữ dữ liệu và quyền an toàn

- `applicationId=vn.cws.aitrade` không đổi; `versionCode` tăng nghiêm ngặt, khóa ký release ổn định do Founder quản lý ngoài repo; không dùng khóa debug mới mỗi CI. Mọi payload cập nhật có HTTPS chính thức, integrity SHA-256 và xác thực phát hành/chữ ký. Play build có thể dùng In-App Updates; bản ngoài Play dùng Android PackageInstaller và consent/permissions hợp lệ, không tự cài lén. Rollout theo nhóm, kiểm báo lỗi rồi mới mở rộng, bảo toàn dữ liệu bằng migration + backup/restore.
- **Rollback chiến lược/model**: giữ champion hiện hành và ít nhất một phiên bản đã được phê duyệt trước đó với artifact, SHA, schema, config, quyền dữ liệu và audit riêng. Khi phát hiện regression/drift/rủi ro: chặn lệnh mới, chờ phiên broker xác nhận, quay về cấu hình/model được ký đã duyệt hoặc chế độ `ABSTAIN`; tuyệt đối không bật lại model `REJECTED`. Rollback không tự đóng lệnh đang mở nếu chưa qua chính sách quản lý rủi ro/consent.
- **Rollback giao diện/cấu hình**: dùng các versioned first-party bundles đã kiểm integrity và tương thích dữ liệu; cho người dùng chọn bản ổn định khi bundle có lỗi, không tải/chạy mã không xác thực từ server. Mọi thay đổi schema có migration/compatibility gate.
- **Rollback APK native**: Android thông thường không chấp nhận giảm `versionCode` tại chỗ. Muốn phục hồi mã phiên bản cũ, **phát hành một bản sửa/recovery có `versionCode` MỚI cao hơn**, cùng applicationId/chứng chỉ, nhưng phục hồi mã/chức năng đã duyệt. Không hứa nút “cài APK cũ một chạm” nếu cần uninstall làm mất dữ liệu. Khách hàng có thể chọn phiên bản giao diện/chiến lược đã hỗ trợ bên trong app, không có đặc quyền vượt quyền hệ điều hành.
- Cập nhật native, UI, knowledge, model và chiến lược là **năm loại version riêng**. Update UI/app tuyệt đối không tự đổi model hoặc bật trading permission. Release metadata ký số/audit, kênh stable + recovery, test upgrade/rollback/migration trên Android thực.

## 4. Tự động “cày” kiến thức và backtest

Nạp và index sách/nghiên cứu được phép, Masterbook, nguồn giá và báo cáo đã đối chiếu; giữ tách biệt **retrieval văn bản / numerical dataset / backtest evidence / candidate weights / approved model**. Mỗi nguồn: owner, giấy phép ML/inference/trade/redistribute, source id, SHA, ngày và coverage thực, thị trường, timezone, giá/spread/cost, regime, bản học.

Nguồn mới → quarantine → kiểm license/provenance/quality/dedup/leakage → tạo knowledge/dataset version → train candidate **ngoài runtime chính** → IS/OOS khóa trước, walk-forward, realistic spread/slippage/commission/swap, stress, paper forward → kiểm lỗi/so sánh champion → đưa vào registry. Mọi nguồn chưa đủ quyền và model REJECTED **không bao giờ tự promote**; chỉ được promote theo phê duyệt và evidence gate có sẵn. Không tự đổi rủi ro, code, quyền broker hoặc chiến lược production. Có lựa chọn batch chạy khi có compute được phê duyệt/quota, tiết kiệm pin/mạng của khách; nhật ký mỗi lần “cày” hiển thị `đang quét`/`quarantined`/`candidate`/`rejected`/`approved`.

**Không gọi 90–100 năm đã được train/test chỉ vì có tệp lịch sử**. Báo cáo hiện đã xác minh `reports/MULTIASSET_10Y_BACKTEST_2026-09-27.md` là 14 market khoảng 10 năm, và một số cost mới proxy/gross. Kiểm kê source dài hơn và license độc lập trước khi công bố hoặc train. Kho tri thức cá nhân giữ quyền riêng, không chia sẻ qua app khách hay dùng data khách để train toàn cục nếu thiếu consent/quyền.

## 5. Quyền khách hàng và chart: ĐỀ XUẤT THIẾT KẾ, CHƯA THAY EXECUTION

Đề xuất UX mặc định `AUTO_DISCIPLINED`: EA quyết định điểm vào/ra theo **model đã duyệt và risk gate**, giao diện gọn, không ép khách nhìn biểu đồ liên tục. Khách hàng nên luôn có thể `PAUSE_NEW_ORDERS` và thoát khỏi chế độ auto; nút khẩn cấp luôn hiện. **Đề xuất** cho khách đóng lệnh thủ công theo account permission, với xác nhận rõ cho thao tác thường (không trì hoãn emergency), server audit và freeze auto-reentry của symbol/position cho đến resume/reevaluation. Lệnh broker MT5 mở/đóng bên ngoài APK phải được reconcile và xử lý không tự đảo lại hành động của chủ tài khoản.

Đây là **phương án đang xin quyết định sản phẩm**, không cho phép sửa order execution/risk/kill-switch cho đến khi Founder chốt quy tắc can thiệp chi tiết. Không thể tước quyền khách tự đóng lệnh trực tiếp tại broker.

TradingView **tùy chọn trong tab Biểu đồ nâng cao, view-only**; không đặt BUY/SELL thuận tay trên màn hình mặc định. Dữ liệu third-party widget không tự thành dữ liệu được phép train hoặc phát lệnh. Hiển thị chart kỹ thuật khi cần, không bắt khách dùng TradingView, không nhân đôi nền tảng sẵn có.

## 6. Release gates bắt buộc, giữ trạng thái thực

Android UX/device offline có bằng chứng, Google Founder login thật, MT5 DEMO broker readback thật, dữ liệu có quyền và model được duyệt với OOS/WF/cost/forward, risk/kill-switch/The5ers, demo auto-trade có e2e/rollback/reconciliation, đường thoát cho khách đã kiểm, release signing có chủ sở hữu, update in-place + recovery rollout giữ dữ liệu, và Founder sign-off; sau đó mới build/phát hành. `scripts/check_android_release_gate.py` chỉ xác minh cấu trúc evidence, **không thay test runtime**.

Hiện tại: model `REJECTED`, `demo_send_enabled=false`, `risk_profile_approved=false`, The5ers `BLOCKED_APPROVAL`, live-money `LOCKED`. Không được gọi demo auto-trade hay auto-learning production PASS trước bằng chứng. Web hosting bị BLOCKED không chặn viết/test mã Android, nhưng MT5/risk/QA blocking vẫn giữ nguyên.
