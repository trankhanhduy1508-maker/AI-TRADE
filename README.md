# AI-TRADE

Hệ thống nghiên cứu giao dịch có hỗ trợ AI, theo trường phái **Reaction — không dự đoán cảm tính**.

## Triết lý cốt lõi

- **Reaction, không dự đoán.** Chỉ hành động khi giá đã thực sự phản ứng theo đúng
  kịch bản đã định nghĩa trước — không đoán trước đỉnh/đáy, không "cảm thấy" thị trường sẽ đi đâu.
- **Trend Following.** Đi theo xu hướng đã được xác nhận bằng cấu trúc thị trường,
  không cố bắt đáy/đỉnh, không đánh ngược xu hướng chính.
- **Price Action và cấu trúc thị trường là chính.** Đỉnh/đáy, breakout, pullback,
  trendline là dữ liệu quyết định.
- **Volume, EMA, RSI chỉ để xác nhận** — không bao giờ là điều kiện đủ để vào lệnh một mình.
- **Quản lý rủi ro quan trọng hơn tỷ lệ thắng.** Một chiến lược thắng 40% nhưng
  kiểm soát rủi ro tốt có giá trị hơn một chiến lược thắng 70% nhưng không có giới hạn lỗ rõ ràng.

## Giới hạn hiện tại (bắt buộc đọc trước khi đóng góp)

- ❌ **Chưa kết nối tài khoản giao dịch thật.**
- ❌ **Chưa có bot đặt lệnh thật.**
- ❌ **Chưa tự ý huấn luyện model.**
- ✅ Đây là giai đoạn **xây dựng nền tảng tài liệu, giả thuyết và quy tắc** — chưa
  phải giai đoạn vận hành.

Xem chi tiết đầy đủ tại [`PROJECT_CONTEXT.md`](./PROJECT_CONTEXT.md).

## Cấu trúc repository

| Thư mục/File | Nội dung |
|---|---|
| `AGENTS.md` | Quy tắc vận hành cho AI Agent làm việc trên repo này |
| `PROJECT_CONTEXT.md` | Bối cảnh, mục tiêu, giới hạn cứng của dự án |
| `CURRENT_STATUS.md` | Tiến độ hiện tại |
| `DECISIONS.md` | Các quyết định đã chốt, không tranh luận lại |
| `knowledge/` | Kiến thức nền: trend following, price action, volume, RSI |
| `strategies/` | Chiến lược giao dịch cụ thể, theo template chuẩn |
| `risk/` | Chính sách rủi ro, cách tính khối lượng lệnh, kill switch |
| `research/` | Giả thuyết, nhật ký thử nghiệm, các ca thất bại |
| `backtests/` | Chuẩn backtest và template báo cáo kết quả |
| `prompts/` | Prompt chuẩn cho các vai trò AI (phân tích/phản biện/hậu kiểm) |
| `src/` | Mã nguồn (hiện chưa có code thật — xem `CURRENT_STATUS.md`) |

## Nguyên tắc viết tài liệu trong repo này

- Toàn bộ tài liệu viết bằng tiếng Việt, rõ ràng, thực dụng — không quảng cáo.
- Không chép nguyên văn sách/khóa học có bản quyền — chỉ tổng hợp ý tưởng bằng ngôn ngữ riêng.
- Không khẳng định bất kỳ chiến lược nào chắc chắn sinh lời.
- Luôn phân biệt rõ 4 tầng: **giả thuyết → quy tắc → điều kiện kiểm chứng → kết quả backtest**.
