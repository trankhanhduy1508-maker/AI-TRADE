# Execution Engine — Kiến trúc Thực thi Lệnh

> **Tài liệu thiết kế Execution Engine của AI-TRADE.** Mô tả kiến trúc và luồng xử lý
> để biến Trade Signal (được phát hành bởi Rule Engine) thành lệnh thực thi, hỗ trợ
> cả Paper Trading (giai đoạn 4) và Live Trading (giai đoạn 7) mà không cần viết code
> kết nối broker thật ngay bây giờ. Tất cả quy tắc rủi ro đều từ `risk/RISK_POLICY.md`,
> `risk/KILL_SWITCH_RULES.md`, không AI tự quyết định.

---

## 1. Mục tiêu Execution Engine

**Vai trò chính:**
- Nhận Trade Signal từ Rule Engine (qua Signal Queue) — các signal đã có score >= ngưỡng (80 đề xuất)
- Kiểm tra LẠI mọi giới hạn rủi ro (Risk Gateway — double-check vì có độ trễ giữa phát tín hiệu và thực thi)
- Tạo lệnh chi tiết (Order Manager) với entry, stop loss, take profit, khối lượng (từ risk/POSITION_SIZING.md)
- Gửi lệnh qua Broker Adapter (interface trừu tượng, chưa tích hợp broker cụ thể bây giờ)
- Theo dõi trạng thái Position (Position Manager) — cập nhật thực thi hay giả lập
- Ghi log đầy đủ (Audit Log) mỗi bước để audit/reconcile sau
- Xử lý retry, timeout, error theo quy tắc (không loop vô tận)

**Nguyên tắc thiết kế:**
- **Fail-safe:** Nếu nghi ngờ vi phạm rủi ro, từ chối lệnh (không linh hoạt)
- **Idempotent:** Tránh gửi trùng lệnh nếu retry, bằng order reference
- **Audit-first:** Ghi log trước khi thực thi, không ghi lại sau
- **Layered architecture:** Signal Queue → Risk Gateway → Order Manager → Broker Adapter → Position Manager + Audit Log, mỗi lớp có trách nhiệm riêng

---

## 2. Kiến trúc tổng thể

### 2.1 Các thành phần chính

Execution Engine bao gồm **8 thành phần quy tắc + 1 interface hỗ trợ đa broker**:

| Thành phần | Vai trò | Input | Output | File chi tiết |
|---|---|---|---|---|
| **Signal Queue** | Hàng đợi nhận Trade Signal từ Rule Engine, xử lý tuần tự hoặc theo ưu tiên | Trade Signal (strategy, hướng, entry, SL, target, score) | Signal ở trạng thái QUEUED, PROCESSING, DISPATCHED, DROPPED | SIGNAL_QUEUE.md |
| **Risk Gateway** | Kiểm tra LẠI rủi ro trước khi Order Manager gửi lệnh (double-check do độ trễ) | Signal, trạng thái hiện tại (position đang mở, account balance, portfolio risk) | PASS hoặc REJECT (lý do chi tiết) | RISK_GATEWAY.md |
| **Order Manager** | Tạo lệnh chi tiết (entry, SL, TP, size), gửi qua Broker Adapter | Signal đã qua Risk Gateway, position sizing formula | Lệnh tạo (order_id, status: CREATED), gửi đi (status: SENT) | ORDER_MANAGER.md |
| **Position Manager** | Theo dõi position đang mở, cập nhật trạng thái từ broker/paper, áp dụng exit rule | Lệnh fill từ broker, price stream (nếu có) | Position mở (size, entry, SL, TP, status) | POSITION_MANAGER.md |
| **Retry & Timeout Policy** | Quy tắc retry khi lệnh gửi fail, giới hạn thời gian chờ phản hồi | Lệnh gửi thất bại, tín hiệu timeout | Retry (với backoff), hoặc Fail final | RETRY_TIMEOUT_POLICY.md |
| **Error Handling** | Phân loại lỗi (kỹ thuật vs nghiệp vụ vs dữ liệu), quyết định hành động | Lỗi phát sinh (trong lúc gửi lệnh, xử lý signal...) | Log lỗi, trigger kill switch nếu cần, alert | ERROR_HANDLING.md |
| **Audit Log** | Ghi log append-only mỗi sự kiện (signal nhận, risk check, order gửi, fill, error) | Mọi sự kiện trong Execution Engine | Log entry (timestamp, event_type, signal_id, order_id, detail, result) | AUDIT_LOG.md |
| **Broker Adapter Interface** | Định nghĩa hành vi bắt buộc mà bất kỳ broker adapter nào phải implement | — (interface, không có logic xử lý riêng) | Đặc tả hành vi: place_order, cancel_order, get_position, get_balance... | BROKER_ADAPTER_INTERFACE.md |

