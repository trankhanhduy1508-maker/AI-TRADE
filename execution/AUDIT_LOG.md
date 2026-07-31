# Audit Log — Ghi lại Mọi Sự kiện Thực thi

> **Tài liệu thiết kế Audit Log của Execution Engine.** Mô tả cách ghi lại đầy đủ,
> append-only (không sửa/xóa), tất cả sự kiện trong Execution Engine (signal nhận,
> risk check, order gửi, order fill, error) để phục vụ audit, reconcile paper trade
> vs backtest (giai đoạn 5), và bắt buộc cho live trading giai đoạn 7. Log không chứa
> sensitive data (API key, credential).

---

## 1. Mục đích Audit Log

**Vai trò chính:**
- Ghi **toàn bộ sự kiện** trong Execution Engine (append-only, không sửa/xóa)
- Phục vụ **audit trail** sau: truy xuất lịch sử, reconcile, tìm nguyên nhân
- Hỗ trợ **backtest validation** (giai đoạn 3-5): so sánh backtest vs paper trade vs live
- Bắt buộc cho **live trading** (giai đoạn 7): regulatory + risk management
- Không chứa **sensitive data** (API key, password, account credential)

**Nguyên tắc:**
- **Append-only:** Chỉ thêm, không sửa/xóa (historical record)
- **Timestamped:** Mỗi event có timestamp chính xác (để ordering, latency measure)
- **Detailed:** Ghi đủ context để audit (không generic, phải specific)
- **Non-sensitive:** Không ghi secret key, password

---

## 2. Event Types

### 2.1 Signal Events

| Event type | Mô tả | Thông tin ghi |
|---|---|---|
| **signal_received** | Nhận Trade Signal từ Rule Engine | signal_id, symbol, direction, entry, SL, TP, score, timestamp |
| **signal_queued** | Signal thêm vào queue | signal_id, queue_entry_time, status=QUEUED |
| **signal_processing** | Signal bắt đầu xử lý | signal_id, processing_start_time |
| **signal_dispatched** | Signal qua Risk Gateway, gửi Order Manager | signal_id, order_id_created, queue_exit_time |
| **signal_rejected** | Signal bị reject (Risk Gateway hoặc invalid) | signal_id, rejection_reason, rejection_time |
| **signal_dropped** | Signal bị drop khỏi queue | signal_id, drop_reason (duplicate, timeout, etc), drop_time |

### 2.2 Risk Gateway Events

| Event type | Mô tả | Thông tin ghi |
|---|---|---|
| **risk_check_started** | Bắt đầu kiểm tra rủi ro | signal_id, check_start_time |
| **risk_check_passed** | Signal qua tất cả 5 checks | signal_id, checks_passed=[1,2,3,4,5], pass_time |
| **risk_check_1_failed** | Check 1 fail (risk/trade > limit) | signal_id, risk_actual, risk_limit, fail_time |
| **risk_check_2_failed** | Check 2 fail (portfolio risk > limit) | signal_id, portfolio_risk_total, portfolio_limit, fail_time |
| **risk_check_3_failed** | Check 3 fail (kill switch active) | signal_id, kill_switch_status, fail_time |
| **risk_check_4_failed** | Check 4 fail (consecutive losses) | signal_id, consecutive_losses, threshold, fail_time |
| **risk_check_5_failed** | Check 5 fail (duplicate symbol) | signal_id, symbol, existing_position, fail_time |
| **kill_switch_triggered** | Kill switch tự động kích hoạt | trigger_reason, triggered_at, who_triggered (auto/manual) |
| **kill_switch_reset** | Kill switch được reset | reset_by (Project Owner), reset_at, notes |

### 2.3 Order Manager Events

| Event type | Mô tả | Thông tin ghi |
|---|---|---|
| **order_created** | Lệnh được tạo | order_id, signal_id, symbol, direction, quantity, entry, SL, TP, created_at |
| **order_sent** | Lệnh gửi tới broker | order_id, sent_at, timeout_sec |
| **order_filled** | Lệnh được fill | order_id, filled_price, filled_quantity, filled_at, slippage |
| **order_partial** | Lệnh fill một phần | order_id, filled_qty, pending_qty, filled_at |
| **order_rejected** | Broker reject lệnh | order_id, rejection_reason, rejected_at |
| **order_timeout** | Lệnh timeout (chưa response) | order_id, timeout_at, timeout_sec |
| **order_canceled** | Lệnh bị cancel | order_id, cancel_reason, canceled_at |

