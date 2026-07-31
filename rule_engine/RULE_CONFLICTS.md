# RULE_CONFLICTS — Mâu thuẫn tiềm năng giữa các Rule

Tài liệu này liệt kê các **cặp rule có thể xung đột** khi phân tích một setup, cách **xử lý xung
đột**, và **thứ bậc ưu tiên** rõ ràng để không có nhập nhằng.

---

## Nguyên tắc chung

**Priority ranking (từ cao đến thấp):**
1. **Price Action/Market Structure** (RULE_001, RULE_002, RULE_003, RULE_004) — **Bắt buộc**.
2. **Risk Management** (RULE_008) — **Bắt buộc**.
3. **Volume xác nhận** (RULE_005) — **Xác nhận chính**.
4. **Indicators** (RULE_006 RSI, RULE_007 EMA, RULE_009 Liquidity) — **Xác nhận phụ**.

**Quy tắc giải quyết xung đột:** Nếu có mâu thuẫn, **priority cao thắng priority thấp**. Không bao
giờ để indicator (low priority) phủ nhận Price Action (high priority).

---

## 1. RULE_001 (Trend) vs RULE_007 (EMA Bias)

### Xung đột
- **Tình huống:** RULE_001 xác định TREND_UP (chuỗi HH/HL), nhưng RULE_007 cho thấy giá dưới EMA
  (down bias).
- **Ai đúng?**

### Giải quyết
- **Ưu tiên:** RULE_001 > RULE_007.
- **Hành động:** Coi TREND_UP là chính (từ cấu trúc giá), RULE_007 chỉ cảnh báo: "Trend UP nhưng EMA
  bias DOWN → khả năng pullback sâu, hoặc trend yếu".
- **Scoring:** Không reject, nhưng giảm điểm:
  - RULE_001: 25 (full, vì cấu trúc có thật).
  - RULE_007: 0 (EMA bias sai, giảm điểm phụ).
  - Tổng score không bị reject, chỉ thấp hơn nếu EMA bias đúng.

### Ví dụ
```
Setup UP: HH/HL rõ ràng (TREND_UP) ✓
Nhưng giá = 99, EMA50 = 100 (giá < EMA, không phù hợp)

Giải quyết: Vẫn coi TREND_UP (priority cao), nhưng ghi chú "EMA bias yếu → risk cao" →
Score cao nhất 25 + 0 + ... (các rule khác)
```

---

## 2. RULE_003 (Breakout TRUE) vs RULE_005 (Volume POOR)

### Xung đột
- **Tình huống:** Breakout rõ ràng (close vượt swing level, body > 60%), nhưng volume quá thấp
  (< 80% SMA20).
- **Bước 4 Decision Flow:** "Breakout được Volume xác nhận?" → KHÔNG.

### Giải quyết
- **Ưu tiên:** Price Action (breakout TRUE) > Volume.
- **Hành động:** Không reject cứng ngay, tuỳ mức độ volume yếu:
  - Volume < 50% SMA20 → REJECT (quá yếu, khả năng false break cao).
  - Volume 50-80% SMA20 → Giảm điểm: Breakout từ 15 → 10, Volume từ 10 → 5.
  - Volume 80-100% SMA20 → Giảm điểm nhẹ.
- **Scoring:**
  - RULE_003: 10-15 (tuỳ body quality).
  - RULE_005: 0-7 (tuỳ volume level).

### Ví dụ
```
Breakout: Close = 110.8 (> 110 swing high), Body = 65% → BREAKOUT_TRUE (15 điểm)
Volume: 0.6M (< 1M SMA20, chỉ 60% SMA20) → VOLUME_WEAK (5 điểm)

Decision Flow Bước 4: Volume không đủ, nhưng không reject hẳn (breakout thực) →
Giảm điểm Volume từ 10 → 5, setup vẫn WAIT hoặc vào với score thấp hơn.
```

---

## 3. RULE_004 (Pullback) vs RULE_003 (Breakout)

### Xung đột
- **Tình huống:** Breakout xảy ra, nhưng giá không hôi, mà tiếp tục lên. Setup có nên vào tại
  breakout hay chờ pullback?

