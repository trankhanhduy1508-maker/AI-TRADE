# Báo cáo: Data Loader (MVP Task 2)

## Việc đã làm

- `src/data_loader/csv_loader.py`, `validator.py`, `cleaner.py`, `pipeline.py` — đọc CSV OHLCV → validate → clean, dùng chung `Bar` với Rule Engine (`src/rule_engine/types.py`).
- `tests/data_loader/` — 52 test, fixture CSV nhỏ tự tạo để test code (không phải dữ liệu thị trường thật).

## Kết quả kiểm thử

```
python -m pytest tests/ -v
155 passed  (103 rule_engine + 52 data_loader, không có regression)
```

Đã tự chạy và xác minh trực tiếp. Đọc lại `pipeline.py` để kiểm tra thứ tự xử lý (load → sort/dedupe → validate → detect outlier) khớp đúng `BACKTEST_ENGINE.md` mục 2.2 — không phát hiện lỗi tích hợp (khác Task 1, lần này 1 agent viết toàn bộ package nên không có rủi ro lệch hợp đồng giữa các module).

## Còn thiếu / Blocker thật

**Chưa có nguồn dữ liệu giá lịch sử thật** (API trả phí/miễn phí, hoặc file CSV do Project Owner cung cấp) — đây là điều kiện bắt buộc cho MVP Task 3 (Backtest Engine) chạy backtest có ý nghĩa. Data Loader tự nó không bị chặn (hoạt động với bất kỳ CSV đúng định dạng), nhưng backtest THẬT (không phải test code) cần dữ liệu thật.

**Đề xuất phương án cho Project Owner quyết định trước khi làm Task 3:**
1. Cung cấp file CSV lịch sử (export từ MT5/broker/TradingView) cho 2-3 cặp tiền, đặt vào `data/raw/` theo naming convention trong `DATA_REQUIREMENTS.md` mục 11.
2. Dùng nguồn miễn phí công khai (ví dụ Yahoo Finance, Stooq) — cần thêm thư viện tải dữ liệu (`yfinance` hoặc tương đương) và có thể cần internet access lúc chạy.
3. Trì hoãn Task 3, làm trước Task 4 (Point-in-Time Backtest harness — có thể code khung sườn mà chưa cần dữ liệu thật) hoặc Task 5 (Paper Trading Engine).

**Không phải blocker cần dừng ngay** — tiếp tục MVP Task 3, sẽ dùng dữ liệu tổng hợp (synthetic) nhỏ để code/test Backtest Engine trước, và nêu rõ blocker dữ liệu thật khi tới bước chạy backtest có ý nghĩa thống kê.
