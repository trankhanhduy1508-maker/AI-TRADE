# TF_002_TRENDLINE_REACTION

## Trạng thái

- [x] Giả thuyết (chưa backtest)
- [ ] Đang backtest
- [ ] Đã backtest, đang đánh giá
- [ ] Đã xác nhận trên thị trường/timeframe cụ thể

## 1. Giả thuyết

Một trendline đã được thị trường "tôn trọng" qua nhiều lần chạm (không chỉ vẽ
qua 2 điểm) đại diện cho một vùng cung/cầu động đang được thị trường công nhận.
Phản ứng giá tại trendline đó (không phải bản thân việc chạm) là tín hiệu có kỳ
vọng dương để vào lệnh theo hướng xu hướng chính, dựa trên
`knowledge/PRICE_ACTION_AND_MARKET_STRUCTURE.md` (mục Trendline). **Chưa được
backtest.**

## 2. Thị trường và khung thời gian áp dụng

Chưa xác định — không giả định hiệu quả giống nhau ở mọi thị trường/timeframe
(theo `DECISIONS.md`).

## 3. Tiêu chuẩn trendline hợp lệ

- Vẽ qua tối thiểu 2 swing high (trendline giảm) hoặc 2 swing low (trendline
  tăng) đã hình thành rõ ràng (xem `knowledge/PRICE_ACTION_AND_MARKET_STRUCTURE.md`).
- Trendline chỉ được coi là "hợp lệ để giao dịch" sau khi có **điểm chạm thứ 3**
  trở đi mà giá phản ứng đúng hướng trendline — 2 điểm đầu chỉ đủ để vẽ, không đủ
  để giao dịch.
- Không được vẽ lại/điều chỉnh trendline sau khi đã biết kết quả giá đi tiếp theo
  (nhìn lại quá khứ để "vẽ cho khớp") — đây là ép trendline, bị cấm rõ trong
  `knowledge/PRICE_ACTION_AND_MARKET_STRUCTURE.md`.

## 4. Số điểm chạm

- Tối thiểu 3 điểm chạm (2 điểm hình thành đường + 1 điểm xác nhận) trước khi
  trendline được coi là có giá trị giao dịch.
- Từ điểm chạm thứ 4 trở đi, độ tin cậy được coi là tăng thêm, nhưng **không**
  tuyến tính vô hạn — trendline chạm quá nhiều lần trong thời gian ngắn có thể
  đang chuẩn bị bị phá vỡ (giá "cọ sát" nhiều = năng lượng tích lũy để phá vỡ).

## 5. Độ dốc

- Trendline quá dốc (hình thành trong biến động mạnh bất thường, ví dụ sau tin
  tức) dễ bị phá vỡ bởi biến động bình thường tiếp theo → độ tin cậy thấp hơn.
- Trendline quá thoải (gần như đi ngang) không phản ánh xu hướng rõ ràng, dễ
  nhầm với vùng support/resistance ngang thông thường.
- Ngưỡng độ dốc cụ thể "chấp nhận được": chưa xác định bằng số — cần backtest để
  tìm khoảng hợp lý, không đặt tùy ý.

## 6. Cấu trúc thị trường đi kèm bắt buộc

Trendline chỉ được giao dịch khi đi cùng chiều với xu hướng xác định qua cấu
trúc HH/HL hoặc LH/LL (xem `knowledge/TREND_FOLLOWING.md`) — không giao dịch
trendline ngược lại xu hướng chính đã xác định qua cấu trúc giá.

## 7. Phản ứng giá bắt buộc tại trendline

Chỉ chạm trendline **không đủ điều kiện vào lệnh** (nguyên tắc cứng, xem
`DECISIONS.md`). Bắt buộc phải có thêm một trong các phản ứng sau tại điểm chạm:

- Nến đảo chiều rõ ràng (ví dụ: bóng nến dài về phía ngược hướng phá vỡ, thân
  nến đóng cửa quay lại đúng hướng xu hướng).
- Break of Structure nhỏ hơn theo đúng hướng xu hướng ngay sau điểm chạm (xác
  nhận bằng cấu trúc giá khung thời gian nhỏ hơn).

Nếu giá chạm trendline nhưng không có phản ứng nào ở trên trong số nến quy định
(số lượng cụ thể xác định khi backtest): **không vào lệnh**, tiếp tục quan sát.

## 8. Breakout trendline

- Breakout trendline hợp lệ: giá đóng cửa vượt hẳn qua trendline, thân nến breakout
  có tỷ lệ đáng kể, tốt nhất kèm volume tăng (tham chiếu
  `knowledge/VOLUME_RESEARCH.md`) — tương tự điều kiện breakout ở `TF_001_BREAKOUT_PULLBACK.md`.
- Sau breakout trendline hợp lệ, có thể áp dụng logic pullback tương tự
  `TF_001_BREAKOUT_PULLBACK.md` mục 5-6 nếu giá hồi lại kiểm tra trendline vừa
  phá vỡ (trendline lúc này đổi vai trò từ kháng cự/hỗ trợ động).

## 9. False break (phá vỡ giả)

- Giá phá qua trendline nhưng đóng cửa quay lại bên trong trong vòng ít nến quy
  định (số cụ thể xác định khi backtest) → coi là false break, không phải
  breakout hợp lệ.
- False break tại trendline, đặc biệt kèm volume thấp, có thể tự nó là một tín
  hiệu phản ứng ngược hướng đáng cân nhắc (giá bị từ chối tại breakout giả) —
  nhưng đây là **một giả thuyết riêng**, cần ghi vào `research/HYPOTHESES.md` và
  backtest độc lập, không mặc định áp dụng chung với chiến lược này.

## 10. Điều kiện không giao dịch

- Không giao dịch nếu trendline chưa đủ 3 điểm chạm (mục 4).
- Không giao dịch nếu độ dốc trendline bất thường do 1 sự kiện tin tức đơn lẻ
  gây ra (mục 5).
- Không giao dịch trendline ngược chiều xu hướng chính (mục 6).
- Không giao dịch nếu không có phản ứng giá xác nhận tại điểm chạm (mục 7) —
  đây là nguyên tắc cứng, không có ngoại lệ dù "nhìn có vẻ chắc chắn".
- **Không được ép vẽ trendline để hợp thức hóa một setup đã muốn vào lệnh từ
  trước** — nếu phải chỉnh nhiều lần mới ra được đường "đẹp", đó là dấu hiệu
  đang ép, không phải trendline thật.

## 11. Lỗi thường gặp

- Vẽ trendline chủ quan, chỉnh sửa liên tục cho khớp ý muốn (confirmation bias).
- Vào lệnh ngay khi giá chạm trendline, bỏ qua yêu cầu phản ứng xác nhận ở mục 7.
- Nhầm false break thành breakout thật do phản ứng quá nhanh.
- Giao dịch trendline ngược xu hướng chính chỉ vì đường vẽ "đẹp" về mặt hình học.

## 12. Dữ liệu cần để backtest

Tương tự `TF_001_BREAKOUT_PULLBACK.md` mục 11 — cặp/mã, timeframe, khoảng thời
gian, nguồn dữ liệu cụ thể chưa được chọn, sẽ xác định theo
`backtests/BACKTEST_STANDARD.md` khi bắt đầu backtest.

## 13. Kết quả backtest

Chưa có — xem `backtests/RESULTS_TEMPLATE.md`.
