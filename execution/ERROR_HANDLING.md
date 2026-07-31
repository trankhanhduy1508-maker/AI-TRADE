# Error Handling — Phân loại lỗi và Hành động Khôi phục

> **Tài liệu thiết kế Error Handling của Execution Engine.** Mô tả cách phân loại lỗi
> phát sinh (kỹ thuật vs nghiệp vụ vs dữ liệu), quyết định hành động (retry, fail-safe,
> trigger kill switch), và alert Project Owner. Nguyên tắc: nếu nghi ngờ → fail-safe
> (dừng an toàn) hơn là cố gắng tiếp tục.

---

## 1. Mục đích Error Handling

**Vai trò chính:**
- Phân loại lỗi: kỹ thuật (retry được) vs nghiệp vụ (không retry) vs dữ liệu (stop an toàn)
- Quyết định hành động: retry, final fail, trigger kill switch, alert
- Đảm bảo **fail-safe:** Nếu nghi ngờ vi phạm an toàn → dừng lệnh, không linh hoạt
- Ghi log đầy đủ: lỗi gì, lúc nào, hành động gì (audit trail)

**Nguyên tắc thiết kế:**
- **Fail-safe:** An toàn vốn > cố gắng giao dịch
- **No silence:** Không lặng lẽ bỏ qua lỗi — phải log + alert
- **Escalate urgent:** Lỗi liên quan an toàn vốn → alert ngay Project Owner

---

## 2. Phân loại Lỗi (Error Categories)

### 2.1 Lỗi Kỹ thuật (Technical Errors) → RETRY

| Loại lỗi | Ví dụ | Hành động | Ghi chú |
|---|---|---|---|
| **Network timeout** | Broker không response > 30s | Retry (Retry Policy, max 3 lần) | Tạm thời, có thể phục hồi |
| **Connection refused** | Connection to broker API failed | Retry (limited, exponential backoff) | Broker tạm down, chờ khôi phục |
| **Temporary server error (5xx)** | Broker API 500/502/503 | Retry với backoff | Server overload, chờ được |
| **Socket/DNS error** | Network layer fail | Retry | Infrastructure issue, phục hồi được |
| **Partial fill retry** | Order fill một phần, chờ nốt | Retry query status | Check order ở broker |

**Xử lý:** Retry Policy xử lý (xem RETRY_TIMEOUT_POLICY.md)

---

### 2.2 Lỗi Nghiệp vụ (Business Logic Errors) → NO RETRY

| Loại lỗi | Ví dụ | Hành động | Ghi chú |
|---|---|---|---|
| **Insufficient margin** | Account balance không đủ | Final fail, log, alert | Vốn thực sự không đủ, retry vô ích |
| **Invalid symbol** | Symbol "EURUSD999" không tồn tại | Final fail, investigate | Config error, cần fix thủ công |
| **Risk violation (Business)** | Rủi ro vượt limit (từ Risk Gateway) | REJECT, không gửi lệnh | Risk Gateway đã kiểm tra, không lệnh này |
| **Kill switch active** | System bị dừng do quá nhiều loss | REJECT mọi lệnh mới | Wait Project Owner reset |
| **Account suspended** | Broker khóa tài khoản | Emergency stop, alert urgent | Critical, không thể giao dịch |
| **Order size invalid** | Quantity quá bé (< min) hoặc quá lớn (> max) | Adjust size, manual resubmit | Broker limit, không auto fix |
| **Market closed** | Gửi lệnh ngoài giờ trading | WAIT hoặc REJECT | Chờ market mở (nếu chốt WAIT strategy) |
| **Invalid order type** | Broker không hỗ trợ order type này | Fix order type, retry manual | Config issue, không auto retry |

**Xử lý:** Final fail, log detailed, alert Project Owner, không retry

---

### 2.3 Lỗi Dữ liệu (Data Integrity Errors) → FAIL-SAFE

| Loại lỗi | Ví dụ | Hành động | Ghi chú |
|---|---|---|---|
| **Price gap (anomaly)** | Price jump 1000 pips bất thường | Stop an toàn, trigger kill switch | Data corruption hoặc news gap, không tin |
| **Missing data** | Không nhận price bar mới > X phút | Stop monitoring, alert | Data feed fail, không thể theo dõi |
| **Null fields** | Signal có null entry_price | Reject signal, log error | Lỗi ở Rule Engine, không thực thi |
| **Corrupted order** | Order object có field invalid | Reject, log, investigate | Lỗi serialization, không gửi |
| **State inconsistency** | Position cache vs broker state khác lớn | Reconcile, alert | Mất kết nối, cần sync lại |
| **Negative balance** | Account balance < 0 (không thể) | Emergency stop, investigate | Critical bug, dừng ngay |

