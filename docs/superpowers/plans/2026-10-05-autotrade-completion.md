# Kế hoạch hoàn thiện kiểm chứng AutoTrade

Goal: tiến tới bot DEMO độc lập, giữ TF-013A và không dùng LLM chọn BUY/SELL.

Spec: auto_trade/MASTER_GOAL.md; R3 prereg 2026-09-29; risk/RISK_POLICY.md.

Thực hiện trực tiếp theo yêu cầu Founder, không tạo agent phụ.

## Ràng buộc
- Không mở live/funded, không tự đặt giới hạn risk chưa chốt.
- Không tạo provider trả phí hoặc dùng PC Founder.
- Dữ liệu đã mở luôn HISTORICAL_REUSED; kết quả synthetic không là lợi nhuận thực.

## Công việc
- [ ] Kiểm tra các module execution và chạy regression hiện có.
- [ ] Chặn dữ liệu nến/tick sai trước khi sinh tín hiệu; viết regression lỗi trước khi sửa.
- [ ] Triển khai R3 offline giữ vị thế xuyên fold, chọn ứng viên chỉ từ quá khứ; không sửa runtime strategy.
- [ ] Kiểm thử carry, stop gap, phí và bất biến khi thay tương lai.
- [ ] Kiểm tra provider/risk readiness; không gọi login thành order-fill.
- [ ] Lưu evidence/test/code vào nhánh duy nhất và ghi rõ blocker còn lại.

## Review focus
Nến chưa đóng/giá NaN, mất kết nối và restart, lệnh trùng sau timeout, trailing không nới stop, vị thế tồn tại xuyên lần chọn lại model. Không gán snapshot balance thành equity/P&L trực tiếp.
