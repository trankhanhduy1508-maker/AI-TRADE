# RULE_005_VOLUME — Đánh giá Xác nhận Volume

## 1. Tên Rule
**RULE_005_VOLUME**: Đánh giá khối lượng giao dịch xác nhận breakout/phản ứng.

---

## 2. Mục đích
Volume là chỉ báo **xác nhận** độ tin cậy của breakout. Breakout kèm volume cao → thật. Breakout
với volume thấp → khả năng false break cao.

---

## 3. Input
- **Volume của nến breakout** (hoặc nến phản ứng đầu tiên).
- **Volume trung bình gần đây** (SMA 20 nến, theo `knowledge/VOLUME_RESEARCH.md`).
- **Volume của các nến pullback** (xem RULE_004).

---

## 4. Output

| Kết quả | Ý nghĩa | Điểm |
|---|---|---|
| **VOLUME_STRONG** | Volume breakout > 150% SMA 20 | 10 |
| **VOLUME_NORMAL** | Volume 100-150% SMA 20 | 7 |
| **VOLUME_WEAK** | Volume 80-100% SMA 20 | 5 |
| **VOLUME_POOR** | Volume < 80% SMA 20 | 0 → cảnh báo false break |

---

## 5. Điều kiện

### 5.1 VOLUME_STRONG
- Volume breakout > 150% SMA20.
- Coi là xác nhận mạnh → độ tin cậy breakout cao.
- Điểm: 10 (max).

### 5.2 VOLUME_NORMAL
- Volume 100-150% SMA20 → bình thường.
- Điểm: 7.

### 5.3 VOLUME_WEAK
- Volume 80-100% SMA20 → hơi yếu.
- Điểm: 5.

### 5.4 VOLUME_POOR
- Volume < 80% SMA20 → quá thấp.
- Đây là cảnh báo false break cao → có thể trigger REJECT ở Decision Flow Bước 4.
- Điểm: 0.

---

## 6. Ngoại lệ

| Tình huống | Xử lý |
|---|---|
| SMA20 bị skew bởi 1 nến khối lượng bất thường | Dùng SMA50 hoặc median volume thay thế |
| Thị trường phi tập trung (crypto nhiều sàn) | Ghi rõ nguồn dữ liệu volume, vì SMA khác nhau giữa sàn |
| Volume giảm dần theo xu hướng | Cơn lực trượt dần, cảnh báo xu hướng có thể suy yếu → kết hợp RULE_001 để verify trend |

---

## 7. Ví dụ

**Ví dụ VOLUME_STRONG:**
```
SMA20 volume = 1M
Nến breakout volume = 1.8M (180% SMA20)
→ VOLUME_STRONG → Điểm = 10
```

**Ví dụ VOLUME_POOR:**
```
SMA20 volume = 1M
Nến breakout volume = 0.7M (70% SMA20)
→ VOLUME_POOR → Cảnh báo false break
```

---

## 8. Dữ liệu cần
- **Volume của từng nến**.
- **SMA20 volume** (tính từ 20 nến trước).

---

## 9. Khả năng Backtest
✅ **Backtest được dễ dàng** — volume là số cụ thể, tính toán mộc mạc.

---

## 10. Độ khách quan
✅ **Rất khách quan — 95%** — tính toán SMA20 là tự động.

---

## 11. Điểm dễ gây Overfitting
⚠️ **Rủi ro: Thấp-trung bình**

| Vấn đề | Cách tránh |
|---|---|
| **Thay đổi SMA period (20 → 10 → 50)** | Chốt SMA20 làm standard, không điều chỉnh sau. |
| **Thay đổi ngưỡng 150%/100%/80%** | Chốt qua backtest, không điều chỉnh tuỳ ý. |

---

## 12. Ghi chú bổ sung
- Volume là **xác nhận**, không phải **quyết định** — breakout yếu về volume vẫn có thể là setup
  nếu các rule khác mạnh.
- Phân biệt: Volume **xác nhận breakout** vs Volume **trong pullback** (phải giảm).