**Xử lý:** Stop an toàn (fail-safe), log chi tiết, trigger kill switch nếu cần, alert urgent

---

## 3. Error Handling Decision Tree

```
┌─ Lỗi phát sinh (tại bất kỳ bước nào)
│  │ error_message, error_type, error_code (nếu có)
│  │
│  ↓
├─ Phân loại lỗi:
│  │
│  ├─ Là Technical Error (network, timeout, 5xx)?
│  │  ├─ YES → Retry Policy (max 3 lần, exponential backoff)
│  │  │        Nếu retry max exceeded → goto Business Error handling
│  │  │
│  │  └─ NO → tiếp tục phân loại
│  │
│  ├─ Là Business Error (risk, margin, invalid symbol)?
│  │  ├─ YES → Final fail (không retry)
│  │  │        Log error, alert Project Owner
│  │  │        (không trigger kill switch, chỉ log)
│  │  │
│  │  └─ NO → tiếp tục phân loại
│  │
│  └─ Là Data Integrity Error (price gap, null data, negative balance)?
│     ├─ YES → FAIL-SAFE (dừng an toàn)
│     │        Trigger kill switch (tạm dừng trading)
│     │        Alert urgent Project Owner
│     │
│     └─ NO → Unknown error (đặc biệt)
│            Log, alert, manual investigate
│
└─ Kết thúc (hành động tương ứng đã thực hiện)
```

---

## 4. Hành động Chi tiết cho Mỗi Loại Lỗi

### 4.1 Technical Error

```
Error: Network timeout (broker không response)

Xử lý:
  1. Log: "Technical error: network timeout (attempt 1/3)"
  2. Trigger Retry Policy (RETRY_TIMEOUT_POLICY.md):
     - Wait: 2 seconds (exponential backoff)
     - Retry place_order (same order_id, idempotent)
  3. Nếu retry thành công: XO tiếp (normal flow)
  4. Nếu retry lần 3 fail: goto max retry exceeded
     - Log: "Order failed after 3 retries"
     - Alert Project Owner: "Order timeout, max retry exceeded"
     - Không trigger kill switch (chỉ lỗi kỹ thuật, không rủi ro)
```

### 4.2 Business Error (Risk/Margin/Config)

```
Error: Insufficient margin (broker reject)

Xử lý:
  1. Identify: Lỗi loại Business Error
  2. Log: "Business error: insufficient margin"
  3. Decision: Retry? NO (không retry lỗi permanent)
  4. Final fail:
     - order.status = REJECTED
     - order.error_message = "Insufficient margin"
  5. Alert Project Owner:
     - Message: "Order rejected: insufficient margin. Check account balance."
     - Severity: WARNING (không CRITICAL, có thể fix bằng deposit)
  6. Không trigger kill switch (lỗi cụ thể, không chính sách toàn cục)
```

### 4.3 Kill Switch Trigger (Auto)

**Khi nào trigger auto kill switch:**
- Consecutive losses >= threshold (từ KILL_SWITCH_RULES.md)
- Drawdown >= threshold % (từ RISK_POLICY.md)
- Data anomaly lớn (price gap > 500 pips)
- Negative account balance (critical)
- System crash/unrecoverable state

**Xử lý:**

```
Data Error: Price gap 1000 pips (data corruption)

1. Detect: price_jump = abs(new_price - old_price) = 1000 pips > threshold (500)
2. Classify: Data Integrity Error
3. Decision: Không thể tin dữ liệu này, FAIL-SAFE
4. Action:
   - Stop position monitoring (không close position dựa trên bad data)
   - Trigger kill switch:
     kill_switch_status = ACTIVE
     kill_switch_reason = "Data anomaly: price gap 1000 pips"
   - Log: "Kill switch triggered: data anomaly"
   - Alert URGENT Project Owner:
     "KILL SWITCH TRIGGERED: Data anomaly detected (price gap 1000 pips). 
      Trading halted. Manual investigation required."
   - Audit: Ghi chi tiết lỗi, timestamp, vị trí
```

---

## 5. Alert Levels

| Level | Ví dụ lỗi | Hành động |
|---|---|---|
| **INFO** | Order sent successfully, position opened | Log only |
| **WARNING** | Order rejected (margin low), slow response | Log + alert (email/dashboard) |
| **ERROR** | Retry max exceeded, business error | Log + alert urgent (email) |
| **CRITICAL** | Kill switch triggered, account suspended, negative balance | Log + alert URGENT + SMS nếu available |

**Alert destination:** Project Owner email/phone (chưa chốt channel)

---

## 6. Ví dụ Error Scenarios

### 6.1 Scenario: Network Timeout + Recovery

