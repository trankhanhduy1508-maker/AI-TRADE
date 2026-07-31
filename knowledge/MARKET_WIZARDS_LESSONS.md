# Bài học tổng hợp từ giới Trend Following / Market Wizards

> Đây là **tổng hợp ý tưởng bằng ngôn ngữ riêng**, không chép nguyên văn bất kỳ
> cuốn sách/phỏng vấn nào. Mục đích: rút ra nguyên tắc chung được nhiều trader
> Trend Following thành công lặp lại độc lập, không phải trích dẫn nguồn cụ thể.

## 1. Cắt lỗ nhanh, để lợi nhuận chạy

Nguyên tắc được lặp lại nhiều nhất: giới hạn số tiền thua trên mỗi lệnh ở mức nhỏ
và cố định, nhưng không giới hạn lợi nhuận tiềm năng khi xu hướng đang đúng hướng.
Hệ quả: tỷ lệ thắng có thể thấp (nhiều lệnh thua nhỏ) nhưng kỳ vọng dương nhờ vài
lệnh thắng lớn bù lại toàn bộ.

→ Áp dụng: xem `risk/RISK_POLICY.md` (giới hạn lỗ cố định mỗi lệnh) và
`strategies/STRATEGY_TEMPLATE.md` (mục "thoát lệnh" tách biệt hoàn toàn khỏi "stop loss").

## 2. Không có gì đảm bảo — chỉ có xác suất

Không trader Trend Following nào tự nhận là dự đoán đúng thị trường. Họ mô tả
công việc của mình là **quản lý một tập hợp các cược có kỳ vọng dương**, chấp
nhận từng lệnh riêng lẻ có thể sai.

→ Áp dụng: mọi chiến lược trong `strategies/` phải được coi là **giả thuyết chờ
kiểm chứng**, không phải sự thật đã chứng minh (xem `research/HYPOTHESES.md`).

## 3. Kỷ luật quan trọng hơn dự đoán chính xác

Điểm chung của nhiều trader thành công: hệ thống giao dịch của họ không đặc biệt
phức tạp, nhưng họ **tuân thủ tuyệt đối** quy tắc đã đặt ra, kể cả khi "cảm thấy"
thị trường sẽ đi ngược lại tín hiệu.

→ Áp dụng: đây là lý do `PROJECT_CONTEXT.md` cấm LLM tự quyết định mức rủi ro —
kỷ luật phải đến từ luật cứng, không phải phán đoán tại thời điểm giao dịch.

## 4. Rủi ro theo danh mục, không chỉ theo từng lệnh

Nhiều bài học nhấn mạnh: rủi ro thật sự nguy hiểm không phải là 1 lệnh thua, mà là
**nhiều lệnh có tương quan cùng thua cùng lúc** (ví dụ nhiều lệnh cùng hướng trên
các thị trường liên quan). Quản lý rủi ro danh mục (tổng rủi ro mở tại 1 thời
điểm) quan trọng không kém rủi ro từng lệnh.

→ Áp dụng: `risk/RISK_POLICY.md` cần định nghĩa cả giới hạn rủi ro/lệnh **và**
giới hạn rủi ro tổng đang mở.

## 5. Thị trường thay đổi, chiến lược cần được đánh giá lại định kỳ

Không có hệ thống nào hiệu quả mãi mãi trên mọi giai đoạn thị trường. Người có
kinh nghiệm liên tục theo dõi hiệu suất thực tế và sẵn sàng tạm dừng một chiến
lược khi nó không còn khớp với điều kiện thị trường hiện tại — thay vì cố "chờ nó
quay lại".

→ Áp dụng: `risk/KILL_SWITCH_RULES.md` (tạm dừng khi hiệu suất xấu đi) và
`research/EXPERIMENT_LOG.md` (theo dõi hiệu suất theo thời gian, không chỉ 1 lần
backtest duy nhất).

## Giới hạn của tài liệu này

Đây là các nguyên tắc **định tính**, chưa phải quy tắc vào lệnh cụ thể — không
được dùng trực tiếp để vào lệnh. Quy tắc cụ thể, có thể kiểm chứng, nằm trong
`strategies/`.
