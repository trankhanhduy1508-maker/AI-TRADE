# Position Manager — Theo dõi và Quản lý Position

> **Tài liệu thiết kế Position Manager của Execution Engine.** Mô tả cách Position Manager
> theo dõi tất cả position đang mở, cập nhật trạng thái từ broker (hoặc paper adapter),
> áp dụng exit rule (RULE_010 từ Rule Engine), và đồng bộ dữ liệu khi mất kết nối tạm thời.

---

## 1. Mục đích Position Manager

**Vai trò chính:**
- Nhận position mới từ Order Manager (khi order fill)
- Lưu trữ + theo dõi tất cả position đang mở
- Cập nhật trạng thái từ broker (hoặc paper simulator)
- Monitor price stream: kiểm tra SL/TP hit, exit signal
- Áp dụng RULE_010 (Exit Rule) từ Rule Engine
- Cập nhật lại Risk Gateway: portfolio_risk_current (để check signal mới)
- Ghi log mỗi thay đổi position (open, update, close)
- Reconcile với broker khi mất kết nối (tương lai, khi có kết nối thật)

**Nguyên tắc:**
- **Source of truth:** Broker adapter (hoặc paper adapter) là nơi lưu trữ position thực tế
- **Local cache:** Position Manager có bản sao local, nếu mất kết nối → reconcile lại
- **Event-driven:** Mỗi thay đổi price, SL/TP hit → cập nhật position
- **Exit discipline:** Tuân thủ RULE_010, không tự quyết định exit

---

## 2. Cấu trúc Position Object

Mỗi position tạo bởi Position Manager:

```
{
  position_id: string (unique, format: {order_id}_pos)
  order_id: string (reference tới order gốc)
  
  symbol: string (EURUSD, BTC/USDT, ...)
  direction: enum (LONG, SHORT)
  
  entry_price: float (giá vào lệnh thực tế từ order.filled_price)
  entry_quantity: float (khối lượng vào thực tế)
  entry_time: datetime (khi order fill)
  
  stop_loss: float (mức dừng lỗ)
  take_profit: float (mục tiêu lợi nhuận, có thể None)
  
  current_price: float (giá hiện tại, cập nhật real-time hoặc per bar)
  current_unrealized_pnl: float (lợi/lỗ chưa hoàn tất)
  current_unrealized_pnl_pct: float (% lợi/lỗ)
  
  status: enum (OPEN, PARTIAL_CLOSE, CLOSED, ERROR)
  
  close_price: float (giá đóng thực tế, nếu closed)
  close_time: datetime
  close_reason: enum (SL_HIT, TP_HIT, EXIT_SIGNAL, MANUAL, ERROR)
  
  realized_pnl: float (lợi/lỗ cuối cùng, nếu closed)
  realized_pnl_pct: float
  
  sl_order_id: string (order ID của SL, nếu riêng)
  tp_order_id: string (order ID của TP, nếu riêng)
  
  last_update_time: datetime
}
```

---

## 3. Luồng xử lý Position

### 3.1 Nhận Position từ Order Manager

```
Input từ Order Manager:
  order: {order_id, symbol, direction, filled_price, filled_quantity, SL, TP, ...}
  
Order Manager → Position Manager:
  "Order filled, tạo position"
  
Position Manager:
  1. Kiểm tra: order.status == FILLED?
  2. Tạo position object:
     position_id = "{order_id}_pos"
     entry_price = order.filled_price
     entry_quantity = order.filled_quantity
     entry_time = order.filled_at
     status = OPEN
  3. Thêm vào list "open_positions"
  4. Cập nhật "portfolio_risk_current" (Risk Gateway cần dùng)
  5. Log: "Position opened"
```

### 3.2 Monitor Price Stream

**Real-time price update** (hoặc per-bar nếu chưa có data real-time):

