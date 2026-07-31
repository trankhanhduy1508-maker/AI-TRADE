# Price Action và Cấu trúc thị trường

## Vì sao đây là dữ liệu chính, không phải chỉ báo phụ

Chỉ báo (EMA, RSI, Volume...) đều là hàm tính toán **từ** giá — chúng luôn đi sau
giá. Price Action (hành vi giá thô: đỉnh, đáy, thân nến, bóng nến, tốc độ di
chuyển) là dữ liệu gốc, chưa qua biến đổi. Trong hệ thống này, Price Action và
cấu trúc thị trường quyết định **có setup hay không**; chỉ báo chỉ xác nhận thêm
setup đã tồn tại.

## Thành phần cấu trúc thị trường

- **Swing High / Swing Low:** đỉnh/đáy cục bộ, được xác nhận khi có ít nhất N cây
  nến hai bên thấp/cao hơn (N cụ thể do từng chiến lược định nghĩa trong
  `strategies/`, không có số chung cho toàn hệ thống).
- **Higher High / Higher Low (HH/HL):** dấu hiệu xu hướng tăng đang tiếp diễn.
- **Lower High / Lower Low (LH/LL):** dấu hiệu xu hướng giảm đang tiếp diễn.
- **Break of Structure (BOS):** giá phá qua 1 swing high/low theo hướng xu hướng
  hiện tại — xác nhận xu hướng tiếp diễn.
- **Change of Character (CHoCH):** giá phá qua swing high/low **ngược** hướng xu
  hướng hiện tại lần đầu tiên — dấu hiệu **cảnh báo** khả năng đảo chiều, chưa
  phải xác nhận đảo chiều (cần thêm BOS theo hướng mới để xác nhận).

## Vùng giá quan trọng

- **Support/Resistance (Vùng hỗ trợ/kháng cự):** vùng giá đã từng khiến giá đảo
  chiều hoặc dừng lại nhiều lần — nên coi là **vùng**, không phải 1 mức giá chính
  xác tuyệt đối.
- **Breakout (phá vỡ):** giá đóng cửa vượt hẳn ra khỏi vùng support/resistance
  hoặc trendline, có xác nhận thêm (ví dụ volume, xem `VOLUME_RESEARCH.md`) —
  không tính râu nến chạm qua rồi đóng cửa lại bên trong vùng.
- **Pullback (hồi giá):** sau breakout, giá hồi lại gần vùng vừa phá vỡ trước khi
  tiếp tục theo hướng breakout. Đây là điểm vào lệnh phổ biến trong Trend
  Following vì cho tỷ lệ lời/lỗ tốt hơn vào ngay tại điểm breakout.
- **False break (phá vỡ giả):** giá phá vỡ vùng/trendline nhưng nhanh chóng quay
  lại bên trong — một trong những lỗi phổ biến nhất khi giao dịch theo breakout
  nếu không có điều kiện xác nhận đủ chặt (xem `strategies/TF_002_TRENDLINE_REACTION.md`
  mục "false break").

## Trendline — vai trò và giới hạn

Trendline là công cụ **quan sát**, không phải công cụ **quyết định** một mình:

- Trendline hợp lệ cần tối thiểu 2 điểm để vẽ, nhưng **cần điểm chạm thứ 3 trở đi
  mới có giá trị xác nhận** (2 điểm đầu chỉ đủ để vẽ đường, không đủ để coi là xu
  hướng đã được thị trường "tôn trọng").
- Độ dốc quá lớn khiến trendline dễ bị phá vỡ do biến động bình thường — không
  phản ánh xu hướng bền vững.
- **Không được coi việc giá chạm vào trendline là đủ điều kiện vào lệnh** — đây là
  1 trong các nguyên tắc cứng của toàn hệ thống (xem `DECISIONS.md`). Giá chạm
  trendline chỉ là **điều kiện cần**, phải có thêm phản ứng giá cụ thể (nến đảo
  chiều, breakout cấu trúc nhỏ hơn...) mới đủ điều kiện.
- Không được **cố ép vẽ trendline** cho khớp với 1 setup đã muốn vào lệnh từ
  trước (xác nhận thiên lệch/confirmation bias) — trendline phải được vẽ trước
  và độc lập với ý định vào lệnh.

## Mối quan hệ với các file khác

- Quy tắc vào lệnh cụ thể dựa trên các khái niệm ở đây: `strategies/TF_001_BREAKOUT_PULLBACK.md`,
  `strategies/TF_002_TRENDLINE_REACTION.md`.
- Xác nhận thêm bằng volume: `knowledge/VOLUME_RESEARCH.md`.
- Toàn bộ khái niệm ở đây là **định nghĩa**, không phải **thống kê đã kiểm chứng**
  — hiệu quả thực tế phải qua backtest (`backtests/`).
