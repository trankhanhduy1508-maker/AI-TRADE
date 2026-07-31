# Periodic Review — Daily, Weekly, Monthly Check

> **Tài liệu thiết kế Periodic Review** — Một quy trình kiểm tra định kỳ (hàng
> ngày, hàng tuần, hàng tháng) để đánh giá hiệu suất paper trading, kiểm tra tuân
> thủ quy tắc, và phát hiện các vấn đề early. Mục đích: không để hệ thống "lặng
> lẽ" chạy mà bỏ sót các cảnh báo, và đảm bảo kill switch được kích hoạt đúng lúc
> nếu cần.

---

## 1. Các cấp độ Review

Paper Trading Engine sẽ thực hiện 3 cấp độ review định kỳ:

| Cấp độ | Tần suất | Phạm vi | Mục đích |
|---|---|---|---|
| **Daily** | Hàng ngày (EOD - end of day) | 1 ngày giao dịch | Kiểm tra cơ bản: số lệnh, PnL ngày, vi phạm rule |
| **Weekly** | Hàng tuần (cuối tuần) | 1 tuần | Tổng hợp chi tiết, so sánh kỳ vọng, kiểm tra drawdown |
| **Monthly** | Hàng tháng (cuối tháng) | 1 tháng | Đánh giá tổng thể, quyết định tiếp tục/điều chỉnh strategy |

---

## 2. Daily Review (Hàng ngày)

### 2.1 Thời điểm thực hiện

- **End of Day (EOD)**: Sau khi session giao dịch kết thúc hoặc lúc 17:00 UTC (tùy
  thị trường).
- Tự động / bán tự động (trigger hàng ngày).

### 2.2 Nội dung Daily Review

| Kiểm tra | Thông tin | Ngưỡng cảnh báo | Hành động |
|---|---|---|---|
| **Số lệnh hôm nay** | Tổng trade mở + đóng | Quá ít (<1) hoặc quá nhiều (>10?) | Ghi log, không alert |
| **Daily PnL** | Lợi/lỗ trong ngày | Lỗ quá nhiều (< -2% account?) — **chưa chốt** | Alert nếu vượt ngưỡng, chuẩn bị trigger kill switch nếu kéo dài |
| **Daily Max Drawdown** | Mức lỗ cực đại trong ngày | > 5% — **chưa chốt** | Alert, monitor |
| **Số lệnh thua liên tiếp hôm nay** | Dãy loss consecutive | >= 3 — **chưa chốt** | Alert, ghi log |
| **Kill Switch status** | ACTIVE / KILL_SWITCH | - | Nếu KILL_SWITCH, báo cáo ngay lý do |
| **Account status** | balance, equity, positions_open | - | Ghi snapshot |
| **Execution issue** | Có signal bị missed? Order reject? | > 0 | Ghi log, debug |

### 2.3 Output: Daily Review Report

**Format (ví dụ):**
```
=== DAILY REVIEW ===
Date: 2026-08-01
Session: PT_20260801_001

Trades:
  Total trades today: 3
  Wins: 2
  Losses: 1
  Win rate (today): 66.7%
  Daily PnL: +0.79 USD

Account Status:
  Starting balance: 10,000 USD
  Ending balance: 10,000.79 USD
  Unrealized PnL: +50 USD (1 position open)
  Equity: 10,050.79 USD

Alerts:
  - None

Kill Switch Status: ACTIVE

Snapshot saved: daily_snapshot_20260801.json
```

### 2.4 Trigger điều kiện cảnh báo

**Nếu xảy ra:**
- Daily loss > ngưỡng (chưa chốt, ví dụ: 2% account).
- Số lệnh thua liên tiếp >= ngưỡng (chưa chốt, ví dụ: 3).
- Kill Switch kích hoạt.
- Signal missed hoặc order reject liên tiếp.

**→ Output**: Alert log, có thể gửi thông báo cho Project Owner (nếu có cơ chế).

---

## 3. Weekly Review (Hàng tuần)

### 3.1 Thời điểm thực hiện

- **Cuối tuần**: Thứ Sáu EOD hoặc Chủ Nhật (tùy vào trading schedule).
- Tự động / semi-automated.

### 3.2 Nội dung Weekly Review