### 2.4 Position Manager Events

| Event type | Mô tả | Thông tin ghi |
|---|---|---|
| **position_opened** | Position được tạo (order fill) | position_id, symbol, direction, entry_price, quantity, entry_at, SL, TP |
| **position_updated** | Position update giá (monitoring) | position_id, current_price, unrealized_pnl, update_at |
| **position_sl_hit** | Position hit SL | position_id, close_price, realized_pnl, close_at |
| **position_tp_hit** | Position hit TP | position_id, close_price, realized_pnl, close_at |
| **position_exit_signal** | Position close do exit signal (RULE_010) | position_id, exit_signal_reason, close_price, realized_pnl, close_at |
| **position_closed** | Position đóng (tóm gọn) | position_id, symbol, close_reason, realized_pnl, realized_pnl_pct, close_at |

### 2.5 Retry & Timeout Events

| Event type | Mô tả | Thông tin ghi |
|---|---|---|
| **retry_attempt** | Bắt đầu retry | order_id, retry_count, backoff_delay, retry_at |
| **retry_success** | Retry thành công | order_id, retry_count, result (FILLED/PENDING/...) |
| **retry_max_exceeded** | Max retry exceeded | order_id, retry_count, total_wait_time, failed_at |
| **query_status** | Query broker status (khi timeout) | order_id, query_result (exists/not found/filled), query_at |

### 2.6 Error Events

| Event type | Mô tả | Thông tin ghi |
|---|---|---|
| **error_technical** | Lỗi kỹ thuật (network, timeout) | error_id, error_message, error_code, affected_order_id, occurred_at, recovery_action |
| **error_business** | Lỗi nghiệp vụ (margin, symbol invalid) | error_id, error_message, error_code, affected_order_id, occurred_at, action (no retry) |
| **error_data** | Lỗi dữ liệu (price gap, null field) | error_id, error_message, error_code, affected_position_id, occurred_at, recovery_action |
| **kill_switch_triggered_by_error** | Kill switch trigger bởi lỗi | error_id, error_type, trigger_reason, triggered_at |

### 2.7 System Events

| Event type | Mô tả | Thông tin ghi |
|---|---|---|
| **execution_engine_started** | Execution Engine bắt đầu chạy | start_time, mode (paper/live, chưa chốt), version |
| **execution_engine_stopped** | Execution Engine dừng | stop_time, stop_reason, uptime |
| **portfolio_risk_updated** | Portfolio risk tính lại | portfolio_risk_current, list_open_positions, update_at |

---

## 3. Cấu trúc Log Entry

Mỗi log entry:

```
{
  log_id: string (unique, sequential hoặc UUID)
  timestamp: datetime (YYYY-MM-DD HH:MM:SS.mmm, UTC)
  event_type: string (signal_received, order_filled, error_technical, ...)
  
  signal_id: string (nếu liên quan signal)
  order_id: string (nếu liên quan order)
  position_id: string (nếu liên quan position)
  error_id: string (nếu là lỗi)
  
  details: object (chi tiết tuỳ event type)
    ├─ signal_received: {symbol, direction, entry, SL, score}
    ├─ order_filled: {filled_price, filled_qty, slippage}
    ├─ error_technical: {error_message, error_code, recovery_action}
    ├─ position_closed: {close_reason, realized_pnl, realized_pnl_pct}
    └─ ... (khác)
  
  result: enum (SUCCESS, PARTIAL, REJECTED, ERROR, TIMEOUT)
  
  notes: string (ghi chú bổ sung, không sensitive)
}
```

---

## 4. Lưu trữ Log

### 4.1 Format

**CSV (đơn giản):**

```
log_id,timestamp,event_type,signal_id,order_id,position_id,result,details,notes

1,2024-07-05 10:30:45.123,signal_received,,,,SUCCESS,"symbol=EURUSD,direction=LONG,entry=1.0800,score=92","Rule Engine phát hành setup breakout"

2,2024-07-05 10:30:45.456,signal_queued,sig_001,,,SUCCESS,"status=QUEUED,queue_entry_time=10:30:45.456","Signal vào queue"

3,2024-07-05 10:30:50.123,risk_check_passed,sig_001,,,SUCCESS,"checks_passed=[1,2,3,4,5],pass_time=10:30:50.123","Qua tất cả risk check"
```

