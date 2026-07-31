# Paper Trading Engine — Kiến trúc Giao dịch Giả lập

> **Tài liệu thiết kế Paper Trading Engine của AI-TRADE.** Mô tả đầy đủ hệ thống
> giao dịch trên dữ liệu live nhưng không có tiền thật, phục vụ Giai đoạn 4
> (Paper Trade) trong roadmap. Mục tiêu kiểm chứng chiến lược trên dữ liệu chưa
> "nhìn thấy" (out-of-sample) và xác nhận không có vấn đề kỹ thuật trước khi chuyển
> sang giao dịch thật. Toàn bộ quy tắc nhất quán với `DECISIONS.md`, `RULE_ENGINE.md`,
> `risk/RISK_POLICY.md`, và các chiến lược trong `strategies/`.

---

## 1. Kiến trúc tổng thể

### 1.1 Mục tiêu Paper Trading Engine

- **Giao dịch giả lập**: Tiêu thụ Trade Signal từ Rule Engine, mô phỏng execution mà
  không có tiền thật, không kết nối sàn thật.
- **Dữ liệu live**: Dùng giá hiện tại từ API live (hoặc dữ liệu gần thực tế nhất
  được phân phối), không phải dữ liệu backtest đã biết trước.
- **Kiểm chứng chiến lược**: Xác nhận chiến lược từ Rule Engine hoạt động như kỳ
  vọng trên dữ liệu chưa kiểm chứng (out-of-sample).
- **Ghi lại chi tiết**: Mỗi lệnh, mỗi signal, mỗi exit được ghi log đầy đủ để audit
  và phân tích sau này.
- **Quản lý rủi ro luật cứng**: Áp dụng tất cả giới hạn từ `risk/RISK_POLICY.md` và
  `risk/KILL_SWITCH_RULES.md` trong thời gian thực.

### 1.2 Phạm vi (Scope)

- ✅ **Gồm**: Mô phỏng execution, quản lý account ảo, ghi Trade Journal, tính KPI,
  periodic review, hiển thị performance dashboard.
- ❌ **KHÔNG gồm**: Kết nối thật tới sàn giao dịch, thực thi lệnh thật, rút/nạp tiền
  thật, nạp margin thật. Những điều này sẽ được thiết kế ở tài liệu Execution Engine
  riêng (khi cần cho Giai đoạn 7 - Live Trading).
- ❌ **KHÔNG gồm**: Đặt/quản lý lệnh đang mở trên sàn thật (paper trading chỉ mô
  phỏng, không tương tác sàn thật).

### 1.3 Các thành phần chính

| ID | Tên Thành phần | Vai trò | Input | Output |
|---|---|---|---|---|
| 1 | **Virtual Account** | Quản lý vốn ảo, equity, balance, unrealized PnL | Khởi tạo vốn ban đầu, lệnh mở/đóng | Trạng thái tài khoản hiện tại |
| 2 | **Virtual Order** | Mô phỏng execution (giả lập slippage, spread) | Trade Signal từ Rule Engine | Virtual Order (FILLED/REJECTED) + entry price thực tế |
| 3 | **Position** | Theo dõi lệnh mở (entry, stop loss, target, exit rule) | Virtual Order đã FILLED | Position status: OPEN/CLOSED/PARTIAL |
| 4 | **Trade Journal** | Ghi lại chi tiết mỗi lệnh đóng | Position CLOSED + exit reason | Journal entry (entry/exit, PnL, R multiple, thời gian giữ) |
| 5 | **Periodic Review** | Review Daily/Weekly/Monthly | Trade Journal entries, Position data | Review report + cảnh báo nếu cần |
| 6 | **Performance Dashboard** | Tính KPI, hiển thị hiệu suất | Trade Journal entries, Virtual Account | KPI (win rate, drawdown, expectancy...) |

---

## 2. Luồng dữ liệu tổng quát

```
Rule Engine Output (Trade Signal)
    ├─ [Entry, Stop Loss, Target, Risk amount]
    │
    ↓
Virtual Order (Mô phỏng execution)
    ├─ Giả lập slippage/spread
    ├─ Qua Risk Gateway kiểm tra cuối cùng
    ├─ → FILLED (hoặc REJECTED nếu vi phạm rủi ro)
    │
    ↓ (nếu FILLED)
Position (Theo dõi lệnh mở)
    ├─ Entry price, Stop Loss, Target
    ├─ Monitor exit rule (RULE_010 từ Rule Engine)
    ├─ Cập nhật unrealized PnL
    │
    ↓ (khi exit condition xảy ra)
Position CLOSED (Lệnh đóng)
    ├─ Exit price, exit reason, realized PnL
    │
    ↓
Virtual Account (Cập nhật)
    ├─ Thêm realized PnL vào balance
    ├─ Cập nhật equity = balance + unrealized PnL
    │
    ↓
Trade Journal (Ghi lại)
    ├─ Entry/exit info, PnL, R multiple, nguyên nhân
    │
    ↓
Periodic Review & Dashboard
    ├─ Tính KPI, kiểm tra kill switch
    ├─ Hiển thị performance
```

