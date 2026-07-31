# Trend Following — Kiến thức nền

## Ý tưởng cốt lõi

Trend Following không cố dự đoán thị trường sẽ đảo chiều ở đâu. Nó chấp nhận rằng
xu hướng, một khi đã hình thành, có xu hướng **tiếp diễn lâu hơn** đám đông nghĩ,
và mục tiêu là **bám theo phần giữa của xu hướng** — không cần bắt đúng đáy hay đỉnh.

Ba giả định nền tảng (đây là **giả định**, không phải sự thật tuyệt đối — xem
`research/HYPOTHESES.md` để theo dõi việc kiểm chứng):

1. Giá di chuyển theo xu hướng trong phần lớn thời gian có ý nghĩa giao dịch, xen
   kẽ với giai đoạn đi ngang (sideway) khó giao dịch theo Trend Following.
2. Xu hướng để lại dấu vết quan sát được qua cấu trúc thị trường (đỉnh/đáy cao
   dần hoặc thấp dần) trước khi đảo chiều hẳn.
3. Phản ứng theo xu hướng đã xác nhận, dù vào trễ hơn đáy/đỉnh thật, có kỳ vọng
   toán học tốt hơn cố đoán điểm đảo chiều.

## Vì sao chọn Reaction thay vì Prediction

- **Prediction (dự đoán):** cố xác định trước khi nào xu hướng sẽ đảo chiều hoặc
  bắt đầu — rủi ro cao vì dựa trên cảm tính/mẫu hình chủ quan chưa xảy ra.
- **Reaction (phản ứng):** chỉ vào lệnh sau khi thị trường đã **thực sự** in ra
  bằng chứng theo đúng kịch bản định nghĩa trước (breakout đã xảy ra, pullback đã
  hình thành, giá đã phản ứng đúng vùng). Chấp nhận vào trễ hơn để đổi lấy xác suất
  cao hơn rằng tín hiệu là thật, không phải nhiễu.

Hệ quả trực tiếp: mọi chiến lược trong `strategies/` phải định nghĩa **điều kiện
xác nhận cụ thể, quan sát được trên biểu đồ** — không được viết kiểu "khi cảm thấy
xu hướng sắp đổi chiều".

## Cấu trúc xu hướng (khung tham chiếu, không phải quy tắc vào lệnh)

- **Xu hướng tăng:** chuỗi đáy sau cao hơn đáy trước (Higher Low) và đỉnh sau cao
  hơn đỉnh trước (Higher High).
- **Xu hướng giảm:** chuỗi đỉnh sau thấp hơn đỉnh trước (Lower High) và đáy sau
  thấp hơn đáy trước (Lower Low).
- **Đi ngang / không xu hướng:** đỉnh/đáy không tạo chuỗi rõ ràng theo 1 hướng —
  đây là vùng Trend Following có xác suất thấp, cần thận trọng hoặc đứng ngoài
  (chi tiết điều kiện "không giao dịch" nằm trong từng file `strategies/`).

Xác nhận đảo chiều xu hướng thật sự đòi hỏi **phá vỡ chuỗi đỉnh/đáy hiện tại**,
không phải một cây nến ngược xu hướng đơn lẻ.

## Vai trò của EMA trong khung Trend Following

EMA (đường trung bình động hàm mũ) được dùng ở đây như **bộ lọc xu hướng tham
khảo**, không phải tín hiệu vào lệnh độc lập:

- Giá nằm trên/dưới 1 hoặc vài đường EMA dài hạn giúp xác nhận thiên hướng chủ đạo
  (bias) trước khi tìm setup theo Price Action.
- EMA cắt nhau (golden cross/death cross) **không** được dùng làm tín hiệu vào
  lệnh trực tiếp trong hệ thống này — chỉ là 1 lớp xác nhận bổ sung, đứng sau
  cấu trúc thị trường.

## Giới hạn cần nhớ

- Trend Following có xác suất thắng thường **không cao** (nhiều lệnh thua nhỏ,
  ít lệnh thắng lớn) — đây là đặc điểm của trường phái, không phải lỗi hệ thống.
  Đây chính là lý do `risk/RISK_POLICY.md` đặt quản lý rủi ro lên trên tỷ lệ thắng.
- Hiệu quả của Trend Following thay đổi rất nhiều theo thị trường và khung thời
  gian — không suy diễn kết quả từ thị trường/timeframe này sang thị trường/
  timeframe khác mà chưa kiểm chứng riêng (xem `DECISIONS.md`).
