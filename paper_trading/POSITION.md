# Position — Theo dõi Lệnh Mở

> **Tài liệu thiết kế Position** — Quản lý vòng đời một lệnh từ khi vào (FILLED)
> cho tới khi thoát (CLOSED). Position theo dõi entry price, stop loss, exit
> condition, và tính unrealized PnL real-time. Nó là "bản ghi sinh động" của một
> lệnh đang mở, cập nhật liên tục theo giá thị trường.

---

## 1. Định nghĩa

**Position** là một bản ghi đại diện một lệnh giao dịch đang mở. Nó chứa thông tin
entry, stop loss, target, và theo dõi giá hiện tại để tính unrealized PnL + kiểm
tra exit condition.

---

## 2. Các trường dữ liệu (Data Model)

| Tên trường | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---|---|---|---|
| **position_id** | String/UUID | Bắt buộc | Định danh duy nhất (ví dụ: `POS_20260801_001`) |
| **order_id** | String | Bắt buộc | ID của Virtual Order đã FILLED |
| **account_id** | String | Bắt buộc | ID của Virtual Account |
| **symbol** | String | Bắt buộc | Cặp tiền tệ / mã (ví dụ: `EUR/USD`) |
| **direction** | String (enum) | Bắt buộc | `LONG` / `SHORT` |
| **entry_price** | Decimal | Bắt buộc | Entry price thực tế (từ Virtual Order sau slippage) |
| **quantity** | Decimal | Bắt buộc | Số lượng lệnh |
| **stop_loss_price** | Decimal | Bắt buộc | Stop loss level (từ signal) |
| **target_price** | Decimal | Tùy chọn | Target/Take Profit (từ signal, có thể NULL) |
| **current_price** | Decimal | Bắt buộc | Giá hiện tại (update real-time) |
| **unrealized_pnl** | Decimal | Bắt buộc | Lợi/lỗ chưa thực hiện = (current_price - entry_price) × quantity (LONG), hoặc (entry_price - current_price) × quantity (SHORT) |
| **unrealized_pnl_percent** | Decimal (%) | Tính toán | % return = unrealized_pnl / (entry_price × quantity) × 100 |
| **status** | String (enum) | Bắt buộc | `OPEN` / `CLOSED` / `PARTIAL` (nếu close từng phần, chưa chốt) |
| **opened_at** | Timestamp | Bắt buộc | Thời gian order FILLED (position mở) |
| **closed_at** | Timestamp | Tùy chọn | Thời gian position CLOSED |
| **exit_reason** | String (enum) | Tùy chọn | Lý do thoát: `STOP_LOSS` / `TARGET_HIT` / `EXIT_RULE` / `MANUAL` |
| **exit_price** | Decimal | Tùy chọn | Exit price thực tế (khi closed) |
| **realized_pnl** | Decimal | Tùy chọn | Lợi/lỗ thực hiện (khi closed) |
| **hold_time_minutes** | Integer | Tùy chọn | Thời gian giữ lệnh (tính từ opened_at → closed_at) |
| **exit_rule_trigger** | String | Tùy chọn | Chi tiết rule trigger (ví dụ: "RULE_010: Exit signal từ breakout pullback") |
| **strategy_id** | String | Bắt buộc | Chiến lược dùng (ví dụ: `TF_001`, `TF_002`) |
| **setup_score** | Decimal | Bắt buộc | Setup score từ Rule Engine (để audit) |

---

## 3. Vòng đời Position

```
Virtual Order FILLED → Tạo Position (status = OPEN)
    │
    ├─ Real-time: Update current_price, recalculate unrealized_pnl
    │
    ├─ Kiểm tra Exit Condition (RULE_010 từ Rule Engine)
    │   ├─ Nếu stop_loss hit → exit_reason = STOP_LOSS → CLOSED
    │   ├─ Nếu target_price hit → exit_reason = TARGET_HIT → CLOSED
    │   ├─ Nếu exit_rule trigger → exit_reason = EXIT_RULE → CLOSED
    │   └─ Nếu không → tiếp tục OPEN
    │
    └─ Position CLOSED (status = CLOSED)
        ├─ Tính realized_pnl (exit_price - entry_price) × quantity
        ├─ Tính hold_time
        ├─ Ghi vào Trade Journal
        └─ Cập nhật Virtual Account (balance += realized_pnl, positions_open -= 1)
```

---

## 4. Quy tắc tính PnL

### 4.1 Unrealized PnL (lợi/lỗ chưa thực hiện)

**LONG position:**
```
unrealized_pnl = (current_price - entry_price) × quantity
```

