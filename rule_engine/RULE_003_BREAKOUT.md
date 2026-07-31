# RULE_003_BREAKOUT — Xác định Breakout Hợp lệ

## 1. Tên Rule
**RULE_003_BREAKOUT**: Xác định xem giá có thực sự phá vỡ swing high/low theo cách hợp lệ hay chỉ
chạm bằng bóng nến.

---

## 2. Mục đích
Phân biệt giữa **true breakout** (phá thực sự) vs **bóng nến chạm** hoặc **false break** (quay lại
ngay). Đây là tiêu chí quyết định setup có xảy ra hay không.

---

## 3. Input

- **Close price của nến breakout**: Giá đóng cửa của nến phá vỡ swing level.
- **Swing high/low level** (từ RULE_002).
- **Body ratio**: Tỷ lệ thân nến (body) so với toàn bộ nến (high - low).
- **Volume** (xem RULE_005, nhưng nó không quyết định ở đây, chỉ xác nhận).

---

## 4. Output

| Kết quả | Ý nghĩa | Điểm |
|---|---|---|
| **BREAKOUT_TRUE** | Close vượt hẳn swing level, body ratio > 60%, không phải doji | 15 |
| **BREAKOUT_WEAK** | Close vượt nhưng body yếu (40-60%), hoặc chỉ chạm bằng bóng | 10 |
| **NO_BREAKOUT** | Không có breakout, hoặc chỉ chạm | 0 |

---

## 5. Điều kiện

### 5.1 BREAKOUT_TRUE

**Bắt buộc:**
- Close price > Swing High (setup UP) hoặc Close price < Swing Low (setup DOWN).
- Close vượt hẳn swing level (không chỉ bằng) — đề xuất tối thiểu **1-2 pip hoặc 0.1% giá**.
- **Body ratio > 60%**: (Close - Open) / (High - Low) > 0.6 (setup UP) hoặc (Open - Close) / (High - 
  Low) > 0.6 (setup DOWN).
- Không phải nến doji (Open = Close) hoặc indecision.

**Điểm:** 15 (max).

### 5.2 BREAKOUT_WEAK

**Kích hoạt khi:**
- Close vượt swing level, nhưng body ratio 40-60% (nến yếu, nhưng còn signal).
- Hoặc: Chỉ high/low chạm swing level, chưa close vượt hẳn (bóng nến chạm), nhưng có động lực.

**Điểm:** 10.

### 5.3 NO_BREAKOUT

**Kích hoạt khi:**
- Close không vượt swing level.
- Hoặc: High/Low chạm rồi quay lại ngay (bóng nến chạm), nhưng không đủ body ratio.
- Hoặc: Nến doji/indecision tại mức swing level.

**Điểm:** 0 → WAIT hoặc REJECT (tuỳ Decision Flow bước 3).

---

## 6. Ngoại lệ

| Tình huống | Xử lý |
|---|---|
| Nến breakout có wick dài nhưng body OK (40-60%) | Coi là BREAKOUT_WEAK (10 điểm), không phải TRUE. |
| Gap qua swing level (open đã vượt) | Nếu open + close đều vượt hẳn → coi là TRUE. Nếu open vượt nhưng close quay lại → FALSE (lạ). |
| Multiple swings tại cùng level | Coi là **cùng 1 swing level** để breakout, không tính riêng. |
| Tin tức bất thường gây breakout mạnh | Vẫn coi là TRUE nếu điều kiện breakout thỏa mãn, nhưng ghi chú để cảnh báo (risk cao hơn bình thường). |

---

## 7. Ví dụ

**Ví dụ BREAKOUT_TRUE (Setup UP):**
```
Swing High = 110, Swing Low = 100
Nến breakout: Open=109.5, High=111, Low=109, Close=110.8

Close > Swing High? 110.8 > 110 ✓
Body ratio = (110.8 - 109.5) / (111 - 109) = 1.3 / 2 = 65% ✓ (> 60%)
→ BREAKOUT_TRUE → Điểm = 15
```

**Ví dụ BREAKOUT_WEAK:**
```
Nến breakout: Open=110.2, High=111, Low=109.8, Close=110.6
Body ratio = (110.6 - 110.2) / (111 - 109.8) = 0.4 / 1.2 = 33% ✗ (< 40%)
Hoặc: Close = 109.9 (chưa vượt hẳn swing high 110)
→ BREAKOUT_WEAK → Điểm = 10
```

---

## 8. Dữ liệu cần

- **OHLC** của nến breakout (Open, High, Low, Close).
- **Swing High/Low level** từ RULE_002.
- **Công thức tính body ratio**: (|Close - Open|) / (High - Low).

---

## 9. Khả năng Backtest

✅ **Backtest được, nhưng cần định nghĩa "vượt hẳn".**

- Body ratio là số cụ thể, dễ tính.
- Cần xác định: "vượt hẳn" = bao nhiêu pip/% để lọc false break?
- Backtest: So sánh true breakout vs weak breakout, cái nào cho tỷ lệ lời cao hơn.

---

## 10. Độ khách quan

✅ **Khách quan — 85-90%**

- Body ratio là tính toán mộc mạc.
- Ngưỡng "vượt hẳn" là con số cụ thể, không chủ quan.
- **Nhưng:** Định nghĩa "vượt hẳn" bao nhiêu (1 pip vs 2 pip vs 0.1%?) có ảnh hưởng, cần chốt cụ
  thể qua backtest.

---

## 11. Điểm dễ gây Overfitting

⚠️ **Rủi ro: Trung bình**

| Vấn đề | Cách tránh |
|---|---|
| **Tham số body ratio** | Chốt body ratio 60% qua backtest, không điều chỉnh sau mỗi lệnh thua. |
| **Định nghĩa "vượt hẳn"** | Cài cứng con số pip/% vào từng chiến lược, không thay đổi tuỳ ý. |
| **Chấp nhận breakout yếu quá nhiều** | Khi score thấp, có thể cám dỗ giảm body ratio để có signal — KHÔNG. Giữ body ratio 60% không đổi. |

---

## 12. Ghi chú bổ sung

- Rule này **xác định** setup có xảy ra hay không — không có breakout = không có setup.
- Body ratio 60% là **đề xuất**, có thể điều chỉnh qua backtest (ví dụ: 55% hoặc 70%).
- Close price là tiêu chí dùng (không dùng high/low của nến breakout).
- Kết hợp với RULE_005 (Volume) để xác nhận, nhưng breakout weak vẫn có thể là setup hợp lệ nếu
  volume xác nhận mạnh.

