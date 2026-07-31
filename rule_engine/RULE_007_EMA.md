# RULE_007_EMA — Đánh giá EMA Bias

## 1. Tên Rule
**RULE_007_EMA**: Đánh giá Exponential Moving Average (EMA) để xác định bias xu hướng dài hạn.

---

## 2. Mục đích
EMA là **bộ lọc bias**. Setup UP nên có giá trên EMA; setup DOWN nên có giá dưới EMA. Nếu trái
chiều, cảnh báo rủi ro cao.

---

## 3. Input
- **Price hiện tại** (close, high).
- **EMA period** (tham chiếu strategy, ví dụ 50, 100, 200).
- **EMA value** (tính từ giá lịch sử).

---

## 4. Output

| Kết quả | Ý nghĩa | Điểm |
|---|---|---|
| **EMA_UP_BIAS** | Setup UP + Giá > EMA (đúng bias) | 5 |
| **EMA_NEUTRAL** | Giá gần EMA (±2% giá) | 3 |
| **EMA_DOWN_BIAS** | Setup UP + Giá < EMA (sai bias) | 0 |

---

## 5. Điều kiện

### 5.1 EMA_UP_BIAS
- Setup LONG: Giá > EMA (hiện tại close hoặc high > EMA).
- Khoảng cách ít nhất 0.5-1% giá để tránh noise.
- Điểm: 5.

### 5.2 EMA_NEUTRAL
- Giá nằm trong ±2% EMA.
- Bias không rõ ràng.
- Điểm: 3.

### 5.3 EMA_DOWN_BIAS
- Setup LONG nhưng giá < EMA (sai chiều bias).
- Hoặc Setup SHORT nhưng giá > EMA.
- Điểm: 0.

---

## 6. Ngoại lệ
- EMA cắt giá (crossover): Tạm coi bias là NEUTRAL cho tới khi cắt hẳn.

---

## 7. Ví dụ
**Setup UP, EMA50=100, Giá=102:** Giá > EMA → EMA_UP_BIAS → Điểm = 5
**Setup UP, EMA50=100, Giá=98:** Giá < EMA → EMA_DOWN_BIAS → Điểm = 0

---

## 8. Dữ liệu cần
- **EMA period** (chốt từ strategy).
- **Giá 50+ nến** (tính EMA).

---

## 9. Khả năng Backtest
✅ **Backtest được dễ dàng.**

---

## 10. Độ khách quan
✅ **Rất khách quan — 95%** — so sánh giá vs EMA là mộc mạc.

---

## 11. Điểm dễ gây Overfitting
⚠️ **Rủi ro: Trung bình** — lựa chọn EMA period có ảnh hưởng.

| Vấn đề | Cách tránh |
|---|---|
| **Thay đổi EMA period** | Chốt 50/100/200 từ strategy, không điều chỉnh |
| **Tính khoảng cách % để gọi "gần"** | Chốt 2% standard |

---

## 12. Ghi chú
- EMA là **lọc bias**, không quyết định vào lệnh.
- Setup có thể vào ngay cả khi EMA bias sai (nhưng giảm điểm).
- EMA period phải được chốt **trước** backtest, không thay đổi để fit kết quả.

