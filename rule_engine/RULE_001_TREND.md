# RULE_001_TREND — Xác định Xu hướng Hợp lệ

## 1. Tên Rule
**RULE_001_TREND**: Xác định xu hướng hợp lệ qua cấu trúc Higher High/Higher Low (tăng) hoặc Lower
High/Lower Low (giảm).

---

## 2. Mục đích
Đây là rule **bắt buộc đầu tiên** trong Decision Flow. Xác định liệu thị trường hiện tại có một xu
hướng rõ ràng hay không, từ đó quyết định có tiếp tục phân tích hay loại bỏ setup.

---

## 3. Input

- **Cấu trúc giá lịch sử**: Dữ liệu nến/bar gần đây (tối thiểu 20-50 nến để xác định xu hướng).
- **Swing High/Low đã xác định** (từ định nghĩa trong `knowledge/PRICE_ACTION_AND_MARKET_STRUCTURE.md`):
  - Swing High: Nến có high cao hơn N nến trái và N nến phải (N cụ thể tùy timeframe, ví dụ N=2).
  - Swing Low: Nến có low thấp hơn N nến trái và N nến phải.

---

## 4. Output

| Kết quả | Ý nghĩa | Hành động |
|---|---|---|
| **TREND_UP** | Xu hướng tăng được xác nhận (chuỗi HH + HL) | Tiếp tục Decision Flow |
| **TREND_DOWN** | Xu hướng giảm được xác nhận (chuỗi LH + LL) | Tiếp tục Decision Flow |
| **TREND_NEUTRAL** | Không có xu hướng rõ ràng (đi ngang, cấu trúc không rõ) | REJECT cứng |

---

## 5. Điều kiện

### 5.1 Điều kiện vào TREND_UP

**Bắt buộc:**
- Tối thiểu **2 cặp (Higher High + Higher Low) liên tiếp** trong 20-50 nến gần nhất.
  - Cặp 1: Swing High 1 > Swing High 0; Swing Low 1 > Swing Low 0.
  - Cặp 2: Swing High 2 > Swing High 1; Swing Low 2 > Swing Low 1.
- Các cặp này phải **liên tiếp không bị gián đoạn** bởi LH hoặc LL ngược chiều.

**Tính điểm:**
- 3+ cặp HH/HL rõ ràng, khoảng cách giữa các swing hợp lý → **25 điểm (max)**.
- 2 cặp HH/HL rõ ràng → **20-22 điểm**.
- 2 cặp nhưng yếu (khoảng cách nhỏ, hơi mập mờ) → **15-18 điểm**.

### 5.2 Điều kiện vào TREND_DOWN

**Bắt buộc:**
- Tối thiểu **2 cặp (Lower High + Lower Low) liên tiếp** trong 20-50 nến gần nhất.
  - Cặp 1: Swing High 1 < Swing High 0; Swing Low 1 < Swing Low 0.
  - Cặp 2: Swing High 2 < Swing High 1; Swing Low 2 < Swing Low 1.
- Các cặp này phải **liên tiếp không bị gián đoạn** bởi HH hoặc HL ngược chiều.

**Tính điểm:**
- 3+ cặp LH/LL rõ ràng, khoảng cách giữa các swing hợp lý → **25 điểm (max)**.
- 2 cặp LH/LL rõ ràng → **20-22 điểm**.
- 2 cặp nhưng yếu (khoảng cách nhỏ, hơi mập mờ) → **15-18 điểm**.

### 5.3 Điều kiện vào TREND_NEUTRAL (Không có xu hướng)

**Trigger REJECT:**
- Không đủ 2 cặp HH/HL hoặc LH/LL.
- Cấu trúc không rõ ràng (swing high/low mập mờ, hoặc đi ngang rõ ràng).
- Thị trường vừa đảo chiều: có HH + HL rồi lại chuyển thành LH + LL, hoặc ngược lại → coi là
  **đang thử bộc lộ xu hướng mới**, chưa xác nhận → **NEUTRAL, chờ thêm xác nhận**.

---

## 6. Ngoại lệ

| Tình huống | Xử lý |
|---|---|
| Thị trường vừa đảo chiều (CHoCH xảy ra) | Chưa coi là TREND mới cho tới khi có tối thiểu 2 cặp theo hướng mới. Hiện là NEUTRAL. |
| Nến doji/indecision ở các swing high/low | Swing vẫn được xác nhận nếu có ít nhất N nến trái/phải cao/thấp hơn. Nến doji không "vô hiệu" swing. |
| Thị trường bị đình chỉ do tin tức | Nếu gap lớn bất thường sau tin tức, cần đánh giá lại cấu trúc swing high/low (có thể bị vô hiệu). Tạm thời coi TREND là NEUTRAL cho tới khi cấu trúc ổn định trở lại. |
| Xu hướng quá dài (50+ nến cùng hướng) | Vẫn coi là TREND_UP hoặc TREND_DOWN, không có giới hạn thời gian. Nhưng cần chú ý khả năng đảo chiều cao — kết hợp với RSI/EMA để cảnh báo. |

---

## 7. Ví dụ

### 7.1 Ví dụ TREND_UP

