# Trade Journal — Ghi lại Chi tiết Lệnh Đóng

> **Tài liệu thiết kế Trade Journal** — Một nhật ký ghi lại chi tiết mỗi lệnh
> (trade) đã đóng. Mục đích: tạo dữ liệu đầu vào cho post-trade review (phân tích
> bằng AI), audit tuân thủ quy tắc, và research để rút kinh nghiệm. Trade Journal
> là "bằng chứng" của hệ thống, nơi mà mỗi quyết định được ghi lại một cách khách
> quan.

---

## 1. Định nghĩa và Mục đích

**Trade Journal** là một bản ghi lưu lại chi tiết mỗi lệnh **đã đóng** từ paper
trading. Khác với:
- **EXPERIMENT_LOG.md**: Ghi lại **mỗi lần chạy toàn bộ backtest/phiên trade**
  (date, chiến lược, kết quả summary).
- **FAILURE_CASES.md**: Ghi lại các **ca thất bại điển hình** để tránh lặp lại
  (khi có bằng chứng thật).
- **Trade Journal**: Ghi lại **chi tiết từng lệnh đóng** để phân tích chi tiết,
  audit quy trình, và input cho POST_TRADE_REVIEWER prompt.

---

## 2. Các trường dữ liệu (Data Model)

| Tên trường | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---|---|---|---|
| **journal_id** | String/UUID | Bắt buộc | Định danh duy nhất (ví dụ: `JNL_20260801_001`) |
| **trade_number** | Integer | Bắt buộc | Số thứ tự lệnh trong phiên (1, 2, 3...) |
| **session_id** | String | Bắt buộc | ID của phiên paper trade (ví dụ: `PT_20260801_001`) |
| **position_id** | String | Bắt buộc | ID của Position đóng |
| **order_id** | String | Bắt buộc | ID của Virtual Order |
| **symbol** | String | Bắt buộc | Cặp tiền tệ / mã |
| **direction** | String (enum) | Bắt buộc | `LONG` / `SHORT` |
| **strategy_id** | String | Bắt buộc | Chiến lược dùng (ví dụ: `TF_001`, `TF_002`) |
| **setup_score** | Decimal (0-100) | Bắt buộc | Setup score từ Rule Engine |
| **entry_date_time** | Timestamp | Bắt buộc | Ngày/giờ lệnh được FILLED |
| **entry_price** | Decimal | Bắt buộc | Entry price thực tế (sau slippage) |
| **exit_date_time** | Timestamp | Bắt buộc | Ngày/giờ lệnh CLOSED |
| **exit_price** | Decimal | Bắt buộc | Exit price |
| **exit_reason** | String (enum) | Bắt buộc | `STOP_LOSS` / `TARGET_HIT` / `EXIT_RULE` / `MANUAL` |
| **quantity** | Decimal | Bắt buộc | Số lượng lệnh |
| **stop_loss_price** | Decimal | Bắt buộc | Stop loss level (đặt trước) |
| **target_price** | Decimal | Tùy chọn | Target level (nếu có) |
| **realized_pnl_usd** | Decimal | Bắt buộc | Lợi/lỗ thực hiện (USD) |
| **realized_pnl_percent** | Decimal (%) | Bắt buộc | Lợi/lỗ % = realized_pnl / (entry_price × quantity) × 100 |
| **slippage_amount** | Decimal | Bắt buộc | Slippage từ Virtual Order (khác biệt entry signal vs thực tế) |
| **hold_time_minutes** | Integer | Bắt buộc | Thời gian giữ lệnh (tính từ entry → exit) |
| **hold_time_hours** | Decimal | Tính toán | hold_time_minutes / 60 |
| **risk_per_trade_pct** | Decimal (%) | Bắt buộc | % rủi ro của lệnh này (từ RISK_POLICY) |
| **r_multiple** | Decimal | Tính toán | R multiple = realized_pnl / (risk_per_trade_pct × account_balance) |
| **win_loss** | String (enum) | Tính toán | `WIN` (nếu pnl > 0) / `LOSS` (nếu pnl < 0) / `BREAKEVEN` (nếu pnl = 0) |
| **rule_breakdown** | Text | Bắt buộc | Mô tả chi tiết: điều kiện entry vào lệnh (RULE_001-009 nào được áp dụng) |
| **exit_reason_detail** | Text | Bắt buộc | Chi tiết lý do thoát (ví dụ: "RULE_010: Breakout pullback failure detected") |
| **notes** | Text | Tùy chọn | Ghi chú thêm từ trader/AI (ví dụ: "Pin bar xác nhận tốt", "High volatility session") |
| **audit_status** | String (enum) | Tùy chọn | `PENDING` / `REVIEWED` / `VIOLATION` (sau khi audit bằng POST_TRADE_REVIEWER) |
| **audit_notes** | Text | Tùy chọn | Nhận xét từ post-trade reviewer (tuân thủ quy tắc? vi phạm gì?) |
| **created_at** | Timestamp | Bắt buộc | Lúc journal entry được tạo (= khi position CLOSED) |

