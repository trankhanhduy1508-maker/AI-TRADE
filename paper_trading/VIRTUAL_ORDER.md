# Virtual Order — Mô phỏng Execution

> **Tài liệu thiết kế Virtual Order** — Xử lý đơn lệnh ảo từ Trade Signal (Rule
> Engine) cho tới khi thực thi hoặc từ chối. Virtual Order mô phỏng các yếu tố
> thực tế như slippage, spread, và kiểm tra rủi ro cuối cùng trước khi cho phép
> execution. Nó là cầu nối giữa Rule Engine (quyết định lý thuyết) và Position
> (theo dõi thực tế).

---

## 1. Định nghĩa

**Virtual Order** là một bản ghi đại diện một lệnh giao dịch ảo. Nó chứa thông tin
from Trade Signal (entry, SL, target) và theo dõi vòng đời từ khi nhận signal cho
tới khi được FILLED hoặc REJECTED.

---

## 2. Loại Order hỗ trợ

| Loại | Mô tả | Ghi chú |
|---|---|---|
| **Market (giả lập)** | Mô phỏng market order: đặt lệnh, thực thi ngay tại giá hiện tại + slippage | Chủ yếu, từ Trade Signal của Rule Engine |
| **Limit (giả lập)** | Mô phỏng limit order: đặt lệnh, chờ đến giá + slippage | Hiện chưa áp dụng (strategy chưa định rõ) |

*Ghi chú: Cả hai loại đều là giả lập trên dữ liệu live, không phải lệnh thật tới
sàn.*

---

## 3. Vòng đời Order (State Machine)

```
PENDING (nhận signal từ Rule Engine)
    ↓
[Kiểm tra Risk Gateway]
    ├─ FAIL → REJECTED (portfolio risk exceed)
    │         → ghi log lý do
    │         → không tạo Position
    │
    └─ PASS → tiếp tục
        ↓
[Mô phỏng Execution]
    ├─ Tính entry price thực tế (+ slippage)
    │
    ↓
FILLED (entry price được xác định)
    ├─ → Tạo Position mới
    ├─ → Cập nhật Virtual Account (positions_open, total_portfolio_risk)
    │
    └─ Hoặc EXPIRED (nếu signal quá cũ, chưa xử lý được)
```

---

## 4. Các trường dữ liệu (Data Model)

| Tên trường | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---|---|---|---|
| **order_id** | String/UUID | Bắt buộc | Định danh duy nhất (ví dụ: `ORD_20260801_001`) |
| **signal_id** | String | Bắt buộc | ID của Trade Signal từ Rule Engine |
| **signal_timestamp** | Timestamp | Bắt buộc | Thời gian phát hành signal |
| **symbol** | String | Bắt buộc | Cặp tiền tệ / mã (ví dụ: `EUR/USD`, `AAPL`) |
| **direction** | String (enum) | Bắt buộc | `LONG` / `SHORT` |
| **order_type** | String (enum) | Bắt buộc | `MARKET` / `LIMIT` |
| **signal_entry_price** | Decimal | Bắt buộc | Entry price từ signal (lý thuyết) |
| **setup_score** | Decimal (0-100) | Bắt buộc | Setup score từ Rule Engine |
| **stop_loss** | Decimal | Bắt buộc | Stop loss level (từ signal) |
| **target_price** | Decimal | Tùy chọn | Target/Take Profit (từ signal, có thể NULL) |
| **quantity** | Decimal | Bắt buộc | Số lượng (tính từ position sizing formula) |
| **signal_risk_amount** | Decimal | Bắt buộc | Risk amount từ signal (% vốn, từ RISK_POLICY) |
| **status** | String (enum) | Bắt buộc | `PENDING` / `FILLED` / `REJECTED` / `EXPIRED` |
| **rejection_reason** | String | Tùy chọn | Lý do nếu REJECTED (ví dụ: "portfolio risk limit exceeded") |
| **actual_entry_price** | Decimal | Tùy chọn | Entry price thực tế (sau slippage) — nếu FILLED |
| **slippage_amount** | Decimal | Tùy chọn | Slippage thực tế = signal_entry_price - actual_entry_price (LONG), hoặc actual - signal (SHORT) |
| **risk_gateway_check** | String | Bắt buộc | Result: `PASS` / `FAIL` (Risk Gateway validation) |
| **risk_gateway_details** | String | Tùy chọn | Chi tiết kiểm tra rủi ro (portfolio risk, limit exceeded by...) |
| **filled_at** | Timestamp | Tùy chọn | Thời gian order được FILLED |
| **rejected_at** | Timestamp | Tùy chọn | Thời gian order REJECTED/EXPIRED |
| **account_id** | String | Bắt buộc | ID của Virtual Account |

---

## 5. Quy trình xử lý Virtual Order

### 5.1 Bước 1: Nhận Trade Signal từ Rule Engine

**Input:**
```
Trade Signal {
  signal_id: "SIG_20260801_001",
  symbol: "EUR/USD",
  direction: "LONG",
  entry_price: 1.0850,
  stop_loss: 1.0820,
  target_price: 1.0900,
  setup_score: 85,
  risk_amount: "1% of account" (từ RISK_POLICY)
}
```