| Kiểm tra | Thông tin | Mục đích | Ghi chú |
|---|---|---|---|
| **Tổng trades tuần** | Số lệnh, win/loss count | Kiểm tra tần suất | >= 5 trades là đủ sample tạm thời |
| **Weekly Win Rate** | % thắng tuần này | So sánh với backtest (~45-50% kỳ vọng?) | Chưa chốt kỳ vọng |
| **Weekly Expectancy** | PnL / số lệnh | Kỳ vọng mỗi lệnh tuần này | So sánh với backtest |
| **Max Drawdown (tuần)** | Độ lỗ cực đại tuần này | Monitor rủi ro | So sánh với portfolio limit |
| **Profit Factor** | Gross Profit / Gross Loss | Lợi lỗ balance | > 1.5 là tốt |
| **Average Hold Time** | Trung bình giữ lệnh bao lâu | Strategy phù hợp không? | Nếu quá dài/ngắn so với kỳ vọng → cảnh báo |
| **R Multiple** | Avg R mỗi trade | Lợi so với rủi ro | > 0.5 R là tốt |
| **So sánh vs Backtest** | Weekly KPI vs backtest result | Drawdown, win rate, PnL có khác quá lớn không? | Nếu khác > 30% → debug |
| **Strategy effectiveness** | Có setup bị missed? Có false signal? | Kiểm tra Rule Engine output | Ghi vào EXPERIMENT_LOG |
| **Killswitch cảnh báo** | Có trigger không? | Monitor | Nếu có → check nguyên nhân |

### 3.3 Output: Weekly Review Report

**Format (ví dụ):**
```
=== WEEKLY REVIEW ===
Week: 2026-08-01 to 2026-08-05
Session(s): PT_20260801_001 (ongoing)

Trades:
  Total: 8 trades
  Wins: 4 (50%)
  Losses: 4 (50%)
  Win Rate: 50%
  Gross Profit: +3.50 USD
  Gross Loss: -2.80 USD
  Net PnL: +0.70 USD
  Expectancy: +0.0875 USD/trade

Risk Metrics:
  Max Drawdown: -50 USD (-0.5% account)
  Avg R Multiple: +0.7 R
  Profit Factor: 1.25

Backtest Comparison:
  Weekly PnL vs Backtest: +0.70 / +1.50 (expected) = 47% of expected
  → Slippage/spread assumptions need adjustment?
  
Alerts:
  - Daily loss on 2026-08-03: -0.60 USD (within normal range)
  - No kill switch triggered

Action Items:
  - Backtest slippage assumptions (current seems higher than actual)
  - Monitor weekly PnL trend (47% of expected, investigate)
  
Approved for continuation.
```

---

## 4. Monthly Review (Hàng tháng)

### 4.1 Thời điểm thực hiện

- **Cuối tháng**: Cùng ngày hàng tháng (ví dụ: ngày 01 của tháng sau).
- Semi-automated + Project Owner participation.

### 4.2 Nội dung Monthly Review

| Kiểm tra | Thông tin | Mục đích | Quyết định |
|---|---|---|---|
| **Tổng trades tháng** | Số lệnh, tỷ lệ win | Đủ sample không? | >= 20 trades là tốt |
| **Monthly Win Rate** | % thắng trong tháng | Tỷ lệ thắng tổng thể | So sánh với backtest |
| **Monthly Expectancy** | Tổng PnL / số lệnh | ROI trung bình | Positive = ok, negative = debug |
| **Max Drawdown (tháng)** | Độ lỗ cực đại tháng | Rủi ro thực tế | > 20% → cảnh báo, > 30% → stop |
| **Risk/Reward (thực tế)** | Avg Win / Avg Loss | Lợi lỗ balance | >= 1.5 là tốt (tương tự backtest) |
| **Sharpe Ratio (nếu tính)** | Return / Volatility | Lợi suất điều chỉnh | > 1.0 là tốt |
| **Recovery Factor** | Net Profit / Max Drawdown | Phục hồi | > 1.0 là ok |
| **vs Backtest (chi tiết)** | Tất cả KPI so backtest | Có overfitting không? | Nếu khác > 50% → re-backtest |
| **Strategy violations** | Có vi phạm quy tắc? | Audit từ Trade Journal | Nếu có → fix, backtest lại |
| **Kill Switch event** | Bao nhiêu lần trigger? Lý do gì? | Quản lý rủi ro | Nếu quá thường → tăng threshold? giảm position size? |
| **Market condition** | Thị trường trending hay range? High vol? | Strategy match | Nếu không match → pause strategy, revert |
| **Signal quality** | Bao % signal từ Rule Engine → filled? | Rule Engine tuning | < 70% → check Rule Engine |

### 4.3 Output: Monthly Review + Decision