```
Dữ liệu 30 nến gần nhất:
Bar 30 (oldest): High=100, Low=95
Bar 25: High=102 (Swing High 0), Low=98 (Swing Low 0)
Bar 20: High=105 (Swing High 1 > SH0), Low=101 (Swing Low 1 > SL0) ← Cặp 1: HH + HL ✓
Bar 15: High=107 (Swing High 2 > SH1), Low=103 (Swing Low 2 > SL1) ← Cặp 2: HH + HL ✓
Bar 10: High=106 (LH, phá cấu trúc một chút)
Bar 5: High=108 (HH3 > SH2), Low=104 (HL3 > SL2) ← Cặp 3: HH + HL ✓
Bar 1 (newest): High=110, Low=105

Kết luận: TREND_UP (3 cặp HH/HL) → Điểm = 25
```

### 7.2 Ví dụ TREND_DOWN

```
Dữ liệu 30 nến:
Bar 25: High=110 (Swing High 0), Low=95 (Swing Low 0)
Bar 20: High=108 (Swing High 1 < SH0), Low=90 (Swing Low 1 < SL0) ← Cặp 1: LH + LL ✓
Bar 15: High=106 (Swing High 2 < SH1), Low=85 (Swing Low 2 < SL1) ← Cặp 2: LH + LL ✓
Bar 10: High=104 (LH3 < SH2), Low=80 (LL3 < SL2) ← Cặp 3: LH + LL ✓
Bar 1 (newest): High=103, Low=78

Kết luận: TREND_DOWN (3 cặp LH/LL) → Điểm = 25
```

### 7.3 Ví dụ TREND_NEUTRAL (đi ngang)

```
Dữ liệu 30 nến:
Bar 25: High=105, Low=95
Bar 20: High=106, Low=94
Bar 15: High=105, Low=96
Bar 10: High=107, Low=95
Bar 5: High=104, Low=97
Bar 1 (newest): High=106, Low=96

Nhận xét: Swing high/low không rõ ràng, không có 2 cặp HH/HL hoặc LH/LL liên tiếp.
→ TREND_NEUTRAL → REJECT cứng
```

---

## 8. Dữ liệu cần

- **Loại dữ liệu**: OHLCV (Open, High, Low, Close, Volume) của mỗi bar/nến.
- **Số bar lịch sử**: Tối thiểu 50 bar gần đây để xác nhận xu hướng (có thể tùy timeframe, xem
  `backtests/BACKTEST_STANDARD.md`).
- **Timeframe**: Phụ thuộc vào chiến lược (ví dụ TF_001 có thể dùng 4h, daily; TF_002 có thể dùng
  1h, 4h).
- **Độ chính xác swing high/low**: N (số nến trái/phải) phải được định nghĩa rõ trong từng
  chiến lược (ví dụ TF_001 dùng N=2, TF_002 dùng N=3).

---

## 9. Khả năng Backtest

✅ **Backtest được dễ dàng.**

- Swing high/low là định nghĩa mộc mạc (so sánh high/low của các bar), dễ lập trình.
- Có thể backtest trên dữ liệu lịch sử 1-2 năm để thống kê bao nhiêu % thị trường có xu hướng rõ
  ràng vs đi ngang.
- Không phụ thuộc vào dữ liệu real-time, chỉ cần dữ liệu OHLC lịch sử.

**Mục tiêu backtest:**
- Kiểm chứng: Khi TREND_UP/TREND_DOWN được xác nhận, xu hướng có tiếp tục? (Kỳ vọng: > 60% các
  setup sau này kiếm được lợi nhuận).
- So sánh: Xu hướng 2 cặp vs 3 cặp, cái nào cho tỷ lệ thắng cao hơn?

---

## 10. Độ khách quan

✅ **Rất khách quan — 95%+**

- Định nghĩa HH/HL/LH/LL là so sánh mộc mạc các high/low của bar — không có sắc thái chủ quan.
- Không phụ thuộc vào diễn giải hay "cảm giác" của người phân tích.
- Dễ lập trình tự động, AI có thể tính toán chính xác 100%.

---

## 11. Điểm dễ gây Overfitting

⚠️ **Rủi ro: Thấp, nhưng có thể gặp vấn đề với tham số N (số nến định swing high/low)**

| Vấn đề | Mô tả | Cách tránh |
|---|---|---|
| **Tham số N quá nhạy** | N=1 → bất kỳ high/low nào cũng là swing (quá nhạy, nhiều false signal). N=5 → swing quá khắt khe, bỏ lỡ xu hướng thực sự. | Chốt N dựa trên backtest (ví dụ N=2 hoặc 3), không tùy ý điều chỉnh sau mỗi lệnh thua. |
| **Lựa chọn lookback period** | Nếu chỉ xem 10 nến để xác nhận xu hướng vs 50 nến, kết quả khác. Tuỳ ý chọn lookback → overfit. | Định nghĩa rõ: "luôn xem 50 nến gần nhất" → không thay đổi. |
| **Thay đổi định nghĩa swing** | Ví dụ: tạo ra "semi-swing" cho phù hợp với setup muốn vào lệnh. | Định nghĩa swing trước khi phân tích setup, không sửa lại sau. |

---

## 12. Ghi chú bổ sung

- Rule này là **nền tảng** của toàn Rule Engine. Nếu fail ở đây, setup bị reject ngay, không thực
  hiện các rule tiếp theo.
- Xu hướng do **cấu trúc giá** quyết định, không phải chỉ báo (EMA, RSI). EMA dùng làm **xác nhận
  bias** thêm ở RULE_007, không quyết định xu hướng chính.
- Cần xác định rõ **timeframe** (1h, 4h, 1d, v.v.) cho mỗi chiến lược, vì xu hướng ở 1h có thể
  khác 1d.

