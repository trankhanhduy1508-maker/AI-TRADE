# KPI Standard — Định nghĩa và Giải thích Các Chỉ số Hiệu suất

> **Tài liệu định nghĩa tất cả Key Performance Indicators (KPI) cho backtest.**  
> Mỗi KPI có: công thức (nếu đơn giản), ý nghĩa thực tế, cảnh báo khi sử dụng độc lập.

---

## Quy tắc Gold: Không tin 1 KPI một mình

**Nguyên tắc bắt buộc:** Xem tất cả KPI cùng lúc, đặc biệt:
- Win Rate cao + Expectancy âm = **thua lỗ** (lỗ lớn > lợi lợi nhỏ)
- Max Drawdown thấp + Win Rate thấp = **kém khả năng** (ít cơ hội, rủi ro cao)
- Sharpe Ratio cao + số lệnh < 30 = **quá ít sample** (không đủ thống kê)

---

## I. Chỉ số Profit & Loss (Lợi tức & Lỗ)

### 1.1 Net Profit (Lợi nhuận ròng)

**Công thức:**
```
Net Profit = Tổng lợi / thua từ tất cả trades
           = Sum(PnL_trade) cho tất cả trade đã đóng
           = (Gross Profit) - (Gross Loss)
```

**Ví dụ:**
```
Trade 1: +50 USD
Trade 2: -30 USD
Trade 3: +70 USD
Trade 4: -20 USD

Net Profit = 50 - 30 + 70 - 20 = 70 USD
```

**Ý nghĩa thực tế:**
- > 0: Chiến lược có lợi (tổng)
- = 0: Hòa vốn (không lợi, không lỗ)
- < 0: Chiến lược thua lỗ (tổng)

**Cảnh báo:**
- Net Profit dương không có nghĩa chiến lược "tốt" nếu không xem Max Drawdown, Win Rate.
- Ví dụ: Net Profit = +1000 USD nhưng Max DD = 50% (từ tài khoản 2000 USD) + số lệnh = 10 (quá ít)

---

### 1.2 Gross Profit (Tổng lợi)

**Công thức:**
```
Gross Profit = Sum(PnL_trade) cho tất cả trade có PnL > 0
```

**Ví dụ:** Trade thắng (50, 70) → Gross Profit = 120 USD

**Ý nghĩa thực tế:**
- Tổng lợi tức từ các trade thắng, không trừ lỗ.
- So sánh với Gross Loss để xem "chiều dài lợi" vs "chiều dài lỗ".

---

### 1.3 Gross Loss (Tổng lỗ)

**Công thức:**
```
Gross Loss = Sum(|PnL_trade|) cho tất cả trade có PnL < 0
           = Tổng giá trị tuyệt đối của loss
```

**Ví dụ:** Trade thua (-30, -20) → Gross Loss = 50 USD

**Ý nghĩa thực tế:**
- Tổng lỗ từ các trade thua, được tính dương để so sánh.
- Gross Profit / Gross Loss = Profit Factor (xem mục 1.4).

---

### 1.4 Profit Factor (Hệ số Lợi)

**Công thức:**
```
Profit Factor = Gross Profit / Gross Loss
```

**Ví dụ:**
```
Gross Profit = 1000 USD
Gross Loss = 500 USD
Profit Factor = 1000 / 500 = 2.0
```

**Ý nghĩa thực tế:**
- **> 2.0:** Rất tốt (lợi gấp 2x lỗ)
- **1.5 - 2.0:** Tốt (lợi gấp 1.5-2x lỗ)
- **1.0 - 1.5:** Trung bình (hòa vốn hoặc lợi đôi chút)
- **< 1.0:** Thua lỗ (lỗ > lợi)

**Cảnh báo:**
- Profit Factor cao nhưng số lệnh ít: có thể chỉ là may mắn (luck).
- Ví dụ: Profit Factor = 3.0 nhưng tổng 5 trade (4 thắng +250, 1 thua -100) → quá ít để kết luận.

---

