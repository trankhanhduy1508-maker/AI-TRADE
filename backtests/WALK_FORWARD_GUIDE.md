# Walk Forward Analysis Guide

> **Hướng dẫn thực hiện Walk Forward Analysis (WFA) cho backtest.**  
> Mục đích: Kiểm tra khả năng tổng quát hóa khi điều chỉnh tham số liên tục.

---

## 1. Định nghĩa Walk Forward Analysis

### 1.1 Khái niệm

**Walk Forward Analysis** là phương pháp kiểm tra chiến lược bằng cách:
1. Chia dữ liệu thành nhiều **window** (cửa sổ) liên tiếp
2. Tối ưu tham số trên mỗi window **in-sample**
3. Test kết quả trên **out-of-sample** window tiếp theo
4. Lặp lại cho tất cả window (rolling forward)
5. Tổng hợp kết quả tất cả out-of-sample window

### 1.2 Ví dụ minh họa

```
Dữ liệu: 2015-2020 (6 năm)

Window 1:
  In-sample (calibration):  2015-2016 (optimize tham số)
  Out-of-sample (test):     2017 (kiểm tra tham số optimal trên dữ liệu mới)

Window 2:
  In-sample (calibration):  2015-2017 (optimize tham số)
  Out-of-sample (test):     2018 (kiểm tra)

Window 3:
  In-sample (calibration):  2015-2018 (optimize tham số)
  Out-of-sample (test):     2019 (kiểm tra)

Window 4:
  In-sample (calibration):  2015-2019 (optimize tham số)
  Out-of-sample (test):     2020 (kiểm tra)

Kết quả WFA: Gộp tất cả out-of-sample window (2017, 2018, 2019, 2020)
```

---

## 2. Tại sao cần Walk Forward Analysis

### 2.1 Vấn đề với In-sample testing

```
Vấn đề:
- Tối ưu tham số dựa trên dữ liệu 2015-2019
- Test trên 2019-2020 (chỉ 2 năm)
- Dữ liệu 2019 vừa được dùng để optimize (data leakage)
→ Kết quả out-of-sample còn "bị ảnh hưởng" bởi in-sample
```

### 2.2 Walk Forward tránh vấn đề này

```
WFA:
- Optimize trên 2015-2016, test trên 2017 (hoàn toàn tách biệt)
- Optimize trên 2015-2017, test trên 2018 (hoàn toàn tách biệt)
- Optimize trên 2015-2018, test trên 2019 (hoàn toàn tách biệt)
- ...
→ Mỗi out-of-sample window hoàn toàn độc lập với in-sample
```

### 2.3 Lợi ích WFA

- **Tránh overfitting:** Optimize liên tục chỉ trên phần cũ, test trên phần mới chưa biết.
- **Mô phỏng thực tế:** Trong thực tế, ta cũng optimize theo thời gian (khi có dữ liệu mới, điều chỉnh tham số).
- **Kiểm tra stability:** Xem kết quả có ổn định nếu optimize liên tục hay không.

---

## 3. Quy trình thực hiện WFA

### 3.1 Bước 1: Định nghĩa Window Size

**Chọn kích thước in-sample và out-of-sample:**

```
Option A (Symmetric):
  In-sample: 2 năm
  Out-of-sample: 2 năm
  Total: 4 năm
  Số window: Có thể có 3-4 window tùy dữ liệu

Option B (Asymmetric — Growing):
  In-sample: Tăng dần (2yr → 3yr → 4yr → ...)
  Out-of-sample: Cố định 1 năm
  Total: 6 năm dữ liệu → 5-6 window

Option C (Fixed — Best Practice):
  In-sample: 2 năm (cố định)
  Out-of-sample: 1 năm (cố định)
  Slide window lần lượt
  Total: 6 năm dữ liệu → 4 window
```

**Khuyến cáo:** Option C (fixed window, sliding) là dễ implement nhất.

### 3.2 Bước 2: Xác định tham số cần optimize

```
Ví dụ: Chiến lược TF_001_BREAKOUT_PULLBACK

Tham số cần optimize:
- RSI period (RULE_006): 14? 10? 21?
- EMA period (RULE_007): 50? 100? 200?
- Volume SMA period (RULE_005): 20? 14? 30?
- Breakout body ratio (RULE_003): 60%? 50%? 70%?

(Nhưng R/R minimum, SL level, scoring threshold 80 → KHÔNG optimize, fix cứng)
```

### 3.3 Bước 3: Tối ưu trên In-sample Window 1

```
In-sample Window 1: 2015-01-01 → 2016-12-31

Grid search: Test tất cả biến thể tham số
  RSI period: [10, 14, 21, 28]
  EMA period: [50, 100, 200]
  Volume SMA: [14, 20, 30]
  → Tổng 4 × 3 × 3 = 36 biến thể

Mỗi biến thể:
  - Chạy backtest trên 2015-2016
  - Tính KPI (Win Rate, Expectancy, Sharpe, Max DD)
  - Chọn biến thể có **Best KPI** (ví dụ: highest Expectancy + lowest Max DD)

Kết quả: Tham số optimal cho Window 1
  RSI period: 14
  EMA period: 100
  Volume SMA: 20
```

