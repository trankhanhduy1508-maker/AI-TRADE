# Order Manager — Tạo và Gửi Lệnh

> **Tài liệu thiết kế Order Manager của Execution Engine.** Mô tả cách Order Manager
> nhận signal đã qua Risk Gateway, tạo lệnh chi tiết (entry, SL, TP, khối lượng),
> và gửi qua Broker Adapter Interface. Order Manager là lớp thực thi, không tự quyết định
> rủi ro (Risk Gateway đã check) nhưng bảo đảm tính idempotent và tracking chính xác.

---

## 1. Mục đích Order Manager

**Vai trò chính:**
- Nhận signal đã qua Risk Gateway (PASS)
- Tạo lệnh chi tiết (order object) từ signal
- Tính khối lượng lệnh (từ `risk/POSITION_SIZING.md`)
- Gửi lệnh qua Broker Adapter Interface
- Theo dõi trạng thái lệnh (CREATED → SENT → FILLED/PARTIAL/REJECTED)
- Đảm bảo idempotency (không gửi trùng lệnh nếu retry)
- Ghi log đầy đủ (Audit Log)

**Nguyên tắc:**
- **Không tự quyết định rủi ro:** Risk Gateway đã kiểm tra, Order Manager chỉ thực thi
- **Idempotent:** order_id là duy nhất, retry không tạo duplicate order ở broker
- **Simple:** Tạo lệnh rõ ràng, không xử lý complex logic (exit, trailing SL...) — để Position Manager

---

## 2. Cấu trúc Order Object

Mỗi lệnh tạo bởi Order Manager bao gồm:

```
{
  order_id: string (unique, format: {strategy}_{symbol}_{timestamp}_{random})
  signal_id: string (reference tới signal gốc)
  
  symbol: string (EURUSD, BTC/USDT, ...)
  direction: enum (LONG, SHORT)
  order_type: enum (MARKET, LIMIT) [chưa chốt, giả định MARKET đơn giản]
  
  entry_price: float (từ signal.entry_price)
  stop_loss: float (từ signal.stop_loss)
  take_profit: float (từ signal.take_profit, hoặc None)
  
  quantity: float (tính từ risk/POSITION_SIZING.md)
  
  time_in_force: enum (GTC, IOC, FOK) [chưa chốt, giả định GTC]
  
  status: enum (CREATED, SENT, FILLED, PARTIAL, REJECTED, CANCELED)
  created_at: datetime
  sent_at: datetime (khi gửi broker)
  filled_at: datetime (khi fill)
  filled_price: float (giá thực tế fill, có thể khác entry_price)
  filled_quantity: float (size thực tế fill, có thể < quantity nếu partial)
  
  error_message: string (nếu REJECTED)
  retry_count: int (số lần retry)
}
```

---

## 3. Luồng tạo Order

### 3.1 Nhận Signal từ Risk Gateway

```
Input:
  signal: {symbol, direction, entry, SL, TP, risk_amount_pct, score, ...}
  
Checks:
  - Signal valid? (có đủ trường bắt buộc)
  - Risk Gateway result = PASS?
  
Nếu FAIL checks → Error Handling (không tạo order)
```

### 3.2 Tạo Order ID (Idempotency)

```
Tạo unique order_id:
  timestamp = current_time (unix timestamp, hoặc YYYYMMDD_HHMMSS)
  random_suffix = 4-char random string (hoặc UUID)
  
  order_id = "{signal.strategy}_{signal.symbol}_{timestamp}_{random_suffix}"
  
  Ví dụ: TF_001_EURUSD_1720123456_A5F2
  
Purpose:
  - Broker adapter kiểm tra: order_id đã tồn tại? → No (not duplicate)
  - Nếu retry: dùng order_id CŨ (không tạo ID mới)
```

### 3.3 Tính Khối Lượng Lệnh (Position Sizing)

**Công thức từ `risk/POSITION_SIZING.md`:**