### 1.5 Expectancy (Kỳ vọng / Expected Value)

**Công thức:**
```
Expectancy = Net Profit / Số lệnh
           = Trung bình lợi/lỗ mỗi lệnh
```

**Ví dụ:**
```
Net Profit = 150 USD
Số lệnh = 100
Expectancy = 150 / 100 = 1.5 USD/trade
```

**Ý nghĩa thực tế:**
- **> 0:** Mỗi lệnh kỳ vọng kiếm được (dương bình quân)
- **= 0:** Mỗi lệnh hòa vốn bình quân
- **< 0:** Mỗi lệnh mất (thua bình quân)

**Công thức mở rộng (nếu cân nhắc Win Rate + R/R):**
```
Expectancy = (Win Rate × Avg Win) - ((1 - Win Rate) × Avg Loss)
           = Kỳ vọng toán học từ xác suất thắng/thua
```

**Ví dụ:**
```
Win Rate = 50%
Avg Win = 30 pips
Avg Loss = 20 pips

Expectancy = (0.5 × 30) - (0.5 × 20) = 15 - 10 = 5 pips/trade
```

**Cảnh báo:**
- **Win Rate cao nhưng Expectancy âm:** Thắng nhiều lần nhưng lỡ ít. Ví dụ Win Rate 70%, nhưng avg loss (50 pips) > avg win (20 pips) → Expected = (0.7 × 20) - (0.3 × 50) = 14 - 15 = **-1 pips/trade** (thua).

---

## II. Chỉ số Win Rate (Tỷ lệ Thắng)

### 2.1 Win Rate (%)

**Công thức:**
```
Win Rate = Số trade thắng / Tổng số trade
```

**Ví dụ:**
```
Trade thắng: 45
Trade thua: 55
Tổng: 100

Win Rate = 45 / 100 = 45% (hoặc 0.45)
```

**Ý nghĩa thực tế:**
- **> 50%:** Thắng nhiều hơn thua (tốt)
- **50%:** Hòa vốn về tỷ lệ
- **< 50%:** Thua nhiều hơn thắng (cần xem Avg Loss vs Avg Win)

**Cảnh báo:**
- **Win Rate 70% nhưng Avg Loss >> Avg Win:** Thua lỗ dù thắng nhiều. Ví dụ:
  - 70 trade thắng × 10 pips = 700 pips
  - 30 trade thua × 40 pips = -1200 pips
  - Net = -500 pips (thua tổng dù 70% win rate)
- **Win Rate 40% nhưng Avg Win >> Avg Loss:** Có thể lợi. Ví dụ:
  - 40 trade thắng × 50 pips = 2000 pips
  - 60 trade thua × 10 pips = -600 pips
  - Net = +1400 pips (lợi dù 40% win rate)

---

### 2.2 Average Win (Lợi bình quân)

**Công thức:**
```
Average Win = Tổng lợi / Số trade thắng
            = Gross Profit / Winning Trades
```

**Ví dụ:**
```
Gross Profit = 1000 pips
Winning Trades = 50
Average Win = 1000 / 50 = 20 pips/trade
```

**Ý nghĩa thực tế:**
- Mỗi trade thắng, bình quân kiếm được bao nhiêu.
- So sánh với Average Loss để xem Risk/Reward thực tế.

---

### 2.3 Average Loss (Lỗ bình quân)

**Công thức:**
```
Average Loss = Tổng lỗ / Số trade thua
             = Gross Loss / Losing Trades
```

**Ví dụ:**
```
Gross Loss = 500 pips
Losing Trades = 50
Average Loss = 500 / 50 = 10 pips/trade
```

**Ý nghĩa thực tế:**
- Mỗi trade thua, bình quân mất bao nhiêu.
- So sánh với Average Win để xem chiến lược "cut loss" tốt không.

---

## III. Chỉ số Risk/Reward

### 3.1 Risk/Reward Ratio (R/R Thực tế)