**Format (ví dụ):**
```
=== MONTHLY REVIEW ===
Month: August 2026
Session(s): PT_20260801_001 to PT_20260831_00N (multiple sessions)

Performance Summary:
  Total Trades: 32
  Win Rate: 48%
  Expectancy: +0.68 USD/trade
  Total PnL: +21.76 USD (+0.22% account)
  Max Drawdown: -80 USD (-0.8% account)
  Risk/Reward: 1.42
  Sharpe Ratio: 0.85

Backtest Comparison:
  Backtest Win Rate: 50% → Actual: 48% ✓ (within margin)
  Backtest Drawdown: 1.0% → Actual: 0.8% ✓ (better)
  Backtest Expectancy: +0.75 → Actual: +0.68 USD ✓ (close, slippage accounts)
  Conclusion: Paper trading MATCHES backtest (within 10% margin)

Strategy Violations:
  - 1 trade violated Score threshold (entered with score 78 < 80)
    → Tightened rule in code (no score < 80 allowed)
  - No other violations

Kill Switch Events:
  - None triggered (good)
  - Max consecutive loss: 2 (within normal)

Market Observations:
  - August: Mostly trending market (EUR/USD)
  - Good for TF_001 (breakout strategy)
  - No major volatility spikes

Signal Quality:
  - 89% of signals → filled (good)
  - 11% rejected due to portfolio risk limit

DECISION: ✅ APPROVED FOR GIAI ĐOẠN 5 (AI Scoring)
  - Chiến lược stable
  - Paper trade matches backtest
  - No major issues
  - Proceed to AI Scoring phase

Action Items for Giai Đoạn 5:
  1. Integrate AI reviewer (POST_TRADE_REVIEWER prompt)
  2. Test AI confirmation rate (target: > 80%)
  3. Continue monitoring for 2-4 more weeks
```

---

## 5. Trigger điều kiện cảnh báo chung (mọi cấp độ)

### 5.1 Từ KILL_SWITCH_RULES.md

**Auto-trigger kill switch nếu:**
- Consecutive losses: N lệnh thua liên tiếp (chưa chốt N).
- Drawdown: > X% vốn (chưa chốt X).
- Portfolio risk vượt limit.

**Hành động**: Set Virtual Account status = `KILL_SWITCH`, dừng signal mới, ghi log
rõ ràng.

### 5.2 Từ RISK_POLICY.md

**Alert (không auto kill switch, nhưng cảnh báo):**
- Daily loss > threshold (chưa chốt).
- Drawdown approaching limit (90% of limit).
- Số signal missed quá nhiều.

---

## 6. Cấu trúc lưu trữ Review Reports

**Tùy chọn:**
1. **Markdown file**: `paper_trading/reviews/REVIEW_20260801_DAILY.md`, `REVIEW_20260805_WEEKLY.md`, etc.
2. **JSON file**: `paper_trading/reviews/reviews.json` (append each review).
3. **Database table**: `reviews` (queryable).

---

## 7. Liên hệ với các file khác

- **`risk/RISK_POLICY.md`** → Ngưỡng alert (drawdown, daily loss, consecutive loss).
- **`risk/KILL_SWITCH_RULES.md`** → Điều kiện auto-trigger kill switch.
- **`paper_trading/TRADE_JOURNAL.md`** → Raw data từng trade dùng để tính metrics.
- **`paper_trading/VIRTUAL_ACCOUNT.md`** → Balance, equity snapshot.
- **`backtests/KPI_STANDARD.md`** → Định nghĩa KPI dùng trong review.
- **`research/EXPERIMENT_LOG.md`** → Link tới weekly/monthly review của mỗi phiên.
- **`research/FAILURE_CASES.md`** → Nếu phát hiện vi phạm qua review.

---

## 8. Chú ý về thời điểm review

**Timezone issue (chưa chốt):**
- UTC vs local time?
- Forex: nên review tại 17:00 UTC (kết thúc session NY)?
- Crypto: 24/7, nên review tại giờ cố định hàng ngày (ví dụ: 08:00 UTC)?

**Cần Project Owner chốt rõ.**

---

## 9. Trạng thái và ghi chú

- **Thiết kế**: Hoàn tất cấu trúc 3 cấp độ review (Daily/Weekly/Monthly).
- **Chưa chốt**:
  - Ngưỡng cảnh báo cụ thể (% daily loss, max consecutive loss, etc.) → từ RISK_POLICY.md.
  - Timezone cho EOD review.
  - Format lưu trữ chính thức (Markdown/JSON/Database).
  - Ai thực hiện semi-automated review (AI prompt hay manual check)?
- **Cần Project Owner review**: Xác nhận cấp độ review, ngưỡng alert, quy trình
  decision (tiếp tục/pause/debug).
- **Tiếp theo**: Viết PERFORMANCE_DASHBOARD.md (KPI hiển thị), audit tính nhất quán
  toàn bộ paper trading engine.
