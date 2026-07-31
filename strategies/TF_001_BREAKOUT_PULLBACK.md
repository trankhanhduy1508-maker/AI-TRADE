# TF_001_BREAKOUT_PULLBACK

## Trạng thái

- [x] Giả thuyết (chưa backtest)
- [ ] Đang backtest
- [ ] Đã backtest, đang đánh giá
- [ ] Đã xác nhận trên thị trường/timeframe cụ thể

## 1. Giả thuyết

Sau khi giá phá vỡ một vùng cấu trúc quan trọng (đỉnh/đáy trước đó) theo hướng xu
hướng chính, một nhịp hồi giá (pullback) về gần vùng vừa phá vỡ — mà không phá
ngược lại sâu vào vùng đó — là điểm vào lệnh có tỷ lệ lời/lỗ tốt hơn vào ngay lúc
breakout, vì rủi ro (khoảng cách tới stop loss) nhỏ hơn trong khi vẫn theo đúng
xu hướng đã xác nhận. Đây là giả thuyết dựa trên `knowledge/TREND_FOLLOWING.md`
và `knowledge/PRICE_ACTION_AND_MARKET_STRUCTURE.md`, **chưa được backtest**.

## 2. Thị trường và khung thời gian áp dụng

Chưa xác định — sẽ chọn 1 thị trường + 1 timeframe cụ thể khi bắt đầu backtest
(xem `CURRENT_STATUS.md` mục Next Task). Không giả định chiến lược này hiệu quả
như nhau ở mọi thị trường/timeframe (theo `DECISIONS.md`).

## 3. Cách xác định xu hướng

- Xác định chuỗi swing high/swing low gần nhất (xem
  `knowledge/PRICE_ACTION_AND_MARKET_STRUCTURE.md`).
- Xu hướng tăng: tối thiểu 2 cặp Higher High + Higher Low liên tiếp đã hình
  thành trước điểm breakout đang xét.
- Xu hướng giảm: tối thiểu 2 cặp Lower High + Lower Low liên tiếp, tương tự.
- EMA dài hạn (tham số cụ thể xác định khi backtest) dùng làm bộ lọc bias phụ:
  chỉ tìm setup breakout tăng khi giá trên EMA, setup breakout giảm khi giá dưới
  EMA — đây là lớp lọc bổ sung, không thay thế điều kiện cấu trúc ở trên.

## 4. Điều kiện breakout hợp lệ

1. Giá **đóng cửa** (không chỉ chạm bằng râu nến) vượt hẳn ra ngoài swing
   high/low gần nhất theo hướng xu hướng đã xác định ở mục 3.
2. Cây nến breakout có thân nến (body) chiếm tỷ lệ đáng kể so với toàn bộ nến
   (không phải nến doji/indecision) — ngưỡng cụ thể xác định khi backtest.
3. Volume tại nến breakout cao hơn rõ rệt so với trung bình gần đây (tham chiếu
   `knowledge/VOLUME_RESEARCH.md`) — đây là điều kiện xác nhận, không thay thế
   điều kiện 1 và 2.

Nếu thiếu bất kỳ điều kiện nào ở trên: **không tính là breakout hợp lệ**, kể cả
nếu giá sau đó tiếp tục đi đúng hướng — vì tại thời điểm ra quyết định, tín hiệu
chưa đủ điều kiện.

## 5. Điều kiện pullback

1. Sau breakout hợp lệ, giá hồi ngược lại **về phía** vùng vừa phá vỡ.
2. Pullback **không được đóng cửa trở lại sâu bên trong** vùng cấu trúc cũ (tức
   là không phá hỏng chính breakout vừa xảy ra) — nếu xảy ra, coi đây là false
   break (xem mục 8), không phải pullback hợp lệ.
3. Pullback nên đi kèm volume **giảm** so với nến breakout — dấu hiệu lực bán/mua
   ngược chiều yếu, phù hợp một nhịp hồi kỹ thuật thay vì đảo chiều thật.

## 6. Xác nhận vào lệnh

Chỉ vào lệnh khi, sau khi pullback đã xảy ra theo mục 5, xuất hiện thêm **một
nến phản ứng xác nhận** theo đúng hướng breakout ban đầu (ví dụ: nến đảo chiều
tăng tại vùng pullback trong setup breakout tăng) — không vào lệnh ngay khi giá
vừa chạm tới vùng pullback mà chưa có phản ứng xác nhận.

## 7. Stop Loss

Đặt dưới (setup tăng) / trên (setup giảm) điểm thấp nhất/cao nhất của chính nhịp
pullback, cộng thêm biên an toàn nhỏ (tham số cụ thể xác định khi backtest, ví
dụ theo ATR). Khối lượng lệnh tính từ khoảng cách này theo
`risk/POSITION_SIZING.md` — không tự ý đặt % rủi ro khác `risk/RISK_POLICY.md`.

## 8. Thoát lệnh

- Thoát sớm toàn bộ nếu giá đóng cửa phá ngược lại qua vùng cấu trúc vừa phá vỡ
  (xác nhận breakout ban đầu là false break) — không chờ chạm stop loss nếu tín
  hiệu vô hiệu hóa đã rõ ràng hơn.
- Dời stop loss theo cấu trúc giá mới hình thành (swing low/high tiếp theo cùng
  hướng lệnh) khi xu hướng tiếp diễn — không dời ngược lại gần entry hơn.
- Quy tắc chốt lời từng phần cụ thể: chưa xác định, cần backtest trước khi chốt
  quy tắc.

## 9. Điều kiện bỏ qua / không giao dịch

- Không giao dịch khi thị trường đang trong giai đoạn đi ngang rõ rệt (không có
  chuỗi HH/HL hoặc LH/LL theo mục 3).
- Không vào lệnh nếu breakout xảy ra ngay trước một sự kiện tin tức quan trọng đã
  biết trước.
- Không vào lệnh nếu pullback phá quá sâu vào vùng cấu trúc cũ (xem mục 5.2).
- Không ép coi một cú hồi giá là "pullback hợp lệ" chỉ vì muốn có setup để vào
  lệnh — nếu điều kiện mục 5 không rõ ràng, đứng ngoài.

## 10. Lỗi thường gặp

- Vào lệnh ngay tại breakout, bỏ qua chờ pullback → stop loss xa hơn cần thiết,
  tỷ lệ lời/lỗ xấu đi.
- Nhầm lẫn 1 cú hồi giá sâu (đã phá cấu trúc) với pullback hợp lệ.
- Bỏ qua điều kiện volume khi breakout, dẫn tới vào nhiều false break.
- Dời stop loss về hướng có lợi cho lệnh đang thua (di chuyển ngược mục 8) —
  đây là vi phạm kỷ luật, không phải điều chỉnh hợp lý.

## 11. Dữ liệu cần để backtest

- Cặp/mã cụ thể: chưa chọn (xem `CURRENT_STATUS.md` Next Task).
- Timeframe cụ thể: chưa chọn.
- Khoảng thời gian dữ liệu: tối thiểu đủ dài để bao gồm cả giai đoạn xu hướng rõ
  và giai đoạn đi ngang (tránh backtest chỉ trên 1 giai đoạn thị trường thuận
  lợi) — số ngày/nến cụ thể xác định theo `backtests/BACKTEST_STANDARD.md`.
- Nguồn dữ liệu: chưa xác định.

## 12. Kết quả backtest

Chưa có — xem `backtests/RESULTS_TEMPLATE.md` khi bắt đầu chạy backtest thật.