**Công thức:**
```
R/R = Average Win / Average Loss
    = Kỳ vọng lợi / kỳ vọng lỗ
```

**Ví dụ:**
```
Avg Win = 20 pips
Avg Loss = 10 pips
R/R = 20 / 10 = 2.0 (hoặc 1:2)
```

**Ý nghĩa thực tế:**
- **R/R = 2.0:** Thắng một lần = mất 2 lần (nếu 50% win rate, hòa vốn)
- **R/R = 1.5:** Thắng một lần = mất 1.5 lần
- **R/R = 1.0:** Thắng = thua (50% win rate → hòa vốn)
- **R/R < 1.0:** Lỗ > lợi → thua lỗ (không nên chấp nhận nếu không có > 55% win rate)

**RULE_008 trong RULE_ENGINE.md:** R/R >= 1.5 (hay 1:1.5) được coi là lý thuyết tốt.

**Cảnh báo:**
- R/R lý thuyết (được set trước) khác R/R thực tế (kết quả backtest):
  - Nếu sai lệch > 20%, có vấn đề trong setup hoặc position sizing.

---

## IV. Chỉ số Rủi ro (Drawdown)

### 4.1 Max Drawdown (Độ lỗ cực đại)

**Công thức:**
```
Max Drawdown = Peak - Trough
             = Điểm cao nhất từ lúc bắt đầu → điểm thấp nhất tiếp theo
             = Tuyệt đối (USD) hoặc Phần trăm (%)
```

**Ví dụ (tiền tệ):**
```
Peak equity: 10,000 USD (lợi nhuận tối đa tới giờ)
Trough: 8,000 USD (rớt xuống)
Max Drawdown = 10,000 - 8,000 = 2,000 USD
```

**Ví dụ (phần trăm):**
```
Peak: 10,000 USD
Trough: 8,000 USD
Max Drawdown % = (10,000 - 8,000) / 10,000 = 20%
```

**Ý nghĩa thực tế:**
- **< 10%:** Rủi ro rất thấp (rất tốt)
- **10-20%:** Rủi ro thấp đến trung bình (tốt)
- **20-30%:** Rủi ro trung bình (chấp nhận được)
- **30-50%:** Rủi ro cao (cảnh báo)
- **> 50%:** Rủi ro rất cao (không khuyên dùng)

**Cảnh báo:**
- Max Drawdown 50% = tài khoản giảm nửa → cần 100% lợi nhuận để gỡ lại 50% mất.
- Chiến lược có Expectancy +2 pips nhưng Max Drawdown 40% = không đáng rủi ro.

---

### 4.2 Relative Drawdown (Độ lỗ Tương đối)

**Công thức (phần trăm):**
```
Relative Drawdown % = (Peak - Trough) / Peak × 100
```

**Ví dụ:**
```
Peak: 10,000 USD
Trough: 8,000 USD
Relative DD % = (10,000 - 8,000) / 10,000 × 100 = 20%
```

**Ý nghĩa thực tế:**
- Cùng như Max Drawdown nhưng tính lại dạng %, dễ so sánh.
- Công thức trên chính là "Drawdown %" thường gặp.

**Khác biệt Relative vs Absolute:**
- **Absolute:** 10,000 → 8,000 = loss 2,000 USD (số tiền cụ thể)
- **Relative:** Loss 20% từ peak (con số %)

---

## V. Chỉ số Rủi ro Điều chỉnh (Risk-Adjusted Returns)

### 5.1 Sharpe Ratio

**Công thức (simplified):**
```
Sharpe = (Return - Risk-free Rate) / StdDev(Return)
       = Kỳ vọng dôi so với tài sản rủi ro thấp / Độ dao động
```

**Ví dụ (giản lược):**
```
Avg daily return: 0.5%
Std Dev of daily return: 1.2%
Risk-free rate: 0% (hoặc 2% p.a.)

Sharpe ≈ 0.5% / 1.2% = 0.42
```

