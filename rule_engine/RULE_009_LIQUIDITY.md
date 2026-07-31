# RULE_009_LIQUIDITY — Đánh giá Thanh khoản Thị trường

## 1. Tên Rule
**RULE_009_LIQUIDITY**: Đánh giá thanh khoản tại vùng giá đang giao dịch — tránh trượt giá quá lớn
khi vào/thoát lệnh.

---

## 2. Mục đích
Thanh khoản kém → trượt giá lớn → rủi ro thực tế cao hơn tính toán. Rule này cảnh báo khi vùng
giá thiếu thanh khoản.

---

## 3. Input
- **Bid-Ask Spread** (chênh lệch giá mua/bán).
- **Order book depth** (độ sâu danh sách lệnh chờ).
- **Volume giao dịch tại vùng** (nếu có dữ liệu chi tiết).

---

## 4. Output

| Kết quả | Ý nghĩa | Điểm |
|---|---|---|
| **LIQUIDITY_GOOD** | Spread < 2 pip, depth tốt, không lo trượt | 5 |
| **LIQUIDITY_FAIR** | Spread 2-5 pip, depth trung bình | 3 |
| **LIQUIDITY_POOR** | Spread > 5 pip, depth sâu, risk trượt cao | 0 → cảnh báo |

---

## 5. Điều kiện

### 5.1 LIQUIDITY_GOOD
- Spread < 2 pip (forex/derivative standard).
- Order book depth đủ (ví dụ >= 1M volume ở các mức ngoài).
- Điểm: 5.

### 5.2 LIQUIDITY_FAIR
- Spread 2-5 pip.
- Depth trung bình.
- Điểm: 3.

### 5.3 LIQUIDITY_POOR
- Spread > 5 pip.
- Depth sâu, ít lệnh ở ngoài.
- Điểm: 0 → cảnh báo risk trượt cao, có thể tạm chờ hoặc chấp nhận risk cao hơn.

---

## 6. Ngoại lệ
- Thị trường phi tập trung (crypto): Spread có thể > 1% — cần ghi rõ nguồn dữ liệu, cái nào có
  thanh khoản tốt.
- Gần giờ close market: Spread tăng, depth giảm — tạm coi POOR.

---

## 7. Ví dụ
**Forex EURUSD:** Spread = 1.2 pip, Depth good → LIQUIDITY_GOOD → Điểm = 5
**Altcoin:** Spread = 3%, Depth sâu → LIQUIDITY_POOR → Cảnh báo

---

## 8. Dữ liệu cần
- **Bid-Ask spread** từ broker/sàn.
- **Order book depth** (nếu có).
- **Volume tại vùng giá**.

---

## 9. Khả năng Backtest
⚠️ **Khó backtest chính xác** — backtester thường không mô phỏng slippage chi tiết.
- Có thể dùng spread giả định (ví dụ: +2 pip vào entry) để ước lượng impact.

---

## 10. Độ khách quan
✅ **Khách quan — 85%** — spread/depth là dữ liệu thực tế, nhưng ngưỡng "tốt/kém" có
phần quy ước.

---

## 11. Điểm dễ gây Overfitting
⚠️ **Rủi ro: Trung bình**

| Vấn đề | Cách tránh |
|---|---|
| **Thay đổi spread threshold** | Chốt 2 pip, 5 pip từ backtest, không điều chỉnh |
| **Chỉ kiểm tra spread entry, quên thoát** | Kiểm tra cả vùng entry và vùng SL/TP |

---

## 12. Ghi chú
- Liquidity là **xác nhận phụ** — setup không bị reject vì liquidity POOR, nhưng score giảm.
- Nếu liquidity quá kém, có thể **chờ thanh khoản tốt hơn** (không rush vào).
- Liên quan: `risk/POSITION_SIZING.md` (khối lượng lệnh ảnh hưởng slippage).

