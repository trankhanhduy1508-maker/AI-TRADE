# Performance Dashboard — Chỉ báo Hiệu suất Paper Trading

> **Tài liệu thiết kế Performance Dashboard** — Mô tả các chỉ số KPI cần hiển thị
> để theo dõi hiệu suất paper trading trong real-time hoặc per-session. Dashboard
> là giao diện "nhìn thấy ngay" hiệu suất, phục vụ:
> 1. **Real-time monitoring**: Theo dõi phiên giao dịch hiện tại.
> 2. **Historical reporting**: Xem lại hiệu suất các phiên/tuần/tháng trước.
> 3. **Comparison with backtest**: Đối chiếu paper trade vs backtest expectation.

---

## 1. Định nghĩa

**Performance Dashboard** là một bộ chỉ số (KPI) được tính toán từ Trade Journal và
Virtual Account, dùng để đánh giá hiệu suất paper trading. Nó **tái sử dụng định
nghĩa KPI từ `backtests/KPI_STANDARD.md`**, không phải định nghĩa lại.

**Điểm khác biệt:**
- **Backtest Dashboard**: Dữ liệu **lịch sử đã xác định** (historical, fixed).
- **Paper Trade Dashboard**: Dữ liệu **live/semi-live** (real-time hoặc per-session,
  có thể còn position mở chưa close).

---

## 2. Các chỉ số KPI (tái sử dụng từ KPI_STANDARD.md)

### 2.1 Lợi/Lỗ (Profit & Loss)

| Chỉ số | Công thức | Ý nghĩa | Mục tiêu |
|---|---|---|---|
| **Net Profit** | Tổng realized_pnl | Lợi/lỗ tổng | > 0 |
| **Realized PnL %** | (Net Profit / starting_balance) × 100 | Lợi suất % | > 0 |
| **Unrealized PnL** | Tổng unrealized PnL từ position mở | Lợi/lỗ chưa thực hiện | - (info) |
| **Gross Profit** | Tổng PnL WIN | Tổng lợi từ trade thắng | Tracking |
| **Gross Loss** | Tổng |PnL LOSS| | Tổng lỗ từ trade thua | Tracking |
| **Profit Factor** | Gross Profit / Gross Loss | Hệ số lợi/lỗ | > 1.5 |

### 2.2 Tỷ lệ Thắng (Win Rate)

| Chỉ số | Công thức | Ý nghĩa | Mục tiêu |
|---|---|---|---|
| **Win Rate %** | (Wins / Total Trades) × 100 | % trade thắng | Tùy strategy (~40-50%) |
| **Consecutive Wins** | Dãy thắng dài nhất | Streak tốt | Tracking |
| **Consecutive Losses** | Dãy thua dài nhất | Streak xấu, trigger kill switch? | < ngưỡng |
| **Average Win** | Gross Profit / Wins | Lợi bình quân/trade | Tracking |
| **Average Loss** | Gross Loss / Losses | Lỗ bình quân/trade | Tracking |

### 2.3 Risk/Reward

| Chỉ số | Công thức | Ý nghĩa | Mục tiêu |
|---|---|---|---|
| **R/R Ratio** | Avg Win / Avg Loss | Lợi so với lỗ | >= 1.5 |
| **Expectancy** | Net Profit / Total Trades | Kỳ vọng mỗi trade | > 0 |
| **Avg R Multiple** | Tổng R / Total Trades | R multiple trung bình | > 0.5 |

### 2.4 Rủi ro (Drawdown & Risk-Adjusted)

| Chỉ số | Công thức | Ý nghĩa | Mục tiêu |
|---|---|---|---|
| **Max Drawdown %** | (Peak - Trough) / Peak × 100 | Lỗ cực đại % | < 20% |
| **Current Drawdown %** | (Current Equity - Peak Equity) / Peak × 100 | Lỗ hiện tại so peak | Tracking |
| **Sharpe Ratio** | Return / Volatility | Lợi suất/rủi ro | > 1.0 (nếu có) |
| **Sortino Ratio** | Return / Downside Vol | Lợi suất/downside risk | > 1.0 (nếu có) |
| **Calmar Ratio** | Annual Return / Max DD | Năm/rủi ro | > 1.0 (nếu có) |
| **Recovery Factor** | Net Profit / Max DD | Phục hồi | > 1.0 |