**Ý nghĩa thực tế:**
- **> 1.0:** Tốt (lợi suất cao so với rủi ro)
- **0.5-1.0:** Trung bình (chấp nhận được)
- **< 0.5:** Yếu (lợi suất không xứng với rủi ro)
- **< 0:** Thua lỗ (lợi suất âm)

**Cảnh báo:**
- Sharpe Ratio cao (2.0) nhưng Max Drawdown 50% = mâu thuẫn, kiểm tra lại.
- Sharpe dùng Std Dev, chỉ nhạy cảm với volatility, không phải rủi ro khách quan (downside risk).

---

### 5.2 Sortino Ratio

**Công thức:**
```
Sortino = (Return - Risk-free Rate) / Downside Std Dev
        = Lợi suất / Độ dao động XUỐNG (chỉ tính loss days)
```

**Ví dụ:**
```
Avg daily return: 0.5%
Downside Std Dev (chỉ ngày lỗ): 0.8%
Sortino ≈ 0.5% / 0.8% = 0.625
```

**Ý nghĩa thực tế:**
- Giống Sharpe nhưng chỉ tính độ dao động của **loss** (không tính gain).
- Phản ánh "rủi ro thực sự" tốt hơn Sharpe (vì chỉ quan tâm lỗ, không quan tâm lợi).
- **> 1.0:** Tốt (lợi suất cao so với rủi ro downside)
- **< 1.0:** Yếu

**Cảnh báo:**
- Nếu Sortino >> Sharpe: chiến lược có lợi suất cao nhưng ổn định (downside thấp), rất tốt.
- Nếu Sortino << Sharpe: chiến lược ít ổn định trên phía downside (rủi ro thực tế cao).

---

### 5.3 Calmar Ratio

**Công thức:**
```
Calmar = Annual Return / Max Drawdown %
       = Lợi suất năm / Độ lỗ cực đại
```

**Ví dụ:**
```
Annual Return: 20%
Max Drawdown: 25%
Calmar = 20% / 25% = 0.8
```

**Ý nghĩa thực tế:**
- **> 1.0:** Tốt (lợi suất năm > rủi ro max)
- **0.5-1.0:** Trung bình
- **< 0.5:** Yếu (rủi ro cao so với lợi suất)

**Cảnh báo:**
- Calmar chỉ dùng Max Drawdown 1 lần, bỏ qua rủi ro trung gian.
- Ví dụ: Chiến lược A có 3 lần drawdown 20%, chiến lược B có 1 lần drawdown 20% → Calmar giống nhau, nhưng A rủi ro gấp đôi (3 lần rủi ro).

---

## VI. Chỉ số Chuỗi (Streaks)

### 6.1 Consecutive Wins (Dãy Thắng)

**Định nghĩa:** Số trade thắng liên tiếp dài nhất.

**Ví dụ:**
```
W W L W W W L L W W L
Dãy thắng dài nhất: 3 (3 trade thắng liên tiếp)
```

**Ý nghĩa thực tế:**
- Cao = chiến lược có nhiều lần "nóng" (hot streak).
- Thấp = chiến lược không có streak dài (hoặc quá may mắn nếu cao quá).

---

### 6.2 Consecutive Losses (Dãy Thua)

**Định nghĩa:** Số trade thua liên tiếp dài nhất.

**Ví dụ:**
```
W W L L L W W L L W
Dãy thua dài nhất: 3 (3 trade thua liên tiếp)
```

**Ý nghĩa thực tế:**
- Cao = chiến lược có dãy thua dài (có thể trigger drawdown lớn, hoặc kill switch trong `risk/RISK_POLICY.md`).
- Thấp = chiến lược ít có dãy thua dài (tốt).

**RISK_POLICY.md:** "Khi xảy ra chuỗi thua liên tiếp (số cụ thể chưa chốt) hoặc drawdown vượt ngưỡng → bắt buộc tạm dừng".

---

## VII. Chỉ số Phục hồi (Recovery)

### 7.1 Recovery Factor (Hệ số Phục hồi)

