# RULE_010_EXIT — Quy tắc Thoát Lệnh

## 1. Tên Rule
**RULE_010_EXIT**: Xác định khi nào thoát lệnh (dừng lỗ, chốt lời, dời stop loss).

---

## 2. Mục đích
Khác với các rule 001-009 (xác định **vào lệnh**), rule này xác định **thoát lệnh** trong quá trình
giữ lệnh. Đây là quy tắc **quản lý lệnh**, không phải phát hiện setup.

---

## 3. Input
- **Entry price** (giá vào lệnh).
- **Stop loss level** (định sẵn từ chiến lược).
- **Lợi nhuận/lỗ hiện tại** (P&L).
- **Cấu trúc giá sau vào lệnh** (có xu hướng tiếp tục, đảo chiều, hay đi ngang).
- **Tín hiệu thoát** từ `strategies/TF_001` hay `strategies/TF_002`.

---

## 4. Output

| Kết quả | Ý nghĩa | Hành động |
|---|---|---|
| **EXIT_STOP_LOSS_HIT** | Giá chạm/vượt SL → bị kill | Thoát ngay |
| **EXIT_FALSE_BREAK** | Breakout bị phá ngược lại → false break | Thoát sớm (bảo tồn capital) |
| **EXIT_STRUCTURE_BREAK** | Cấu trúc bị phá (đảo chiều), không còn xu hướng | Thoát hoặc dời SL |
| **TRAIL_STOP_LOSS** | Xu hướng tiếp tục → dời SL theo structure mới | Không thoát, chỉ dời SL |
| **HOLD** | Xu hướng vẫn mạnh, chưa có signal thoát | Giữ lệnh |
| **TAKE_PROFIT** | Giá chạm profit target hoặc thoát từng phần | Chốt lời |

---

## 5. Điều kiện

### 5.1 EXIT_STOP_LOSS_HIT
- Giá **close dưới/trên** SL level (tuỳ long/short).
- **Hành động:** Thoát ngay, không chờ.
- **Ưu tiên:** Cao nhất — SL luôn được thực thi trước.

### 5.2 EXIT_FALSE_BREAK
- Giá phá qua swing level (breakout xảy ra) → nhưng sau 5-20 nến, giá quay lại sâu bên trong vùng
  cũ.
- Close phá hỏng cấu trúc breakout → coi là false break.
- **Hành động:** Thoát toàn bộ hoặc 50% (tuỳ strategy định).
- **Ưu tiên:** Cao — tín hiệu ngược lại rõ ràng.

### 5.3 EXIT_STRUCTURE_BREAK
- Giá hình thành **CHoCH (Change of Character)** ngược hướng lệnh → xu hướng đang đảo chiều.
- Không còn xu hướng ban đầu.
- **Hành động:** Thoát hoặc dời SL tới điểm an toàn mới (breakeven).
- **Ưu tiên:** Trung-cao.

### 5.4 TRAIL_STOP_LOSS
- Xu hướng vẫn tiếp tục theo lệnh → hình thành new swing low (setup LONG) hay swing high (setup
  SHORT).
- **Hành động:** Dời SL tới điểm thấp/cao mới của nhịp pullback hoặc breakout tiếp theo.
- **Quy tắc dời:** SL luôn dời **cùng hướng với lợi nhuận**, không được dời lại gần entry hơn.
- **Ưu tiên:** Trung — để lợi chạy, bảo vệ lợi nhuận tích lũy.

### 5.5 HOLD
- Xu hướng vẫn mạnh, không có signal thoát → giữ lệnh, chờ signal tiếp theo.
- **Hành động:** Không thay đổi SL (trừ trailing), theo dõi.

### 5.6 TAKE_PROFIT
- Giá chạm profit target được định sẵn (ví dụ ATR x 2).
- Hoặc: Chốt từng phần (ví dụ: 50% ở target 1, 25% ở target 2).
- **Hành động:** Chốt lời theo plan.

---

## 6. Ngoại lệ

| Tình huống | Xử lý |
|---|---|
| Tin tức bất thường gây gap | Nếu gap qua SL, vẫn exit (không thể tránh gap). Ghi log vào `research/FAILURE_CASES.md` |
| SL quá gần entry (no room to work) | Có thể thoát sớm nếu cấu trúc không phát triển trong 5-10 nến (không chờ SL) |
| Multiple SL (Chandelier Stop) | Nếu dùng SL động theo ATR, cập nhật mỗi nến theo công thức, không tùy ý |

---

## 7. Ví dụ

**Ví dụ 1: TRAIL_STOP_LOSS (Setup LONG)**
```
Entry = 100, SL = 98
Nến 1-3: Giá lên 102 (lợi 2), swing low hình thành tại 101
Nến 4-5: Giá lên 104, swing low mới tại 102
→ Dời SL từ 98 → 102 (trailing) → Giữ lệnh
```

**Ví dụ 2: EXIT_FALSE_BREAK**
```
Entry breakout = 110, SL = 108
Nến 1: Giá lên 111 (breakout)
Nến 2-5: Giá hôi xuống, close = 108.5 (close dưới entry)
Close phá hỏng breakout → FALSE BREAK
→ EXIT ngay, chốt loss = 1.5
```

**Ví dụ 3: EXIT_STRUCTURE_BREAK (Setup LONG)**
```
Entry = 100, Trend UP (HH/HL), SL = 98
Nến 5: Giá hình thành Lower High (phá xu hướng) → CHoCH
→ Cấu trúc đảo chiều
→ EXIT hoặc dời SL tới breakeven (100) để bảo vệ
```

---

## 8. Dữ liệu cần
- **Entry price, SL level, Profit target** (định sẵn).
- **Real-time price** (hoặc bar data nếu backtest).
- **Cấu trúc giá sau vào lệnh** (swing high/low mới, CHoCH).
- **P&L tích lũy** (lợi nhuận/lỗ).

---

## 9. Khả năng Backtest
✅ **Backtest được**, nhưng cần dữ liệu intra-bar:
- Nếu chỉ có OHLC, phải giả định SL chạm khi high >= SL (không biết giờ chính xác).
- Nếu có tick data, chính xác hơn.

---

## 10. Độ khách quan
✅ **Khách quan — 90%**
- SL chạm là mộc mạc.
- FALSE_BREAK có phần chủ quan (định nghĩa "phá hỏng cấu trúc" bao nhiêu %).

---

## 11. Điểm dễ gây Overfitting
⚠️ **Rủi ro: Cao** — Trailing SL và False Break cần tham số cụ thể.

| Vấn đề | Cách tránh |
|---|---|
| **Tham số trailing (bao nhiêu % hoặc ATR multiplier)** | Chốt từ backtest, không điều chỉnh tuỳ lệnh |
| **False Break threshold (phá bao nhiêu % cấu trúc)** | Chốt rõ: ví dụ "close dưới 50% breakout distance" |
| **Chốt lời từng phần** | Nếu dùng, chốt tỷ lệ % từ trước, không tuỳ ý |

---

## 12. Ghi chú bổ sung
- **SL là tuyệt đối** — không được di chuyển gần entry hơn, không được bỏ qua.
- **Exit không phải vào lệnh** — rule này áp dụng **sau** khi đã vào lệnh.
- **Trailing SL:** Dời theo structure mới (swing low/high), không phải ngẫu nhiên.
- **Mối quan hệ:** RULE_010 kết hợp với `strategies/TF_001` và `TF_002` để quy định exit cụ thể.

