# Retry & Timeout Policy — Xử lý Lỗi Tạm thời

> **Tài liệu thiết kế Retry & Timeout Policy của Execution Engine.** Mô tả chính sách
> retry khi gửi lệnh thất bại (network fail, broker timeout...), giới hạn thời gian chờ
> phản hồi broker, backoff strategy, và điều kiện KHÔNG được retry (loại lỗi nào không
> phục hồi được bằng retry).

---

## 1. Mục đích Retry & Timeout

**Vai trò chính:**
- Xử lý **lỗi tạm thời** (transient errors): network fail, broker timeout, connection unstable
- **Tránh lỗi vô hạn** (infinite loop): giới hạn số lần retry + timeout
- **Idempotent retry:** Sử dụng order_id, không tạo duplicate order
- **Phân biệt lỗi:** Lỗi nào được retry (kỹ thuật), lỗi nào không (nghiệp vụ)
- **Exponential backoff:** Tăng khoảng cách giữa mỗi lần retry, tránh overwhelm broker

**Nguyên tắc:**
- **Chỉ retry lỗi kỹ thuật** (network, timeout, server down)
- **KHÔNG retry lỗi nghiệp vụ** (margin không đủ, symbol invalid, rủi ro vượt hạn)
- **Có timeout cứng** (timeout tối đa, sau đó coi lệnh fail)
- **Max retry limit** (không retry vô hạn)

---

## 2. Phân loại Lỗi (Retry vs No-Retry)

### 2.1 Loại lỗi CÓ THỂ Retry (Transient)

| Lỗi | Mô tả | Retry? | Lý do |
|---|---|---|---|
| **Network timeout** | Không nhận phản hồi từ broker > X giây | ✅ YES | Tạm thời, thử lại |
| **Connection refused** | Broker API không response (down/maintenance) | ✅ YES (limited) | Có thể broker tạm khôi phục |
| **Temporary server error (5xx)** | Broker API trả 500/502/503 | ✅ YES (limited) | Server tạm bị overload |
| **Socket timeout** | TCP connection timeout | ✅ YES | Network issue, có thể phục hồi |
| **Rate limited (429)** | Broker chặn quá nhiều request | ✅ YES (với backoff lớn) | Backoff + retry sau |

### 2.2 Loại lỗi KHÔNG Retry (Permanent)

| Lỗi | Mô tả | Retry? | Hành động |
|---|---|---|---|
| **Insufficient margin** | Account balance không đủ | ❌ NO | Final fail, alert Project Owner |
| **Invalid symbol** | Symbol không tồn tại trên broker | ❌ NO | Fix order, retry nếu fix lỗi (nhưng không auto) |
| **Order size invalid** | Quantity quá bé/quá lớn | ❌ NO | Adjust size, manual resubmit |
| **Account suspended** | Tài khoản bị khóa | ❌ NO | Alert urgent, không retry |
| **Risk violation (lỗi nghiệp vụ)** | Rủi ro vượt limit (từ Risk Gateway) | ❌ NO | Không lệnh này, chờ position close |
| **Invalid API key** | Authorization fail | ❌ NO | Config error, không retry |
| **Market closed** | Market không phải giờ trading | ❌ NO (hoặc WAIT) | Chờ market mở, không retry ngay |

---

## 3. Luồng Retry & Timeout

### 3.1 Gửi lệnh lần đầu

```
Order Manager:
  order.status = CREATED
  order.retry_count = 0
  
Call: broker_adapter.place_order(order, timeout=30s)
  → Start timer (30 giây)
  → Chờ phản hồi: FILLED, REJECTED, PARTIAL, TIMEOUT
  
If phản hồi trong 30s:
  → Xử lý (chi tiết ở ORDER_MANAGER.md)
  
If KHÔNG phản hồi sau 30s:
  → Timeout trigger
  → order.status = TIMEOUT
  → Tiếp tục mục 3.2 (Retry Logic)
```

### 3.2 Retry Logic

