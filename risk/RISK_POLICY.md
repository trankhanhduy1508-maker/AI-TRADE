# Risk Policy — Luật cứng, không do LLM tự quyết định

> Mọi con số trong file này là **luật cứng**. LLM/AI hỗ trợ trong hệ thống này
> KHÔNG được tự đề xuất thay đổi các ngưỡng dưới đây khi phân tích 1 lệnh cụ thể —
> thay đổi ngưỡng chỉ được thực hiện qua việc sửa trực tiếp file này, có ý thức,
> không phải "linh hoạt" theo từng tình huống.

## Nguyên tắc tối thượng

**Quản lý rủi ro quan trọng hơn tỷ lệ thắng.** Một hệ thống thắng 40% với rủi ro
kiểm soát chặt có giá trị hơn một hệ thống thắng 70% không có giới hạn rõ ràng.
Toàn bộ file này tồn tại để đảm bảo nguyên tắc này được thực thi bằng luật, không
phải bằng ý chí tại thời điểm giao dịch.

## Giới hạn rủi ro mỗi lệnh

- Rủi ro tối đa mỗi lệnh: **giá trị cụ thể chưa chốt số** — cần Project Owner xác
  nhận % vốn cụ thể (ví dụ 1% hay 2%) trước khi hệ thống được phép tính toán
  khối lượng lệnh thật. Cho tới khi chốt, **không có lệnh nào được coi là hợp lệ
  về mặt rủi ro**.
- Rủi ro mỗi lệnh được tính từ khoảng cách entry → stop loss (xem
  `risk/POSITION_SIZING.md`), không phải ước lượng cảm tính.
- Không được vào lệnh nếu không thể xác định trước một mức stop loss cụ thể.

## Giới hạn rủi ro danh mục (tổng rủi ro đang mở)

- Tổng rủi ro của tất cả lệnh đang mở cùng lúc không được vượt quá một ngưỡng cố
  định — **giá trị cụ thể chưa chốt số**, cần xác nhận cùng lúc với ngưỡng rủi
  ro/lệnh ở trên.
- Các lệnh có tương quan cao (cùng hướng trên các thị trường liên quan) phải được
  tính gộp khi đánh giá tổng rủi ro, không tính riêng lẻ như thể độc lập hoàn
  toàn (xem `knowledge/MARKET_WIZARDS_LESSONS.md` mục 4).

## Giới hạn thua lỗ liên tiếp / Drawdown

- Khi xảy ra một chuỗi thua lỗ liên tiếp (số lệnh cụ thể: **chưa chốt số**) hoặc
  drawdown vượt một ngưỡng % vốn (**chưa chốt số**): **bắt buộc tạm dừng giao
  dịch** theo chiến lược đang gây thua lỗ đó, đánh giá lại trước khi tiếp tục.
- Việc "đánh giá lại" nghĩa là xem lại `research/EXPERIMENT_LOG.md` và
  `research/FAILURE_CASES.md`, không phải chỉ chờ hết cảm giác rồi tiếp tục như
  cũ.
- Chi tiết cơ chế dừng khẩn cấp: `risk/KILL_SWITCH_RULES.md`.

## Vai trò của AI/LLM đối với rủi ro

- LLM có thể: tính toán khối lượng lệnh dựa trên công thức đã chốt trong
  `risk/POSITION_SIZING.md`, cảnh báo khi một đề xuất vi phạm giới hạn ở trên,
  tổng hợp lịch sử rủi ro đã dùng.
- LLM **không được**: tự đề xuất "lần này rủi ro cao hơn một chút cũng được vì
  setup đẹp", tự nới lỏng giới hạn thua lỗ liên tiếp, hoặc tự quyết định bỏ qua
  kill switch.

## Trạng thái hiện tại

Các ngưỡng số cụ thể (% rủi ro/lệnh, % rủi ro danh mục, số lệnh thua liên tiếp,
% drawdown tối đa) **chưa được Project Owner chốt** — đây là việc bắt buộc phải
làm trước khi có bất kỳ hoạt động backtest nào mô phỏng quản lý vốn thật (backtest
tín hiệu thuần túy, không tính PnL theo vốn, vẫn có thể thực hiện trước khi chốt
số — xem `backtests/BACKTEST_STANDARD.md`).
