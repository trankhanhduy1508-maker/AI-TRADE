# Báo cáo: Rule Engine — Code (Phase 2 Code, MVP Task 1)

## Việc đã làm

- Cài đặt môi trường Python (trước đó máy chưa có runtime nào — blocker chặn toàn bộ MVP đã được gỡ bằng cách cài Python 3.14.6 cục bộ).
- Code `src/rule_engine/`: 10 module (RULE_001-010) + `scoring.py` (orchestrator Decision Flow 9 bước + Setup Score 0-100), theo đúng đặc tả `rule_engine/*.md` và `RULE_ENGINE.md`.
- Viết `tests/rule_engine/`: 103 test (unit test từng rule + `test_scoring_integration.py` chạy `evaluate_setup()` qua các module RULE_001-005 **thật, không mock**).
- `src/ARCHITECTURE.md` — mô tả kiến trúc code, luồng dữ liệu.

## Lỗi phát hiện và đã sửa

Rule Engine được code song song bởi 2 agent (RULE_001-005 và RULE_006-010+scoring). Khi tích hợp và tự chạy `pytest` để xác minh (không chỉ tin báo cáo của agent), phát hiện **`scoring.py` gọi sai chữ ký hàm** của RULE_001-004 (ví dụ gọi `eval_rule_001(bars, direction)` trong khi hàm thật chỉ nhận `(bars, n=2)`; gọi `eval_rule_003(bars, direction, entry)` thay vì `(bars, structure_level, direction)`). Lỗi này không bị 65+35 test ban đầu phát hiện vì các test `scoring.py` đều dùng `unittest.mock.patch` để giả lập RULE_001-005, không bao giờ gọi hàm thật.

**Đã sửa:** viết lại phần orchestration trong `scoring.py` để gọi đúng chữ ký thật, lấy `structure_level` (swing_high/swing_low) từ `detail` của RULE_002 để truyền cho RULE_003/004, hướng giao dịch (`direction`) được đối chiếu với xu hướng RULE_001 tự phát hiện (reject nếu lệch). Thêm 3 test tích hợp không mock để việc này không tái diễn.

## Kết quả kiểm thử

```
python -m pytest tests/rule_engine/ -v
103 passed
```

Đã tự chạy và xác minh trực tiếp (không dựa vào báo cáo của agent).

## Còn thiếu / chưa làm

- `position_sizing.py`, `risk_checker.py` (portfolio-level), `trendline_reaction.py` — dời sang MVP Task 2 (Data Loader) / Task 5 (Paper Trading Engine).
- RULE_009 (Liquidity) chưa có nguồn spread/order-book thật.
- Chưa test với dữ liệu giá lịch sử thật (chờ Data Loader).
- Tham số rủi ro (`rr_min=1.5`...) vẫn là giá trị đề xuất, chưa được Project Owner chốt.

## Không phải blocker cần dừng

Toàn bộ việc trên nằm trong phạm vi có thể tự làm (code nội bộ, dữ liệu test tự tạo). Tiếp tục MVP Task 2: Data Loader.
