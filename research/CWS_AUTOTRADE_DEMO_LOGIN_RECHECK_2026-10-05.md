# CWS AutoTrade — kiểm tra tài khoản DEMO được Founder cung cấp, 2026-10-05

## Kết quả thực
- Founder cho phép dùng tài khoản DEMO trong ảnh để kiểm tra kết nối; không lưu ảnh/mật khẩu/login vào source hoặc báo cáo này.
- POST mt5/session/connect qua API với Origin web app hiện hành: HTTP 200 CONNECTED, DEMO, auto_trade OFF, order_send_enabled false, orders_sent 0. Đăng nhập thành công ở ba lần kiểm tra.
- GET mt5/session/account có Bearer: HTTP 200 CONNECTED, DEMO, TRADING_ALLOWED, orders_sent 0. Đây là snapshot phiên đăng nhập, không phải fresh broker positions/equity.
- POST mt5/session/disconnect: HTTP 200 DISCONNECTED ở kiểm tra thứ hai. Kiểm tra thứ ba gửi disconnect sau đọc account.
- Chưa chạy UI end-to-end trên Android; chưa tái hiện được lỗi lần trước của Founder; không khẳng định đã sửa nguyên nhân. Không thay đổi code đăng nhập để giả thành công.
- Một bước diagnostic gọi nhầm /mt5/account thay vì /mt5/session/account trả 404; sửa đường gọi diagnostic, không phải lỗi của web client.
- Không gửi lệnh broker hoặc bật execution/risk flags. Không lưu session token ra tệp.

## Backtest: tiếp tục từ bằng chứng hiện có
Đã đọc lại research/CWS_AUTOTRADE_R2B_MULTI_MARKET_COST_LEARNINGS_CHECKPOINT_2026-09-29.md và prereg R3. Không nghiên cứu lại từ đầu. R2b đã có 15 D1 + 11 H4 = 26 series, 738 fold, 1434 lệnh mô phỏng đóng; không phải 26 thị trường độc lập hay toàn bộ thị trường thế giới. 10bps MODELED: D1 7/15 series dương, H4 0/11; phí này không được coi là fee venue thực. Dữ liệu đã mở là HISTORICAL_REUSED, EDGE_UNPROVEN, không được đổi nhãn OOS mới.

R2 reset vị thế ở ranh giới fold; cần triển khai và kiểm tra carry liên tục + nested fit/validation theo prereg R3 trước nghiên cứu mới. Không chọn riêng series có lời sau khi đã thấy kết quả. Giữ bản hiện hành và tất cả kết quả âm. Dữ liệu mới cần source/clock/quyền dùng/vintage/cost được kiểm toán và khóa manifest trước khi xem hiệu suất. Phiên này chưa chạy backtest mới tất cả thị trường, chưa triển khai R3, chưa huấn luyện mô hình ML, chưa bật lịch mới.

## Verification
20 unittest phần R2/knowledge pipeline PASS tại workspace; synthetic verification không chứng minh lợi nhuận thị trường hoặc broker execution. Không chạy full repo regression. Tiếp tục ưu tiên dữ liệu broker mới và bridge execution/risk đã kiểm chứng trước DEMO autonomous.