```
Khối lượng lệnh = (Vốn x % rủi ro cho phép) / Khoảng cách Entry → Stop Loss

Trong đó:
  - Vốn: từ Project Owner (chưa chốt)
  - % rủi ro: từ signal.risk_amount_pct (tính bởi Rule Engine)
  - Khoảng cách: abs(entry_price - stop_loss)
  
quantity = (account_capital x risk_amount_pct) / abs(entry - SL)

Làm tròn:
  - Với FOREX: làm tròn tới Lot chuẩn (0.01, 0.1, 1.0 lot)
  - Với Stock: làm tròn tới số cổ phiếu nguyên
  - Với Crypto: làm tròn tới độ chính xác của sàn
```

**Ví dụ minh họa:**

```
account_capital = 10,000 USD
risk_amount_pct = 1.5% (từ signal)
entry_price = 1.0800
stop_loss = 1.0700
distance = 1.0800 - 1.0700 = 0.0100 (100 pips)

quantity = (10,000 x 0.015) / 0.0100
         = 150 / 0.0100
         = 15,000 units = 0.15 lot (hoặc 15 micro lot)
```

### 3.4 Tạo Order Object

```
order = {
  order_id: "TF_001_EURUSD_1720123456_A5F2"
  signal_id: signal.signal_id
  
  symbol: "EURUSD"
  direction: "LONG"
  order_type: "MARKET"
  
  entry_price: 1.0800
  stop_loss: 1.0700
  take_profit: 1.0950 (hoặc None)
  
  quantity: 0.15 (lot)
  
  time_in_force: "GTC"
  
  status: "CREATED"
  created_at: now()
  
  retry_count: 0
}

Log: "Order created" (order_id, symbol, direction, quantity)
```

### 3.5 Gửi Order qua Broker Adapter

```
Call broker_adapter.place_order(order)
  → gửi lệnh tới broker (Paper Adapter hoặc Real Adapter)

Broker Adapter phản hồi:
  ├─ FILLED: lệnh được kích hoạt ngay, fill price nhận được
  ├─ PARTIAL: lệnh fill một phần
  ├─ PENDING: lệnh chưa fill (chờ điều kiện limit order)
  ├─ REJECTED: broker reject (không đủ margin, symbol invalid...)
  └─ TIMEOUT: không có phản hồi trong X giây
  
Order Manager:
  - Cập nhật order.status dựa trên phản hồi
  - order.sent_at = now()
  - Log: "Order sent" (order_id, status_response)
```

---

## 4. Xử lý Phản hồi từ Broker Adapter

### 4.1 FILLED

```
Broker phản hồi: order filled ngay, fill_price = 1.0800 (bằng entry, slippage 0)

Order Manager:
  order.status = FILLED
  order.filled_at = now()
  order.filled_price = 1.0800
  order.filled_quantity = 0.15 (toàn bộ)
  
Log: "Order filled" (order_id, filled_price, filled_quantity)
→ Gửi order tới Position Manager (để tạo position)
```

### 4.2 PARTIAL

```
Broker phản hồi: fill một phần, 0.10 lot đã fill, 0.05 còn pending

Order Manager:
  order.status = PARTIAL
  order.filled_quantity = 0.10
  order.filled_price = 1.0800
  order.pending_quantity = 0.05
  
Xử lý:
  - Tạo position từ filled_quantity (0.10 lot)
  - Còn pending quantity (0.05 lot): chờ fill thêm hoặc cancel
  
Log: "Order partial" (order_id, filled: 0.10, pending: 0.05)
```

### 4.3 REJECTED

```
Broker phản hồi: reject, lý do "insufficient margin"

Order Manager:
  order.status = REJECTED
  order.error_message = "insufficient margin"
  
Xử lý:
  - Không tạo position
  - Error Handling module (xem ERROR_HANDLING.md) quyết định:
    • Nếu lỗi kỹ thuật (broker down) → retry
    • Nếu lỗi nghiệp vụ (margin thực sự không đủ) → final fail, log, alert
    
Log: "Order rejected" (order_id, reason)
```

### 4.4 TIMEOUT

