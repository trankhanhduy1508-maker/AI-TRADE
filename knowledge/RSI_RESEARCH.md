# RSI — Nghiên cứu và giới hạn sử dụng

## Vai trò trong hệ thống này

RSI (Relative Strength Index) **chỉ được dùng để xác nhận**, không bao giờ là
điều kiện đủ để vào lệnh một mình. Đây là quyết định đã chốt trong `DECISIONS.md`.

## Vì sao KHÔNG dùng RSI kiểu máy móc

Cách dùng phổ biến nhưng **bị cấm trong hệ thống này**: "RSI > 70 → quá mua → bán,
RSI < 30 → quá bán → mua". Lý do:

- Trong một xu hướng mạnh, RSI có thể duy trì ở vùng "quá mua"/"quá bán" **rất
  lâu** trong khi giá vẫn tiếp tục đi theo xu hướng — vào lệnh ngược xu hướng chỉ
  vì RSI chạm ngưỡng là đi ngược lại chính triết lý Trend Following của hệ thống.
- Ngưỡng 70/30 là quy ước tùy ý, không có cơ sở toán học cố định đúng cho mọi thị
  trường/timeframe — dùng máy móc là một dạng "quy tắc giả khoa học".

## Cách dùng RSI được chấp nhận (chỉ để xác nhận)

- **Phân kỳ (Divergence):** giá tạo đỉnh/đáy mới nhưng RSI không xác nhận (đỉnh
  sau thấp hơn đỉnh trước dù giá cao hơn, hoặc ngược lại) — dùng như **một tín
  hiệu cảnh báo suy yếu động lượng**, kết hợp với cấu trúc thị trường
  (`PRICE_ACTION_AND_MARKET_STRUCTURE.md`), không tự vào lệnh chỉ vì có phân kỳ.
- **Xác nhận động lượng theo xu hướng:** trong xu hướng tăng, RSI giữ trên vùng
  trung tính (thường quanh 40-50) khi hồi giá là một dấu hiệu xu hướng còn khỏe —
  dùng để **tăng độ tin cậy** của một setup Price Action đã có sẵn, không tự tạo
  setup mới.
- **Không dùng RSI để xác định điểm vào/ra lệnh chính xác** — điểm vào/ra do cấu
  trúc giá và quy tắc trong `strategies/` quyết định.

## Câu hỏi cần trả lời khi backtest (chưa có câu trả lời — đây là giả thuyết)

Ghi vào `research/HYPOTHESES.md` khi bắt đầu kiểm chứng:

- RSI có thực sự cải thiện tỷ lệ thắng khi thêm vào làm bộ lọc cho TF_001/TF_002
  hay chỉ làm giảm số lượng lệnh mà không cải thiện kỳ vọng?
- Ngưỡng phân kỳ RSI có ổn định giữa các thị trường/timeframe khác nhau không?

## Giới hạn

Đây là tài liệu **định hướng cách dùng**, không phải kết luận đã kiểm chứng bằng
số liệu — mọi khẳng định "RSI giúp ích" phải được kiểm chứng qua `backtests/`
trước khi coi là quy tắc chính thức trong bất kỳ `strategies/*.md` nào.