### 2.2 Kiến trúc hỗ trợ đa broker (Multi-Broker Support)

```
Execution Engine (logic chung)
    │
    ├─ Risk Gateway (kiểm tra rủi ro) ← áp dụng mọi broker
    ├─ Order Manager (tạo lệnh chung) ← không phụ thuộc broker cụ thể
    │
    └─ Broker Adapter Interface (abstract, không phụ thuộc sàn)
        │
        ├─ Paper Broker Adapter (implementation 1: giả lập, dùng cho paper trading)
        │   ├─ place_order() → Virtual Order (mô phỏng, không real)
        │   ├─ cancel_order()
        │   └─ get_position() → local position cache
        │
        ├─ [Tương lai] MT5 Broker Adapter (implementation 2)
        │   ├─ place_order() → MT5 API
        │   ├─ cancel_order() → MT5 API
        │   └─ get_position() → MT5 account
        │
        ├─ [Tương lai] Binance Broker Adapter (implementation 3)
        │   ├─ place_order() → Binance API
        │   └─ ...
        │
        └─ [Tương lai] Interactive Brokers Adapter...
```

**Hiện tại (Giai đoạn 1-4):**
- Chỉ có **Paper Broker Adapter** (giả lập, xem `paper_trading/` sau)
- Execution Engine được thiết kế để không phụ thuộc hard-code broker MT5/Binance/IB cụ thể
- Thêm broker mới trong tương lai: chỉ cần implement interface này, không sửa Risk Gateway/Order Manager

---

## 3. Luồng xử lý tổng quát (Happy Path)

```
┌─ Trade Signal từ Rule Engine (score >= 80)
│  │ symbol, direction (LONG/SHORT), entry, SL, target,
│  │ risk_amount (%), strategy, score
│  │
│  ↓
├─ Signal Queue
│  │ Kiểm tra deduplicate: có signal cùng symbol đang chờ?
│  │ → Nếu CÓ: REJECT signal thứ 2 (một lệnh cho một symbol)
│  │ → Nếu KHÔNG: thêm vào queue, status = QUEUED
│  │
│  ↓
├─ Risk Gateway ← CỔNG KIỂM TRA RỦI RO (DOUBLE-CHECK)
│  │ Kiểm tra 5 điều:
│  │  1. Rủi ro/lệnh mới <= hạn mức (từ RISK_POLICY.md)
│  │  2. Tổng rủi ro portfolio (đang mở) + mới <= hạn mức
│  │  3. Kill switch chưa kích hoạt?
│  │  4. Số lệnh thua liên tiếp chưa vượt ngưỡng?
│  │  5. Không trùng lặp position hiện có (nếu chính sách cấm)?
│  │
│  │ Nếu ANY check fail → REJECT (log lý do chi tiết)
│  │ Nếu ALL pass → signal được phép tiếp tục
│  │
│  ↓
├─ Order Manager (nếu Risk Gateway pass)
│  │ 1. Tạo order chi tiết:
│  │    - order_id (unique reference, tránh duplicate khi retry)
│  │    - entry_price = signal.entry
│  │    - stop_loss = signal.SL
│  │    - take_profit = signal.target
│  │    - quantity = tính từ formula (risk_amount / (entry - SL))
│  │    - symbol, direction
│  │
│  │ 2. Ghi log: Order CREATED
│  │ 3. Gửi qua Broker Adapter (interface)
│  │    status = SENT (chưa phản hồi)
│  │
│  ↓
├─ Broker Adapter (Paper hoặc Real trong tương lai)
│  │ place_order(order) → gửi order
│  │ Phản hồi: FILLED / PARTIAL / REJECTED / TIMEOUT
│  │
│  ├─ Nếu FILLED ngay → order.status = FILLED, log, chuyển Position Manager
│  ├─ Nếu PARTIAL → đợi fill nốt hoặc cancel nốt (xem RETRY_TIMEOUT_POLICY.md)
│  ├─ Nếu REJECTED → Error Handling (có thể retry nếu lỗi kỹ thuật)
│  └─ Nếu TIMEOUT → Retry Policy (theo quy tắc backoff)
│
│  ↓
├─ Position Manager (khi order FILLED)
│  │ 1. Tạo position entry mới
│  │    - position_id
│  │    - entry_price, entry_size, entry_time
│  │    - stop_loss, take_profit
│  │    - status = OPEN
│  │
│  │ 2. Cập nhật portfolio risk (thêm position mới)
│  │ 3. Theo dõi price stream:
│  │    - Nếu price hit SL → order stop loss fill → position CLOSED (loss)
│  │    - Nếu price hit TP → order take profit fill → position CLOSED (profit)
│  │    - Nếu có exit signal (RULE_010) → apply exit rule
│  │
│  │ 4. Cập nhật back vào Risk Gateway:
│  │    (tái tính portfolio risk sau khi position close)
│  │
│  ↓
└─ Audit Log (ghi đầy đủ mỗi bước)
   - Signal received (timestamp, source, score)
   - Risk Gateway check (pass/reject, reason)
   - Order created (order_id, entry, SL, quantity)
   - Order sent (status, timestamp)
   - Order filled (price, size, timestamp)
   - Position opened (position_id, entry, SL, TP)
   - Position closed (close_price, PnL, exit_reason)
   - Error/Retry (if any)
```

