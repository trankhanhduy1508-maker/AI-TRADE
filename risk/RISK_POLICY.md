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


## Chính sách DEMO thường — 2026-10-05

Founder đã trực tiếp giao quyền chọn và thiết lập giới hạn thử nghiệm DEMO lúc 17:10 (Asia/Saigon). Phần này thay trạng thái chưa chốt số **chỉ cho MetaQuotes-Demo thường**; tài khoản tiền thật/quỹ vẫn chưa được mở quyền.

- Rủi ro theo stop mỗi lệnh: tối đa **0,25% equity broker đã xác minh**.
- Tổng rủi ro theo stop đang mở cộng lệnh mới: tối đa **1% equity**; cộng gross risk, không bù trừ các hướng đối nghịch.
- Lỗ ngày: dừng thêm rủi ro tại **1% equity**, tính chi phí và lỗ nổi; khi bổ sung runtime phải dùng mốc đầu ngày đã lưu và dữ liệu đối soát, không dùng balance cache.
- Drawdown: dừng tại **5% từ đỉnh equity đã lưu bền vững**; không đặt lại đỉnh khi restart.
- Chuỗi thua: dừng tại **5 lệnh đóng thua liên tiếp**; không tự mở lại.
- Giai đoạn đầu: tối đa **1 vị thế, tổng 0,01 lot**, EURUSD; không pyramiding/martingale/nới stop. Nếu lot tối thiểu vượt ngân sách thì bỏ lệnh.
- Stop broker bắt buộc; trailing được phép theo rule có sẵn, không yêu cầu TP/RR cố định.
- Không ép giao dịch khi engine TF-013A chưa có tín hiệu hợp lệ.

Nguồn các con số: **IMPLEMENTATION_DERIVATION**, cấu hình thử nghiệm bảo thủ được chọn theo quyền Founder giao; không phải mức tối ưu đã chứng minh bằng sách/backtest. CME mô tả quy tắc 2% là ngưỡng lựa chọn tùy ý, không phải bảo đảm: https://www.cmegroup.com/education/courses/trade-and-risk-management/the-2-percent-rule . Lot không thay thế cách tính risk theo stop.

Cấu hình máy đọc: `risk/ORDINARY_MT5_DEMO_POLICY.json`. Bản được áp dụng cho tài khoản nằm trong bảng riêng server-side `ai_trade.ordinary_demo_policies`; không có mật khẩu trong repo. Policy được lưu không đồng nghĩa engine đã gửi lệnh hoặc runtime đã áp dụng đủ các kiểm soát. Execution chỉ được bật sau khi adapter thực thi đầy đủ các giới hạn và đối soát broker.