### 2.5 Thống kê (Statistics)

| Chỉ số | Mô tả | Mục tiêu |
|---|---|---|
| **Total Trades** | Số lệnh closed | >= 5 (tạm thời), >= 20 (tốt) |
| **Open Positions** | Số lệnh đang mở | Tracking |
| **Duration (trades)** | Thời gian giao dịch | Từ start → hiện tại |
| **Avg Hold Time** | Trung bình giữ lệnh | Matching strategy expectation |

### 2.6 Hiệu quả (Efficiency)

| Chỉ số | Mô tả | Mục tiêu |
|---|---|---|
| **Signal Quality** | % signal → order filled | > 85% |
| **Missed Signals** | Số signal reject do risk limit | Tracking |
| **Strategy Match** | Paper trade KPI vs Backtest KPI | Sai margin < 30% |

---

## 3. Cấu trúc Dashboard (Real-time & Historical)

### 3.1 Real-time Dashboard (Phiên hiện tại)

**Hiển thị LIVE (update mỗi trade/bar/phút):**

```
┌─────────────────────────────────────────────────────────┐
│ PAPER TRADING DASHBOARD — LIVE                          │
│ Session: PT_20260801_001 | Started: 09:00 UTC          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ ACCOUNT SNAPSHOT                                        │
│ ┌──────────────────────────────────────────────────────┐
│ │ Starting Balance: 10,000 USD                         │
│ │ Current Balance:  10,050 USD                         │
│ │ Unrealized PnL:     +50 USD (1 position open)       │
│ │ Current Equity:   10,100 USD                         │
│ │ Drawdown:           -0.5% (from peak 10,150 USD)   │
│ └──────────────────────────────────────────────────────┘
│
│ CLOSED TRADES (TODAY)                                  │
│ ┌──────────────────────────────────────────────────────┐
│ │ Total Closed: 2 trades                               │
│ │ Win Rate:     50% (1 WIN, 1 LOSS)                   │
│ │ Net PnL:      +50 USD                                │
│ │ Expectancy:   +25 USD/trade                          │
│ │ Profit Factor: 2.0x                                  │
│ │ R/R Ratio:    1.5                                    │
│ │ Avg Hold:     3.5 hours                              │
│ └──────────────────────────────────────────────────────┘
│
│ OPEN POSITIONS                                         │
│ ┌──────────────────────────────────────────────────────┐
│ │ Position 1: EUR/USD LONG                             │
│ │   Entry: 1.0851 | Current: 1.0870 | Unrealized: +19│
│ │   SL: 1.0820 | Target: 1.0900 | Hold: 4h 45m       │
│ └──────────────────────────────────────────────────────┘
│
│ ALERTS                                                 │
│ ┌──────────────────────────────────────────────────────┐
│ │ ✓ All systems OK                                    │
│ │ ✓ Kill Switch: ACTIVE                              │
│ └──────────────────────────────────────────────────────┘
│
└─────────────────────────────────────────────────────────┘
```

### 3.2 Historical Dashboard (Session/Week/Month Report)

**Hiển thị HISTORICAL (fixed data sau khi đóng phiên):**

