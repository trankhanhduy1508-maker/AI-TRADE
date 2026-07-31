# Chuẩn Backtest

> Bất kỳ backtest nào không tuân theo chuẩn này đều **không được coi là kết quả
> đáng tin cậy**, dù số liệu có đẹp đến đâu.

## Nguyên tắc chống tự lừa dối (self-deception)

- **Không nhìn về tương lai (no look-ahead bias):** tại mỗi thời điểm mô phỏng,
  chỉ được dùng dữ liệu đã có tính đến thời điểm đó. Cấm dùng dữ liệu tương lai
  để xác nhận tín hiệu quá khứ (ví dụ: dùng swing high đã biết sau này để vẽ
  trendline cho quá khứ).
- **Không tối ưu quá mức (no overfitting):** không được chỉnh tham số liên tục
  cho tới khi ra kết quả đẹp trên đúng 1 bộ dữ liệu rồi dừng lại — phải kiểm tra
  trên dữ liệu ngoài mẫu (out-of-sample) trước khi coi là có giá trị.
- **Không chọn lọc thời gian có lợi (no cherry-picking):** phải backtest trên
  khoảng thời gian đủ dài, bao gồm cả giai đoạn thị trường thuận lợi và bất lợi
  cho chiến lược — không chỉ chọn đúng giai đoạn chiến lược thắng nhiều.

## Yêu cầu tối thiểu cho một backtest hợp lệ

1. **Nguồn dữ liệu** phải ghi rõ (sàn/nhà cung cấp cụ thể), kèm khoảng thời gian
   chính xác (từ ngày → đến ngày).
2. **Số lượng mẫu (số lệnh) tối thiểu** để kết quả có ý nghĩa thống kê — số cụ
   thể tùy chiến lược, nhưng **dưới 30 lệnh không được coi là đủ để kết luận**,
   chỉ được coi là thử nghiệm sơ bộ.
3. **Chia dữ liệu in-sample / out-of-sample:** nếu có bất kỳ tham số nào được
   điều chỉnh dựa trên dữ liệu, phải kiểm tra lại kết quả trên phần dữ liệu chưa
   từng dùng để điều chỉnh.
4. **Ghi rõ giả định** đã dùng khi backtest (ví dụ: % rủi ro/lệnh giả định nếu
   `risk/RISK_POLICY.md` chưa chốt số chính thức — xem `risk/POSITION_SIZING.md`).
5. **Không tính phí/trượt giá bằng 0** — phải có giả định tối thiểu về phí giao
   dịch và trượt giá (slippage), dù là ước lượng, để không phóng đại kết quả.

## Các chỉ số bắt buộc phải báo cáo

- Tổng số lệnh, tỷ lệ thắng/thua.
- Kỳ vọng trung bình mỗi lệnh (expectancy).
- Drawdown lớn nhất (Max Drawdown).
- Tỷ lệ Risk/Reward trung bình thực tế đạt được (khác với R/R lý thuyết đặt ra).
- Số lệnh thua liên tiếp dài nhất.
- Khoảng thời gian (số lệnh) im lặng không có tín hiệu, nếu có ý nghĩa.

## Quy trình bắt buộc

1. Ghi giả thuyết vào `research/HYPOTHESES.md` **trước khi** backtest.
2. Chạy backtest theo đúng quy tắc trong file `strategies/*.md` tương ứng — nếu
   phải diễn giải một điều kiện mơ hồ, ghi rõ cách diễn giải đã chọn.
3. Điền kết quả vào bản sao của `backtests/RESULTS_TEMPLATE.md`.
4. Ghi nhận vào `research/EXPERIMENT_LOG.md`.
5. Cập nhật kết luận trong `research/HYPOTHESES.md` (mục Kết luận).
6. Nếu phát hiện lỗi/sai lệch trong quá trình, ghi vào `research/FAILURE_CASES.md`.

## Điều cấm

- Không công bố kết quả backtest như "chiến lược đã được chứng minh sinh lời" —
  chỉ được nói "kết quả trên [dữ liệu cụ thể] cho thấy...", luôn kèm giới hạn
  phạm vi đã kiểm chứng (theo `DECISIONS.md`).
- Không bịa số liệu backtest chưa từng chạy thật.