**Tiêu chí tối ưu:** Nên dùng nhiều tiêu chí (Expectancy + Max DD), không chỉ 1 KPI.

### 3.4 Bước 4: Test trên Out-of-sample Window 1

```
Out-of-sample Window 1: 2017-01-01 → 2017-12-31

Dùng tham số optimal từ Bước 3:
  RSI period: 14
  EMA period: 100
  Volume SMA: 20

Chạy backtest trên 2017 (dữ liệu chưa từng thấy)
→ Ghi nhận KPI: Win Rate, Expectancy, Max DD, Sharpe...
```

**Lưu ý:** Không optimize lại trên 2017, chỉ test với tham số từ in-sample.

### 3.5 Bước 5: Lặp lại Window 2, 3, 4...

```
Window 2:
  In-sample: 2015-2017 (tối ưu)
  Out-of-sample: 2018 (test)

Window 3:
  In-sample: 2015-2018 (tối ưu)
  Out-of-sample: 2019 (test)

Window 4:
  In-sample: 2015-2019 (tối ưu)
  Out-of-sample: 2020 (test)
```

### 3.6 Bước 6: Tổng hợp kết quả WFA

```
Tất cả out-of-sample:
  2017 (OOS1): Win Rate = 52%, Expectancy = 1.8 pips, Max DD = 18%
  2018 (OOS2): Win Rate = 48%, Expectancy = 2.1 pips, Max DD = 22%
  2019 (OOS3): Win Rate = 55%, Expectancy = 1.5 pips, Max DD = 15%
  2020 (OOS4): Win Rate = 50%, Expectancy = 2.0 pips, Max DD = 20%

WFA Summary (Gộp tất cả OOS):
  Total Win Rate: (2017 trades × 52% + 2018 trades × 48% + ...) / Total trades
  Total Expectancy: (Sum all OOS PnL) / (Sum all OOS trades)
  Max DD across all OOS: 22% (từ window 2018)
  Avg Sharpe: (OOS1 Sharpe + OOS2 Sharpe + ...) / 4

Kết luận:
  WFA Expectancy = 1.85 pips/trade (trung bình tất cả OOS)
  WFA Max DD = 22%
  Consistency: Expectancy dao động 1.5-2.1 (ổn định)
```

---

## 4. Cách diễn giải kết quả WFA

### 4.1 Kịch bản A: WFA tốt (Stable & Positive)

```
In-sample Expectancy: +2.2 pips/trade, Max DD: 18%
WFA Expectancy: +1.9 pips/trade, Max DD: 20%
Sai lệch: 14% (Expectancy), 10% (Max DD)

Diễn giải:
✓ In-sample và WFA gần nhau
✓ Sai lệch < 20% (chấp nhận được)
✓ WFA Expectancy vẫn dương
→ Chiến lược có khả năng tổng quát, có thể dùng thực tế
```

### 4.2 Kịch bản B: WFA cảnh báo (Overfitting Detected)

```
In-sample Expectancy: +3.5 pips/trade, Max DD: 15%
WFA Expectancy: +0.5 pips/trade, Max DD: 35%
Sai lệch: 86% (Expectancy), 133% (Max DD)

Diễn giải:
✗ In-sample lạc quan quá so với WFA
✗ Sai lệch > 30% (cực đoan)
✗ WFA Expectancy gần 0 (không rõ hiệu quả)
✗ WFA Max DD tăng gấp đôi (rủi ro thực tế cao hơn)
→ Có dấu hiệu overfitting, cần điều chỉnh strategy/parameters
```

### 4.3 Kịch bản C: WFA tệ (Negative)

```
In-sample Expectancy: +1.8 pips/trade, Max DD: 20%
WFA Expectancy: -0.3 pips/trade, Max DD: 28%
Sai lệch: 117% (Expectancy), 40% (Max DD)

Diễn giải:
✗ WFA Expectancy âm (thua lỗ)
✗ Chiến lược không tổng quát hóa được
→ Loại bỏ chiến lược, thiết kế lại
```

### 4.4 Kịch bản D: WFA lộn xộn (Unstable Across Windows)

```
OOS Window 1: Expectancy = +3.0 pips
OOS Window 2: Expectancy = -1.5 pips
OOS Window 3: Expectancy = +2.5 pips
OOS Window 4: Expectancy = -0.8 pips

Diễn giải:
✗ Kết quả dao động quá lớn (từ +3 tới -1)
✗ Chiến lStrategy không ổn định theo thời gian
→ Có khả năng chiến lược tốt ở 1 market condition (ví dụ trend), tệ ở condition khác
→ Cần làm thêm out-of-sample testing trên market condition khác
```

