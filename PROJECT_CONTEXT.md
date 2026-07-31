# PROJECT CONTEXT — AI-TRADE

## AI-TRADE là gì

AI-TRADE là **hệ thống nghiên cứu giao dịch** có sự hỗ trợ của AI/LLM, không phải
sản phẩm giao dịch tự động sẵn sàng chạy thật. Mục tiêu giai đoạn hiện tại là xây
dựng **nền tảng tài liệu, giả thuyết, quy tắc và khung kiểm chứng** trước khi bàn
tới việc tự động hóa bất kỳ phần nào.

Trường phái cốt lõi:

- **Reaction, không dự đoán cảm tính** — chỉ hành động khi thị trường đã thực sự
  phản ứng đúng kịch bản đã định nghĩa sẵn, không đoán trước đỉnh/đáy.
- **Trend Following** — đi theo xu hướng đã được cấu trúc thị trường xác nhận.
- **Price Action và cấu trúc thị trường là dữ liệu quyết định chính.**
- **Volume, EMA, RSI chỉ dùng để xác nhận** thêm cho tín hiệu Price Action, không
  bao giờ là điều kiện đủ để tự vào lệnh.
- **Quản lý rủi ro quan trọng hơn tỷ lệ thắng** — một hệ thống kiểm soát lỗ tốt
  với tỷ lệ thắng thấp vẫn có giá trị hơn một hệ thống thắng nhiều nhưng không có
  giới hạn rủi ro rõ ràng.

## Giới hạn cứng của giai đoạn hiện tại

Ba giới hạn dưới đây là **luật cứng**, không được coi là "có thể cân nhắc thêm"
trong bất kỳ prompt hay yêu cầu nào sau này, trừ khi Project Owner xác nhận trực
tiếp và rõ ràng bằng văn bản:

1. **Chưa kết nối tài khoản giao dịch thật** — không API key sàn thật, không tài
   khoản thật ở bất kỳ đâu trong repo.
2. **Chưa viết bot đặt lệnh thật** — code trong `src/` (khi có) chỉ phục vụ
   nghiên cứu/backtest trên dữ liệu lịch sử, không được gửi lệnh ra sàn thật.
3. **Chưa tự ý huấn luyện model** — không tự động fine-tune/huấn luyện bất kỳ mô
   hình máy học nào mà chưa có yêu cầu và xác nhận rõ ràng.

## Nguyên tắc vận hành khi rủi ro thực tế xuất hiện

- Khi xảy ra **thua lỗ liên tiếp** hoặc **drawdown vượt ngưỡng đã định nghĩa**
  (xem `risk/RISK_POLICY.md`), hệ thống — dù là con người hay AI hỗ trợ — **phải
  tạm dừng giao dịch và đánh giá lại** trước khi tiếp tục, không được tự động
  "gồng" tiếp để gỡ lỗ.
- Phải luôn có **kill switch**: một cơ chế dừng khẩn cấp toàn bộ hoạt động giao
  dịch/tín hiệu, có thể kích hoạt thủ công bất kỳ lúc nào, không phụ thuộc vào
  việc AI có "đồng ý" hay không. Chi tiết tại `risk/KILL_SWITCH_RULES.md`.
- **Không có chiến lược nào hiệu quả như nhau ở mọi thị trường và mọi khung thời
  gian.** Mỗi chiến lược trong `strategies/` phải ghi rõ thị trường/timeframe đã
  thử nghiệm, và kết quả backtest ở thị trường/timeframe khác **không được suy
  diễn** là sẽ tương tự — phải kiểm chứng lại riêng.

## AI/LLM không được tự quyết định gì

- LLM có thể **đề xuất phân tích, gợi ý giả thuyết, phản biện chiến lược, tổng
  hợp kết quả backtest** — nhưng **không được tự quyết định mức rủi ro của một
  lệnh** (khối lượng, stop loss %, đòn bẩy...). Mọi con số rủi ro đến từ
  `risk/RISK_POLICY.md`/`risk/POSITION_SIZING.md`, là luật cứng đã chốt trước.
- Vai trò cụ thể của LLM trong hệ thống (phân tích thị trường, phản biện setup,
  hậu kiểm sau lệnh) được chuẩn hoá thành prompt trong `prompts/`.

## Phạm vi hiện tại (KHÔNG PHẢI phạm vi tương lai)

Đang làm: tài liệu nền tảng, giả thuyết, quy tắc chiến lược, khung backtest.
Chưa làm: kết nối dữ liệu thật, code chạy thật, kết nối sàn, huấn luyện model.
Xem tiến độ chi tiết tại `CURRENT_STATUS.md`.
