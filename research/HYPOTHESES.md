# Nhật ký giả thuyết

> Mỗi giả thuyết phải được ghi lại ở đây **trước** khi backtest, và cập nhật kết
> luận **sau** khi có kết quả — không viết giả thuyết sau khi đã biết kết quả
> (tránh hindsight bias).

## Cách dùng file này

Mỗi mục gồm: **Giả thuyết** (điều muốn kiểm chứng) → **Nguồn gốc** (từ đâu trong
`knowledge/`/`strategies/`) → **Trạng thái** (chưa kiểm chứng / đang kiểm chứng /
đã kiểm chứng) → **Kết luận** (chỉ điền sau khi có kết quả backtest thật, link
tới `backtests/`).

---

## H001 — Pullback sau breakout cho tỷ lệ lời/lỗ tốt hơn vào ngay tại breakout

- **Nguồn gốc:** `strategies/TF_001_BREAKOUT_PULLBACK.md`.
- **Trạng thái:** Chưa kiểm chứng.
- **Kết luận:** (chưa có)

## H002 — Trendline chỉ có giá trị giao dịch từ điểm chạm thứ 3 trở đi

- **Nguồn gốc:** `strategies/TF_002_TRENDLINE_REACTION.md`.
- **Trạng thái:** Chưa kiểm chứng.
- **Kết luận:** (chưa có)

## H003 — RSI làm bộ lọc bổ sung cải thiện kỳ vọng của TF_001/TF_002

- **Nguồn gốc:** `knowledge/RSI_RESEARCH.md`.
- **Trạng thái:** Chưa kiểm chứng.
- **Kết luận:** (chưa có)

## H004 — Volume tăng tại breakout giảm tỷ lệ false break

- **Nguồn gốc:** `knowledge/VOLUME_RESEARCH.md`.
- **Trạng thái:** Chưa kiểm chứng.
- **Kết luận:** (chưa có)

## H005 — False break tại trendline kèm volume thấp là tín hiệu ngược hướng đáng
tin cậy

- **Nguồn gốc:** `strategies/TF_002_TRENDLINE_REACTION.md` mục 9.
- **Trạng thái:** Chưa kiểm chứng — cần backtest độc lập, không mặc định đúng.
- **Kết luận:** (chưa có)

---

## Nguyên tắc thêm giả thuyết mới

- Đánh số tiếp theo (H006, H007...), không đánh số lại.
- Ghi rõ nguồn gốc — không có giả thuyết "từ trên trời rơi xuống" không tham
  chiếu tới `knowledge/`/`strategies/`.
- Không xóa giả thuyết đã bị bác bỏ — cập nhật trạng thái, giữ lại làm lịch sử
  (tham chiếu chéo với `research/FAILURE_CASES.md` nếu giả thuyết sai gây ra lỗi
  thực tế).