**Công thức:**
```
Recovery Factor = Net Profit / Max Drawdown
               = Lợi nhuận / Rủi ro cực đại
```

**Ví dụ:**
```
Net Profit = 5000 USD
Max Drawdown = 2000 USD (20%)
Recovery Factor = 5000 / 2000 = 2.5
```

**Ý nghĩa thực tế:**
- **> 2.0:** Rất tốt (lợi gấp 2x rủi ro)
- **1.0-2.0:** Tốt (lợi >= rủi ro)
- **< 1.0:** Yếu (rủi ro > lợi)

**Cảnh báo:**
- Recovery Factor cao (5.0) nhưng số lệnh 5 = quá ít để kết luận (may mắn).

---

## VIII. Chỉ số Thống kê (Statistical)

### 8.1 Trade Count (Số Lệnh)

**Định nghĩa:** Tổng số trade đã khép lại trong backtest.

**Ý nghĩa thực tế:**
- **< 30:** Quá ít, kết quả "sơ bộ", không đủ để kết luận (theo `backtests/BACKTEST_STANDARD.md`)
- **30-100:** Đủ để bước đầu kiểm chứng
- **> 100:** Rất tốt (đủ sample thống kê)

---

### 8.2 Profit / Number of Trades

**Công thức:**
```
Profit per Trade = Net Profit / Trade Count
                 = Kỳ vọng lợi mỗi trade
```

(Giống Expectancy)

---

## IX. Chỉ số Return (Lợi suất)

### 9.1 Return on Account / ROA (%)

**Công thức:**
```
ROA = (Net Profit / Starting Capital) × 100
    = Lợi suất so với vốn ban đầu
```

**Ví dụ:**
```
Starting Capital = 10,000 USD
Net Profit = 2,000 USD
ROA = (2,000 / 10,000) × 100 = 20%
```

**Ý nghĩa thực tế:**
- ROA 50% = lợi suất cao (tốt)
- ROA 5% = lợi suất thấp (cảnh báo, chỉ 0.5% per month nếu chia 100 tháng)
- ROA -50% = loss 50% (risk rất cao)

**Cảnh báo:**
- ROA cao nhưng backtest kéo dài 10 năm = lợi suất thực tế rất thấp (0.5% năm).

---

### 9.2 Annualized Return (%)

**Công thức:**
```
Annualized Return = ((Ending Capital / Starting Capital) ^ (1 / Years)) - 1
                  = CAGR (Compound Annual Growth Rate)
```

**Ví dụ:**
```
Starting Capital: 10,000 USD
Ending Capital: 14,641 USD (sau 4 năm)
Annualized Return = (14,641 / 10,000) ^ (1/4) - 1 = 0.10 = 10% per year
```

**Ý nghĩa thực tế:**
- 10% per year = tốt (S&P 500 trung bình 10%)
- 5% per year = thấp (chỉ bằng risk-free bond)
- 30% per year = rất cao (hiếm, thường là overfitting)

---

## X. Bảng Tóm tắt KPI & Cách Diễn giải

| KPI | Công thức | Ý nghĩa | Cách diễn giải |
|---|---|---|---|
| **Net Profit** | Sum(PnL) | Lợi/Lỗ tổng | > 0: Lợi |
| **Win Rate** | Win / Total | % thắng | > 50%: Tốt |
| **Expectancy** | Net Profit / Trade Count | Kỳ vọng/lệnh | > 0: Lợi bình quân |
| **Profit Factor** | Gross Profit / Gross Loss | Hệ số lợi/lỗ | > 2.0: Tốt |
| **R/R Ratio** | Avg Win / Avg Loss | Lợi vs Lỗ | > 1.5: Tốt |
| **Max Drawdown %** | (Peak - Trough) / Peak | Rủi ro cực đại | < 20%: Tốt |
| **Sharpe Ratio** | Return / Volatility | Lợi suất/rủi ro | > 1.0: Tốt |
| **Sortino Ratio** | Return / Downside Vol | Lợi suất/downside | > 1.0: Tốt |
| **Calmar Ratio** | Annual Return / Max DD | Năm/rủi ro | > 1.0: Tốt |
| **Recovery Factor** | Net Profit / Max DD | Phục hồi | > 2.0: Tốt |
| **Consecutive Losses** | Max loss streak | Dãy thua dài | Thấp: Tốt |
| **ROA %** | Net Profit / Starting Capital | Lợi suất | > 10%: Tốt (năm) |

