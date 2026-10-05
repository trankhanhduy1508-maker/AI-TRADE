# CWS AutoTrade — Web + MT5 checkpoint 2026-10-05

## Hướng đã thực hiện
Founder giao quyền chọn phương án chi phí thấp và nhấn mạnh Login / Password / Server MT5 là yêu cầu chính. Dùng Web/PWA + backend hiện có; không mua VPS, không thêm API AI vào runtime, không xây lại TF-013A.

Web riêng tư đã xuất bản:
https://cws-autotrade-lab.trankhanhduy1508.chatgpt.site
Trang MT5: /mt5-login.html
Cửa Google Founder cũ vẫn là đường tới dashboard nội bộ. Form mới xác minh bằng credential MT5, chưa mở order route.

## Evidence thật
- 7 cron hiện active; lượt cron gần nhất 2026-10-05 đều succeeded. Đây chỉ là scheduler evidence.
- Arena 2026-10-05 03:35 UTC: 14 open, 2 closed; PAPER_ONLY.
- Forward evaluation: COLLECTING, 0 closed trades. Không đủ evidence promote.
- Investor broker readback thật của DEMO đã liên kết: HTTP 200, DEMO_VERIFIED, mode DEMO, server MetaQuotes-Demo, readOnly=true, readbackSource=MT5_INVESTOR_BROKER, brokerOrders=false, liveMoneyLocked=true. Không expose login/password/balance trong báo cáo.
- Session endpoint v9 ACTIVE: OPTIONS 204, brokers 200; origin mới chính xác được phép CORS. Empty connect 400; account không có session 401. Chưa có Founder nhập mật khẩu trên web mới; không claim credential-login E2E PASS.
- Brokers runtime: provider_ready=false, demo_autotrade_ready=false; blockers RUNTIME_DISABLED, DEMO_SEND_DISABLED, RISK_NOT_APPROVED, PROVIDER_NOT_READY.
- runtime_config: enabled=false, demo_send_enabled=false, risk_profile_approved=false, max_total_volume_demo=NULL.
- Phiên web giữ token trong bộ nhớ, remember=false, xóa password input ngay sau submit và clear payload sau request; không lưu mật khẩu trong browser storage.
- Account endpoint hiện trả snapshot lúc đăng nhập, chưa phải equity/P&L theo tick. UI ghi rõ.
- Chỉ MetaQuotes-Demo được hỗ trợ; không tuyên bố hỗ trợ mọi broker.

## Lỗi dữ liệu phát hiện và bản sửa
State forward lưu position dạng JSON string. Runtime v1 đọc chuỗi như object, biến direction thành undefined và giá thành NaN/null. 7 state hỏng; 7 state có đủ giá trị nhưng vẫn dạng string.
- Parser chấp nhận object/legacy JSON string hợp lệ, chặn thiếu direction/stop/risk hoặc riskPrice không khớp initialStop.
- Ghi position/result/details mới dùng sql.json thay JSON.stringify interpolation.
- Invalid state bị chặn trước advance checkpoint; run trả STATE_INTEGRITY_BLOCKED/409, không giả PASS.
- Forward v2 ACTIVE; deployed index.ts đã so với local source: parity TRUE.
- Chưa phục hồi 7 state đã mất dữ liệu. Không xóa hoặc bịa vị thế; cần replay từ journal/entry/exit evidence.
- Không thay TF-013A, risk limits, cron schedule hoặc mở broker send.

## Kiểm tra
28/28 test chọn đúng phạm vi PASS; Node syntax checks hai Edge function PASS; portable static PWA build PASS; Sites deployment succeeded.
Hai source-contract test cũ trong bộ web tổng vẫn FAIL trước bản sửa: assert samePassword không còn đúng với backend hiện tại, frozen Edge asset style lệch canonical style. Không gọi toàn repo PASS; không sửa assertions để che lỗi.
Node mới nhận diện .ts dùng syntax strip; đây không phải Deno full typecheck.
Web mới chưa có password-login thực trên tài khoản Founder và chưa có broker order/fill.

## Việc còn lại theo ưu tiên
1. Người sở hữu nhập credential DEMO vào web; không gửi mật khẩu qua chat.
2. Khắc phục data integrity từ evidence gốc, rồi kiểm tra forward evaluator/journal cũng đọc JSON đúng.
3. Chốt giới hạn rủi ro và volume DEMO bằng xác nhận Founder; không tự điền số.
4. Hoàn thiện bridge đặt lệnh thực: existing route vẫn phụ thuộc provider chưa ready. Không mua dịch vụ/claim cloud execution free nếu chưa có runtime.
5. Dedupe, visible stop, risk gate, kill switch, account-authoritative DEMO + trade-permission gate.
6. Gửi lệnh DEMO khi đủ gate; broker ticket + position readback + restart/reconcile mới là PASS.
7. Chạy nghiên cứu ứng viên, ngoài mẫu/walk-forward; promotion giữ server-authoritative. Live/funded money vẫn HARD LOCKED.

## Chi phí
Không mua hoặc nâng cấp gói trong phiên. Tái sử dụng Supabase và hosting web hiện có. Không cam kết 0 đồng/24h vĩnh viễn; quota/free plan và bridge đặt lệnh phải đánh giá riêng. Supabase Free hiện có 500 MB DB, 5 GB egress; không coi serverless là terminal MT5 chạy liên tục.

