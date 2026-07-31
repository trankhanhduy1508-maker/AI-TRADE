# RULE_004_PULLBACK — Xác định Pullback Hợp lệ

## 1. Tên Rule
**RULE_004_PULLBACK**: Xác định xem sau breakout, giá có hồi lại gần swing level một cách hợp lệ
(không phá ngược lại).

---

## 2. Mục đích
Để từng khi setup tiếp tục diễn ra, pullback cung cấp điểm vào lệnh tốt hơn vào tại breakout (rủi
ro thấp hơn). Rule này xác định pullback có hợp lệ không.

---

## 3. Input

- **Giá sau breakout** (5-20 nến sau breakout).
- **Swing high/low vừa phá** (từ RULE_003).
- **Volume của các nến hồi** (xem RULE_005).
- **Cấu trúc giá trong pullback** (có phá ngược hay không).

---

## 4. Output

| Kết quả | Ý nghĩa | Điểm |
|---|---|---|
| **PULLBACK_VALID** | Hồi gần swing level, không phá ngược, volume giảm | 15 |
| **PULLBACK_WAITING** | Chưa có pullback rõ ràng, giá tiếp tục theo breakout | 8-12 |
| **PULLBACK_FALSE_BREAK** | Hồi quá sâu (phá ngược), hoặc false break | 0 → REJECT |

---

## 5. Điều kiện

### 5.1 PULLBACK_VALID

**Bắt buộc:**
- Sau breakout 1-20 nến, giá hồi lại gần swing level vừa phá (trong khoảng 50-100% của breakout
  distance).
- Close không phá ngược lại sâu bên trong vùng cũ (phá hỏng breakout).
- Volume pullback **thấp hơn** volume breakout (giảm dần).
- Không có CHoCH (đảo chiều cấu trúc).

**Điểm:** 15.

### 5.2 PULLBACK_WAITING

**Kích hoạt khi:**
- Breakout đã xảy ra, nhưng 20+ nến sau, giá vẫn **tiếp tục theo hướng breakout** mà không hồi.
- Setup vẫn hợp lệ, chỉ chưa có pullback để vào lệnh tốt hơn.
- Có thể vào lệnh tại breakout (rủi ro cao hơn) hoặc chờ pullback.

**Điểm:** 8-12 (tuỳ mức độ "nóng" của setup).

### 5.3 PULLBACK_FALSE_BREAK

**Trigger REJECT:**
- Giá hồi quá sâu vào vùng cũ, phá ngược lại quá xa swing level (ví dụ: close quay lại giữa swing
  level và breakout level).
- Hoặc: Breakout chỉ kéo dài 2-3 nến rồi quay lại ngay — false break.
- Cấu trúc giá bị phá hỏng (CHoCH xảy ra).

**Điểm:** 0 → REJECT cứng.

---

## 6. Ngoại lệ

| Tình huống | Xử lý |
|---|---|
| Hồi có xu hướng (chứ không phải chỉ 1 nến) | Vẫn coi là VALID nếu không phá ngược hẳn. Hồi 5-10 nến là bình thường. |
| Volume pullback cao nhưng giá hôi nhẹ | Có thể là lực bán/mua ngược chiều mạnh — cảnh báo high risk, nhưng vẫn coi VALID nếu không phá ngược. |
| Multiple pullback (hôi 2-3 lần) | Coi là bình thường trong xu hướng mạnh, vẫn VALID. |

---

## 7. Ví dụ

**Ví dụ PULLBACK_VALID (Setup UP):**
```
Breakout level: 110, Breakout distance: 2 (từ 108)
Nến 1-3 sau breakout: Giá lên 111 (tiếp tục), volume cao
Nến 4-8: Giá hôi xuống 109.5 (nằm trong 50-100% breakout distance ✓)
         Close = 109.5 > 108 (không phá ngược) ✓
         Volume giảm dần ✓
→ PULLBACK_VALID → Điểm = 15
```

**Ví dụ FALSE_BREAK:**
```
Breakout xảy ra: Close = 110.5
Nến 2: Giá lên 111
Nến 3: Giá xuống 108.5 (phá ngược quá sâu, close < 109 swing low)
→ FALSE_BREAK → REJECT
```

---

## 8. Dữ liệu cần

- **OHLC 20 nến sau breakout**.
- **Swing level** từ RULE_003.
- **Volume của từng nến** (xem RULE_005).

---

## 9. Khả năng Backtest

✅ **Backtest được, nhưng cần định nghĩa khoảng hồi.**

- Khoảng hồi "50-100% breakout distance" là tham số có thể điều chỉnh qua backtest.
- Backtest: So sánh vào tại breakout (ngay) vs tại pullback (chờ) → cái nào cho kết quả tốt hơn.

---

## 10. Độ khách quan

✅ **Khách quan — 80%**

- Tính khoảng hồi là mộc mạc.
- **Nhưng:** Định nghĩa "hôi quá sâu" bao nhiêu % là chủ quan, cần chốt qua backtest.

---

## 11. Điểm dễ gây Overfitting

⚠️ **Rủi ro: Trung bình-cao**

| Vấn đề | Cách tránh |
|---|---|
| **Khoảng hôi 50-100%** | Chốt qua backtest, không điều chỉnh tuỳ ý. |
| **Thay đổi ngưỡng "phá ngược quá sâu"** | Ví dụ: chốt là "close không được xuống dưới trung điểm breakout-swing level", không thay đổi. |
| **Chấp nhận false break** | Khi muốn có setup, có thể ép coi hôi sâu là "pullback hợp lệ" — KHÔNG. Giữ tiêu chí cứng. |

---

## 12. Ghi chú bổ sung

- Rule này **chưa bắc buộc** vào lệnh — setup vẫn có thể vào tại breakout nếu không có pullback rõ
  ràng (WAITING status).
- Pullback là **tối ưu** cho ratio risk/reward tốt, nhưng không phải lựa chọn duy nhất.
- Thời gian chờ pullback quy định (20 nến) là **đề xuất**, có thể điều chỉnh theo timeframe và
  chiến lược cụ thể.
- Mối quan hệ: RULE_004 + RULE_005 (Volume) + xác nhận phản ứng = điều kiện vào lệnh.