**Xử lý:**
1. Tạo Virtual Order với status = `PENDING`.
2. Lưu tất cả thông tin signal vào order fields.
3. Ghi log nhận signal.

### 5.2 Bước 2: Kiểm tra Kill Switch

**Điều kiện:**
- Nếu Virtual Account status = `KILL_SWITCH`:
  → Order REJECTED ngay, lý do: "Kill switch activated".
  → STOP.

- Nếu Virtual Account status = `ACTIVE`:
  → Tiếp tục Bước 3.

### 5.3 Bước 3: Risk Gateway Validation

**Kiểm tra Rủi ro Danh mục (Portfolio Risk):**

```
Rủi ro lệnh mới = (Signal Risk Amount / 100) × Virtual Account balance
(hoặc dùng công thức từ POSITION_SIZING.md)

Tổng rủi ro sau khi thêm lệnh = 
  Virtual Account.total_portfolio_risk + Rủi ro lệnh mới

Nếu: Tổng rủi ro sau > Giới hạn danh mục (từ RISK_POLICY.md)
  → Risk Gateway FAIL
  → Order REJECTED
  → rejection_reason: "Portfolio risk limit exceeded"
  → risk_gateway_details: "Current: $X, New trade: $Y, Limit: $Z"
  → STOP.

Nếu: Tổng rủi ro sau <= Giới hạn danh mục
  → Risk Gateway PASS
  → Tiếp tục Bước 4.
```

### 5.4 Bước 4: Mô phỏng Execution (Slippage/Spread)

**Giả định Slippage:**

Slippage là sự chênh lệch giữa entry price trong signal và entry price thực tế.
Nguyên nhân: thị trường di chuyển nhanh, liquidity hạn chế, hoặc bid-ask spread.

**Công thức giả định slippage (chưa chốt, cần Project Owner xác nhận):**

```
slippage_pips = (liquidity_rating) × (volatility_factor) × (spread_estimate)

Ví dụ:
- Spread thường: 2 pips (EUR/USD)
- Volatility: 1.5x (thị trường hơi bất ổn)
- Liquidity: Tốt (GOOD) → hệ số 0.5

slippage_pips = 0.5 × 1.5 × 2 = 1.5 pips

Nếu LONG: actual_entry = signal_entry + slippage (xấu hơn)
Nếu SHORT: actual_entry = signal_entry - slippage (xấu hơn)
```

**Ghi lại slippage:**
- `slippage_amount = |signal_entry_price - actual_entry_price|`
- `slippage_pips = slippage_amount / point_value` (tuỳ asset)

*Ghi chú: Con số slippage chưa chốt. Cần Project Owner xác nhận % hoặc pips dùng
giả định, và sau khi paper trade chạy thật, so sánh với slippage thực tế từ dữ liệu
live để điều chỉnh.*

### 5.5 Bước 5: Phát hành Virtual Order

**Nếu tất cả bước trên PASS:**
- status = `FILLED`
- actual_entry_price = signal_entry + slippage (LONG) hoặc signal_entry - slippage
  (SHORT)
- filled_at = timestamp hiện tại
- Tạo Position mới (xem POSITION.md)
- Cập nhật Virtual Account:
  - positions_open += 1
  - total_portfolio_risk += risk_lệnh_mới
  - unrealized_pnl cập nhật (= 0 tại thời điểm fill)

**Nếu Risk Gateway hoặc Kill Switch FAIL:**
- status = `REJECTED`
- rejection_reason = mô tả cụ thể
- rejected_at = timestamp hiện tại
- KHÔNG tạo Position
- KHÔNG cập nhật Virtual Account

**Nếu signal quá cũ (chưa xử lý trong N giây, chưa chốt N):**
- status = `EXPIRED`
- rejected_at = timestamp hiện tại

---

## 6. Ví dụ chi tiết: Một Virtual Order FILLED

**Scenario: LONG EUR/USD**

```
Input Signal (từ Rule Engine):
  signal_id: SIG_20260801_001
  symbol: EUR/USD
  direction: LONG
  signal_entry_price: 1.0850
  stop_loss: 1.0820
  target_price: 1.0900
  setup_score: 85
  signal_risk_amount: 1.0 (1% account)

Virtual Account lúc đó:
  balance: 10,000 USD
  total_portfolio_risk: 2,000 USD (20% × 10,000)
  portfolio_risk_limit: 2,500 USD (25% × 10,000, từ RISK_POLICY)

Xử lý:
1. Tạo order_id: ORD_20260801_001
2. status = PENDING
3. Kill Switch check: ACTIVE → PASS
4. Risk check:
   - Rủi ro lệnh mới = 1% × 10,000 = 100 USD
   - Tổng sau = 2,000 + 100 = 2,100 USD (<= 2,500) → PASS
5. Mô phỏng execution:
   - Spread EUR/USD: 2 pips = 0.0002
   - Volatility: normal (factor = 1.0)
   - Liquidity: GOOD (factor = 0.5)
   - slippage_pips = 0.5 × 1.0 × 2 = 1 pip = 0.0001
   - actual_entry_price = 1.0850 + 0.0001 = 1.0851 (LONG, xấu hơn)
   - slippage_amount = 0.0001 (1 pip)

Output:
  order_id: ORD_20260801_001
  status: FILLED
  actual_entry_price: 1.0851
  slippage_amount: 0.0001 pips
  filled_at: 2026-08-01T09:30:45Z
  risk_gateway_check: PASS
  
Cập nhật Virtual Account:
  positions_open: 1 (từ 0)
  total_portfolio_risk: 2,100 USD (từ 2,000)
  unrealized_pnl: 0 USD (entry vừa fill)
```