```
┌─ order.status = TIMEOUT hoặc REJECTED (lỗi kỹ thuật)
│
├─ Kiểm tra: Có phải lỗi retry được?
│  (xem mục 2.1, phân loại lỗi)
│  
│  Nếu NO → goto Fail Final (mục 3.4)
│  Nếu YES → tiếp tục
│
├─ Kiểm tra: retry_count < max_retry?
│  max_retry = 3 (chưa chốt, đề xuất)
│  
│  Nếu NO → goto Fail Final
│  Nếu YES → tiếp tục
│
├─ Calculate backoff delay:
│  delay = base_delay * (2 ^ retry_count) [exponential]
│  
│  Ví dụ:
│    retry_count = 0: delay = 2 * (2^0) = 2 seconds
│    retry_count = 1: delay = 2 * (2^1) = 4 seconds
│    retry_count = 2: delay = 2 * (2^2) = 8 seconds
│  
│  Optional: cap max delay (ví dụ 60 seconds)
│
├─ Wait (delay) seconds
│
├─ Retry attempt:
│  order.retry_count += 1
│  Call: broker_adapter.place_order(order, timeout=30s)
│  
│  (use order_id OLD, không tạo ID mới → idempotent)
│
├─ Nếu phản hồi thành công:
│  → Xử lý như bình thường (ORDER_MANAGER.md)
│
└─ Nếu TIMEOUT lại:
   Nếu retry_count < max_retry: Loop lại từ "Calculate backoff delay"
   Nếu retry_count >= max_retry: goto Fail Final
```

### 3.3 Idempotent Retry (Tránh Duplicate Order)

**Khi retry, sử dụng order_id CŨ:**

```
Lần 1: place_order(order_id=TF_001_EURUSD_1720123456_A5F2)
  → Timeout
  
Lần 2: place_order(order_id=TF_001_EURUSD_1720123456_A5F2) [same ID]
  → Broker kiểm tra: ID này đã tồn tại?
  → Nếu CÓ: "Order TF_001_... already exists, status=..."
  → Nếu KHÔNG: tạo order mới
  
Result: Dù retry bao nhiêu lần, chỉ có 1 order ở broker
```

### 3.4 Fail Final (Max Retry Exceeded)

```
After max retry lần thất bại:

order.status = FAILED
order.error_message = "Max retry exceeded (3 attempts)"

Error Handling module (xem ERROR_HANDLING.md):
  - Loại lỗi: transient nhưng không phục hồi được
  - Hành động: log chi tiết, alert Project Owner
  - Không tạo position (retry không thành công)
  
Position Manager:
  → Không nhận position mới
  
Audit Log:
  → "Order failed after 3 retries"
```

---

## 4. Timeout Cứng (Hard Timeout)

**Mục đích:** Tránh order "chết" vô thời hạn trong TIMEOUT state.

**Cơ chế:**

```
Nếu order ở TIMEOUT state quá lâu (total_wait_time > hard_timeout):
  hard_timeout = 5 minutes (chưa chốt, đề xuất)
  
  total_wait_time = tổng thời gian order chờ phản hồi
                    (bao gồm timeout + tất cả retry delays)
  
  If total_wait_time > 5 minutes:
    → Fail final (không retry thêm nữa)
    → Log: "Hard timeout exceeded"
    → Order coi là fail
```

**Ví dụ:**

```
Lần 1: place_order() → timeout 30s
Delay + Retry 1: wait 2s, place_order() → timeout 30s (total: 2+30=32s)
Delay + Retry 2: wait 4s, place_order() → timeout 30s (total: 32+4+30=66s)
Delay + Retry 3: wait 8s, place_order() → timeout 30s (total: 66+8+30=104s)

Total: 104 giây < 5 minutes (300s) → Còn được retry nếu cần

Nếu sau retry 3 vẫn timeout, kiểm tra:
  - Nếu total < 300s: có thể retry thêm (nhưng retry_count >= max_retry → NO)
  - Nếu total >= 300s: hard timeout → FAIL FINAL
```

---

## 5. Query Status Khi Timeout (Recovery)

**Tình huống:** Order timeout, nhưng có thể order đã được tạo ở broker, chỉ là response bị mất.

**Handling:**

```
Khi order.status = TIMEOUT:

1. Thay vì place_order() lại ngay:
   → Query broker: "Order TF_001_... có tồn tại không?"
   
2. Broker response:
   ├─ "Order exists, status = PENDING"
   │  → No need to place_order lại
   │  → Chỉ cập nhật order.status = PENDING
   │  → Tiếp tục monitor
   │
   ├─ "Order exists, status = FILLED, filled_price = ..."
   │  → Order đã fill, không biết!
   │  → Cập nhật order.status = FILLED
   │  → Tạo position từ filled data
   │
   └─ "Order not found"
      → Order thực sự chưa tạo
      → Retry place_order()
```

**Flow chi tiết:**

```
┌─ order.status = TIMEOUT
│
├─ Query broker:
│  query_result = broker.get_order_status(order_id)
│
├─ If query_result exists:
│  ├─ Cập nhật order.status = query_result.status
│  └─ Tính filled_price, filled_quantity (nếu filled)
│
├─ Else (order not found):
│  └─ Thực hiện Retry Logic (mục 3.2)
│
└─ Monitor order status (chờ fill hoặc final fail)
```

---

## 6. Các tham số chưa chốt

