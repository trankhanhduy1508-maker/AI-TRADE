# Signal Queue — Hàng đợi xử lý Trade Signal

> **Tài liệu thiết kế Signal Queue của Execution Engine.** Mô tả cách hệ thống nhận,
> sắp xếp, xử lý Trade Signal từ Rule Engine (score >= 80), bao gồm deduplication,
> xử lý đa signal cùng lúc, và theo dõi trạng thái signal trong pipeline thực thi.

---

## 1. Mục đích Signal Queue

**Vai trò chính:**
- Nhận Trade Signal từ Rule Engine (output của SCORING SYSTEM từ RULE_ENGINE.md)
- Lưu trữ tạm thời signal (trong bộ nhớ, chưa ghi database — giai đoạn 1-4 chưa có DB)
- Xử lý tuần tự hoặc ưu tiên (FIFO mặc định, hoặc score-based nếu chốt sau)
- **Deduplicate:** Kiểm tra không có 2 signal cùng symbol đang xử lý (một symbol = một position tối đa)
- Cập nhật trạng thái signal: QUEUED → PROCESSING → DISPATCHED → CLOSED (hoặc DROPPED)
- Alert nếu queue bị tắc / quá lâu chưa xử lý

**Nguyên tắc:**
- Không drop signal tùy ý — nếu drop phải có lý do rõ ràng (deduplicate, REJECT từ Risk Gateway)
- FIFO là default, nhưng có thể sort theo score nếu Project Owner muốn ưu tiên setup mạnh hơn
- Signal không được mất trong queue (có log audit)

---

## 2. Cấu trúc Signal

Mỗi Trade Signal từ Rule Engine bao gồm:

```
{
  signal_id: string (unique)
  timestamp: datetime (khi Rule Engine phát hành)
  strategy: string (TF_001, TF_002, ...)
  symbol: string (EURUSD, BTC/USDT, ...)
  direction: enum (LONG, SHORT)
  entry_price: float
  stop_loss: float
  take_profit: float (hoặc None nếu không có target cứng)
  risk_amount_pct: float (% vốn được rủi ro, từ RULE_008)
  setup_score: int (0-100, từ SCORING)
  confidence: enum (HIGH, MEDIUM, LOW) [optional]
  additional_notes: string [optional]
  
  status: enum (QUEUED, PROCESSING, DISPATCHED, CLOSED, DROPPED) ← được cập nhật bởi Signal Queue
  queue_entry_time: datetime (khi thêm vào queue)
  queue_exit_time: datetime (khi rời queue)
  rejection_reason: string (nếu DROPPED)
}
```

---

## 3. Luồng xử lý Signal trong Queue

### 3.1 Nhận Signal từ Rule Engine

1. **Kiểm tra signal valid:**
   - Có đủ các trường bắt buộc? (symbol, direction, entry, SL, score)
   - Score >= 80 (ngưỡng từ RULE_ENGINE.md)?
   - Timestamp hợp lệ (không quá cũ)?
   - Nếu KHÔNG valid → reject ngay, log lý do, **không thêm vào queue**

2. **Nếu valid → thêm vào queue:**
   - signal.status = QUEUED
   - signal.queue_entry_time = now()
   - Ghi audit log: "Signal received" (signal_id, strategy, symbol, score)

### 3.2 Deduplication (cơ chế quan trọng)

**Quy tắc:** Không được có 2 signal cùng symbol đang chờ xử lý hoặc đang PROCESSING.

```
┌─ Signal mới đến (symbol = EURUSD)
│
├─ Kiểm tra queue + current processing:
│  │ Có signal EURUSD ở trạng thái QUEUED hoặc PROCESSING?
│  │
│  ├─ Nếu CÓ (signal cũ chưa xử lý xong):
│  │  → REJECT signal mới
│  │  → reason: "Duplicate symbol in queue"
│  │  → log audit
│  │  → return (không thêm vào queue)
│  │
│  └─ Nếu KHÔNG:
│     → Thêm signal mới vào queue
```

**Lý do:** Tránh mở 2 lệnh cùng symbol cùng lúc (nếu chính sách cấm).

**Lưu ý:** Nếu có 1 position EURUSD đang mở (từ lệnh trước), signal EURUSD mới sẽ:
- Được thêm vào queue (vì position manager khác queue)
- Nhưng Risk Gateway sẽ check "đã có position EURUSD?" → reject (nếu chính sách không cho trùng symbol)
- Signal sẽ được mark DROPPED ở Risk Gateway, không phải ở Queue

---

## 3.3 Xử lý tuần tự hoặc ưu tiên

**Mode default: FIFO (First In First Out)**
- Signal đầu tiên vào queue được xử lý trước
- Tuyến tính, đơn giản