```
For each position in open_positions:
  1. Lấy current_price (từ broker API hoặc price stream)
  2. Tính unrealized PnL:
     if direction == LONG:
       unrealized_pnl = (current_price - entry_price) * quantity
     else (SHORT):
       unrealized_pnl = (entry_price - current_price) * quantity
     
  3. Cập nhật position.current_price, position.unrealized_pnl
  4. Log: "Position update" (position_id, current_price, unrealized_pnl)
  
  5. Kiểm tra điều kiện thoát:
     a. SL hit? (current_price <= SL nếu LONG, >= SL nếu SHORT)
     b. TP hit? (current_price >= TP nếu LONG, <= TP nếu SHORT)
     c. Exit signal từ RULE_010?
     
  6. Nếu BẤT KỲ điều kiện, tiếp tục 3.3
```

### 3.3 Xử lý Điều kiện Thoát

#### A. SL (Stop Loss) Hit

```
If (direction == LONG && current_price <= SL) OR
   (direction == SHORT && current_price >= SL):
   
  → Close position ngay
  → close_price = SL (hoặc current_price nếu gap)
  → close_reason = SL_HIT
  → Gửi cancel order (nếu có pending TP order)
  → Tính realized_pnl = (close_price - entry_price) * quantity
  → position.status = CLOSED
  → Log: "Position closed - SL hit"
  → Alert: "Loss realized, {realized_pnl}"
```

#### B. TP (Take Profit) Hit

```
If (direction == LONG && current_price >= TP) OR
   (direction == SHORT && current_price <= TP):
   
  → Close position
  → close_price = TP
  → close_reason = TP_HIT
  → Gửi cancel order (nếu có pending SL order)
  → Tính realized_pnl = (close_price - entry_price) * quantity
  → position.status = CLOSED
  → Log: "Position closed - TP hit"
  → Alert: "Profit realized, {realized_pnl}"
```

#### C. Exit Signal (RULE_010)

Áp dụng exit rule từ `rule_engine/RULE_010_EXIT.md`:

```
Kiểm tra: Có exit signal cho symbol này không?
  → Exit signal có thể là:
    - Breakout structure bị phá (false breakout)
    - Trendline bị phá
    - Price action reversal
    - Thời gian exit (tối đa X bar, nếu rule định)
    - Trailing SL được trigger
  
If exit signal triggered:
  → Close position tại current_price (hoặc áp dụng exit strategy)
  → close_reason = EXIT_SIGNAL
  → realized_pnl = (close_price - entry_price) * quantity
  → position.status = CLOSED
  → Log: "Position closed - Exit signal (RULE_010)"
```

#### D. Partial Close (nếu chính sách cho phép)

```
Ví dụ: Đóng một phần position khi TP đạt 50% target
  (chưa chốt chính sách này)
  
Nếu có:
  → close_quantity = entry_quantity * 50%
  → position.status = PARTIAL_CLOSE
  → Tính realized_pnl cho phần đã close
  → Phần còn lại: entry_quantity_remaining = 50%
  → Cập nhật stop loss (có thể trailing)
  → Log: "Position partial close"
```

### 3.4 Cập nhật Portfolio Risk

Mỗi khi position open/close → cập nhật Risk Gateway:

```
portfolio_risk_current = Σ (risk_per_position) cho tất cả open position

Gửi back tới Risk Gateway:
  "Portfolio risk updated: {portfolio_risk_current}%"
  
Risk Gateway dùng trong Check 2 (portfolio limit check)
```

---

## 4. Cấu trúc Local Position Cache

Position Manager duy trì list positions:

```
{
  open_positions: [
    {position_id_1, symbol, direction, entry_price, ...},
    {position_id_2, ...},
    ...
  ]
  
  closed_positions (history): [
    {position_id_old, close_time, close_price, realized_pnl, ...},
    ...
  ]
  
  position_index (tìm nhanh): {position_id → index in open_positions}
}
```

**Lưu trữ:** Chưa chốt là in-memory (dùng Python dict) hay persistent (DB). Hiện giai đoạn 1-4 dùng in-memory, giai đoạn 7 (live) cần persistent DB.

---

## 5. Reconciliation với Broker (tương lai, giai đoạn 7)

**Tình huống:** Mất kết nối tạm thời với broker (network fail, broker down).