---

## 7. Ví dụ chi tiết: Một Virtual Order REJECTED

**Scenario: Vượt portfolio risk limit**

```
Input Signal:
  signal_risk_amount: 1.0 (1% account)

Virtual Account:
  balance: 10,000 USD
  total_portfolio_risk: 2,400 USD (24% × 10,000)
  portfolio_risk_limit: 2,500 USD (25%)

Xử lý:
1. Risk check:
   - Rủi ro lệnh mới = 1% × 10,000 = 100 USD
   - Tổng sau = 2,400 + 100 = 2,500 USD (NOT <= 2,500) → FAIL
   
   Wait: 2,500 = 2,500, bằng nhau → có nên accept không?
   → Định luật: > là reject, >= thì accept? Cần chốt.
   → Tạm định: >= limit → REJECT (safety margin)

Output:
  order_id: ORD_20260801_002
  status: REJECTED
  rejection_reason: Portfolio risk limit exceeded
  risk_gateway_check: FAIL
  risk_gateway_details: Current risk 2,400 + New 100 = 2,500 > Limit 2,500
  rejected_at: 2026-08-01T09:31:20Z

Virtual Account:
  [Không thay đổi — order bị reject]
```

---

## 8. Liên hệ với Risk Gateway (Execution Engine)

- **Virtual Order sử dụng logic Risk Gateway** từ Execution Engine (tài liệu
  `execution/RISK_GATEWAY.md`, chưa viết).
- **Điểm khác**:
  - Virtual Order chỉ mô phỏng risk check (tính toán trên dữ liệu, không kết nối thật).
  - Execution Engine thực thi (kết nối sàn, gửi lệnh thật).
  - Cả hai dùng cùng logic Risk Gateway, nhưng Virtual Order dùng ở Paper Trading
    (giai đoạn 4), Execution Engine dùng cho cả Paper Trading (4) và Live Trading
    (7) sau này.

---

## 9. Ghi log Virtual Order

**Mỗi Virtual Order phải ghi log rõ ràng:**

```
[2026-08-01 09:30:00] ORDER_CREATED
  order_id: ORD_20260801_001
  signal_id: SIG_20260801_001
  symbol: EUR/USD
  direction: LONG
  status: PENDING

[2026-08-01 09:30:01] RISK_GATEWAY_CHECK
  risk_gateway: PASS
  portfolio_risk_before: 2000 USD
  new_risk: 100 USD
  portfolio_risk_limit: 2500 USD

[2026-08-01 09:30:02] EXECUTION_SIMULATION
  signal_entry: 1.0850
  slippage_amount: 0.0001
  actual_entry: 1.0851

[2026-08-01 09:30:03] ORDER_FILLED
  order_id: ORD_20260801_001
  actual_entry_price: 1.0851
  quantity: 100
  status: FILLED
```

---

## 10. Liên hệ với các file khác

- **`RULE_ENGINE.md`** → Trade Signal input (entry, SL, target, setup score).
- **`risk/RISK_POLICY.md`** → Giới hạn portfolio risk để Risk Gateway check.
- **`risk/POSITION_SIZING.md`** → Công thức tính quantity từ vốn/SL.
- **`paper_trading/VIRTUAL_ACCOUNT.md`** → Cập nhật khi order FILLED (positions_open,
  total_portfolio_risk).
- **`paper_trading/POSITION.md`** → Tạo Position mới khi order FILLED.
- **`paper_trading/TRADE_JOURNAL.md`** → Ghi log Virtual Order info khi Position
  CLOSED.
- **`risk/KILL_SWITCH_RULES.md`** → Kiểm tra kill switch trước khi cho phép order
  FILLED.

---

## 11. Trạng thái và ghi chú

- **Thiết kế**: Hoàn tất vòng đời order, risk gateway logic, mô phỏng slippage.
- **Chưa chốt**: 
  - Công thức slippage chính xác (% hoặc pips, dựa vào volatility/liquidity như thế nào).
  - Thời gian hết hạn signal (`EXPIRED`) bao lâu.
  - Portfolio risk limit có accept `==` hay chỉ `<` (safety margin).
- **Cần Project Owner review**: Slippage assumption hợp lý không, risk check logic.
- **Tiếp theo**: Viết POSITION.md (theo dõi position mở), TRADE_JOURNAL.md.