**Mode optional: Score-based Priority** (chưa chốt, tùy Project Owner)
- Signal có score cao hơn được xử lý trước
- Ví dụ: 95 score vào queue sau, nhưng xử lý trước signal 82 score
- Cần chốt: score threshold nào được ưu tiên, hay tất cả 80+ đều xếp hạng?

**Ghi chú:** Hiện chưa chốt, để mục tiêu cơ bản là FIFO. Nếu sau nếu muốn ưu tiên, cập nhật logic ở đây.

### 3.4 Xử lý signal từ Queue

1. **Lấy signal từ queue (đứng đầu)**
   - signal.status = PROCESSING
   - signal.processing_start_time = now()
   - Ghi audit log: "Signal processing started"

2. **Gửi signal tới Risk Gateway**
   - Risk Gateway kiểm tra rủi ro (chi tiết xem RISK_GATEWAY.md)
   - Risk Gateway trả về: PASS hoặc REJECT

3. **Nếu Risk Gateway PASS:**
   - Signal được gửi tới Order Manager
   - Order Manager tạo lệnh, gửi Broker Adapter
   - signal.status = DISPATCHED (lệnh đã gửi đi, chờ phản hồi broker)
   - signal.queue_exit_time = now()
   - Ghi audit log: "Signal dispatched to Order Manager"

4. **Nếu Risk Gateway REJECT:**
   - Signal **không được gửi** tới Order Manager
   - signal.status = DROPPED
   - signal.rejection_reason = (lý do từ Risk Gateway)
   - signal.queue_exit_time = now()
   - Ghi audit log: "Signal rejected at Risk Gateway" (lý do chi tiết)

---

## 4. Trạng thái Signal trong Queue

| Trạng thái | Ý nghĩa | Khi nào | Tiếp theo |
|---|---|---|---|
| **QUEUED** | Signal vừa đến, chờ xử lý | Thêm vào queue | PROCESSING (xử lý signal tiếp theo) |
| **PROCESSING** | Signal đang được Risk Gateway kiểm tra | Lấy từ queue để kiểm tra | DISPATCHED hoặc DROPPED |
| **DISPATCHED** | Signal qua Risk Gateway, lệnh đã gửi Order Manager, chờ broker phản hồi | Order Manager tạo + gửi lệnh | CLOSED (khi order fill hoặc cancel) |
| **CLOSED** | Signal xử lý xong (order filled hoặc cancel sau do exit rule) | Order đã fill/cancel, position đã close hoặc vẫn mở (tracking bởi Position Manager) | — (khỏi queue) |
| **DROPPED** | Signal bị loại (reject ở Risk Gateway hoặc invalid từ đầu) | Risk Gateway reject hoặc invalid check | — (khỏi queue, ghi lý do) |

---

## 5. Xử lý Backpressure (Queue tắc)

**Tình huống:** Queue tích tụ quá nhiều signal chưa xử lý.

**Nguyên nhân:**
- Risk Gateway hoặc Order Manager chậm (xử lý lâu)
- Broker adapter bị timeout (signal stuck ở PROCESSING)
- Quá nhiều signal tới cùng lúc (market volatile)

**Xử lý:**
1. **Monitor queue size:** Nếu > N signal (ví dụ 10), ghi alert
2. **Timeout mechanism:**
   - Nếu signal ở PROCESSING lâu hơn X giây (ví dụ 60s) → coi là fail, move to DROPPED, log "timeout in queue"
   - Không để signal "chết" vô thời hạn trong PROCESSING
3. **Priority:** Nếu áp dụng score-based priority, signal low score có thể bị skip (ghi log)
4. **Alert:** Thông báo Project Owner nếu queue không xử lý được (không phải drop tùy ý, phải investigate)

---

## 6. Deduplicate Details

### 6.1 Kiểm tra duplicates

**Khi signal mới đến:**

```
signal_in = new_signal
existing_signals = list all signals ở trạng thái QUEUED hoặc PROCESSING

for each existing in existing_signals:
  if existing.symbol == signal_in.symbol:
    → REJECT signal_in
    → reason = "Duplicate symbol in queue"
    → return

→ ADD signal_in to queue
```

### 6.2 Trường hợp đặc biệt

| Trường hợp | Xử lý |
|---|---|
| Signal EURUSD đã DISPATCHED (Order Manager đang xử lý), signal EURUSD mới tới | ✅ ACCEPT (vì DISPATCHED không còn ở queue). Nhưng Risk Gateway sẽ check position, có thể reject |
| 2 signal cùng symbol, cùng direction, nhưng entry/SL khác → TRY2 retry của signal cũ? | Nếu order_id khác → coi là 2 signal khác nhau. Nếu order_id giống (retry) → check idempotency, không duplicate |
| Signal SHORT EURUSD + Long GBP/USD cùng lúc → Có vấn đề? | ✅ OK, 2 symbol khác nhau, không cấm |

---

## 7. Các tham số chưa chốt

