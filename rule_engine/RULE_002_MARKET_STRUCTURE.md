# RULE_002_MARKET_STRUCTURE — Xác định Cấu trúc Thị trường

## 1. Tên Rule
**RULE_002_MARKET_STRUCTURE**: Xác định cấu trúc thị trường hợp lệ và hướng phá vỡ theo xu hướng chính.

---

## 2. Mục đích
Sau khi xác nhận xu hướng ở RULE_001, rule này xác định **swing high/low cụ thể** mà giá sẽ phá vỡ,
và đảm bảo setup phá vỡ theo **cùng hướng** với xu hướng chính (không giao dịch ngược xu hướng).

---

## 3. Input

- **Trend status**: TREND_UP, TREND_DOWN, hoặc TREND_NEUTRAL (từ RULE_001).
- **Swing High/Low gần nhất**: Xác định từ cấu trúc giá lịch sử.
- **Hướng phá vỡ hiện tại**: Giá đang hướng phá qua mức nào (swing high hay swing low).

---

## 4. Output

| Kết quả | Ý nghĩa | Hành động |
|---|---|---|
| **STRUCTURE_VALID_UP** | Cấu trúc hợp lệ, phá qua swing high (theo TREND_UP) | Tiếp tục Decision Flow |
| **STRUCTURE_VALID_DOWN** | Cấu trúc hợp lệ, phá qua swing low (theo TREND_DOWN) | Tiếp tục Decision Flow |
| **STRUCTURE_INVALID** | Cấu trúc không rõ hoặc setup ngược xu hướng chính | REJECT cứng |

---

## 5. Điều kiện

### 5.1 STRUCTURE_VALID_UP

**Bắt buộc:**
- TREND_UP đã được xác nhận ở RULE_001.
- Swing high gần nhất rõ ràng (hình thành từ cứu cấu HH+HL).
- Setup **hiện tại** đang phá qua swing high đó (không phá qua swing low).
- Không có CHoCH (Change of Character — phá qua swing low ngược chiều) xảy ra trước khi setup vào.

**Tính điểm:** 20 điểm.

### 5.2 STRUCTURE_VALID_DOWN

**Bắt buộc:**
- TREND_DOWN đã được xác nhận ở RULE_001.
- Swing low gần nhất rõ ràng (hình thành từ cấu trúc LH+LL).
- Setup **hiện tại** đang phá qua swing low đó (không phá qua swing high).
- Không có CHoCH xảy ra trước khi setup vào.

**Tính điểm:** 20 điểm.

### 5.3 STRUCTURE_INVALID

**Trigger REJECT:**
- TREND_NEUTRAL (không có xu hướng).
- Setup ngược chiều TREND_UP (phá swing low khi TREND_UP) → cấm tuyệt đối.
- Setup ngược chiều TREND_DOWN (phá swing high khi TREND_DOWN) → cấm tuyệt đối.
- CHoCH đã xảy ra, chưa có BOS xác nhận hướng mới → REJECT tạm thời (không có cấu trúc xác định).

---

## 6. Ngoại lệ

| Tình huống | Xử lý |
|---|---|
| CHoCH vừa xảy ra, giá đang kiểm tra xu hướng mới | Tạm dùng RULE_002 để xác định swing của **hướng mới** (nếu có), chưa vào lệnh cho tới khi RULE_001 xác nhận xu hướng mới với 2+ cặp. |
| Swing high/low bị phá liên tục (market accelerate) | Vẫn coi là STRUCTURE_VALID miễn là xu hướng từ RULE_001 vẫn rõ ràng, update swing level mới. |
| Multiple swing high/low (nhiều mức tương tương) | Chọn swing **gần nhất** có ý nghĩa (được hình thành từ đúng cấu trúc HH/HL hoặc LH/LL), không chọn tùy ý. |

---

## 7. Ví dụ

### 7.1 STRUCTURE_VALID_UP

```
RULE_001 kết luận: TREND_UP (có 2+ cặp HH/HL)
Swing High gần nhất: 110 (tại bar 15)
Swing Low gần nhất: 100 (tại bar 20)

Hiện tại (bar 1): Giá = 111, Close = 111 > 110 (Swing High)
Hướng phá qua: Swing High (theo TREND_UP) ✓

→ STRUCTURE_VALID_UP → Điểm = 20
```

### 7.2 STRUCTURE_INVALID (ngược xu hướng)

```
RULE_001 kết luận: TREND_UP
Swing High: 110, Swing Low: 100

Hiện tại (bar 1): Giá = 99, Close = 99 < 100 (Swing Low)
Hướng phá qua: Swing Low (ngược TREND_UP) ✗ → Cấm vào lệnh

→ STRUCTURE_INVALID → REJECT cứng
```

---

## 8. Dữ liệu cần

- **Swing high/low gần nhất** (được tính từ RULE_001).
- **Giá hiện tại** (close price, có thể check high của nến hiện tại).
- **Định nghĩa N** (số nến để xác định swing high/low, từ từng chiến lược).

---

## 9. Khả năng Backtest

✅ **Backtest được dễ dàng.**

- Kiểm chứng: Khi phá qua swing high (TREND_UP), tỷ lệ lời bao nhiêu %?
- So sánh: Phá swing gần nhất vs swing xa hơn, cái nào cho kết quả tốt hơn?
- Tính toán tự động, không cần diễn giải.

---

## 10. Độ khách quan

✅ **Rất khách quan — 95%+**

- Swing high/low được định nghĩa mộc mạc.
- So sánh giá vs swing level là phép tính chính xác tuyệt đối.
- Nguyên tắc "không giao dịch ngược xu hướng" là luật cứng, không có ngoại lệ.

---

## 11. Điểm dễ gây Overfitting

⚠️ **Rủi ro: Thấp**

| Vấn đề | Cách tránh |
|---|---|
| **Chọn swing level tùy ý** | Luôn dùng swing **gần nhất** được xác nhận từ cấu trúc, không chọn swing xa hơn để "vào được setup". |
| **Thay đổi định nghĩa "gần nhất"** | Định nghĩa rõ: swing gần nhất = swing level cuối cùng được hình thành theo cấu trúc HH/HL hoặc LH/LL, không thay đổi. |

---

## 12. Ghi chú bổ sung

- Rule này **bắc buộc** "không giao dịch ngược xu hướng" — đây là nguyên tắc từ `DECISIONS.md`.
- RULE_002 + RULE_001 tạo thành **cơ sở** để phát hiện setup. Không có cả hai, không thể tiếp tục.
- Khi xu hướng đảo chiều (CHoCH xảy ra), tạm thời coi STRUCTURE_INVALID cho tới khi RULE_001 xác
  nhận xu hướng mới đủ mạnh.

