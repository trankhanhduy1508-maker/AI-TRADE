# Bài học tổng hợp từ giới Trend Following / Market Wizards

> Đây là **tổng hợp ý tưởng bằng ngôn ngữ riêng**, không chép nguyên văn bất kỳ
> cuốn sách/phỏng vấn nào. Mục đích: rút ra nguyên tắc để nghiên cứu, không phải
> trích dẫn nguồn cụ thể hay claim đã được Covel/Fifth Edition xác nhận toàn bộ.
>
> **Provenance P0:** phần nguyên tắc author material được đối chiếu tại
> `knowledge/COVEL_TREND_FOLLOWING_PROVENANCE.md` (`TF-COV-003` đến
> `TF-COV-005`). Các câu về tỷ lệ thắng, tương quan danh mục và chiến lược cụ
> thể là `IMPLEMENTATION_DERIVATION`/`UNVERIFIED` cho tới khi có nguồn hoặc
> backtest phù hợp.

## 1. Cắt lỗ nhanh, để lợi nhuận chạy

Author material của Covel nhấn mạnh kiểm soát lỗ và để vị thế thắng có cơ hội tiếp
diễn. Việc một hệ thống có tỷ lệ thắng thấp hay kỳ vọng dương là claim cần được
đo bằng backtest/paper evidence, không được suy ra mặc định từ triết lý.

→ Áp dụng: xem `risk/RISK_POLICY.md` (giới hạn lỗ cố định mỗi lệnh) và
`strategies/STRATEGY_TEMPLATE.md` (mục "thoát lệnh" tách biệt hoàn toàn khỏi "stop loss").

## 2. Không có gì đảm bảo — chỉ có xác suất

Không nên biến một tín hiệu thành lời hứa dự đoán đúng thị trường. AI-TRADE coi
mỗi strategy là **giả thuyết chờ kiểm chứng**, chấp nhận từng lệnh riêng lẻ có
thể sai.

→ Áp dụng: mọi chiến lược trong `strategies/` phải được coi là **giả thuyết chờ
kiểm chứng**, không phải sự thật đã chứng minh (xem `research/HYPOTHESES.md`).

## 3. Kỷ luật quan trọng hơn dự đoán chính xác

Điểm chung của nhiều trader thành công: hệ thống giao dịch của họ không đặc biệt
phức tạp, nhưng họ **tuân thủ tuyệt đối** quy tắc đã đặt ra, kể cả khi "cảm thấy"
thị trường sẽ đi ngược lại tín hiệu.

→ Áp dụng: đây là lý do `PROJECT_CONTEXT.md` cấm LLM tự quyết định mức rủi ro —
kỷ luật phải đến từ luật cứng, không phải phán đoán tại thời điểm giao dịch.

## 4. Rủi ro theo danh mục, không chỉ theo từng lệnh

Trong portfolio research, rủi ro cần xem cả từng lệnh và khả năng nhiều vị thế
cùng chịu một cú sốc. Đây là nguyên tắc thiết kế cần kiểm chứng bằng correlation,
exposure và stress test; không phải một ngưỡng số đã được chốt trong tài liệu này.

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
`strategies/`; kết quả phải ghi rõ provenance và phạm vi market/timeframe.