**SHORT position:**
```
unrealized_pnl = (entry_price - current_price) × quantity
```

**Ví dụ:**
```
LONG EUR/USD:
  entry_price: 1.0850
  quantity: 100 units
  current_price: 1.0870
  unrealized_pnl = (1.0870 - 1.0850) × 100 = 0.0020 × 100 = 0.20 USD (lợi 0.2)
  unrealized_pnl_percent = 0.20 / (1.0850 × 100) × 100 = 0.184%
```

### 4.2 Realized PnL (lợi/lỗ đã thực hiện, khi close)

**LONG position:**
```
realized_pnl = (exit_price - entry_price) × quantity
```

**SHORT position:**
```
realized_pnl = (entry_price - exit_price) × quantity
```

---

## 5. Exit Conditions (Điều kiện Thoát)

### 5.1 Stop Loss Hit

**Định nghĩa:**
- Giá chạm mức `stop_loss_price`.

**Hành động:**
- Status = `CLOSED`.
- exit_reason = `STOP_LOSS`.
- exit_price = stop_loss_price (giả định luôn fill tại SL).
- realized_pnl = (SL - entry_price) × quantity (thường âm).
- Ghi vào Trade Journal với reason = "Stop Loss hit".

### 5.2 Target Hit

**Định nghĩa:**
- Giá chạm mức `target_price` (nếu có).

**Hành động:**
- Status = `CLOSED`.
- exit_reason = `TARGET_HIT`.
- exit_price = target_price.
- realized_pnl = (target - entry_price) × quantity (thường dương).
- Ghi vào Trade Journal với reason = "Target hit".

### 5.3 Exit Rule Trigger (RULE_010)

**Định nghĩa:**
- Điều kiện exit từ RULE_010_EXIT.md (ví dụ: breakout pullback loss hiệu lực, exit
  signal từ structure change, trailing stop trigger, etc.).

**Hành động:**
- Status = `CLOSED`.
- exit_reason = `EXIT_RULE`.
- exit_rule_trigger = chi tiết rule (ví dụ: "RULE_010: False break pullback").
- exit_price = current price khi rule trigger.
- realized_pnl = (exit_price - entry_price) × quantity.
- Ghi vào Trade Journal với reason chi tiết.

*Ghi chú: Chi tiết RULE_010_EXIT.md chưa viết. Tạm định: exit rule là bất kỳ điều
kiện exit được định nghĩa trong strategy, không phải chỉ SL/Target.*

### 5.4 Manual Exit

**Định nghĩa:**
- Project Owner hoặc Admin tự thoát lệnh (hiếm gặp trong paper trade tự động).

**Hành động:**
- Status = `CLOSED`.
- exit_reason = `MANUAL`.
- exit_price = được chỉ định thủ công.
- Ghi vào Trade Journal với reason = "Manual close by Project Owner".

---

## 6. Real-time Monitoring (Update current_price)

### 6.1 Update Frequency

**Tần suất cập nhật:** Mỗi bar/tick dữ liệu live mới nhận được (từ API, hoặc mỗi
phút nếu dùng dữ liệu delayed).

*Ghi chú: Chưa chốt tần suất cụ thể (real-time? per-minute? per-5m?) — phụ thuộc
nguồn dữ liệu và yêu cầu Project Owner.*

### 6.2 Hành động mỗi update

```
1. Lấy current_price mới từ market data
2. Recalculate unrealized_pnl
3. Recalculate unrealized_pnl_percent
4. Cập nhật Virtual Account.unrealized_pnl (tổng từ tất cả position mở)
5. Cập nhật Virtual Account.equity = balance + unrealized_pnl
6. Kiểm tra exit condition:
   - Nếu current_price <= stop_loss_price (LONG) / >= stop_loss_price (SHORT)
     → Position CLOSED, exit_reason = STOP_LOSS
   - Nếu current_price >= target_price (LONG) / <= target_price (SHORT) (nếu có target)
     → Position CLOSED, exit_reason = TARGET_HIT
   - Nếu exit_rule condition trigger (RULE_010)
     → Position CLOSED, exit_reason = EXIT_RULE
7. Nếu position không close → tiếp tục giám sát
```

---

## 7. Ví dụ chi tiết: Vòng đời Position LONG

**Scenario: LONG EUR/USD từ 1.0850 → 1.0870 → 1.0815 (thua SL)**