### Giải quyết
- **Ưu tiên:** Cả hai rule không xung đột, mà **tuần tự**. Breakout xảy ra trước, Pullback sau.
- **Hành động:** Nếu pullback không xảy ra trong 20 nến:
  - Decision Flow Bước 5 → PULLBACK_WAITING (8-12 điểm).
  - Setup vẫn có thể vào tại breakout (rủi ro cao hơn nhưng điểm còn đủ).
- **Không reject vì không có pullback.**

### Ví dụ
```
Breakout: Giá vượt 110, tiếp tục lên 115 (không hôi)
Sau 20 nến: Không có pullback rõ ràng

Giải quyết: PULLBACK_WAITING → Score từ 15 → 8-12 → Có thể vào tại breakout nếu score >= 80
```

---

## 4. RULE_006 (RSI) vs RULE_003 (Breakout)

### Xung đột
- **Tình huống:** Breakout rõ ràng (body 70%, volume tốt), nhưng RSI > 80 (quá mua).
- **Nghi ngờ:** Quá mua → khả năng pullback sâu.

### Giải quyết
- **Ưu tiên:** RULE_003 (Breakout) > RULE_006 (RSI).
- **Hành động:** Không reject, giảm điểm RSI:
  - RULE_003: 15 (breakout TRUE).
  - RULE_006: 0 (RSI quá mua).
- **Ghi chú:** "RSI cảnh báo pullback sâu có thể xảy ra → risk cao".

### Ví dụ
```
Breakout: Close = 111, Body = 70%, Volume = 180% SMA → BREAKOUT_TRUE (15)
RSI: 85 (quá mua) → RSI_BEARISH (0)

Setup vẫn được phép vào, nhưng điểm RSI bị 0 → Score thấp hơn nếu cộng các rule khác.
```

---

## 5. RULE_008 (Risk) vs RULE_004 (Pullback)

### Xung đột
- **Tình huống:** Pullback hợp lệ, nhưng distance (Entry - SL) quá lớn → R/R < 1.0.
- **Vấn đề:** Setup tốt nhưng R/R xấu.

### Giải quyết
- **Ưu tiên:** RULE_008 (Risk) = **Priority bắt buộc, không thương lượng**.
- **Hành động:** REJECT cứng nếu R/R < 1.0, không có exception.
- **Không thể nói:** "Setup tốt nhưng accept R/R 0.8 vì muốn vào" → **KHÔNG ĐƯỢC**.

### Ví dụ
```
Entry = 100, SL = 95 (lỗ 5), Target = 103 (lời 3)
R/R = 3 ÷ 5 = 0.6 < 1.0 → REJECT cứng, không vào
(Có thể điều chỉnh entry hoặc target để R/R >= 1.0, nhưng không hạ tiêu chuẩn)
```

---

## 6. RULE_002 (Market Structure) vs RULE_001 (Trend)

### Xung đột
- **Tình huống:** TREND_UP được xác nhận, nhưng swing high/low hiện tại **không rõ ràng** (mập mờ,
  không có 2 cây nến trái/phải cao/thấp hơn đủ).

### Giải quyết
- **Ưu tiên:** RULE_002 = **Priority bắt buộc cùng RULE_001**.
- **Hành động:** Không thể phát hiện setup nếu swing high/low không rõ ràng → **REJECT**, chờ swing
  level rõ ràng hơn.
- **Không thể nói:** "Trend UP ok, nhưng swing low hơi mập mờ, vẫn vào được" → **KHÔNG**.

---

## 7. RULE_005 (Volume) vs RULE_009 (Liquidity)

### Xung đột (thực ra không phải xung đột, mà **bổ sung**)
- **Tình huống:** Volume cao (breakout volume > 150% SMA), nhưng spread rộng (> 5 pip), liquidity
  kém.

### Giải quyết
- **Không xung đột:** Volume cao cho biết **sự tham gia nhiều**, Liquidity kém cho biết **spread
  rộng**.
- **Hành động:** Volume STRONG (10), Liquidity POOR (0).
- **Ghi chú:** "Volume tốt, nhưng liquidity kém → có thể bị trượt giá khi vào" → chốc lại hoặc
  chọn timeframe/mã khác.

---

## 8. RULE_001 (Trend) vs RULE_004 (Pullback)