```
1. Order Manager gửi order
   broker.place_order(order, timeout=30s)
   
2. Wait 30s → No response → Timeout
   
3. Error Handling:
   error_type = "Network timeout"
   retry_count = 0
   
4. Classify: Technical Error → Retry
   
5. Retry Policy:
   delay = 2 * (2^0) = 2s
   wait 2s...
   retry place_order (same order_id)
   
6. Response: FILLED (thành công lần retry)
   
7. Result:
   ✅ RECOVERED
   Log: "Order filled after 1 retry"
```

### 6.2 Scenario: Insufficient Margin

```
1. Order Manager gửi order
   quantity = 10 lot (account balance thực sự không đủ)
   
2. Broker response: REJECTED, reason = "Insufficient margin"
   
3. Error Handling:
   error_type = "Insufficient margin"
   classify = Business Error
   
4. Decision: Retry? NO
   
5. Final fail:
   order.status = REJECTED
   Log: "Order rejected - insufficient margin"
   
6. Alert Project Owner:
   "Order REJECTED: Insufficient margin. 
    Please check account balance or adjust order size."
   
7. Result:
   ❌ FAILED (không retry, cần manual fix)
```

### 6.3 Scenario: Data Anomaly → Kill Switch

```
1. Position Manager monitor price
   old_price = 1.0800
   new_price = 2.0800 (jump 1000 pips)
   
2. Error Handling:
   error_type = "Price gap anomaly"
   gap = 2.0800 - 1.0800 = 1000 pips > threshold (500)
   classify = Data Integrity Error
   
3. Decision: FAIL-SAFE
   → Cannot trust this data, stop trading
   
4. Action:
   - Stop position monitoring
   - Trigger kill switch
   - kill_switch_status = ACTIVE
   - kill_switch_reason = "Price gap anomaly (1000 pips)"
   
5. Alert URGENT:
   "⚠️ KILL SWITCH TRIGGERED ⚠️
    Reason: Price gap anomaly (1000 pips detected)
    Time: 2024-07-05 14:32:15
    Last price: 1.0800, New price: 2.0800
    Action: All trading HALTED. Manual investigation required.
    Please check data feed and market conditions."
   
6. Result:
   🛑 TRADING HALTED
   Chờ Project Owner: "reset kill switch" sau khi investigate
```

### 6.4 Scenario: Consecutive Losses → Kill Switch (Auto)

```
1. Position 1 closed: loss -$100
   consecutive_losses = 1
   
2. Position 2 closed: loss -$150
   consecutive_losses = 2
   
3. Position 3 closed: loss -$120
   consecutive_losses = 3 = threshold_losses
   
4. Signal 4 tới Risk Gateway
   
5. Risk Gateway Check 4:
   "Consecutive losses (3) >= threshold (3)"
   → REJECT signal 4
   → Trigger auto kill switch
   
6. Error Handling:
   error_type = "Consecutive losses threshold reached"
   classify = Business Error → Kill Switch Trigger
   
7. Action:
   kill_switch_status = ACTIVE
   Log: "Kill switch triggered - consecutive losses (3)"
   Alert Project Owner:
   "Kill switch triggered: 3 consecutive losses.
    Thua 3 lệnh liên tiếp: -$100, -$150, -$120.
    Trading halted. Please review strategy and market conditions."
   
8. Result:
   🛑 TRADING HALTED (auto)
   Mọi signal mới sẽ REJECT ở Risk Gateway (Check 3: kill switch active)
```

---

## 7. Liên hệ với các file khác

**Input từ:**
- `execution/ORDER_MANAGER.md` → Order rejection/timeout
- `execution/POSITION_MANAGER.md` → Data anomaly, state inconsistency
- `execution/RETRY_TIMEOUT_POLICY.md` → Lỗi timeout (phân loại, quyết định retry)
- `risk/KILL_SWITCH_RULES.md` → Điều kiện trigger kill switch

**Output đi tới:**
- `execution/RISK_GATEWAY.md` → Trigger kill switch → Risk Gateway kiểm tra ở Check 3
- `execution/AUDIT_LOG.md` → Ghi log error chi tiết
- `research/FAILURE_CASES.md` (tương lai) → Ghi lại các lỗi để analysis

**Tham chiếu:**
- `risk/RISK_POLICY.md` → Ngôn ngữ, giới hạn (thua liên tiếp, drawdown)

---

## 8. Trạng thái và ghi chú

- **Thiết kế:** Đã chốt phân loại lỗi 3 loại, decision tree, alert levels
- **Ngôn ngữ:** Tiếng Việt, không code thực
- **Chưa chốt:** Alert channel (email/SMS?), response time SLA, exact thresholds (data gap, etc)
- **Quan trọng:** Fail-safe > linh hoạt (nghi ngờ → dừng, không cố tiếp)
- **Alert:** Project Owner là người duy nhất quyết định next action (retry, reset kill switch)
- **Tiếp theo:** Audit Log (chi tiết trong AUDIT_LOG.md)