---

## XI. Quy trình Check KPI (QA Checklist)

### Bước 1: Xem toàn bộ bảng KPI (không chỉ 1 số)

```
Expectancy: +2 pips/trade ✓ (dương)
Win Rate: 35% ✗ (thấp)
Profit Factor: 3.0 ✓ (cao)
Max Drawdown: 50% ✗ (rất cao)

Kết luận sơ bộ: Chiến lược lợi suất cao (PF=3), lỗi ít (WR=35% nhưng PF cao),
nhưng rủi ro cực kỳ cao (DD=50%), không nên dùng trực tiếp.
```

### Bước 2: Kiểm tra xung đột giữa KPI

- Nếu Expectancy > 0 nhưng Profit Factor < 1.0: → Xảy ra lỗi tính toán
- Nếu Win Rate 80% nhưng ROA = -10%: → Avg Loss rất lớn, avg win nhỏ
- Nếu Sharpe Ratio 2.0 nhưng Max Drawdown 60%: → Mâu thuẫn, kiểm tra lại

### Bước 3: So sánh In-sample vs Out-of-sample

```
In-Sample:  Win Rate 55%, Max DD 20%, Sharpe 1.2
Out-of-Sample: Win Rate 40%, Max DD 35%, Sharpe 0.6

Kết luận: Có overfitting (WR giảm 15%, DD tăng 15%), không nên tin kết quả.
```

### Bước 4: Kiểm tra số lệnh

```
Trade Count: 15 trades
→ Quá ít, chỉ mang tính tham khảo, không đủ để kết luận.

Trade Count: 150 trades
→ Đủ sample, có thể kết luận (với điều kiện in-sample/out-of-sample OK).
```

---

## XII. Ví dụ: Chiến lược tốt vs tệ

### Ví dụ A: Chiến lược "tốt"
```
Win Rate: 48%
Expectancy: +1.8 pips/trade
Profit Factor: 1.8
R/R: 1.6
Max Drawdown: 18%
Sharpe: 1.1
Consecutive Losses: 5
Trade Count: 87
Annualized Return: 12%

Diễn giải:
- Expectancy dương → mỗi trade lợi trung bình
- Win Rate thấp (48%) nhưng R/R cao (1.6) → bù lại
- Max DD 18% → chấp nhận được
- Annualized 12% → tốt
- 87 trade → đủ sample
→ Chiến lược này có cơ sở, có thể backtest thêm out-of-sample
```

### Ví dụ B: Chiến lược "tệ"
```
Win Rate: 72%
Expectancy: -0.5 pips/trade
Profit Factor: 0.9
R/R: 0.6
Max Drawdown: 45%
Sharpe: -0.3
Consecutive Losses: 12
Trade Count: 95
Annualized Return: -15%

Diễn giải:
- Win Rate cao (72%) nhưng Expectancy âm → lỗ dù thắng nhiều
- R/R < 1.0 → lỗ > lợi
- Max DD 45% → rất cao
- Annualized -15% → thua lỗ
- 12 dãy thua liên tiếp → trigger kill switch
→ Chiến lược này không nên dùng, cần thiết kế lại
```

---

## XIII. Tham chiếu

- `BACKTEST_ENGINE.md` — Step 10 Performance Analyzer (tính KPI)
- `backtests/BACKTEST_STANDARD.md` — Chuẩn backtest
- `backtests/BACKTEST_CHECKLIST.md` — QA checklist
- `risk/RISK_POLICY.md` — Giới hạn rủi ro (trigger kill switch nếu DD hoặc loss streak vượt)