| Tham số | Mục đích | Trạng thái | Ghi chú |
|---|---|---|---|
| **Chế độ xử lý signal** | FIFO hay Score-based priority | ❓ Chưa chốt, đề xuất FIFO | Ảnh hưởng hiệu suất nếu signal nhiều |
| **Queue max size** | Tối đa bao nhiêu signal trong queue | ❓ Chưa chốt, đề xuất 50 | Nếu vượt → alert, không auto drop |
| **Processing timeout** | Chờ signal bao lâu trước khi coi fail | ❓ Chưa chốt, đề xuất 60s | Xem mục Backpressure |
| **Alert threshold** | Queue size bao nhiêu sẽ trigger alert | ❓ Chưa chốt, đề xuất 10 | Thông báo Project Owner |

---

## 8. Ví dụ luồng xử lý

### 8.1 Happy Path

```
1. Rule Engine phát hành:
   signal_1: EURUSD LONG, score=92
   signal_2: GBP/USD SHORT, score=85
   
2. Queue nhận signal_1:
   → Check valid: OK (score >= 80)
   → Check duplicate: queue rỗng, OK
   → Add to queue: signal_1.status = QUEUED
   
3. Queue xử lý signal_1:
   → Pop from queue: signal_1.status = PROCESSING
   → Send to Risk Gateway
   → Risk Gateway: check rủi ro → PASS
   → Send to Order Manager
   → signal_1.status = DISPATCHED
   → signal_1.queue_exit_time = now()
   
4. Queue nhận signal_2 (cùng lúc):
   → Check valid: OK (score >= 80)
   → Check duplicate: queue chỉ còn DISPATCHED signal_1, không xung đột (EURUSD ≠ GBP/USD)
   → Add to queue: signal_2.status = QUEUED
   
5. Queue xử lý signal_2:
   → Pop from queue: signal_2.status = PROCESSING
   → Send to Risk Gateway
   → Risk Gateway: check portfolio risk (EURUSD LONG + GBP/USD SHORT) → PASS
   → Send to Order Manager
   → signal_2.status = DISPATCHED
   
→ Kết quả: 2 lệnh được gửi tới broker (nếu broker adapter là real, sẽ đặt 2 lệnh cùng lúc)
```

### 8.2 Duplicate Case

```
1. Queue nhận signal_1: EURUSD LONG
   → Add to queue, signal_1.status = QUEUED
   
2. Queue start processing signal_1:
   → signal_1.status = PROCESSING
   → Chậm do Risk Gateway kiểm tra lâu (chờ data)
   
3. Rule Engine phát hành signal_2: EURUSD SHORT (contradicting)
   → Queue nhận signal_2
   → Check duplicate: signal_1 đang PROCESSING, symbol = EURUSD
   → REJECT signal_2
   → reason = "Duplicate symbol in queue"
   → log audit: "Signal rejected: EURUSD already processing"
   → signal_2.status = DROPPED
   
→ Kết quả: Chỉ signal_1 được xử lý, signal_2 bị drop
```

### 8.3 Risk Gateway Reject

```
1. Queue nhận signal_1: EURUSD LONG, risk_pct = 2%
   → Add to queue
   
2. Queue xử lý signal_1:
   → Risk Gateway check: portfolio risk = 1.5% (đã có EUR position)
   → 1.5% + 2% = 3.5% > limit 3% (giả định)
   → Risk Gateway: REJECT
   → signal_1.status = DROPPED
   → rejection_reason = "Portfolio risk exceeds limit (3.5% > 3%)"
   → Log: "Signal rejected at Risk Gateway"
   
→ Kết quả: Signal không được gửi Order Manager, signal_1 khỏi queue
```

---

## 9. Liên hệ với các file khác

**Input từ:**
- `RULE_ENGINE.md` → Trade Signal (output của Scoring System)

**Output đi tới:**
- `execution/RISK_GATEWAY.md` → Signal được gửi để kiểm tra rủi ro
- `execution/AUDIT_LOG.md` → Ghi log mỗi sự kiện của signal (received, processed, dispatched, dropped)

**Tham chiếu:**
- `DECISIONS.md` → Nguyên tắc "Reaction, không prediction"
- `risk/RISK_POLICY.md` → Giới hạn rủi ro (dùng cho dedup logic nếu chính sách cấm trùng symbol)

---

## 10. Trạng thái và ghi chú

- **Thiết kế:** Đã chốt cấu trúc Signal Queue, deduplication, trạng thái
- **FIFO default:** Xử lý tuần tự, đơn giản, có thể thay bằng score-based sau
- **Chưa chốt:** Queue size, timeout, alert threshold
- **Quan trọng:** Signal không được drop tùy ý — nếu drop phải có lý do (deduplicate, Risk Gateway reject)
- **Tiếp theo:** Tích hợp với Risk Gateway (chi tiết trong RISK_GATEWAY.md)