---

## 5. So sánh In-sample vs Out-of-sample vs WFA

| Phương pháp | Độ chính xác | Overfitting risk | Thời gian | Khi nào dùng |
|---|---|---|---|---|
| **In-sample** | Cao | Cao (nhất) | Nhanh | Bước đầu tìm ý tưởng |
| **Out-of-sample (1 lần)** | Cao | Trung bình | Trung bình | Xác nhận giả thuyết |
| **Walk Forward** | Trung bình | Thấp | Chậm (lâu) | Trước khi dùng thực tế |
| **Monte Carlo** | Thấp (nhất) | Thấp | Rất chậm | Kiểm tra robustness |

**Khuyến cáo:**
1. Bước 1: In-sample → xác định ý tưởng
2. Bước 2: Out-of-sample → xác nhận không overfitting
3. Bước 3: Walk Forward (nếu cần) → kiểm tra stability
4. Bước 4: Paper trade → kiểm tra thực tế (chỉ dữ liệu, không tiền)

---

## 6. Quy tắc quyết định dựa trên WFA

| Kết quả WFA | Quyết định | Bước tiếp theo |
|---|---|---|
| WFA Expectancy > In-sample by 50%+ | 🚫 REJECT | Có overfitting, thiết kế lại |
| In-sample - WFA sai lệch < 20% | ✅ ACCEPT | Có thể dùng (với cảnh báo) |
| In-sample - WFA sai lệch 20-30% | ⚠️ YELLOW | Có khả năng overfitting, monitor thêm |
| WFA Expectancy < 0 | 🚫 REJECT | Chiến lược thua lỗ thực tế |
| WFA Max DD > Expectancy × 50 | 🚫 REJECT | Rủi ro quá cao so với lợi |

---

## 7. Ví dụ thực tế: TF_001 Walk Forward

### 7.1 Dữ liệu

```
Market: EURUSD, Timeframe: 4H
Dữ liệu: 2015-2020 (6 năm)
In-sample window: 2 năm (cố định)
Out-of-sample: 1 năm (cố định)
```

### 7.2 Window 1 (2015-2017)

```
In-sample (2015-2016):
  Optimal tham số: EMA 100, RSI 14, Volume SMA 20
  KPI: Win Rate 53%, Expectancy 2.1 pips, Max DD 17%

Out-of-sample (2017):
  Dùng EMA 100, RSI 14, Volume SMA 20
  KPI: Win Rate 51%, Expectancy 1.9 pips, Max DD 19%
```

### 7.3 Window 2 (2015-2018)

```
In-sample (2015-2017):
  Optimal tham số: EMA 100, RSI 14, Volume SMA 20 (khác window 1?)
  KPI: Win Rate 52%, Expectancy 2.0 pips, Max DD 18%

Out-of-sample (2018):
  Dùng tham số optimal từ in-sample
  KPI: Win Rate 50%, Expectancy 1.8 pips, Max DD 21%
```

### 7.4 Kết quả WFA tổng hợp

```
Tất cả OOS window (2017 + 2018 + 2019 + 2020):
  Total trades: 150
  Total Win Rate: 51%
  Total Expectancy: 1.85 pips/trade
  Total Max DD: 21%
  Consistency: Expectancy dao động 1.8-1.9 (rất ổn định)

So sánh:
  In-sample (best): Win Rate 53%, Expectancy 2.1 pips
  WFA: Win Rate 51%, Expectancy 1.85 pips
  Sai lệch: 4% (WR), 12% (Exp) → CHẤP NHẬN ĐƯỢC

Kết luận: TF_001 đã qua kiểm chứng WFA, có thể đưa vào giai đoạn paper trade
```

---

## 8. Lỗi thường gặp khi làm WFA

| Lỗi | Mô tả | Cách phòng tránh |
|---|---|---|
| **Data Leakage** | Dùng OOS data để optimize tham số | Tách riêng IS/OOS trước khi optimize |
| **Window overlap** | Window 2 overlap với Window 1 | Không overlap, hoặc minimal overlap |
| **Quá ít OOS trades** | Mỗi OOS window < 20 trades | Tăng kích thước OOS window |
| **Chọn tiêu chí sai** | Optimize dựa trên 1 KPI (ví dụ chỉ Win Rate) | Dùng multi-criteria (Expectancy + Max DD) |
| **Thiếu in-sample data** | In-sample window < 100 trades | Tăng kích thước IS window |

---

## 9. Tham chiếu

- `BACKTEST_ENGINE.md` — Luồng data processing
- `backtests/KPI_STANDARD.md` — Định nghĩa KPI để chọn optimal parameters
- `backtests/MONTE_CARLO_GUIDE.md` — Bổ sung kiểm chứng thêm bằng simulation
- `backtests/BACKTEST_CHECKLIST.md` — QA checklist trước khi tin kết quả