**JSON (tương lai, chi tiết hơn):**

```json
{
  "log_id": "1",
  "timestamp": "2024-07-05T10:30:45.123Z",
  "event_type": "signal_received",
  "signal_id": "sig_001",
  "result": "SUCCESS",
  "details": {
    "symbol": "EURUSD",
    "direction": "LONG",
    "entry": 1.0800,
    "score": 92
  }
}
```

### 4.2 Nơi lưu trữ

**Giai đoạn 1-4 (hiện tại):**
- File CSV (append-only, không edit)
- Nơi: `execution_logs/` folder
- Tên file: `execution_log_YYYYMMDD.csv` (rotate daily)
- Ví dụ: `execution_logs/execution_log_20240705.csv`

**Giai đoạn 5-7 (tương lai):**
- Có thể migrate sang database (SQLite / PostgreSQL)
- Hoặc lưu cloud storage
- Nhưng format / columns giữ nguyên để backward compatible

---

## 5. Ví dụ Log Sequence

### 5.1 Happy Path: Signal → Order → Position → Close

```
Log 1:
  timestamp: 10:30:45.123
  event_type: signal_received
  signal_id: sig_001
  result: SUCCESS
  details: {symbol: EURUSD, direction: LONG, entry: 1.0800, score: 92}

Log 2:
  timestamp: 10:30:45.456
  event_type: signal_queued
  signal_id: sig_001
  result: SUCCESS
  details: {status: QUEUED, queue_entry_time: 10:30:45.456}

Log 3:
  timestamp: 10:30:50.123
  event_type: risk_check_passed
  signal_id: sig_001
  result: SUCCESS
  details: {checks_passed: [1,2,3,4,5], portfolio_risk: 3%, limit: 5%}

Log 4:
  timestamp: 10:30:50.456
  event_type: order_created
  order_id: ord_001
  signal_id: sig_001
  result: SUCCESS
  details: {symbol: EURUSD, direction: LONG, quantity: 0.15 lot, entry: 1.0800, SL: 1.0700}

Log 5:
  timestamp: 10:30:50.789
  event_type: order_sent
  order_id: ord_001
  result: SUCCESS
  details: {sent_at: 10:30:50.789, timeout: 30s}

Log 6:
  timestamp: 10:30:51.234
  event_type: order_filled
  order_id: ord_001
  position_id: pos_001
  result: SUCCESS
  details: {filled_price: 1.0800, filled_qty: 0.15, slippage: 0 pips}

Log 7:
  timestamp: 10:35:23.456
  event_type: position_updated
  position_id: pos_001
  result: SUCCESS
  details: {current_price: 1.0850, unrealized_pnl: +0.0075, unrealized_pnl_pct: +0.49%}

... (multiple position_updated logs) ...

Log 10:
  timestamp: 11:15:45.789
  event_type: position_tp_hit
  position_id: pos_001
  result: SUCCESS
  details: {close_price: 1.0950, realized_pnl: +0.0225, realized_pnl_pct: +1.39%}

Log 11:
  timestamp: 11:15:46.123
  event_type: position_closed
  position_id: pos_001
  result: SUCCESS
  details: {symbol: EURUSD, close_reason: TP_HIT, realized_pnl: +0.0225}

Log 12:
  timestamp: 11:15:46.456
  event_type: portfolio_risk_updated
  result: SUCCESS
  details: {portfolio_risk: 2% (down từ 3%)}
```

### 5.2 Error Case: Retry + Recovery

```
Log 1:
  event_type: order_sent
  order_id: ord_002
  result: TIMEOUT
  details: {sent_at: 10:45:00, timeout_reached: 30s}

Log 2:
  event_type: error_technical
  order_id: ord_002
  result: ERROR
  details: {error_message: "Network timeout", recovery_action: "retry"}

Log 3:
  event_type: retry_attempt
  order_id: ord_002
  result: SUCCESS
  details: {retry_count: 1, backoff_delay: 2s, retry_at: 10:45:02}

Log 4:
  event_type: order_filled
  order_id: ord_002
  result: SUCCESS
  details: {filled_price: 1.0800, filled_qty: 0.15}

→ Kết quả: Retry thành công, order fill
```