---

## 3. Cách tính các trường

### 3.1 realized_pnl_percent

```
realized_pnl_percent = (realized_pnl_usd / (entry_price × quantity)) × 100

Ví dụ:
  entry_price: 1.0850
  quantity: 100
  realized_pnl_usd: +0.20 USD
  realized_pnl_percent = (0.20 / (1.0850 × 100)) × 100 = 0.184%
```

### 3.2 hold_time_hours

```
hold_time_hours = hold_time_minutes / 60
```

### 3.3 R Multiple

```
R multiple = realized_pnl / risk_per_trade
           = realized_pnl / (risk_per_trade_pct × account_balance_at_entry)

Ví dụ:
  risk_per_trade_pct: 1% (từ RISK_POLICY)
  account_balance_at_entry: 10,000 USD
  risk_per_trade: 1% × 10,000 = 100 USD
  realized_pnl: +50 USD
  R_multiple: 50 / 100 = +0.5 R (lợi 0.5 lần rủi ro)
```

*Ghi chú: R multiple là chỉ số quan trọng để đánh giá chiến lược — nó biểu thị
mỗi lệnh kiếm được bao nhiêu lần rủi ro, independent của % PnL.*

### 3.4 win_loss

```
if realized_pnl_usd > 0: win_loss = WIN
if realized_pnl_usd < 0: win_loss = LOSS
if realized_pnl_usd = 0: win_loss = BREAKEVEN
```

---

## 4. Format ghi Journal Entry (CSV/JSON/Markdown)

### 4.1 Ví dụ: JSON format

```json
{
  "journal_id": "JNL_20260801_001",
  "trade_number": 1,
  "session_id": "PT_20260801_001",
  "position_id": "POS_20260801_001",
  "symbol": "EUR/USD",
  "direction": "LONG",
  "strategy_id": "TF_001",
  "setup_score": 85,
  "entry_date_time": "2026-08-01T09:30:45Z",
  "entry_price": 1.0851,
  "exit_date_time": "2026-08-01T14:15:30Z",
  "exit_price": 1.0870,
  "exit_reason": "TARGET_HIT",
  "quantity": 100,
  "stop_loss_price": 1.0820,
  "target_price": 1.0900,
  "realized_pnl_usd": 1.90,
  "realized_pnl_percent": 0.175,
  "slippage_amount": 0.0001,
  "hold_time_minutes": 285,
  "hold_time_hours": 4.75,
  "risk_per_trade_pct": 1.0,
  "r_multiple": 1.9,
  "win_loss": "WIN",
  "rule_breakdown": "RULE_001(Trend:UP,25pts) + RULE_002(Structure:VALID,20pts) + RULE_003(Breakout:YES,15pts) + RULE_004(Pullback:VALID,15pts) + RULE_005(Volume:STRONG,10pts) = Total Score: 85",
  "exit_reason_detail": "Target level 1.0900 reached, price phá qua target",
  "notes": "Phiên sáng, volume tốt, entry vào lúc breakout pullback rõ ràng",
  "audit_status": "REVIEWED",
  "audit_notes": "Tuân thủ 100% quy trình: entry hợp lệ, khối lượng đúng công thức, exit theo rule. Lệnh tốt.",
  "created_at": "2026-08-01T14:15:31Z"
}
```

### 4.2 Ví dụ: CSV format (header)