```
Broker không phản hồi trong 30 giây (tham số chưa chốt)

Order Manager:
  order.status = TIMEOUT (tạm thời, chưa phải final)
  
Xử lý:
  - Retry Policy (xem RETRY_TIMEOUT_POLICY.md):
    • Kiểm tra broker: order_id có tồn tại không?
    • Nếu CÓ: order đã tạo, chỉ chưa nhận phản hồi → retry query status
    • Nếu KHÔNG: broker chưa nhận → retry place_order
  - Max retry: 3 lần (chưa chốt)
  
Log: "Order timeout" (order_id) → Retry Policy intervene
```

---

## 5. Idempotency Mechanism

**Mục đích:** Tránh gửi duplicate order khi retry

**Cơ chế:**

```
Mỗi lệnh có order_id duy nhất (không bao giờ thay đổi)

Khi retry:
  1. Lấy order object cũ (từ cache hoặc audit log)
  2. Gửi lại với order_id CŨ
  3. Broker adapter:
     - Query: order_id đã tồn tại? 
     - Nếu CÓ: "OK, order này rồi, trạng thái là..." (không tạo mới)
     - Nếu KHÔNG: tạo order mới với order_id này
     
Result:
  - Dù retry bao nhiêu lần, broker chỉ có 1 order với order_id
  - Không có duplicate order
```

**Ví dụ:**

```
Lần 1: place_order(order_id=TF_001_EURUSD_1720123456_A5F2)
  → Broker: Created, pending fill
  
Network fail, timeout → Retry

Lần 2: place_order(order_id=TF_001_EURUSD_1720123456_A5F2) [same order_id]
  → Broker: "Order TF_001_EURUSD_1720123456_A5F2 already exists, status = pending"
  → No duplicate created

Result: 1 order, not 2
```

---

## 6. Integrasi dengan Position Manager

Khi Order FILLED → Order Manager gửi thông tin tới Position Manager:

```
Signal Order Manager → Position Manager:
  {
    position_id: {order_id}_pos (unique position ID)
    symbol: order.symbol
    direction: order.direction
    entry_price: order.filled_price
    entry_quantity: order.filled_quantity
    entry_time: order.filled_at
    stop_loss: order.stop_loss
    take_profit: order.take_profit
    
    status: OPEN (vừa mới open)
    order_id: order.order_id (reference lại)
  }

Position Manager:
  - Tạo position object
  - Thêm vào tracking list
  - Cập nhật portfolio_risk_current
  - Theo dõi price stream tới khi SL/TP hit hoặc exit signal
```

---

## 7. Order Type và Time-in-Force (chưa chốt)

**Đề xuất hiện tại:**

| Tham số | Giá trị | Lý do |
|---|---|---|
| **order_type** | MARKET | Đơn giản, phản ứng nhanh (reaction, không predict) |
| **time_in_force** | GTC (Good-Till-Canceled) | Lệnh tồn tại tới khi fill hoặc manual cancel |

**Ghi chú:**
- LIMIT order có thể hữu ích (entry tại SL level), nhưng cần chốt entry strategy
- IOC (Immediate or Cancel): fill ngay hoặc cancel, không pending (chưa chốt)
- FOK (Fill or Kill): toàn bộ fill hoặc cancel (chưa chốt)

---

## 8. Các tham số chưa chốt

| Tham số | Mục đích | Trạng thái | Ghi chú |
|---|---|---|---|
| **account_capital** | Vốn tài khoản | ❓ Chưa chốt | Từ Project Owner, dùng cho tính quantity |
| **order_type** | MARKET hay LIMIT | ❓ Chưa chốt, đề xuất MARKET | Loại lệnh gửi broker |
| **time_in_force** | GTC hay IOC hay FOK | ❓ Chưa chốt, đề xuất GTC | Thời gian hiệu lực lệnh |
| **position_sizing_precision** | Làm tròn quantity tới bao nhiêu chữ số | ❓ Chưa chốt | Tùy broker (forex: 0.01 lot, crypto: 0.0001 BTC) |

---

## 9. Ví dụ luồng Order Manager