**Xử lý:**

```
1. Detect mất kết nối:
   → Không nhận price update > X giây (ví dụ 60s)
   → Alert: "Connection lost"
   
2. Trong khi mất kết nối:
   → KHÔNG close position (vẫn OPEN ở local cache)
   → KHÔNG phát tín hiệu mới (Signal Queue bị block)
   
3. Kết nối trở lại:
   → Reconcile: query broker "list tất cả open position"
   → So sánh local cache vs broker state:
     • Position ở local nhưng không ở broker? (đã close bây giờ)
     • Position ở broker nhưng không ở local? (lỗi, investigate)
     • Position có ở cả 2, nhưng trạng thái khác? (update local)
     
4. Sau reconcile:
   → Cập nhật open_positions list
   → Tiếp tục monitor price stream
   → Log: "Reconciliation completed"
```

**Note:** Bây giờ (giai đoạn 1-4) chưa cần reconcile vì paper adapter không mất kết nối. Sẽ implement giai đoạn 7 khi tích hợp broker thật.

---

## 6. Correlation và Portfolio Risk (Multiple Positions)

Nếu có multiple positions cùng lúc (ví dụ EURUSD LONG + GBPUSD LONG):

```
Nguyên tắc từ MARKET_WIZARDS_LESSONS.md:
  - EUR/GBP có tương quan cao (~0.8) → nên tính gộp rủi ro
  - EUR/JPY có tương quan thấp (~0.2) → có thể tính riêng
  
Portfolio risk tính gộp:
  portfolio_risk = risk_eurusd + risk_gbpusd (tương quan cao)
  
  Nếu chính sách cho phép tối đa portfolio 5%:
    → risk_eurusd (1.5%) + risk_gbpusd (1.5%) = 3% < 5% ✓ OK
    → Nếu có signal thứ 3 risk 2%: 3% + 2% = 5% = limit ✓ OK
    → Signal thứ 4 risk 1%: 5% + 1% = 6% > 5% ✗ REJECT ở Risk Gateway
```

**Note:** Chưa chốt công thức tính tương quan (correlation matrix). Có thể từ công thức đơn giản (tương quan chung cho cặp nào) hay machine learning (sau giai đoạn 6). Hiện giả định simple version.

---

## 7. Các tham số chưa chốt

| Tham số | Mục đích | Trạng thái | Ghi chú |
|---|---|---|---|
| **position_close_method** | Close tại SL/TP hay chờ order fill? | ❓ Chưa chốt | Ảnh hưởng slippage |
| **trailing_sl** | Có trailing SL không, trailing bao nhiêu pips? | ❓ Chưa chốt | RULE_010 chưa định |
| **partial_close_ratio** | Đóng một phần khi TP 50%? | ❓ Chưa chốt | Nâng cao, chưa apply |
| **correlation_matrix** | Cách tính tương quan positions | ❓ Chưa chốt | Simple (chung) hay ML |
| **position_cache_storage** | In-memory hay persistent DB | ❓ Chưa chốt, đề xuất in-memory giai đoạn 1-6 | Persistent DB giai đoạn 7 |

---

## 8. Ví dụ luồng Position Manager

### 8.1 Happy Path: SL + TP

```
1. Order Manager: Order fill EURUSD LONG 0.15 lot @ 1.0800
   
2. Position Manager:
   position_id = TF_001_EURUSD_1720123456_A5F2_pos
   entry_price = 1.0800
   stop_loss = 1.0700
   take_profit = 1.0950
   status = OPEN
   
   Thêm vào open_positions
   portfolio_risk_current += 1.5%
   Log: "Position opened"
   
3. Monitor price (per bar hoặc tick):
   Bar 1: current_price = 1.0820
     unrealized_pnl = (1.0820 - 1.0800) * 0.15 = 0.0030
     unrealized_pnl_pct = 0.003 / (1.0800 * 0.15) = 0.19%
     (vẫn chưa hit SL/TP, HOLD)
   
   Bar 5: current_price = 1.0950
     current_price >= TP (1.0950)
     → Close position
     close_price = 1.0950
     close_reason = TP_HIT
     realized_pnl = (1.0950 - 1.0800) * 0.15 = 0.0225
     realized_pnl_pct = (0.0225 / (1.0800 * 0.15)) * 100 = 1.39%
     
     position.status = CLOSED
     
   portfolio_risk_current -= 1.5% (position closed, không còn rủi ro)
   
   Log: "Position closed - TP hit, profit 0.0225"
```

