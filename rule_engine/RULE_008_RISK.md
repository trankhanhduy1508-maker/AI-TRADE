# RULE_008_RISK — Đánh giá Risk/Reward và Stop Loss

## 1. Tên Rule
**RULE_008_RISK**: Xác định stop loss hợp lệ và tỷ lệ risk/reward có chấp nhận được.

---

## 2. Mục đích
**Bắt buộc:** Không có setup nào có thể vào lệnh mà không xác định trước stop loss và R/R hợp lý.
Đây là quy tắc cứng từ `risk/RISK_POLICY.md`.

---

## 3. Input
- **Entry price**.
- **Stop loss level** (từ quy tắc stop loss của strategy).
- **Target/Profit target** (nếu có).
- **Risk/Reward ratio** (lời ÷ lỗ).

---

## 4. Output

| Kết quả | Ý nghĩa | Điểm |
|---|---|---|
| **RISK_ACCEPTABLE** | R/R >= 1.5 (hoặc ngưỡng chốt khác) | 5 |
| **RISK_FAIR** | R/R 1.0-1.5 | 3 |
| **RISK_UNACCEPTABLE** | R/R < 1.0, hoặc SL không xác định | 0 → REJECT |

---

## 5. Điều kiện

### 5.1 RISK_ACCEPTABLE
- R/R >= 1.5 (lời ít nhất gấp 1.5 lần lỗ).
- **Hoặc**: R/R >= 2.0 (tốt nhất).
- Stop Loss xác định rõ (không quá xa entry — tránh rủi ro lớn).
- Điểm: 5.

### 5.2 RISK_FAIR
- R/R 1.0-1.5 (chấp nhận được, nhưng không tối ưu).
- Điểm: 3.

### 5.3 RISK_UNACCEPTABLE
- R/R < 1.0 (lỗ nhiều hơn lời) → REJECT cứng.
- Không thể xác định SL (quá mơ hồ) → REJECT cứng.
- Stop loss quá xa entry (ví dụ > 5% entry, tùy thị trường) → REJECT.
- Điểm: 0 → Setup bị loại.

---

## 6. Ngoại lệ
- Ngưỡng R/R minimum (1.5 hay 2.0) là **chưa chốt** trong `risk/RISK_POLICY.md` — hiện dùng 1.5
  làm đề xuất, cần Project Owner xác nhận.

---

## 7. Ví dụ
**Entry=100, SL=98 (lỗ 2), Target=103 (lời 3):** R/R = 3÷2 = 1.5 → ACCEPTABLE → Điểm = 5
**Entry=100, SL=97 (lỗ 3), Target=102 (lời 2):** R/R = 2÷3 = 0.67 → UNACCEPTABLE → REJECT

---

## 8. Dữ liệu cần
- **Entry price** (xác định từ Pullback confirmation).
- **Stop loss level** (từ strategy quy tắc SL).
- **Target level** (nếu chốt trước, hoặc từ ATR/support nearest).

---

## 9. Khả năng Backtest
✅ **Backtest được** — tính R/R là mộc mạc.

---

## 10. Độ khách quan
✅ **Rất khách quan — 98%** — tính toán đơn giản.

---

## 11. Điểm dễ gây Overfitting
⚠️ **Rủi ro: Thấp**

| Vấn đề | Cách tránh |
|---|---|
| **Thay đổi R/R minimum** | Chốt 1.5 từ backtest, không nới lỏng nếu score thấp |
| **Tính SL tùy ý** | Tuân theo quy tắc stop loss cứng từ strategy |

---

## 12. Ghi chú
- **R/R < 1.0 là cấm tuyệt đối** — không có exception.
- Ngưỡng R/R 1.5 là **đề xuất**, cần backtest xác nhận có phù hợp không.
- Risk/Reward được tính từ **stop loss strategy** (không phải từ AI tự quyết định).
- Liên quan: `risk/POSITION_SIZING.md`, `risk/RISK_POLICY.md`.