---

## 3. Kiến trúc chi tiết — Mối quan hệ với các thành phần khác

### 3.1 Paper Trading Engine ↔ Rule Engine

- **Input**: Rule Engine phát hành Trade Signal (entry, SL, target, setup score).
- **Xử lý**: Virtual Order nhận signal, mô phỏng execution (thêm slippage/spread giả lập).
- **Output**: Tín hiệu "order filled" hoặc "rejected" (nếu vi phạm rủi ro).

### 3.2 Paper Trading Engine ↔ Risk Gateway (Execution Engine)

- **Mối quan hệ**: Paper Trading Engine sử dụng logic Risk Gateway từ Execution Engine
  để kiểm tra cuối cùng trước khi allow order FILLED.
- **Điểm khác**: Execution Engine (thiết kế song song, cho cả giai đoạn 4 và 7) xử lý
  việc kết nối sàn thật. Paper Trading Engine chỉ mô phỏng việc kết nối đó, không
  thực thi lệnh thật.
- **Tài liệu**: Risk Gateway được định nghĩa trong `execution/RISK_GATEWAY.md` (chưa
  viết, nằm ngoài scope hiện tại).

### 3.3 Paper Trading Engine ↔ Risk Management

- **Tham chiếu**: `risk/RISK_POLICY.md` (giới hạn rủi ro), `risk/POSITION_SIZING.md`
  (công thức khối lượng), `risk/KILL_SWITCH_RULES.md` (dừng khẩn cấp).
- **Áp dụng**: Mỗi lệnh phải tuân thủ giới hạn rủi ro/lệnh, tổng rủi ro danh mục,
  và kiểm tra kill switch sau mỗi lệnh đóng.

### 3.4 Paper Trading Engine ↔ Research/Learning

- **Input để phân tích**: Trade Journal làm input cho `POST_TRADE_REVIEWER.md` prompt
  để audit mỗi lệnh (tuân thủ quy tắc hay không).
- **Ghi nhận sai lầm**: Nếu phát hiện vi phạm hoặc tình huống chưa từng gặp, ghi
  vào `research/FAILURE_CASES.md`.
- **Ghi lại thử nghiệm**: Toàn bộ phiên paper trade ghi vào
  `research/EXPERIMENT_LOG.md` (ngày, chiến lược, kết quả link).

### 3.5 Paper Trading Engine ↔ Performance Dashboard

- **Tái sử dụng KPI**: Các chỉ số dashboard dùng lại từ `backtests/KPI_STANDARD.md`
  (win rate, expectancy, max drawdown, Sharpe, Sortino nếu có...).
- **Phân biệt**: Dashboard paper trade hiển thị **live data** (update real-time hoặc
  per-session), khác với backtest report (historical, fixed data).

---

## 4. Luồng quyết định Virtual Order

```
Trade Signal từ Rule Engine (nhận)
    ↓
Kiểm tra Kill Switch
    ├─ Nếu Kill Switch kích hoạt → REJECT ngay, không tiếp tục
    │
    ├─ Nếu Kill Switch không kích hoạt → tiếp tục
    ↓
Kiểm tra Rủi ro Danh mục (Risk Gateway)
    ├─ Tính: tổng rủi ro đang mở + rủi ro setup mới
    ├─ So sánh: có <= giới hạn danh mục không?
    ├─ Nếu KHÔNG → REJECT (vượt portfolio limit)
    │
    ├─ Nếu CÓ → tiếp tục
    ↓
Mô phỏng Execution
    ├─ Thêm slippage giả định (% dựa trên liquidity/spread)
    ├─ Tính entry price thực tế = setup entry + slippage
    ├─ Ghi log: signal entry vs actual entry (slippage amount)
    │
    ↓
Phát hành Virtual Order
    ├─ Status: FILLED (với entry price thực tế)
    ├─ Hoặc: REJECTED (nếu fail ở các bước trên)
```

---

## 5. Trạng thái lệnh (Order Lifecycle)

```
PENDING
  ├─ Setup phát hiện (waiting for breakout, pullback...)
  │
  └─ FILLED (nhận signal từ Rule Engine, qua Risk Gateway)
       ├─ → Position OPEN
       │
       └─ Position chờ exit condition
            ├─ → CLOSED (stop loss hit, target hit, exit rule trigger)
            │    → Trade Journal entry
            │    → realized PnL
            │
            └─ Hoặc REJECTED
                 └─ Risk Gateway không allow (portfolio limit exceed)
                 └─ Kill Switch kích hoạt
```