**Error Path (khi có vấn đề):**

```
┌─ Lỗi phát sinh (tại bất kỳ bước nào)
│  │ Ví dụ: signal có data null, broker timeout, network fail...
│  │
│  ↓
├─ Error Handling
│  │ Phân loại: Kỹ thuật (retry được) vs Nghiệp vụ (không retry) vs Dữ liệu (stop an toàn)
│  │
│  ├─ Nếu kỹ thuật (network fail, timeout) → Retry Policy
│  │    └─ Retry theo backoff, max 3 lần, sau đó fail final, log, alert
│  │
│  ├─ Nếu nghiệp vụ (rủi ro vượt hạn, kill switch) → Reject, log, **NO retry**
│  │    └─ Alert Project Owner (risk violated)
│  │
│  └─ Nếu dữ liệu (giá gap lớn, data invalid) → Stop an toàn, log, trigger kill switch
│      └─ Alert Project Owner (data anomaly, check manual)
│
│  ↓
└─ Audit Log (ghi lỗi chi tiết)
   - Error type, timestamp, message, recovery action
```

---

## 4. Quy tắc thiết kế chi tiết

### 4.1 Nguyên tắc "Risk Gateway KHÔNG SAI LẦM"

**Risk Gateway là nơi DÙNG NHẤT để chặn lệnh** (sau Rule Engine). Nếu nghi ngờ vi phạm rủi ro:
- ✅ Chặn lệnh, log lý do chi tiết (có thể audit sau)
- ❌ Không linh hoạt "lần này tạm được", không có ngoại lệ

**Nguyên tắc:** "Vẫn hơn là cứ chặn khi không chắc" (better safe than sorry)

### 4.2 Order ID (Idempotency)

Mỗi lệnh phải có **order_id duy nhất** để tránh gửi trùng khi retry:

```
order_id = "{strategy}_{symbol}_{timestamp}_{random_suffix}"
Ví dụ: TF_001_EURUSD_1720123456_A5F2

Khi retry: sử dụng order_id CŨ (không tạo order_id mới)
Broker adapter sẽ kiểm tra: order_id đã tồn tại? → No duplicate
```

### 4.3 Position vs Order (hai tầng khác nhau)

| Khía cạnh | Order | Position |
|---|---|---|
| **Nơi quản lý** | Order Manager (tầng thực thi) | Position Manager (tầng theo dõi) |
| **Vòng đời** | CREATED → SENT → FILLED → CLOSED | OPEN → (partial/modification nếu có) → CLOSED |
| **Số lượng** | Có thể là 1 order (entry) + 2 orders (SL + TP) hoặc kết hợp | 1 position = 1 entry logic, có thể có nhiều orders tương liên |
| **Tracking** | Theo broker (broker.order_id) | Theo hệ thống (position_id) |
| **Kiên quyết** | Nếu order fail → có thể retry | Nếu position open → theo dõi tới khi close |