### 5.3 Error Case: Kill Switch Trigger

```
Log 1:
  event_type: position_closed
  position_id: pos_1
  result: SUCCESS
  details: {close_reason: SL_HIT, realized_pnl: -$100}

Log 2:
  event_type: position_closed
  position_id: pos_2
  result: SUCCESS
  details: {close_reason: SL_HIT, realized_pnl: -$150}

Log 3:
  event_type: position_closed
  position_id: pos_3
  result: SUCCESS
  details: {close_reason: SL_HIT, realized_pnl: -$120}

Log 4:
  event_type: risk_check_4_failed
  signal_id: sig_004
  result: REJECTED
  details: {consecutive_losses: 3, threshold: 3}

Log 5:
  event_type: kill_switch_triggered
  result: SUCCESS
  details: {trigger_reason: "consecutive losses threshold", triggered_at: 11:20:30, who: auto}

Log 6:
  event_type: signal_rejected
  signal_id: sig_005
  result: REJECTED
  details: {rejection_reason: "Kill switch active", rejection_time: 11:20:45}

→ Kết quả: Kill switch kích hoạt auto, signal mới bị reject
```

---

## 6. Query & Analysis

**Sau giai đoạn 4-5, có thể query log để:**

1. **Audit trail:** "Tìm tất cả event của order_id = ord_001"
   ```
   SELECT * FROM audit_log WHERE order_id = 'ord_001' ORDER BY timestamp
   ```

2. **Reconcile:** "So sánh paper trade log vs backtest expectation"
   ```
   SELECT event_type, realized_pnl FROM audit_log 
   WHERE event_type = 'position_closed' AND timestamp BETWEEN '2024-07-01' AND '2024-07-31'
   ```

3. **Error analysis:** "Có bao nhiêu retry? Success rate?"
   ```
   SELECT COUNT(*) as retry_attempts FROM audit_log WHERE event_type = 'retry_attempt'
   SELECT SUM(case when event_type='retry_success' then 1 else 0 end) / COUNT(*) as success_rate
   ```

4. **Performance:** "Order fill time (latency)?"
   ```
   SELECT order_id, 
          (filled_at - sent_at) as fill_latency 
   FROM audit_log WHERE event_type = 'order_filled'
   ```

---

## 7. Sensitive Data Policy

**KHÔNG ghi:**
- API key, secret key, token
- Account number (chỉ ghi symbol, direction, quantity)
- Password, credential
- Tên Project Owner (chỉ ghi "Project Owner")
- Full email, phone (hoặc hash)

**CÓ GHI:**
- symbol, direction, entry, SL, TP (trading decision)
- quantity, realized_pnl (financial outcome)
- error_message, error_code (debugging)
- timestamp, latency (performance)

---

## 8. Log Retention Policy

**Chưa chốt:**

| Loại log | Retention | Lý do |
|---|---|---|
| Daily log (CSV) | 1 năm | Audit, reconcile backtest |
| Error log | Vô hạn | Investigate, learning |
| Sensitive audit | 1 năm | Regulatory (giai đoạn 7) |

---

## 9. Liên hệ với các file khác

**Input từ:**
- Tất cả thành phần Execution Engine (Signal Queue, Risk Gateway, Order Manager, Position Manager, Retry/Timeout, Error Handling)

**Output đi tới:**
- `backtests/` → Backtest analysis (so sánh với actual paper trade)
- `research/EXPERIMENT_LOG.md` (tương lai) → Ghi lịch sử thực thi

**Tham chiếu:**
- `ROADMAP.md` → Giai đoạn 4-5 (Paper Trade, AI Scoring) yêu cầu log audit

---

## 10. Trạng thái và ghi chú

- **Thiết kế:** Đã chốt event types, cấu trúc log entry, format CSV
- **Ngôn ngữ:** Tiếng Việt (comments), nhưng event_type + fields bằng English (consistency)
- **Chưa chốt:** Log storage (file vs DB), retention policy, query tools
- **Quan trọng:** Append-only (không edit/delete), timestamped, non-sensitive
- **Lưu ý:** Log là source of truth cho audit — phải complete, chính xác, không bỏ sót event nào
- **Tiếp theo:** Broker Adapter Interface (file cuối cùng, chi tiết trong BROKER_ADAPTER_INTERFACE.md)