### Xung đột
- **Tình huống:** Trend UP rõ ràng (3 cặp HH/HL), nhưng pullback vừa xảy ra **phá ngược lại deep**,
  gần phá cấu trúc tăng ban đầu. Là pullback hợp lệ hay false break?

### Giải quyết
- **Ưu tiên:** RULE_004 (Pullback validation) = **Priority cao**.
- **Hành động:** Nếu pullback phá quá sâu:
  - RULE_004 → PULLBACK_FALSE_BREAK (0) → Setup invalid.
  - Mặc dù RULE_001 vẫn TREND_UP, nhưng setup bị reject (breakout bị phá hỏng).
- **Không vào lệnh, chờ cấu trúc ổn định lại.**

---

## 9. RULE_003 (Breakout) vs RULE_007 (EMA)

### Xung đột
- **Tình huống:** Breakout tài khố rõ ràng, nhưng EMA bias sai chiều (setup UP, giá < EMA).
- **Nghi ngờ:** Breakout ngược bias → risk cao.

### Giải quyết
- **Ưu tiên:** RULE_003 (Breakout TRUE) > RULE_007 (EMA).
- **Hành động:** Không reject, nhưng giảm điểm:
  - RULE_003: 15 (breakout thực).
  - RULE_007: 0 (EMA bias sai).
- **Ghi chú:** "Breakout chất lượng, nhưng EMA bias yếu → khả năng pullback/thoáng sâu".

---

## 10. RULE_008 (Risk) vs RULE_005 (Volume)

### Xung đột
- **Tình huống:** Volume xác nhận rất mạnh (volume > 200% SMA), nhưng để có R/R >= 1.5, phải đặt SL
  quá xa entry (> 3-4%).

### Giải quyết
- **Ưu tiên:** RULE_008 (Risk) = **Priority bắt buộc**.
- **Hành động:** Không được nới lỏng SL vì volume tốt:
  - Nếu SL bắt buộc > 4%, mà không chấp nhận, → **REJECT setup**.
  - Không thể nói "volume quá tốt, accept SL xa hơn" → **KHÔNG**.

---

## 11. RULE_001 (Trend) vs RULE_006 (RSI)

### Xung đột
- **Tình huống:** TREND_UP rõ ràng (4 cặp HH/HL), nhưng RSI phân kỳ âm (giá lên, RSI xuống) →
  cảnh báo đảo chiều sắp xảy ra.

### Giải quyết
- **Ưu tiên:** RULE_001 (Trend từ cấu trúc) > RULE_006 (RSI divergence).
- **Hành động:** Không reject, nhưng ghi chú:
  - RULE_001: 25 (trend rõ).
  - RULE_006: 0 (phân kỳ âm).
- **Ý kiến:** "Trend UP từ cấu trúc OK, nhưng RSI cảnh báo → có thể đảo chiều sắp → risk cao, setup
  WAITING hoặc REJECT nếu score < 80".

---

## Tóm tắt Thứ bậc Ưu tiên (mâu thuẫn)

| Thứ bậc | Rule | Mô tả |
|---|---|---|
| **1 (Bắt buộc)** | RULE_001 + RULE_002 | Trend + Structure — nền tảng |
| **2 (Bắt buộc)** | RULE_003 + RULE_004 | Breakout + Pullback — setup xảy ra |
| **3 (Bắt buộc)** | RULE_008 | Risk — không negotiate |
| **4 (Xác nhận chính)** | RULE_005 | Volume — xác nhận mạnh |
| **5 (Xác nhận phụ)** | RULE_006, RULE_007, RULE_009 | RSI, EMA, Liquidity — cảnh báo |

---

## Quy tắc cuối cùng

Khi xảy ra **bất kỳ mâu thuẫn nào**:

1. **Kiểm tra thứ bậc ưu tiên** → rule priority cao thắng.
2. **Không reject** nếu không cần thiết — giảm điểm thay.
3. **Reject cứng chỉ khi:** RULE_001 (no trend), RULE_002 (no structure), RULE_003 (no breakout),
   RULE_008 (R/R < 1.0), RULE_004 (false break).
4. **Ghi log xung đột** trong audit sau → để backtest kiểm chứng thứ bậc này có đúng không.