| Tham số | Mục đích | Trạng thái | Ghi chú |
|---|---|---|---|
| **timeout** | Chờ broker bao lâu trước khi coi fail | ❓ Chưa chốt, đề xuất 30s | Phụ thuộc broker |
| **max_retry** | Tối đa bao nhiêu lần retry | ❓ Chưa chốt, đề xuất 3 | Không retry vô hạn |
| **base_delay** | Backoff base (exponential: base * 2^n) | ❓ Chưa chốt, đề xuất 2s | Để tránh overwhelm broker |
| **max_delay** | Backoff tối đa giữa mỗi retry | ❓ Chưa chốt, đề xuất 60s | Cap exponential |
| **hard_timeout** | Tổng thời gian tối đa chờ order | ❓ Chưa chốt, đề xuất 5 min | Fail final sau này |
| **backoff_strategy** | Loại backoff (exponential, linear, random) | ❓ Chưa chốt, đề xuất exponential | Tránh thundering herd |

---

## 7. Ví dụ Retry Sequence

### 7.1 Happy Path: Retry thành công

```
Attempt 1:
  place_order(order_id=TF_001_EURUSD_1720123456_A5F2)
  → Timeout (30s không response)
  → status = TIMEOUT, retry_count = 0
  
Query status:
  → order not found ở broker
  → Có thể retry
  
Calculate backoff:
  delay = 2 * (2^0) = 2 seconds
  
Wait 2 seconds...

Attempt 2:
  place_order(order_id=TF_001_EURUSD_1720123456_A5F2, timeout=30s)
  → Response: FILLED, filled_price = 1.0800
  → status = FILLED
  
Result: ✅ SUCCESS (thành công ở lần retry thứ 1)
```

### 7.2 Query Status Recovery

```
Attempt 1:
  place_order(order_id=TF_001_EURUSD_1720123456_A5F2)
  → Timeout (30s)
  → status = TIMEOUT
  
Query status:
  → Broker: "Order TF_001_... exists, status = FILLED, price = 1.0800"
  → Wow! Order đã được tạo + filled, chỉ response bị mất
  
Order Manager:
  → Cập nhật order.status = FILLED
  → order.filled_price = 1.0800
  → Không cần retry (order đã fill)
  
Result: ✅ RECOVERED (tìm lại order thất lạc)
```

### 7.3 Max Retry Exceeded

```
Attempt 1: Timeout (30s)
  backoff = 2s
  
Attempt 2: Timeout (30s)
  backoff = 4s
  
Attempt 3: Timeout (30s)
  backoff = 8s
  
Attempt 4: retry_count >= max_retry (3)
  → Stop retry
  → order.status = FAILED
  → order.error_message = "Max retry (3) exceeded"
  
Error Handling:
  → Alert Project Owner
  → Log detailed error
  
Result: ❌ FAILED (vô hiệu hóa sau 3 lần thất bại)
```

### 7.4 Non-Retryable Error

```
Attempt 1:
  place_order(order_id=TF_001_EURUSD_1720123456_A5F2)
  → Response: REJECTED, reason = "Insufficient margin"
  → status = REJECTED, error_message = "Insufficient margin"
  
Retry Logic checks:
  → Loại lỗi: insufficient margin
  → Retry được không? ❌ NO (permanent error)
  
→ Skip retry, goto Fail Final
→ Log: "Order rejected - insufficient margin (no retry)"
→ Alert Project Owner: "Account balance not enough for this order"

Result: ❌ PERMANENT FAIL (không retry)
```

---

## 8. Liên hệ với các file khác

**Input từ:**
- `execution/ORDER_MANAGER.md` → Lệnh gửi, cần xử lý timeout/fail
- `execution/BROKER_ADAPTER_INTERFACE.md` → Broker response (FILLED, REJECTED, TIMEOUT)

**Output đi tới:**
- `execution/ERROR_HANDLING.md` → Phân loại lỗi, quyết định final action
- `execution/AUDIT_LOG.md` → Ghi log retry attempts, backoff delays

**Tham chiếu:**
- Không tham chiếu file khác (chính sách độc lập)

---

## 9. Trạng thái và ghi chú

- **Thiết kế:** Đã chốt exponential backoff, idempotent retry, phân loại lỗi
- **Ngôn ngữ:** Tiếng Việt, không code thực
- **Chưa chốt:** timeout (30s?), max_retry (3?), base_delay (2s?), hard_timeout (5min?)
- **Quan trọng:** Query status khi timeout để tránh duplicate order + recover thất lạc
- **Idempotent:** order_id không đổi khi retry → broker biết đó là lệnh cũ, không duplicate
- **Tiếp theo:** Error Handling (chi tiết trong ERROR_HANDLING.md)
