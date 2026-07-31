# RULE_006_RSI — Đánh giá RSI Bias

## 1. Tên Rule
**RULE_006_RSI**: Đánh giá chỉ báo RSI (Relative Strength Index) xem có ngược signal hay hỗ trợ signal.

---

## 2. Mục đích
RSI là **xác nhận phụ**, không quyết định vào lệnh. Mục đích: cảnh báo nếu RSI có phân kỳ ngược
chiều (giá lên, RSI xuống).

---

## 3. Input
- **RSI value** (tính từ 14 nến, theo standard).
- **Price direction** (đang tăng hay giảm).
- **RSI trend** (RSI lên hay xuống).

---

## 4. Output

| Kết quả | Ý nghĩa | Điểm |
|---|---|---|
| **RSI_BULLISH** | RSI không ở vùng quá mua, hoặc phân kỳ dương | 5 |
| **RSI_NEUTRAL** | RSI trong vùng 30-70, không rõ signal | 3 |
| **RSI_BEARISH** | RSI quá mua (>70) hoặc phân kỳ âm | 0 |

---

## 5. Điều kiện

### 5.1 RSI_BULLISH
- Setup UP: RSI không > 70 (không quá mua bất thường), hoặc RSI từ cao xuống (phân kỳ dương).
- Setup DOWN: RSI không < 30 (không quá bán).
- Điểm: 5.

### 5.2 RSI_NEUTRAL
- RSI trong vùng 30-70 (middle).
- Không rõ signal.
- Điểm: 3.

### 5.3 RSI_BEARISH
- Setup UP: RSI > 80 (quá mua), hoặc giá lên nhưng RSI xuống (phân kỳ âm).
- Setup DOWN: RSI < 20 (quá bán), hoặc giá xuống nhưng RSI lên (phân kỳ âm).
- Điểm: 0.

---

## 6. Ngoại lệ
- Thị trường mạnh (bull/bear trend): RSI có thể ở 70+ hay 30- lâu dài mà không phải quá mua/bán.
- Phân kỳ không phải signal duy nhất: kết hợp với RULE_001 verify trend.

---

## 7. Ví dụ
**BULLISH (Setup UP):** RSI = 55 (trung bình), Setup tăng → Điểm = 5
**BEARISH (Setup UP):** RSI = 85 (quá mua), Setup tăng → Điểm = 0

---

## 8. Dữ liệu cần
- **Giá 14 nến** (tính RSI).
- **RSI value hiện tại**.

---

## 9. Khả năng Backtest
✅ **Backtest được** — RSI là chỉ báo standard.

---

## 10. Độ khách quan
✅ **Khách quan — 90%** — tính RSI tự động, nhưng diễn giải phân kỳ là 10% chủ quan.

---

## 11. Điểm dễ gây Overfitting
⚠️ **Rủi ro: Trung bình-cao** — phân kỳ khó định nghĩa chính xác.

| Vấn đề | Cách tránh |
|---|---|
| **Định nghĩa phân kỳ mơ hồ** | Chốt rõ: "phân kỳ = giá lên 3+ nến liên tiếp, RSI xuống trong khoảng đó" |
| **Thay đổi ngưỡng quá mua (70 → 60 → 80)** | Chốt 70/30 standard, không điều chỉnh |

---

## 12. Ghi chú
- RSI chỉ dùng để **cảnh báo**, không bao giờ là điều kiện vào lệnh một mình.
- Nếu RSI bearish (phân kỳ âm), không reject setup, chỉ **giảm điểm** từ 5 → 0.

