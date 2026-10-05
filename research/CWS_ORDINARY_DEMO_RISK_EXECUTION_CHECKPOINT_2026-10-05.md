# CWS AutoTrade — chính sách DEMO và kiểm tra execution, 2026-10-05

## Quyền Founder

Lúc 17:10 Asia/Saigon, Founder yêu cầu tự chọn các giới hạn rủi ro và tự giao dịch tài khoản DEMO đã cung cấp. Đây là quyền thiết lập policy cố định cho DEMO thường; không mở tài khoản thật/quỹ. Không tiếp tục yêu cầu Founder chốt lại cùng các số.

## Đã thực hiện

- Lưu policy máy đọc và policy account-bound riêng server-side: risk/lệnh 0,25%, gross portfolio 1%, lỗ ngày 1%, drawdown 5% từ đỉnh equity, 5 lệnh thua liên tiếp, tối đa một vị thế/tổng 0,01 lot, ban đầu EURUSD. Chỉ TF-013A hợp lệ; không ép tín hiệu để tạo lệnh hiển thị.
- Các số là IMPLEMENTATION_DERIVATION, cấu hình thử nghiệm bảo thủ; không gán cho một cuốn sách hoặc gọi là tối ưu. Nguồn tham khảo nguyên tắc position sizing: CME The 2% Rule và Proper Position Size.
- Mở rộng IndependentRiskEngine hiện có để chặn gross portfolio stop risk gồm lệnh mới, drawdown và loss streak. Thiếu hoặc không hữu hạn các state cần thiết thì chặn.
- Sửa MetaApi runtime helper: quote mới không còn mặc nhiên chứng minh risk approval/state known/reconciliation.
- Session service v12 ACTIVE đọc policy từ bảng ai_trade.ordinary_demo_policies sau xác thực, không nhận approval từ client. Bảng RLS bật, anon/authenticated/public không có quyền; policy không chứa mật khẩu. Advisor INFO rls_enabled_no_policy là deny-by-default có chủ ý cho bảng nội bộ này: https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy .

## Evidence

- Login tài khoản DEMO: CONNECTED/TRADING_ALLOWED. Broker trả balance 9.886,73 USD. Equity trong session là cache bằng balance, KHÔNG chứng minh equity hiện tại hoặc không có vị thế. Không giả định các khoản lỗ trước đó thuộc bot.
- 809 Python tests PASS, 1 SKIP do kiểm thử cần JDK; 45 Node tests PASS. Test mới có chu kỳ RED -> GREEN.
- Kiểm tra authenticated preflight sau deploy v12: trả đúng policy 0,0025/0,01/0,01/0,05/5; blocker RISK_NOT_APPROVED đã được giải quyết cho tài khoản này. Vẫn PREFLIGHT_BLOCKED do provider/broker/control/reconciliation/strategy/execution chưa đủ; order_send_enabled=false, orders_sent=0. Đã disconnect sạch.
- Không lệnh nào được gửi bởi agent ở vòng này. Không có broker fill, ticket hoặc lifecycle PASS.
- Cloud hiện tại Linux, không terminal64.exe, không Wine. API public brokers báo provider chưa sẵn sàng; METAAPI token/account chưa được cấu hình. Tick cũ gắn The5ers/TF004 không được bật hoặc sửa approval giả để vượt gate.
- Thử UI web terminal chính thức từ link MetaQuotes: https://web.metatrader.app/terminal chuyển tới /terminal/unsupported.html, hiển thị Browser unsupported. Không đăng nhập qua UI, không đổi fingerprint để vượt hạn chế.

## Chưa đạt goal

User mở MT5 thấy giao dịch: CHƯA ĐẠT. Cần terminal/gateway thực thi MT5 đang hoạt động trên cloud. Policy và unit tests không tự tạo ra kết nối broker hay bot chạy 24/7. Adapter phải nối TF-013A, đọc fresh equity/positions/contract/cost, lưu peak/day baseline/loss streak, tính lỗ nổi + phí, reconcile trước submit và stop/trailing/restart, có kill switch bền vững; lệnh tối thiểu vượt budget phải bỏ. Current session preflight vẫn fail-closed vì các proof này chưa có. Không phát sinh dịch vụ trả phí hoặc dùng PC cá nhân.