```
┌─────────────────────────────────────────────────────────┐
│ PAPER TRADING REPORT — WEEKLY                           │
│ Week: 2026-08-01 to 2026-08-05                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ SUMMARY METRICS                                         │
│ Starting Capital:    10,000 USD                         │
│ Ending Capital:      10,075 USD                         │
│ Net Profit:          +75 USD (+0.75%)                  │
│ Max Drawdown:        -120 USD (-1.2%)                  │
│                                                          │
│ TRADE STATISTICS                                       │
│ Total Trades:        8                                  │
│ Wins:                4 (50%)                            │
│ Losses:              4 (50%)                            │
│ Win Rate:            50%                                │
│ Expectancy:          +9.38 USD/trade                   │
│ Avg Win:             +30 USD                            │
│ Avg Loss:            -20 USD                            │
│ Profit Factor:       1.5x                              │
│ R/R Ratio:           1.5                                │
│                                                          │
│ RISK-ADJUSTED METRICS                                  │
│ Sharpe Ratio:        0.92                              │
│ Sortino Ratio:       1.15                              │
│ Calmar Ratio:        0.63                              │
│ Recovery Factor:     0.625                              │
│ Consecutive Loss:    2 (max)                           │
│ Consecutive Win:     2 (max)                           │
│                                                          │
│ BACKTEST COMPARISON                                    │
│ Expected PnL:        +150 USD (backtest lý thuyết)    │
│ Actual PnL:          +75 USD                           │
│ Match %:             50% (slippage accounts for 50%) │
│ Status:              ⚠ Monitor (need tighter slippage) │
│                                                          │
│ SIGNALING QUALITY                                      │
│ Signals Generated:   10                                 │
│ Orders Filled:       8 (80%)                           │
│ Orders Rejected:     2 (due to risk limit)            │
│ Signal Quality:      Good                              │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 4. Tần suất cập nhật Dashboard

| Dashboard | Tần suất update | Cách thức | Dữ liệu |
|---|---|---|---|
| **Real-time** | Mỗi trade/bar | Auto (code) | Live/semi-live |
| **Session Report** | EOD (end of day) | Auto | Trades đóng hôm đó |
| **Weekly Report** | Cuối tuần (Fri/Sun) | Semi-auto | Trades tuần này |
| **Monthly Report** | Cuối tháng | Manual + auto | Trades tháng này |

---

## 5. Các view Dashboard có thể

### 5.1 View 1: Account Performance (Chính)

**Focus:** Balance, PnL, equity, drawdown, current position.

**Dùng cho:** Real-time monitoring hàng ngày.

### 5.2 View 2: Trade Analysis (Chi tiết)

**Focus:** Win rate, R/R, expectancy, consecutive win/loss, hold time.

**Dùng cho:** Đánh giá chiến lược.

### 5.3 View 3: Risk Dashboard

**Focus:** Current drawdown, max drawdown, portfolio risk, kill switch status.

**Dùng cho:** Monitor rủi ro.

### 5.4 View 4: Backtest Comparison

**Focus:** Paper trade KPI vs backtest KPI, slippage analysis, signal quality.

**Dùng cho:** Kiểm tra xem paper trade có match backtest không.

### 5.5 View 5: Trade List (Bảng)

**Focus:** Danh sách tất cả trade (entry, exit, PnL, hold time).

**Dùng để:** Drill down từng trade.

---

## 6. Công nghệ hiển thị (chưa chốt)

**Tùy chọn (chưa chốt, cần Project Owner decide):**

1. **Web Dashboard** (HTML/CSS/JS): Hiển thị web browser, real-time update qua WebSocket.
   - Pro: Real-time, interactive, beautiful UI.
   - Con: Cần setup web server, frontend code.

2. **Text Dashboard** (Terminal/CLI): Hiển thị terminal, update per-tick.
   - Pro: Simple, zero dependencies, easy to log.
   - Con: Limited visual, terminal-based only.

3. **Spreadsheet (Excel/Google Sheets)**: Manual update hoặc auto via API.
   - Pro: Easy to share, familiar format, easy calculation.
   - Con: Not real-time, manual work.

4. **File-based (Markdown/JSON)**: Update file sau mỗi session, view later.
   - Pro: Simple, persistent, auditable.
   - Con: Not real-time, need manual view.

**Đề xuất cho giai đoạn 4:** File-based (Markdown) hoặc Text Dashboard (real-time),
sau đó nâng cấp web dashboard nếu cần (giai đoạn 5+).

---

## 7. Liên hệ với các file khác

- **`backtests/KPI_STANDARD.md`** → Định nghĩa KPI (tái sử dụng, không định nghĩa lại).
- **`paper_trading/TRADE_JOURNAL.md`** → Raw data từng trade để tính KPI.
- **`paper_trading/VIRTUAL_ACCOUNT.md`** → Balance, equity, unrealized PnL snapshot.
- **`paper_trading/PERIODIC_REVIEW.md`** → Review reports dùng dashboard metrics.
- **`risk/RISK_POLICY.md`** → Ngưỡng alert (max drawdown, daily loss...).
- **`risk/KILL_SWITCH_RULES.md`** → Kill switch status display.

---

## 8. Ví dụ: Tính toán KPI từ Trade Journal

**Giả sử có 10 trades đóng trong 1 tuần:**

```
Trades:
  1. EUR/USD LONG: entry 1.0850, exit 1.0870 → +20 USD ✓
  2. GBP/USD SHORT: entry 1.2750, exit 1.2780 → -30 USD ✗
  3. EUR/USD LONG: entry 1.0860, exit 1.0870 → +10 USD ✓
  4. EUR/JPY LONG: entry 105.00, exit 104.50 → -50 USD ✗
  5. USD/CAD SHORT: entry 1.3600, exit 1.3550 → +50 USD ✓
  6. EUR/USD LONG: entry 1.0875, exit 1.0900 → +25 USD ✓
  7. GBP/USD LONG: entry 1.2700, exit 1.2650 → -50 USD ✗
  8. EUR/USD SHORT: entry 1.0880, exit 1.0860 → +20 USD ✓
  9. USD/JPY SHORT: entry 145.00, exit 145.50 → -50 USD ✗
  10. EUR/GBP SHORT: entry 0.8550, exit 0.8530 → +20 USD ✓

