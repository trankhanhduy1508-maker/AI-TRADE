# Template báo cáo kết quả Backtest

> Copy file này cho mỗi lần backtest, đặt tên theo mẫu:
> `backtests/[MÃ_CHIẾN_LƯỢC]_[THỊ_TRƯỜNG]_[TIMEFRAME]_[YYYY-MM-DD].md`

---

## Thông tin backtest

- **Chiến lược:** [link tới file trong `strategies/`]
- **Giả thuyết liên quan:** [link tới mục trong `research/HYPOTHESES.md`]
- **Thị trường:** [cụ thể]
- **Khung thời gian (timeframe):** [cụ thể]
- **Khoảng dữ liệu:** [từ ngày → đến ngày]
- **Nguồn dữ liệu:** [cụ thể]
- **Ngày chạy backtest:** [YYYY-MM-DD]

## Giả định đã dùng

- % rủi ro/lệnh giả định: [số cụ thể, ghi rõ đây là giả định nếu `risk/RISK_POLICY.md`
  chưa chốt số chính thức]
- Phí giao dịch giả định: [số cụ thể]
- Trượt giá (slippage) giả định: [số cụ thể]
- Cách diễn giải các điều kiện mơ hồ (nếu có) trong file chiến lược: [ghi rõ]

## Kết quả

| Chỉ số | Giá trị |
|---|---|
| Tổng số lệnh | |
| Tỷ lệ thắng | |
| Kỳ vọng trung bình/lệnh (expectancy) | |
| Max Drawdown | |
| R/R trung bình thực tế | |
| Số lệnh thua liên tiếp dài nhất | |

## In-sample vs Out-of-sample

- Kết quả in-sample (dữ liệu dùng để điều chỉnh tham số, nếu có): [ghi rõ]
- Kết quả out-of-sample (dữ liệu chưa từng dùng để điều chỉnh): [ghi rõ, hoặc
  "chưa thực hiện — kết quả trên chỉ mang tính sơ bộ"]

## Nhận xét khách quan

[Mô tả kết quả đúng như số liệu cho thấy — không suy diễn quá mức từ 1 lần chạy,
không khẳng định "chiến lược này sinh lời" nếu chưa đủ mẫu/out-of-sample theo
`backtests/BACKTEST_STANDARD.md`]

## Kết luận và bước tiếp theo

- [ ] Đủ điều kiện coi là "đã kiểm chứng" theo `backtests/BACKTEST_STANDARD.md`
- [ ] Cần thêm dữ liệu/thử nghiệm out-of-sample
- [ ] Giả thuyết bị bác bỏ — cập nhật `research/HYPOTHESES.md` và (nếu cần)
      `research/FAILURE_CASES.md`
