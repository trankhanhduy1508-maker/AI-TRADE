# Monte Carlo Simulation Guide

> **Hướng dẫn thực hiện Monte Carlo Simulation cho backtest.**  
> Mục đích: Kiểm tra độ bền vững (robustness) của chiến lược bằng cách đảo xáo thứ tự giao dịch.

---

## 1. Định nghĩa Monte Carlo Simulation (MCS)

### 1.1 Khái niệm

**Monte Carlo Simulation** trong backtest là phương pháp:
1. Lấy tất cả **trade histories** từ backtest (entry/exit, PnL từng trade)
2. **Đảo xáo lại thứ tự** các trade (shuffle)
3. **Recalculate** equity curve, drawdown từ chuỗi trade mới
4. **Lặp lại** N lần (ví dụ 1000 lần)
5. **Phân tích** độ dao động của kết quả (Max DD, Equity...)

### 1.2 Ví dụ minh họa

```
Original trade sequence (từ backtest):
  Trade 1: +50 pips
  Trade 2: -20 pips
  Trade 3: +80 pips
  Trade 4: -30 pips
  Trade 5: +40 pips

Equity curve: 0 → 50 → 30 → 110 → 80 → 120
Max DD: 80 - 30 = 50 (từ peak 80 xuống trough 30)

Monte Carlo Shuffle 1:
  Trade 3: +80 pips
  Trade 1: +50 pips
  Trade 5: +40 pips
  Trade 2: -20 pips
  Trade 4: -30 pips

Equity curve: 0 → 80 → 130 → 170 → 150 → 120
Max DD: 170 - 120 = 50 (từ peak 170 xuống trough 120)

Monte Carlo Shuffle 2:
  Trade 2: -20 pips
  Trade 4: -30 pips
  Trade 1: +50 pips
  Trade 3: +80 pips
  Trade 5: +40 pips

Equity curve: 0 → -20 → -50 → 0 → 80 → 120
Max DD: 0 - (-50) = 50 (từ peak 0 xuống trough -50)

(Lặp lại 1000 lần → Phân tích min/max/avg Max DD)
```

---

## 2. Tại sao cần Monte Carlo Simulation

### 2.1 Vấn đề: Sequence Dependency

```
Vấn đề:
- Backtest dựa trên thứ tự trade cụ thể (như dữ liệu lịch sử)
- Kết quả backtest (drawdown, equity...) **phụ thuộc** vào thứ tự trade
- Nếu chỉ test 1 sequence → có thể là may mắn (lucky sequence)

Ví dụ:
- Sequence A: Loss, Loss, Gain, Gain → Max DD lớn (thua trước rồi thắng)
- Sequence B: Gain, Gain, Loss, Loss → Max DD nhỏ (thắng trước rồi thua)
- Tất cả có cùng: Net Profit, Win Rate, Expectancy
- Nhưng Max DD khác nhau!
→ Kết quả backtest có phụ thuộc vào "may mắn" của sequence
```

### 2.2 Monte Carlo kiểm tra robustness

```
Lợi ích:
- Test chiến lược trên NHIỀU sequence khác nhau (1000 lần)
- Xem Max DD có thay đổi nhiều khi thứ tự thay đổi không
- Nếu Max DD ổn định dù sequence thay đổi → chiến lược "robust"
- Nếu Max DD quá dao động → cần cảnh báo
```

### 2.3 Giả định của MCS

**Giả định quan trọng:**
- Các trade **độc lập với nhau** (không có correlation)
- Thứ tự trade **không ảnh hưởng** đến xác suất thắng/thua tiếp theo
- Future trades **cùng PnL distribution** như past trades

**Giới hạn (quan trọng đọc):**
- Thực tế trong trading: trades có correlation (ví dụ: trend market, 1 setup thường theo sau setup khác)
- MCS bỏ qua correlation này → kết quả có thể lạc quan
- **MCS không phải perfect**, nhưng vẫn hữu ích để kiểm tra downside risk

---

## 3. Quy trình thực hiện MCS

### 3.1 Bước 1: Lấy Trade History từ Backtest

```
Từ backtest TF_001 trên EURUSD 4H (2015-2020):
  Trade 1: Entry 1.1000, Exit 1.1050, PnL = +50 pips
  Trade 2: Entry 1.1070, Exit 1.1050, PnL = -20 pips
  Trade 3: Entry 1.1100, Exit 1.1180, PnL = +80 pips
  ...
  Trade 150: Entry 1.1200, Exit 1.1180, PnL = -15 pips

Tổng: 150 trades, Net Profit = +250 pips
```

### 3.2 Bước 2: Xác định số lần simulation (N)

```
Khuyến cáo:
  N = 1000 (tiêu chuẩn)
  N = 100 (quick check, rough)
  N = 10000 (rất chi tiết, nhưng chậm)

Chọn N = 1000: Cân bằng độ chính xác vs thời gian tính toán
```

### 3.3 Bước 3: Shuffle trade sequence (lặp N lần)

**Pseudo-code:**