---

## 6. Điều kiện pass/fail Giai đoạn 4 (ROADMAP)

### Pass Condition (chuyển sang Giai đoạn 5 - AI Scoring)

1. **Paper trade chạy liên tục ≥ 2-4 tuần** (tùy tần suất signal, market condition).
2. **Kết quả paper trade ±10-20% so với backtest**: Cho phép slippage/spread thực tế,
   nhưng không được khác quá lớn (< 50% PnL backtest = signal có vấn đề).
3. **Không phát hiện bug kỹ thuật lớn**: Missed signal, calculation error, crash,
   etc.
4. **Kill Switch hoạt động đúng**: Khi điều kiện trigger, hệ thống dừng ngay, ghi
   log rõ ràng.
5. **Trade Journal đầy đủ**: Mỗi lệnh ghi lại chi tiết (entry/exit, rule breakdown,
   PnL, thời gian giữ).
6. **Project Owner xác nhận OK**: Không có cảnh báo major, signal tuân thủ quy tắc.

### Fail Condition (quay lại Giai đoạn 3 - Backtest)

1. **Paper trading kém hơn backtest quá nhiều** (< 50% PnL backtest, hoặc more than
   2x drawdown).
   → Điều tra: strategy logic có vấn đề hay slippage giả định sai?
   → Fix strategy / slippage assumption, backtest lại.

2. **Phát hiện lỗi logic trong chiến lược**:
   → Điều chỉnh rules/strategy, backtest lại (không patch trên paper trade).

3. **Quá nhiều vi phạm quy tắc ghi nhận**:
   → Kiểm tra lại Rule Engine output (signal có hợp lệ không), fix code.

---

## 7. Liên hệ với các file khác

**Tài liệu thiết kế Paper Trading Engine tham chiếu:**
- `RULE_ENGINE.md` — Trade Signal input (entry, SL, target, setup score)
- `rule_engine/RULE_010_EXIT.md` — Exit condition áp dụng trong Position
- `risk/RISK_POLICY.md` — Giới hạn rủi ro (% rủi ro/lệnh, % danh mục, drawdown max)
- `risk/POSITION_SIZING.md` — Công thức tính khối lượng lệnh từ SL
- `risk/KILL_SWITCH_RULES.md` — Điều kiện dừng khẩn cấp
- `strategies/TF_001_BREAKOUT_PULLBACK.md`, `TF_002_TRENDLINE_REACTION.md` — Chi tiết chiến lược test
- `backtests/KPI_STANDARD.md` — Định nghĩa KPI (tái sử dụng cho dashboard)
- `backtests/BACKTEST_STANDARD.md` — Chuẩn backtest để so sánh paper trade vs backtest
- `research/EXPERIMENT_LOG.md` — Ghi lại phiên paper trade (date, chiến lược, kết quả link)
- `research/FAILURE_CASES.md` — Ghi ca thất bại phát hiện từ paper trade
- `prompts/POST_TRADE_REVIEWER.md` — Prompt audit mỗi lệnh từ Trade Journal

**Các file con của Paper Trading Engine (tài liệu này):**
- `paper_trading/VIRTUAL_ACCOUNT.md` — Quản lý vốn ảo, equity, balance
- `paper_trading/VIRTUAL_ORDER.md` — Mô phỏng execution, slippage, Risk Gateway
- `paper_trading/POSITION.md` — Theo dõi lệnh mở, exit rule, unrealized PnL
- `paper_trading/TRADE_JOURNAL.md` — Ghi lại chi tiết lệnh đóng
- `paper_trading/PERIODIC_REVIEW.md` — Daily/Weekly/Monthly review
- `paper_trading/PERFORMANCE_DASHBOARD.md` — KPI và hiệu suất

---

## 8. Trạng thái và ghi chú

- **Thiết kế**: Hoàn tất kiến trúc, luồng dữ liệu, mối quan hệ với các thành phần khác.
- **Chưa code**: Toàn bộ file này là thiết kế tài liệu, không có code thực thi. Code
  sẽ được viết sau khi thiết kế được Project Owner xác nhận.
- **Cần Project Owner review**: Xác nhận scope, phạm vi paper trading (có cần mock
  dữ liệu giá hay dùng real-time API?), tần suất update dashboard.
- **Tiếp theo**: Viết 6 file con chi tiết (VIRTUAL_ACCOUNT, VIRTUAL_ORDER, POSITION,
  TRADE_JOURNAL, PERIODIC_REVIEW, PERFORMANCE_DASHBOARD), sau đó audit tính nhất
  quán.
