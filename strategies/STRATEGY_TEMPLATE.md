# Template chuẩn cho một chiến lược

> Copy file này khi thêm chiến lược mới. Mọi mục dưới đây là bắt buộc — không bỏ
> trống mục nào, ghi rõ "chưa xác định" nếu thật sự chưa có câu trả lời.

---

# [Mã chiến lược]_[TÊN CHIẾN LƯỢC]

## Trạng thái

- [ ] Giả thuyết (chưa backtest)
- [ ] Đang backtest
- [ ] Đã backtest, đang đánh giá
- [ ] Đã xác nhận trên (các) thị trường/timeframe cụ thể — ghi rõ

## 1. Giả thuyết

Mô tả bằng 1-2 câu: vì sao setup này được kỳ vọng có kỳ vọng dương, dựa trên
nguyên tắc nào trong `knowledge/`.

## 2. Thị trường và khung thời gian áp dụng

Ghi rõ thị trường (forex/chứng khoán/crypto...) và timeframe đã/sẽ thử nghiệm.
**Không suy diễn** sang thị trường/timeframe khác chưa kiểm chứng.

## 3. Điều kiện xác định xu hướng

Quy tắc cụ thể, quan sát được, để xác định đang trong xu hướng nào (tham chiếu
`knowledge/TREND_FOLLOWING.md`, `knowledge/PRICE_ACTION_AND_MARKET_STRUCTURE.md`).

## 4. Điều kiện vào lệnh (Entry)

Chuỗi điều kiện **phải xảy ra theo đúng thứ tự**, không được gộp mơ hồ. Mỗi điều
kiện phải quan sát được trên biểu đồ, không mô tả kiểu cảm tính.

## 5. Xác nhận bổ sung (Volume/EMA/RSI)

Ghi rõ chỉ báo nào được dùng để xác nhận thêm, và **xác nhận cái gì cụ thể** —
không dùng chỉ báo làm điều kiện đủ để vào lệnh (xem `DECISIONS.md`).

## 6. Stop Loss

Quy tắc đặt stop loss cụ thể (theo cấu trúc giá, theo ATR, theo % cố định...).
Tham chiếu `risk/POSITION_SIZING.md` để tính khối lượng lệnh từ stop loss này —
**không tự đặt mức rủi ro khác với `risk/RISK_POLICY.md`**.

## 7. Thoát lệnh (Exit / Take Profit)

Tách biệt rõ với Stop Loss — mô tả điều kiện chốt lời từng phần (nếu có), điều
kiện dời stop loss (trailing), và điều kiện thoát sớm nếu setup bị vô hiệu hóa.

## 8. Điều kiện bỏ qua / không giao dịch

Liệt kê rõ các tình huống KHÔNG được vào lệnh dù bề ngoài giống setup (ví dụ: thị
trường đi ngang, tin tức quan trọng sắp ra, volume bất thường...).

## 9. Lỗi thường gặp khi áp dụng

Các lỗi chủ quan phổ biến khi người/AI áp dụng sai chiến lược này (ví dụ: ép vẽ
trendline, vào lệnh khi thiếu 1 điều kiện, FOMO theo breakout không xác nhận...).

## 10. Dữ liệu cần để backtest

Danh sách cụ thể: cặp/mã, khung thời gian, khoảng thời gian dữ liệu, nguồn dữ
liệu, số lượng mẫu tối thiểu để kết quả có ý nghĩa thống kê (tham chiếu
`backtests/BACKTEST_STANDARD.md`).

## 11. Kết quả backtest

Không điền tay ở đây — link tới file kết quả tương ứng trong `backtests/`
(dùng `backtests/RESULTS_TEMPLATE.md` làm chuẩn). Không được ghi số liệu chưa
chạy thật vào mục này.