```python
for i in range(1000):
    shuffled_trades = random.shuffle(trades)
    equity = [0]
    for trade in shuffled_trades:
        equity.append(equity[-1] + trade.PnL)
    
    max_dd_i = calculate_max_dd(equity)
    results.append({
        'simulation': i,
        'equity_final': equity[-1],
        'max_dd': max_dd_i,
        'drawdown_end': equity[-1]  # nếu còn lỗ ở cuối
    })
```

**Lặp N=1000 lần:**
- Lần 1: Shuffle 150 trades → tính Max DD
- Lần 2: Shuffle 150 trades → tính Max DD
- ...
- Lần 1000: Shuffle 150 trades → tính Max DD

### 3.4 Bước 4: Phân tích kết quả MCS

**Kết quả sau 1000 simulations:**

```
Original (từ backtest): Max DD = 18%

MCS Results (1000 simulations):
  Min Max DD: 12%
  Max Max DD: 35%
  Avg Max DD: 22%
  Std Dev: 5.3%
  
  Percentile 5%: 14%
  Percentile 25%: 18%
  Percentile 50% (median): 21%
  Percentile 75%: 26%
  Percentile 95%: 32%
```

---

## 4. Cách diễn giải kết quả MCS

### 4.1 Kịch bản A: MCS Good (Ổn định, Robust)

```
Original backtest Max DD: 18%

MCS Results:
  Min: 15%, Max: 23%, Avg: 18.5%, Std Dev: 2.1%
  Range: 15-23 (8 pips)

Diễn giải:
✓ Max DD ổn định (không dao động quá lớn)
✓ MCS Avg ≈ Original (18.5 vs 18)
✓ Std Dev thấp (2.1%)
✓ Worst case (23%) chỉ gấp 1.3x original
→ Chiến lược ROBUST, có thể tin kết quả backtest
```

### 4.2 Kịch bản B: MCS Warning (Dao động lớn)

```
Original backtest Max DD: 18%

MCS Results:
  Min: 8%, Max: 42%, Avg: 25%, Std Dev: 10%
  Range: 8-42 (34 pips)

Diễn giải:
⚠️ Max DD dao động rất lớn (từ 8% tới 42%)
⚠️ MCS Avg >> Original (25% vs 18%)
⚠️ Std Dev cao (10%)
⚠️ Worst case (42%) gấp 2.3x original
→ Chiến lược CÓ RISK, cần cảnh báo:
   - Backtest result có thể lạc quan (lucky sequence)
   - Worst case Max DD có thể 42% (không 18%)
   - Cân nhắc kỹ trước khi dùng thực tế
```

### 4.3 Kịch bản C: MCS Bad (Tệ hơn dự kiến)

```
Original backtest Max DD: 18%, Net Profit: +250 pips

MCS Results:
  Min Max DD: 20%, Max Max DD: 50%
  Avg Max DD: 35%
  Worst case (95 percentile): 48%
  
  Equity at end (1000 sims):
    Min: -100 pips (!)
    Avg: +200 pips
    Max: +500 pips

Diễn giải:
🚫 MCS Worst case Max DD (50%) >> Original (18%)
🚫 Trong 1000 simulations, có 50 lần Max DD > 40%
🚫 Có scenarios net profit = -100 pips (loss!)
→ Chiến lược KHÔNG SAFE, cần thiết kế lại:
   - Rủi ro thực tế cao hơn dự kiến gấp 3x
   - Không nên dùng thực tế
   - Có dấu hiệu chiến lược phụ thuộc vào sequence cụ thể
```

---

## 5. Các chỉ số MCS quan trọng

### 5.1 Max Drawdown Statistics

| Chỉ số | Công thức | Ý nghĩa |
|---|---|---|
| **MCS Avg Max DD** | Trung bình Max DD từ 1000 simulations | Dự kiến rủi ro trung bình |
| **MCS P95 Max DD** | Percentile 95 của Max DD | Worst case (1/20 scenarios) |
| **MCS P99 Max DD** | Percentile 99 của Max DD | Extreme case (1/100 scenarios) |
| **MCS Range** | Max - Min Max DD | Độ dao động |
| **MCS Std Dev** | Độ lệch chuẩn của Max DD | Tính ổn định |

### 5.2 Equity Statistics

```
Equity at end after 1000 simulations:
  Original net profit: +250 pips
  
  MCS results:
    Min equity: -50 pips (worst case sequence)
    Avg equity: +240 pips
    Max equity: +480 pips
    Std Dev: ±100 pips

Diễn giải:
- Avg ≈ Original (240 vs 250) ✓
- Worst case = -50 (có scenario thua lỗ) ⚠️
- Trong 1000 sim, có % nào thua lỗ? Nếu > 5%, cảnh báo
```

---

## 6. Quy tắc quyết định dựa trên MCS

| Kết quả MCS | Đánh giá | Khuyến cáo |
|---|---|---|
| **MCS Avg ≈ Original ± 10%** | ✅ Ổn định | Tin backtest, có thể dùng |
| **MCS Avg = Original ± 10-25%** | ⚠️ Caution | Backtest có khả năng lạc quan, monitor |
| **MCS Avg >> Original (> 25%)** | 🚫 High Risk | Thiết kế lại, rủi ro cao |
| **MCS P95 > 2× Original Max DD** | 🚫 Dangerous | Worst case quá xấu, không nên dùng |
| **MCS có scenario equity âm** | 🚫 Failure | Có cơ hội thua lỗ, không an toàn |