**Thời điểm 1: Order FILLED (09:30)**
```
position_id: POS_20260801_001
order_id: ORD_20260801_001
entry_price: 1.0851 (sau slippage)
quantity: 100
stop_loss_price: 1.0820
target_price: 1.0900
current_price: 1.0851 (entry vừa fill)
unrealized_pnl: 0 USD
status: OPEN
opened_at: 2026-08-01T09:30:45Z
```

**Thời điểm 2: Price di chuyển lên 1.0870 (09:35)**
```
current_price: 1.0870
unrealized_pnl = (1.0870 - 1.0851) × 100 = 0.0019 × 100 = 0.19 USD
unrealized_pnl_percent = 0.19 / (1.0851 × 100) × 100 = 0.175%
status: OPEN (tiếp tục giám sát)
```

**Thời điểm 3: Price giảm đột ngột 1.0815 (09:45, chạm SL)**
```
current_price: 1.0815 (< stop_loss_price 1.0820)
→ Stop Loss Hit!

Tính realized PnL:
realized_pnl = (1.0820 - 1.0851) × 100 = -0.0031 × 100 = -0.31 USD
hold_time_minutes = 15 (từ 09:30 → 09:45)

status: CLOSED
closed_at: 2026-08-01T09:45:30Z
exit_reason: STOP_LOSS
exit_price: 1.0820
realized_pnl: -0.31 USD

→ Ghi vào Trade Journal:
  entry_price: 1.0851
  exit_price: 1.0820
  pnl: -0.31 USD
  hold_time: 15 minutes
  exit_reason: Stop Loss
```

---

## 8. Ví dụ chi tiết: Exit Rule Trigger

**Scenario: SHORT EUR/USD, exit via EXIT_RULE (breakout pullback loss hiệu lực)**

*Tạm định: RULE_010 định nghĩa: Nếu breakout pullback bị phá hỏng (false break),
thì exit.*

```
position_id: POS_20260801_002
entry_price: 1.0850
quantity: 100
direction: SHORT
stop_loss_price: 1.0880
target_price: 1.0800

Real-time monitoring:
- Price: 1.0850 → 1.0845 → 1.0848 → 1.0858 (phá nhẹ pullback level)

RULE_010 check:
- Detect: Breakout pullback loss hiệu lực (price phá lại pullback level)
- Trigger: EXIT_RULE

Exit:
exit_reason: EXIT_RULE
exit_price: 1.0858 (giá khi rule trigger)
realized_pnl = (1.0850 - 1.0858) × 100 = -0.0008 × 100 = -0.08 USD
exit_rule_trigger: "RULE_010: Pullback loss (false break), phá lại pullback level"
```

---

## 9. Partial Close (Nếu chiến lược hỗ trợ)

*Ghi chú: Chưa chốt nếu các chiến lược (TF_001, TF_002) có hỗ trợ partial close
hay không. Nếu có, cần thêm logic:*

```
status: PARTIAL (nếu close 1 phần)
  ├─ closed_quantity: X units (đã close)
  ├─ remaining_quantity: Y units (còn lại, tiếp tục)
  └─ realized_pnl: tính từ closed_quantity
```

Hiện tạm coi: mỗi position chỉ close hoàn toàn (OPEN → CLOSED), không có PARTIAL.

---

## 10. Liên hệ với các file khác

- **`RULE_ENGINE.md`** → Entry price, SL, target từ Trade Signal.
- **`rule_engine/RULE_010_EXIT.md`** → Exit rule trigger (chưa viết, định nghĩa điều
  kiện exit).
- **`strategies/TF_001_BREAKOUT_PULLBACK.md`, `TF_002_TRENDLINE_REACTION.md`** → Chi
  tiết exit rule của từng chiến lược.
- **`paper_trading/VIRTUAL_ORDER.md`** → Position tạo từ Order FILLED.
- **`paper_trading/VIRTUAL_ACCOUNT.md`** → Cập nhật unrealized_pnl, realized_pnl.
- **`paper_trading/TRADE_JOURNAL.md`** → Ghi lại chi tiết position CLOSED.

---

## 11. Trạng thái và ghi chú

- **Thiết kế**: Hoàn tất data model, exit conditions, unrealized/realized PnL tính
  toán.
- **Chưa chốt**:
  - RULE_010_EXIT.md (chi tiết exit rule từng chiến lược).
  - Tần suất update current_price (real-time? per-minute?).
  - Có hỗ trợ partial close hay không (strategy chưa define rõ).
- **Cần Project Owner review**: Exit rule logic, tần suất monitoring.
- **Tiếp theo**: Viết TRADE_JOURNAL.md (ghi chi tiết position CLOSED), PERIODIC_REVIEW.md.