**Note:** Paper Trading có thể tách biệt Virtual Order (trong paper_trading/ simulation) vs Order ở Execution Engine này. Sẽ rõ hơn khi viết paper_trading/ — bây giờ giả định chung một Order Manager, Paper Adapter implement riêng.

---

## 5. Các tham số chưa chốt (cần Project Owner xác nhận)

| Tham số | Mục đích | Trạng thái | Ghi chú |
|---|---|---|---|
| **% rủi ro/lệnh** | Tối đa bao nhiêu % vốn được rủi ro mỗi lệnh | ❓ Chưa chốt | Tham chiếu RISK_POLICY.md, ví dụ 1% hoặc 2% |
| **% rủi ro portfolio** | Tối đa tổng rủi ro tất cả position đang mở | ❓ Chưa chốt | Tham chiếu RISK_POLICY.md, ví dụ 5% hoặc 10% |
| **Số lệnh thua liên tiếp** | Bao nhiêu lệnh thua liên tiếp sẽ trigger kill switch | ❓ Chưa chốt | Tham chiếu KILL_SWITCH_RULES.md |
| **% drawdown max** | Mức drawdown tối đa trước khi dừng | ❓ Chưa chốt | Tham chiếu KILL_SWITCH_RULES.md |
| **Retry max times** | Tối đa bao nhiêu lần retry khi gửi lệnh fail | ❓ Chưa chốt, đề xuất 3 | Xem RETRY_TIMEOUT_POLICY.md |
| **Timeout (giây)** | Chờ phản hồi broker bao lâu trước khi coi là fail | ❓ Chưa chốt, đề xuất 30s | Xem RETRY_TIMEOUT_POLICY.md |
| **Backoff strategy** | Khoảng cách retry (exponential, linear?) | ❓ Chưa chốt, đề xuất exponential | Xem RETRY_TIMEOUT_POLICY.md |

---

## 6. Liên hệ với các file khác

**Input từ:**
- `RULE_ENGINE.md` → Trade Signal (score >= 80)
- `rule_engine/RULE_010_EXIT.md` → Exit rule áp dụng khi position mở
- `strategies/TF_001_BREAKOUT_PULLBACK.md`, `TF_002_TRENDLINE_REACTION.md` → Chi tiết signal từ strategy
- `risk/RISK_POLICY.md` → Ngưỡng rủi ro (% vốn, portfolio limit, thua liên tiếp, drawdown)
- `risk/KILL_SWITCH_RULES.md` → Điều kiện kích hoạt kill switch
- `risk/POSITION_SIZING.md` → Công thức tính khối lượng lệnh

**Output đi tới:**
- `paper_trading/PAPER_TRADING_ENGINE.md` (tương lai) → Nếu dùng Paper Broker Adapter
- `backtests/` → Log + kết quả backtest sẽ được sinh từ Audit Log

**Chi tiết các thành phần:**
- `execution/SIGNAL_QUEUE.md`
- `execution/RISK_GATEWAY.md`
- `execution/ORDER_MANAGER.md`
- `execution/POSITION_MANAGER.md`
- `execution/RETRY_TIMEOUT_POLICY.md`
- `execution/ERROR_HANDLING.md`
- `execution/AUDIT_LOG.md`
- `execution/BROKER_ADAPTER_INTERFACE.md`

---

## 7. Trạng thái và ghi chú

- **Thiết kế:** Đã chốt kiến trúc 8 thành phần + interface đa broker
- **Ngôn ngữ:** Tiếng Việt, không code thực
- **Chưa chốt:** Tất cả tham số số (% rủi ro, retry max, timeout...) — xem mục 5
- **Quan trọng:** Execution Engine được thiết kế để hỗ trợ cả Paper Trading (giai đoạn 4) lẫn Live Trading (giai đoạn 7) bằng cách đặc tả broker adapter interface — chưa viết code kết nối broker thật bây giờ, sẽ làm khi chuyển giai đoạn
- **Tiếp theo:** Viết 9 file chi tiết (Signal Queue, Risk Gateway, Order Manager, Position Manager, Retry/Timeout, Error Handling, Audit Log, Broker Adapter)
