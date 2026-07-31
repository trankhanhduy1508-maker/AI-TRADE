# Broker Adapter Interface — Kiến trúc Hỗ trợ Đa Broker

> **Tài liệu thiết kế Broker Adapter Interface của Execution Engine.** Mô tả kiến trúc
> trừu tượng (interface) mà BẤT KỲ broker/sàn giao dịch nào tương lai đều phải implement,
> để Execution Engine không phụ thuộc hard-code vào 1 sàn cụ thể. Hiện tại chỉ có
> "Paper Broker Adapter" (giả lập), các adapter thật (MT5, Binance, IB...) sẽ implement
> sau trong giai đoạn tương lai (giai đoạn 7 Live Trading).

---

## 1. Mục đích Broker Adapter Interface

**Vai trò chính:**
- Định nghĩa **hành vi bắt buộc** mà bất kỳ broker adapter nào phải implement
- **Decoupling:** Execution Engine không phụ thuộc broker cụ thể (MT5, Binance, IB, v.v.)
- **Consistency:** Dù là broker nào, giao diện đều giống nhau → dễ swap adapter
- **Extensibility:** Thêm broker mới không cần sửa Execution Engine (chỉ thêm adapter mới)
- **Testability:** Paper Adapter dùng cho paper trading (giai đoạn 4), có thể mock cho unit test

**Nguyên tắc:**
- **Interface, không implementation:** Định nghĩa bằng hành vi (behavior spec), không phải code
- **Adapter pattern:** Mỗi broker = 1 adapter riêng, implement interface này
- **Stateless interface:** Adapter không lưu state, Execution Engine lưu (Order Manager, Position Manager)

---

## 2. Broker Adapter Interface — Đặc tả Hành vi

### 2.1 Hành vi bắt buộc (Required Methods)

| Hành vi | Input | Output | Mô tả |
|---|---|---|---|
| **place_order** | order object (symbol, direction, entry, SL, TP, quantity, order_id, timeout) | Response object (status: FILLED/PARTIAL/PENDING/REJECTED/TIMEOUT, filled_price, filled_qty, error_msg) | Gửi lệnh mở position mới tới broker. Phải hỗ trợ entry + SL + TP (hoặc các format khác của broker) |
| **cancel_order** | order_id | Response (status: CANCELED/NOT_FOUND/ERROR, reason) | Hủy lệnh đang pending (chưa fill) |
| **modify_order** | order_id, new_entry (hoặc new_SL/TP nếu có) | Response (status: MODIFIED/ERROR, reason) | Sửa lệnh đang pending (nếu broker hỗ trợ) |
| **get_open_positions** | symbol (optional, None = all) | List of position objects (symbol, direction, entry_price, quantity, entry_time, current_price) | Lấy danh sách tất cả position đang mở (để reconcile) |
| **get_position_by_id** | position_id | Position object hoặc null | Lấy chi tiết 1 position cụ thể |
| **get_account_balance** | none | Response (balance, equity, margin_used, margin_available) | Lấy thông tin tài khoản (balance để tính khối lượng lệnh) |
| **get_market_price** | symbol | Response (bid, ask, last_price, timestamp) | Lấy giá thị trường hiện tại (để check SL/TP hit) |
| **subscribe_price_stream** | symbol, callback | none (async) | Subscribe giá real-time theo dõi SL/TP (nếu broker hỗ trợ, chưa bắt buộc) |
| **close_position** | position_id, close_price (market hoặc limit) | Response (status: CLOSED/ERROR, close_price, realized_pnl) | Đóng position (thường gửi market order) |
| **get_order_status** | order_id | Response (status, filled_price, filled_qty, rejection_reason) | Query trạng thái lệnh (dùng khi timeout, để tránh duplicate) |

---

## 3. Response Object Structure

### 3.1 place_order Response

```
{
  status: enum (FILLED, PARTIAL, PENDING, REJECTED, TIMEOUT)
  
  order_id: string (broker order ID, có thể khác order_id của system nếu broker generate)
  system_order_id: string (order_id từ system)
  
  filled_price: float (giá fill thực tế, nếu filled/partial)
  filled_quantity: float (số lượng fill, nếu filled/partial)
  pending_quantity: float (số còn lại chưa fill, nếu partial)
  
  fill_time: datetime (khi order fill)
  
  error_message: string (nếu rejected/timeout)
  error_code: int (broker error code, nếu có)
  
  slippage: float (pips, entry_price - filled_price, dùng để measure quality)
  
  metadata: dict (thêm thông tin từ broker, nếu cần)
}
```

### 3.2 get_account_balance Response

```
{
  balance: float (USD hoặc currency khác)
  equity: float (balance + unrealized PnL)
  
  margin_used: float (margin đã dùng, hoặc nó được tính từ open positions)
  margin_available: float (margin còn lại)
  
  leverage: float (hoặc null nếu không dùng leverage)
  
  timestamp: datetime (khi lấy thông tin)
  
  currency: string (USD, EUR, ...)
}
```