```csv
journal_id,trade_number,session_id,symbol,direction,strategy_id,setup_score,entry_date_time,entry_price,exit_date_time,exit_price,exit_reason,quantity,realized_pnl_usd,realized_pnl_percent,hold_time_minutes,r_multiple,win_loss,rule_breakdown,exit_reason_detail,audit_status
JNL_20260801_001,1,PT_20260801_001,EUR/USD,LONG,TF_001,85,2026-08-01T09:30:45Z,1.0851,2026-08-01T14:15:30Z,1.0870,TARGET_HIT,100,1.90,0.175,285,1.9,WIN,"RULE_001(25) + RULE_002(20) + RULE_003(15) + RULE_004(15) + RULE_005(10) = 85","Target hit",REVIEWED
```

---

## 5. Mối quan hệ với POST_TRADE_REVIEWER Prompt

**Trade Journal Entry là input cho `prompts/POST_TRADE_REVIEWER.md` prompt.**

**Quy trình:**
1. Mỗi position CLOSED → tạo Trade Journal entry.
2. Ghi đầy đủ thông tin vào journal (entry/exit, rule breakdown, PnL, etc.).
3. Truyền journal entry tới POST_TRADE_REVIEWER prompt để audit:
   - Có tuân thủ quy tắc không?
   - Có vi phạm gì không?
   - Có tình huống mới chưa từng gặp không?
4. Reviewer output → cập nhật `audit_status` và `audit_notes` trong journal.
5. Nếu phát hiện vi phạm: ghi vào `research/FAILURE_CASES.md`.
6. Nếu phát hiện tình huống mới: đề xuất update `research/HYPOTHESES.md`.

---

## 6. Ví dụ chi tiết: Journal Entry từng lệnh

### 6.1 Lệnh 1: WIN (Target Hit)

```
journal_id: JNL_20260801_001
trade_number: 1
symbol: EUR/USD, LONG
strategy_id: TF_001
setup_score: 85

entry: 1.0851 (2026-08-01 09:30:45)
exit: 1.0870 (2026-08-01 14:15:30) - TARGET_HIT
realized_pnl: +0.19 USD (+0.175%)
hold_time: 285 minutes (4.75 hours)
r_multiple: +1.9 R (lợi 1.9 lần rủi ro)
win_loss: WIN

rule_breakdown: 
  RULE_001_TREND: 25 pts (HH/HL 3 cặp, trend UP rõ ràng)
  RULE_002_STRUCTURE: 20 pts (Swing high/low hợp lệ, setup theo xu hướng)
  RULE_003_BREAKOUT: 15 pts (Breakout rõ ràng, close vượt swing level)
  RULE_004_PULLBACK: 15 pts (Pullback hợp lệ, không phá ngược)
  RULE_005_VOLUME: 10 pts (Volume 150% SMA, xác nhận rõ)
  Total: 85 pts (>= 80 threshold)

exit_reason_detail: 
  Target level 1.0900 reached at 14:15 UTC. Position đạt target, auto-close.

audit_status: REVIEWED
audit_notes: 
  Tuân thủ 100%: entry chính xác theo quy tắc, khối lượng đúng, exit theo target.
  Lệnh tốt, không vi phạm.
```

### 6.2 Lệnh 2: LOSS (Stop Loss Hit)

```
journal_id: JNL_20260801_002
trade_number: 2
symbol: GBP/USD, SHORT
strategy_id: TF_002
setup_score: 78

entry: 1.2750 (2026-08-01 10:45:00)
exit: 1.2780 (2026-08-01 11:30:15) - STOP_LOSS
realized_pnl: -0.30 USD (-0.236%)
hold_time: 45 minutes
r_multiple: -0.3 R (lỗ 0.3 lần rủi ro)
win_loss: LOSS

rule_breakdown:
  RULE_001_TREND: 20 pts (LH/LL 2 cặp, trend DOWN nhưng yếu)
  RULE_002_STRUCTURE: 15 pts (Structure hơi mập mờ)
  RULE_003_BREAKOUT: 10 pts (Breakout nhưng weak)
  RULE_004_PULLBACK: 12 pts (Pullback ổn nhưng hơi sâu)
  RULE_005_VOLUME: 7 pts (Volume bình thường)
  Total: 78 pts (< 80, nhưng vào vì score 60-79 có thể wait → entry sau)

exit_reason_detail:
  Stop loss 1.2780 hit. Price rebound lên SL level, auto-close bằng SL.

audit_status: REVIEWED
audit_notes:
  Score 78 < 80 threshold, nhưng vào lệnh (setup score borderline).
  Xem lại: có nên vào khi score 60-79 không? 
  Đề xuất: strict hơn, chỉ vào khi score >= 80.
  Vi phạm: Setup score chưa đủ ngưỡng nhưng vẫn vào.
```