---

## 7. Giới hạn của Monte Carlo Simulation

### 7.1 Giả định độc lập (Independence Assumption)

```
Giả định MCS: Các trade độc lập, thứ tự không ảnh hưởng xác suất

Thực tế trong trading:
- Loss streak có thể dẫn tới loss tiếp theo (correlation dương)
- Breakout trend thường theo sau breakout khác
- Nhân vật lực của trend làm PnL trade có correlation âm (reversion)

→ MCS bỏ qua correlation này, có thể lạc quan
```

### 7.2 Dữ liệu lịch sử ≠ Tương lai

```
MCS dùng PnL distribution từ dữ liệu lịch sử
- Nếu tương lai có market regime change (ví dụ: từ trending → ranging)
- Distribution PnL sẽ khác
- MCS kết quả không còn áp dụng được

→ MCS chỉ mô phỏng based on quá khứ, không dự đoán tương lai
```

### 7.3 Không kiểm tra look-ahead bias

```
MCS không kiểm tra:
- Có look-ahead bias trong backtest không
- Có overfitting không
- Các trades có legit không

→ MCS là kiểm chứng **bổ sung**, không phải thay thế
   Walk Forward Analysis / Out-of-sample testing
```

---

## 8. Ví dụ thực tế: TF_001 Monte Carlo

### 8.1 Backtest kết quả

```
Strategy: TF_001_BREAKOUT_PULLBACK
Market: EURUSD 4H, 2019-2020 (out-of-sample)

Trades: 95 trades
Win Rate: 52%
Net Profit: +320 pips
Expectancy: +3.4 pips/trade
Max Drawdown: 16%
Consecutive Losses: 5
```

### 8.2 Chạy MCS (N=1000)

```
Monte Carlo: Shuffle 95 trades, lặp 1000 lần

Kết quả:
  Original Max DD: 16%
  MCS Min Max DD: 12%
  MCS Max Max DD: 24%
  MCS Avg Max DD: 17.2%
  MCS Std Dev: 3.1%
  MCS P95 Max DD: 22%
  
  Equity at end:
    Min: -20 pips
    Avg: +315 pips (≈ Original 320)
    Max: +650 pips
    Std Dev: ±95 pips
```

### 8.3 Diễn giải

```
✓ MCS Avg Max DD (17.2%) ≈ Original (16%) → Ổn định
✓ MCS Std Dev = 3.1% → Biến động nhỏ
✓ MCS P95 Max DD = 22% (chỉ gấp 1.38x original) → Chấp nhận được
✓ MCS Avg Equity ≈ Original → Profit không thay đổi
✓ Chỉ 1% scenario equity âm (acceptable risk)

Kết luận: TF_001 ROBUST, Max DD backtest (16%) là ước lượng hợp lý
```

---

## 9. So sánh MCS với các phương pháp kiểm chứng khác

| Phương pháp | Mục đích | Ưu điểm | Nhược điểm |
|---|---|---|---|
| **In-sample backtest** | Xác nhận ý tưởng | Nhanh | Overfitting risk cao |
| **Out-of-sample** | Xác nhận không overfitting | Tốt | Chỉ 1 sequence |
| **Walk Forward** | Kiểm tra stability optimize | Gần với thực tế | Phức tạp, chậm |
| **Monte Carlo** | Kiểm tra robustness, worst case | Xem rủi ro downside | Giả định độc lập, chậm |
| **Paper Trade** | Kiểm tra ngoài đời thực | Thực tế nhất | Lâu (1-3 tháng) |

**Khuyến cáo:** Kết hợp tất cả để có độ tin cậy cao.

---

## 10. Lỗi thường gặp khi làm MCS

| Lỗi | Mô tả | Cách phòng tránh |
|---|---|---|
| **Shuffle sai logic** | Chỉ shuffle timestamp, không shuffle PnL | Shuffle (trade_idx, PnL) pair |
| **Quên recalculate equity** | Chỉ shuffle, không tính equity curve mới | Sau shuffle, tính equity + drawdown |
| **N quá nhỏ** | N = 10, 50 → kết quả sơ sài | Dùng N >= 1000 |
| **Confuse original vs shuffle** | Lẫn original sequence vào shuffle results | Tách riêng original vs MCS |
| **Ignore worst case** | Chỉ xem Avg, bỏ qua P95/P99 | Xem cả Avg, P95, P99 |

---

## 11. Tham chiếu

- `BACKTEST_ENGINE.md` — Data flow, Trade Logger
- `backtests/KPI_STANDARD.md` — Max Drawdown định nghĩa
- `backtests/WALK_FORWARD_GUIDE.md` — Kiểm chứng bổ sung (Walk Forward)
- `backtests/BACKTEST_CHECKLIST.md` — QA checklist trước khi tin kết quả