Aggregate:
  Wins: 6 trades (1,3,5,6,8,10)
  Losses: 4 trades (2,4,7,9)
  Win Rate: 6/10 = 60%
  Gross Profit: 20+10+50+25+20+20 = 145 USD
  Gross Loss: 30+50+50+50 = 180 USD
  Net Profit: 145 - 180 = -35 USD
  Expectancy: -35 / 10 = -3.5 USD/trade
  Avg Win: 145 / 6 = 24.17 USD
  Avg Loss: 180 / 4 = 45 USD
  R/R: 24.17 / 45 = 0.54 (< 1.0, xấu)
  Profit Factor: 145 / 180 = 0.81 (< 1.0, thua lỗ)
  
Kết luận: Tuần này thua lỗ, Win Rate 60% nhưng Avg Loss quá lớn, R/R < 1.0
→ Cần debug: size lệnh thua quá lớn? Stop loss đặt sai?
```

---

## 9. Đặc biệt: So sánh Paper Trade vs Backtest

**Bảng so sánh (ví dụ):**

```
Metric              | Backtest (lý thuyết) | Paper Trade (thực tế) | Khác %  | Status
─────────────────────────────────────────────────────────────────────────────
Win Rate            | 50%                  | 48%                   | -2%     | ✓ OK
Expectancy          | +0.75 USD/trade      | +0.68 USD/trade       | -9%     | ✓ OK
R/R Ratio           | 1.50                 | 1.42                  | -5%     | ✓ OK
Max Drawdown        | 1.0%                 | 0.8%                  | -20%    | ✓ OK (better)
Profit Factor       | 1.80                 | 1.65                  | -8%     | ✓ OK
Consecutive Loss    | 3                    | 2                     | -33%    | ✓ OK (better)
─────────────────────────────────────────────────────────────────────────────
Overall Match       |                      |                       | -8%     | ✓ PASS (< 30%)
```

**Nếu sai số > 30%:** Cần investigate, adjust slippage assumption hoặc strategy.

---

## 10. Trạng thái và ghi chú

- **Thiết kế**: Hoàn tất danh sách KPI (tái sử dụng từ KPI_STANDARD.md), các view
  dashboard, cách tính toán.
- **Chưa chốt**:
  - Công nghệ hiển thị chính thức (web? terminal? file-based?).
  - Tần suất update real-time dashboard (per-trade? per-bar? per-minute?).
  - Các KPI nào là **must-have** vs **nice-to-have** (hiện liệt kê toàn bộ).
- **Cần Project Owner review**: Xác nhận công nghệ dashboard, KPI ưu tiên, tần suất
  update.
- **Tiếp theo**: Audit tính nhất quán toàn bộ Paper Trading Engine (7 file),
  cleanup, ready cho code.