### 3.3 get_open_positions Response

```
[
  {
    position_id: string (broker position ID)
    symbol: string
    direction: enum (LONG, SHORT)
    
    entry_price: float
    quantity: float
    entry_time: datetime
    
    current_price: float (giá hiện tại)
    unrealized_pnl: float
    unrealized_pnl_pct: float
    
    stop_loss: float (nếu broker lưu)
    take_profit: float (nếu broker lưu)
    
    status: enum (OPEN, CLOSING, CLOSED)
    
    metadata: dict (thêm từ broker)
  },
  ...
]
```

### 3.4 get_market_price Response

```
{
  symbol: string
  bid: float
  ask: float
  last_price: float
  
  timestamp: datetime
  
  spread: float (ask - bid, pips nếu forex)
}
```

---

## 4. Error Handling in Adapter

Mỗi adapter phải xử lý các lỗi sau (và báo cáo về Execution Engine):

| Loại lỗi | Broker Adapter trả về | Execution Engine xử lý (Error Handling) |
|---|---|---|
| **Network fail** | status: TIMEOUT, error_code: CONNECTION_ERROR | Retry Policy (max 3 lần) |
| **Broker timeout** | status: TIMEOUT, error_code: BROKER_TIMEOUT | Retry Policy |
| **Insufficient margin** | status: REJECTED, error_message: "Insufficient margin" | Error Handling: Business Error (no retry) |
| **Invalid symbol** | status: REJECTED, error_message: "Invalid symbol" | Error Handling: Business Error (no retry) |
| **Order size invalid** | status: REJECTED, error_message: "Order size out of range" | Error Handling: Business Error (no retry) |
| **Account suspended** | status: REJECTED, error_message: "Account suspended" | Error Handling: CRITICAL (trigger kill switch) |
| **Market closed** | status: REJECTED, error_message: "Market closed" | Error Handling: Business Error (WAIT hay REJECT) |

---

## 5. Adapter Implementations (Current & Future)

### 5.1 Paper Broker Adapter (Current - Giai đoạn 1-4)

**Mục đích:** Giả lập giao dịch (paper trading), không kết nối broker thật.

**Hành vi:**
- place_order: Mô phỏng fill ngay tại entry_price (giả định perfect fill, hoặc thêm noise sau)
- get_account_balance: Trả về balance giả định (từ config, hoặc tính từ realized PnL)
- get_open_positions: Trả về list position từ cache local (Position Manager)
- get_market_price: Trả về giá từ price feed (data lịch sử hoặc tick data)
- close_position: Mô phỏng close tại current_price

**Lưu ý:** Toàn bộ logic paper trading nằm ở Paper Adapter, Order Manager/Position Manager không biết là paper hay real.

**Ví dụ pseudocode:**

```
class PaperBrokerAdapter implements BrokerAdapterInterface:
  
  def place_order(order):
    # Mô phỏng order fill ngay
    filled_price = order.entry_price  # Giả định perfect fill
    filled_qty = order.quantity
    
    # Thêm noise / slippage nếu muốn simulate realistic
    if config.simulate_slippage:
      slippage = random(0, 2) * pips_to_value  # 0-2 pips random
      filled_price += slippage
    
    return {
      status: "FILLED",
      filled_price: filled_price,
      filled_qty: filled_qty,
      ...
    }
  
  def get_account_balance():
    # Tính từ initial balance + realized PnL
    realized_pnl = sum(position.realized_pnl for all closed positions)
    current_balance = initial_balance + realized_pnl
    
    return {
      balance: current_balance,
      equity: current_balance + sum(unrealized PnL),
      ...
    }
  
  def get_open_positions():
    # Trả về từ local cache
    return position_manager.open_positions
```

---

### 5.2 Future Adapters (Giai đoạn 7+)

**MT5 Broker Adapter (khi tích hợp MetaTrader 5):**

```
class MT5BrokerAdapter implements BrokerAdapterInterface:
  
  def place_order(order):
    # Gọi MT5 API
    mt5.initialize()
    request = {
      "action": ORDER_PLACE,
      "symbol": order.symbol,
      "volume": order.quantity,
      "type": (OP_BUY if order.direction == LONG else OP_SELL),
      "price": order.entry_price,
      "sl": order.stop_loss,
      "tp": order.take_profit,
      "magic": 12345,  # custom ID
      ...
    }
    result = mt5.order_send(request)
    
    if result.retcode == 10009:  # Success
      return {
        status: "FILLED",
        order_id: result.order,
        filled_price: result.price,
        ...
      }
    else:
      return {
        status: "REJECTED",
        error_message: result.comment,
        ...
      }
```

**Binance Spot Adapter (khi tích hợp Binance):**

