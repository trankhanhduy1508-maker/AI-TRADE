# Volume — Nghiên cứu và giới hạn sử dụng

## Vai trò trong hệ thống này

Volume (khối lượng giao dịch) dùng để **xác nhận độ tin cậy** của một breakout
hoặc một phản ứng giá — không dùng để tự sinh tín hiệu vào lệnh.

## Nguyên tắc quan sát

- **Breakout kèm volume tăng rõ rệt** so với trung bình gần đây → độ tin cậy cao
  hơn rằng breakout là thật, có lực tham gia thực sự, không chỉ là biến động
  nhiễu.
- **Breakout với volume thấp/không tăng** → cảnh báo khả năng false break cao hơn
  (xem `PRICE_ACTION_AND_MARKET_STRUCTURE.md`) — cần thận trọng hơn, có thể chờ
  thêm xác nhận thay vì vào lệnh ngay.
- **Volume giảm dần trong một xu hướng đang diễn ra** → có thể là dấu hiệu xu
  hướng đang yếu dần, kết hợp với cấu trúc giá (chuỗi HH/HL hoặc LH/LL có đang bị
  phá không) để đánh giá, không kết luận một mình.
- **Volume tăng đột biến bất thường không đi kèm biến động giá tương xứng** — có
  thể là dấu hiệu tích lũy/phân phối (accumulation/distribution), cần quan sát
  thêm trong các nến tiếp theo, không phải tín hiệu tức thời.

## Giới hạn thực tế cần lưu ý khi backtest/triển khai

- Dữ liệu volume ở thị trường **phi tập trung** (ví dụ nhiều sàn crypto giao dịch
  cùng 1 cặp) chỉ phản ánh volume trên **sàn/nguồn dữ liệu cụ thể**, không phải
  tổng volume toàn thị trường — cần ghi rõ nguồn dữ liệu khi backtest
  (`backtests/BACKTEST_STANDARD.md`).
- "Trung bình gần đây" để so sánh volume cần định nghĩa cụ thể (bao nhiêu nến,
  tính trung bình kiểu gì) trong từng chiến lược ở `strategies/` — không có một
  con số chung áp dụng cho mọi timeframe.

## Câu hỏi cần kiểm chứng (giả thuyết, chưa có kết luận)

Ghi vào `research/HYPOTHESES.md`:

- Ngưỡng "volume tăng rõ rệt" nên định nghĩa thế nào (ví dụ: bao nhiêu % so với
  trung bình N nến) để thực sự lọc được false break mà không loại bỏ quá nhiều
  breakout thật?
- Volume có vai trò xác nhận ổn định như nhau giữa các thị trường (forex, chứng
  khoán, crypto) hay khác biệt đáng kể do cấu trúc thị trường khác nhau?

## Giới hạn

Volume trong tài liệu này là **hướng dẫn định tính**, chưa phải ngưỡng số cụ thể
đã kiểm chứng — ngưỡng cụ thể (nếu có) chỉ được đưa vào `strategies/*.md` sau khi
có kết quả backtest thật trong `backtests/`.