### 6.3 Lệnh 3: BREAKEVEN

```
journal_id: JNL_20260801_003
trade_number: 3
symbol: EUR/USD, LONG
strategy_id: TF_001
setup_score: 82

entry: 1.0860
exit: 1.0860 - EXIT_RULE
realized_pnl: 0 USD (0%)
hold_time: 120 minutes
r_multiple: 0 R (hòa vốn)
win_loss: BREAKEVEN

exit_reason_detail:
  RULE_010 triggered: Breakout pullback loss hiệu lực, exit để tránh larger loss.
  Entry hợp lệ, nhưng cấu trúc bị phá hỏng → exit theo rule.

audit_status: REVIEWED
audit_notes:
  Tuân thủ quy trình: exit rule detect đúng, exit ngay.
  Lệnh "tốt" về quy trình (mặc dù hòa vốn), vì tránh được risk lớn hơn.
```

---

## 7. Aggregate Statistics từ Trade Journal

Sau khi có nhiều journal entries, có thể tính aggregate stats:

```
Từ danh sách trades:

Win Rate = Số WIN / (Số WIN + Số LOSS) × 100
Expectancy = Tổng PnL / Số trades
Avg Win = Tổng PnL WIN / Số WIN
Avg Loss = Tổng PnL LOSS / Số LOSS
R/R = Avg Win / Avg Loss
Profit Factor = Gross Profit / Gross Loss
Avg R Multiple = Tổng R / Số trades
Max Consecutive Loss = dãy thua dài nhất
Max Consecutive Win = dãy thắng dài nhất
Avg Hold Time = Tổng hold time / Số trades
```

Các stats này dùng để tính KPI trong PERFORMANCE_DASHBOARD.md.

---

## 8. Lưu trữ và Truy cập Journal

**Tùy chọn lưu trữ:**
1. **JSON lines file**: Mỗi trade là 1 line (easy append, easy parse).
2. **CSV file**: Mỗi trade là 1 row (easy open in Excel).
3. **Database**: Table `trade_journal` (scalable, queryable).
4. **Markdown table**: Human-readable, easy review.

**Tần suất append:**
- Real-time: Mỗi khi position CLOSED, append journal entry ngay.
- Backup: Hàng ngày lưu snapshot journal file.

---

## 9. Liên hệ với các file khác

- **`prompts/POST_TRADE_REVIEWER.md`** → Trade Journal entry là input cho prompt này,
  để audit tuân thủ quy tắc.
- **`research/EXPERIMENT_LOG.md`** → Ghi lại phiên paper trade (summary: ngày, chiến
  lược, số lệnh, PnL), link tới Trade Journal entries của phiên đó.
- **`research/FAILURE_CASES.md`** → Nếu phát hiện vi phạm qua post-trade review,
  ghi vào đây.
- **`paper_trading/POSITION.md`** → Journal tạo từ Position CLOSED.
- **`paper_trading/PERFORMANCE_DASHBOARD.md`** → Dùng journal data để tính KPI
  (win rate, expectancy, Sharpe...).
- **`backtests/KPI_STANDARD.md`** → Định nghĩa KPI, journal cung cấp raw data.

---

## 10. Trạng thái và ghi chú

- **Thiết kế**: Hoàn tất data model, cách tính PnL/R multiple, format ghi journal.
- **Chưa chốt**: Format chính thức lưu trữ (JSON? CSV? Database?), tần suất backup.
- **Cần Project Owner review**: Xác nhận các trường cần thiết, đặc biệt `rule_breakdown`
  (có cần chi tiết từng rule score hay tổng đủ?).
- **Tiếp theo**: Viết PERIODIC_REVIEW.md (daily/weekly/monthly review),
  PERFORMANCE_DASHBOARD.md (KPI hiển thị).