```
class BinanceBrokerAdapter implements BrokerAdapterInterface:
  
  def place_order(order):
    # Gọi Binance API
    if order.order_type == MARKET:
      side = "BUY" if order.direction == LONG else "SELL"
      
      response = binance_client.order_market(
        symbol=order.symbol,  # "BTCUSDT"
        side=side,
        quantity=order.quantity,
        ...
      )
      
      return {
        status: "FILLED" if response['status'] == 'FILLED' else "REJECTED",
        order_id: response['orderId'],
        filled_price: response['executedQty'],
        ...
      }
```

**Interactive Brokers Adapter (tương tự):**

```
class IBrokerAdapter implements BrokerAdapterInterface:
  # Kết nối IB API...
  # Implement place_order, cancel_order, get_open_positions, ...
```

---

## 6. Adapter Selection & Routing

**Execution Engine không phải hardcode broker:**

```
# Config file (config.yaml hoặc tương tự)
broker_type: "paper"  # hoặc "mt5" hoặc "binance" hoặc "ib"

# Runtime
adapter = get_adapter(config.broker_type)
# adapter = PaperBrokerAdapter() nếu paper
# adapter = MT5BrokerAdapter() nếu mt5
# adapter = BinanceBrokerAdapter() nếu binance

# Execution Engine dùng adapter
response = adapter.place_order(order)
# Không cần biết adapter là paper hay real
```

---

## 7. Testing & Mocking

### 7.1 Unit Test with Mock Adapter

```
class MockBrokerAdapter implements BrokerAdapterInterface:
  
  def place_order(order):
    # Test case 1: always fill ngay
    if test_case == "always_fill":
      return {status: "FILLED", filled_price: order.entry_price}
    
    # Test case 2: always reject
    elif test_case == "always_reject":
      return {status: "REJECTED", error_message: "Mock rejection"}
    
    # Test case 3: timeout
    elif test_case == "timeout":
      return {status: "TIMEOUT", error_code: CONNECTION_ERROR}
```

### 7.2 Integration Test

```
# Chạy full flow với Paper Adapter
adapter = PaperBrokerAdapter()
signal = create_signal(...)
order = create_order(signal)

response = adapter.place_order(order)
assert response.status == "FILLED"
assert position_manager.open_positions.length == 1
```

---

## 8. Adapter Migration Path

**Ví dụ: Migrate từ Paper sang MT5**

```
Giai đoạn 4 (Paper Trading):
  config.broker_type = "paper"
  adapter = PaperBrokerAdapter()
  
Giai đoạn 7 (Live Trading - MT5):
  config.broker_type = "mt5"
  adapter = MT5BrokerAdapter()
  
Thay đổi: Chỉ config + adapter, không thay đổi Execution Engine code
```

---

## 9. Liên hệ với các file khác

**Được gọi bởi:**
- `execution/ORDER_MANAGER.md` → place_order, cancel_order
- `execution/POSITION_MANAGER.md` → get_open_positions, get_market_price, close_position
- `execution/RETRY_TIMEOUT_POLICY.md` → get_order_status (khi query status)

**Tham chiếu:**
- `execution/EXECUTION_ENGINE.md` → Mục "Multi-broker support"
- `ROADMAP.md` → Giai đoạn 4 (Paper), Giai đoạn 7 (Live)

---

## 10. Trạng thái và ghi chú

- **Thiết kế:** Đã chốt 10 hành vi bắt buộc (interface)
- **Ngôn ngữ:** Tiếng Việt (mô tả), nhưng method names + types bằng English (standard)
- **Hiện tại:** Chỉ có Paper Broker Adapter (giả lập, giai đoạn 1-4)
- **Tương lai:** MT5, Binance, IB... adapters sẽ implement interface này khi tích hợp (giai đoạn 7)
- **Quan trọng:** Adapter pattern cho phép swap broker mà không sửa Execution Engine
- **Chưa chốt:** Cách xử lý leverage, margin requirement khác nhau giữa broker (sẽ handle ở adapter layer)
- **Tiếp theo:** Toàn bộ 9 file Execution Engine đã hoàn tất, sẵn sàng cho giai đoạn tiếp theo (code, backtest)

---

## Phụ lục: Adapter Checklist

Khi implement adapter mới, kiểm tra:

- [ ] Implement tất cả 10 hành vi (place_order, cancel_order, ..., get_order_status)
- [ ] Response format khớp với spec (status, order_id, filled_price, ...)
- [ ] Error handling (network fail, broker error, insufficient margin, ...)
- [ ] Timeout handling (broker response > timeout → status TIMEOUT)
- [ ] Unit test tối thiểu (place_order, get_account_balance, get_open_positions)
- [ ] Integration test với Order Manager + Position Manager
- [ ] Idempotency (order_id cùng không tạo duplicate)
- [ ] Logging (ghi log mỗi call, response, error)
- [ ] Documentation (ghi rõ broker-specific behavior, if any)
- [ ] Config (cách setup API key, endpoint, authentication, ...)