### 9.1 Happy Path

```
1. Risk Gateway PASS signal:
   signal: EURUSD LONG, entry=1.0800, SL=1.0700, risk=1.5%
   
2. Order Manager nhận signal:
   - Tạo order_id: TF_001_EURUSD_1720123456_A5F2
   - Tính quantity: (10000 x 0.015) / 0.01 = 15000 units = 0.15 lot
   - order.status = CREATED
   - Log: "Order created"
   
3. Gửi order tới Broker Adapter:
   place_order(order)
   
4. Broker Adapter (Paper): 
   - Simulate order: fill ngay tại entry 1.0800
   - Return: status=FILLED, filled_price=1.0800, filled_qty=0.15
   
5. Order Manager:
   - order.status = FILLED
   - order.filled_at = now()
   - order.filled_price = 1.0800
   - Log: "Order filled"
   
6. Gửi Position Manager:
   - Tạo position EURUSD LONG, entry 1.0800, quantity 0.15, SL 1.0700
   - Position.status = OPEN
   
→ Kết quả: Lệnh và position được tạo thành công
```

### 9.2 Timeout + Retry

```
1. Order Manager gửi order tới broker
   broker.place_order(order)
   
2. Network fail, timeout (30s vô phản hồi)
   order.status = TIMEOUT
   order.retry_count = 0
   
3. Retry Policy (xem RETRY_TIMEOUT_POLICY.md):
   - Kiểm tra: order_id TF_001_EURUSD_1720123456_A5F2 có ở broker không?
   - Query broker: "Check order TF_001_EURUSD_1720123456_A5F2"
   
4. Broker response:
   - "Order exists, status = pending"
   
5. Order Manager:
   - order.status = PENDING (đã tạo, chờ fill)
   - Chờ fill, không retry place_order lại
   
→ Kết quả: Tránh duplicate, order được theo dõi
```

### 9.3 REJECTED

```
1. Order Manager gửi order
   - quantity: 10.0 lot (ví dụ, account balance không đủ)
   
2. Broker REJECT:
   - reason: "Insufficient margin for 10.0 lot, max: 2.0 lot"
   
3. Order Manager:
   - order.status = REJECTED
   - order.error_message = "Insufficient margin..."
   - Log: "Order rejected"
   
4. Error Handling:
   - Loại lỗi: kỹ thuật hay nghiệp vụ?
   - "Insufficient margin" = lỗi nghiệp vụ (account thực sự không đủ)
   - Không retry (chỉ retry kỹ thuật)
   - Alert Project Owner
   
→ Kết quả: Lệnh không được tạo, điều tra nguyên nhân (position sizing đúng không?)
```

---

## 10. Liên hệ với các file khác

**Input từ:**
- `execution/RISK_GATEWAY.md` → Signal đã qua risk check (PASS)
- `risk/POSITION_SIZING.md` → Công thức tính khối lượng lệnh
- `risk/RISK_POLICY.md` → Tham chiếu (account capital nếu có)

**Output đi tới:**
- `execution/POSITION_MANAGER.md` → Position tạo khi order fill
- `execution/RETRY_TIMEOUT_POLICY.md` → Xử lý timeout/retry
- `execution/ERROR_HANDLING.md` → Xử lý lỗi REJECTED
- `execution/AUDIT_LOG.md` → Ghi log mỗi step

**Tham chiếu Broker Adapter:**
- `execution/BROKER_ADAPTER_INTERFACE.md` → Interface place_order(), cancel_order(), ...

---

## 11. Trạng thái và ghi chú

- **Thiết kế:** Đã chốt luồng tạo order, idempotency, cấu trúc order object
- **Ngôn ngữ:** Tiếng Việt, không code thực
- **Chưa chốt:** account_capital, order_type, time_in_force, position_sizing_precision
- **Quan trọng:** Order Manager KHÔNG tự quyết định rủi ro (Risk Gateway đã check) — chỉ thực thi theo công thức
- **Tiếp theo:** Tích hợp với Position Manager (chi tiết trong POSITION_MANAGER.md)