### 8.2 SL Hit (Loss)

```
1. Position open, entry 1.0800, SL 1.0700

2. Bar 3: current_price = 1.0695
   current_price < SL (1.0700)
   → Close position
   close_price = 1.0700 (hoặc 1.0695 nếu market order)
   close_reason = SL_HIT
   realized_pnl = (1.0700 - 1.0800) * 0.15 = -0.0015
   realized_pnl_pct = -0.96%
   
   position.status = CLOSED
   
   consecutive_losses += 1 (ghi vào Risk Policy state)
   Log: "Position closed - SL hit, loss 0.0015"
```

### 8.3 Exit Signal (RULE_010)

```
1. Position open, entry 1.0800, LONG

2. Bar 10: Check RULE_010 (Exit Rule)
   "Breakout structure bị phá: swing low vừa mở < swing low trước đó"
   → Exit signal triggered
   
3. Position Manager:
   close_price = current_price (1.0750 ví dụ)
   close_reason = EXIT_SIGNAL
   realized_pnl = (1.0750 - 1.0800) * 0.15 = -0.00075
   
   position.status = CLOSED
   Log: "Position closed - Exit signal (RULE_010), loss 0.00075"
```

### 8.4 Multiple Positions

```
1. Position 1: EURUSD LONG, entry 1.0800, risk 1.5%
   portfolio_risk_current = 1.5%
   
2. Position 2: GBPUSD LONG, entry 1.2600, risk 1.5%
   portfolio_risk_current = 1.5% + 1.5% = 3% (tương quan cao)
   
3. Signal mới: USDJPY SHORT, risk 1.5%
   Risk Gateway Check 2:
   portfolio_risk_total = 3% + 1.5% = 4.5% <= 5% (limit)
   → PASS, Order Manager tạo lệnh
   
4. Position 3 open: USDJPY SHORT
   portfolio_risk_current = 4.5%
   
5. EURUSD position close:
   portfolio_risk_current = 4.5% - 1.5% = 3%
   → Dự phòng cho signal mới tiếp theo
```

---

## 9. Liên hệ với các file khác

**Input từ:**
- `execution/ORDER_MANAGER.md` → Position mới (khi order fill)
- `rule_engine/RULE_010_EXIT.md` → Exit signal (khi close position)
- `execution/BROKER_ADAPTER_INTERFACE.md` → Position data từ broker
- Price stream (từ broker API hoặc market data feed)

**Output đi tới:**
- `execution/RISK_GATEWAY.md` → Portfolio risk update (để check signal mới)
- `execution/AUDIT_LOG.md` → Ghi log mỗi thay đổi position
- `research/EXPERIMENT_LOG.md` (tương lai) → Ghi lịch sử trading cho analysis

**Tham chiếu:**
- `knowledge/MARKET_WIZARDS_LESSONS.md` → Nguyên tắc portfolio management, correlation
- `risk/RISK_POLICY.md` → Portfolio risk limit

---

## 10. Trạng thái và ghi chú

- **Thiết kế:** Đã chốt luồng open/close position, monitor price, exit conditions
- **Ngôn ngữ:** Tiếng Việt, không code thực
- **Chưa chốt:** position_close_method, trailing_sl, partial_close, correlation_matrix, cache_storage
- **Quan trọng:** Position Manager lưu local cache (không phải source of truth), broker adapter là source of truth
- **Reconcile:** Giai đoạn 1-4 không cần (paper adapter simple), giai đoạn 7 sẽ implement khi tích hợp broker thật
- **Tiếp theo:** Retry & Timeout Policy (chi tiết trong RETRY_TIMEOUT_POLICY.md)
