# Risk Gateway — Cổng Kiểm tra Rủi ro (Double-Check)

> **Tài liệu thiết kế Risk Gateway của Execution Engine.** Mô tả cơ chế kiểm tra rủi ro
> lần cuối trước khi Order Manager gửi lệnh thực thi. Risk Gateway là nơi DUY NHẤT có
> quyền chặn lệnh vì lý do rủi ro trong Execution Engine, không có ngoại lệ hay "linh hoạt".
> Tất cả giới hạn đều từ `risk/RISK_POLICY.md` và `risk/KILL_SWITCH_RULES.md`.

---

## 1. Mục đích Risk Gateway

**Vai trò chính:**
- **Double-check rủi ro lần cuối:** Giữa lúc Rule Engine phát tín hiệu (phát hiện setup) và lúc thực thi (gửi lệnh) có thể có độ trễ → tình huống account có thể đã thay đổi (lệnh khác vừa mở/close) → Risk Gateway kiểm tra lại
- **Nơi duy nhất chặn lệnh vì rủi ro:** Order Manager không tự ý chặn, chỉ thực thi nếu Risk Gateway PASS
- **Không tự quyết định:** Mọi giới hạn đều từ RISK_POLICY.md và KILL_SWITCH_RULES.md, không AI tự quyết định "lần này tạm được"

**Nguyên tắc thiết kế:**
- **Fail-safe:** Nếu nghi ngờ vi phạm rủi ro → REJECT (vẫn hơn cứ chặn)
- **No exceptions:** Không có "lệnh vàng", "tạm hoãn", "linh hoạt" — luật cứng thôi

---

## 2. Checklist kiểm tra rủi ro (5 điểm)

Risk Gateway kiểm tra **5 điều kiện** theo thứ tự. Nếu **BẤT KỲ điều kiện nào FAIL** → REJECT:

### 2.1 Check 1: Rủi ro lệnh mới <= Giới hạn mỗi lệnh

**Nguồn giới hạn:** `risk/RISK_POLICY.md` → "Giới hạn rủi ro mỗi lệnh"

**Công thức kiểm tra:**

```
risk_per_trade = signal.risk_amount_pct
limit_per_trade = (từ RISK_POLICY.md, chưa chốt, giả định 1-2%)

Kiểm tra:
  if risk_per_trade > limit_per_trade:
    → REJECT
    → reason = "Risk per trade {risk_per_trade}% exceeds limit {limit_per_trade}%"
  else:
    → PASS check 1
```

**Ghi chú:**
- `risk_amount_pct` được tính bởi Rule Engine (RULE_008 Risk)
- Nếu RISK_POLICY.md chưa chốt số cụ thể → cũng REJECT (fail-safe)

---

### 2.2 Check 2: Tổng rủi ro portfolio (hiện tại + mới) <= Giới hạn danh mục

**Nguồn giới hạn:** `risk/RISK_POLICY.md` → "Giới hạn rủi ro danh mục"

**Công thức kiểm tra:**

```
portfolio_risk_current = Tổng rủi ro của tất cả position đang mở
                         (dữ liệu từ Position Manager)
                         
portfolio_risk_new = signal.risk_amount_pct (lệnh mới sắp vào)

portfolio_risk_total = portfolio_risk_current + portfolio_risk_new

limit_portfolio = (từ RISK_POLICY.md, chưa chốt, giả định 5-10%)

Kiểm tra:
  if portfolio_risk_total > limit_portfolio:
    → REJECT
    → reason = "Portfolio risk {portfolio_risk_total}% exceeds limit {limit_portfolio}%"
  else:
    → PASS check 2
```

**Ghi chú:**
- `portfolio_risk_current` được cập nhật động bởi Position Manager
- Nếu vừa có lệnh close → portfolio_risk_current sẽ giảm → có thể accept lệnh mới
- Các lệnh có tương quan cao (ví dụ: EUR/USD LONG + GBP/USD LONG) phải được tính gộp rủi ro (xem `knowledge/MARKET_WIZARDS_LESSONS.md`), không tính riêng lẻ

---

### 2.3 Check 3: Kill Switch chưa kích hoạt?

**Nguồn:** `risk/KILL_SWITCH_RULES.md` → Các điều kiện kích hoạt kill switch

**Kiểm tra:**

```
kill_switch_status = (từ Risk Policy state)

Kiểm tra:
  if kill_switch_activated:
    → REJECT
    → reason = "Kill switch activated: {reason}"
    → Không phát hành tín hiệu/lệnh mới cho tới khi Project Owner reset
  else:
    → PASS check 3
```

**Kill switch được kích hoạt khi:**
- Số lệnh thua liên tiếp >= ngưỡng (từ RISK_POLICY.md)
- Drawdown >= ngưỡng % vốn (từ RISK_POLICY.md)
- Tổng rủi ro portfolio vượt giới hạn cứng
- Project Owner bấm nút dừng khẩn cấp

---

### 2.4 Check 4: Số lệnh thua liên tiếp chưa vượt ngưỡng?

**Nguồn:** `risk/RISK_POLICY.md` → "Giới hạn thua lỗ liên tiếp"

**Kiểm tra:**

```
consecutive_losses = Số lệnh thua liên tiếp gần nhất
                     (từ Audit Log, Position Manager)

threshold_losses = (từ RISK_POLICY.md, chưa chốt, giả định 3-5)

Kiểm tra:
  if consecutive_losses >= threshold_losses:
    → REJECT
    → reason = "Consecutive losses {consecutive_losses} >= threshold {threshold_losses}"
    → Trigger auto kill switch (tạm dừng, cần đánh giá lại)
  else:
    → PASS check 4
```

**Ghi chú:**
- Nếu vừa win 1 lệnh → reset consecutive_losses counter
- Kiểm tra này bảo vệ tâm lý, tránh "gỡ lệnh" liên tiếp

---

### 2.5 Check 5: Không trùng lặp position hiện có? (nếu chính sách cấm)

**Nguồn:** `risk/RISK_POLICY.md` → "Chính sách trùng symbol" (chưa chốt nếu cấm hay cho phép)

**Kiểm tra:**

```
signal_symbol = signal.symbol (ví dụ EURUSD)

open_positions = Danh sách position đang mở (từ Position Manager)

for each pos in open_positions:
  if pos.symbol == signal_symbol AND pos.status == OPEN:
    → Nếu chính sách CẤM trùng:
       → REJECT
       → reason = "Position {signal_symbol} already open, duplicate not allowed"
    → Nếu chính sách CHO PHÉP trùng:
       → Kiểm tra portfolio risk (check 2 đã cover)
       → PASS check 5
```

**Ghi chú:**
- Chưa chốt chính sách này — cần Project Owner xác nhận "một symbol có được mở 2 position không"
- Ví dụ: có EUR/USD LONG, có được mở EUR/USD SHORT không? (hedge? pyramiding?)

---

## 3. Luồng xử lý Risk Gateway

```
┌─ Signal từ Signal Queue
│  │ symbol, direction, entry, SL, risk_amount_pct, score
│  │
│  ↓
├─ Check 1: Rủi ro/lệnh <= limit?
│  ├─ FAIL → REJECT (reason: "Exceeds per-trade limit")
│  └─ PASS → Check 2
│
├─ Check 2: Portfolio risk (current + new) <= limit?
│  ├─ FAIL → REJECT (reason: "Exceeds portfolio limit")
│  └─ PASS → Check 3
│
├─ Check 3: Kill switch chưa kích hoạt?
│  ├─ FAIL → REJECT (reason: "Kill switch active")
│  └─ PASS → Check 4
│
├─ Check 4: Consecutive losses < threshold?
│  ├─ FAIL → REJECT + trigger auto kill switch (reason: "Too many losses")
│  └─ PASS → Check 5
│
├─ Check 5: No duplicate position?
│  ├─ FAIL → REJECT (reason: "Duplicate position exists")
│  └─ PASS → ALL CHECK PASS
│
├─ Result: PASS
│  │ Ghi log: "Signal passed Risk Gateway"
│  │ Gửi signal tới Order Manager
│  │
│  ↓
└─ Result: REJECT
   │ Ghi log: "Signal rejected at Risk Gateway" + reason
   │ Đánh dấu signal.status = DROPPED
   │ **Không gửi tới Order Manager**
```

---

## 4. Cơ chế Trigger Kill Switch tự động

Nếu Check 4 fail (quá nhiều lệnh thua liên tiếp), Risk Gateway sẽ:

1. **REJECT signal hiện tại** (không gửi lệnh mới)
2. **Set kill_switch_status = ACTIVE**
3. **Log:** "Kill switch triggered: consecutive losses >= threshold"
4. **Alert:** Thông báo Project Owner (không phải tự động enable lại)
5. **Dừng việc phát hành signal mới** (Signal Queue sẽ reject hoặc ignore signal tới tới)
6. **Chờ Project Owner xác nhận:** "đã đánh giá lại, được phép bắt đầu lại"

---

## 5. Trạng thái Risk Gateway

Risk Gateway không phải là thành phần stateless — nó phải lưu:

| Trạng thái | Mục đích | Cập nhật bởi |
|---|---|---|
| **kill_switch_status** | ACTIVE hoặc INACTIVE | Risk Gateway (tự động) hoặc Project Owner (thủ công) |
| **consecutive_losses** | Số lệnh thua liên tiếp gần nhất | Position Manager (khi position close) |
| **portfolio_risk_current** | Tổng rủi ro đang mở | Position Manager (khi position open/close) |
| **last_check_timestamp** | Lần kiểm tra rủi ro cuối cùng | Risk Gateway (sau mỗi check) |

**Lưu trữ:** Dữ liệu này cần lưu ở nơi có thể truy cập được (shared state, chưa chốt là in-memory hay DB bây giờ)

---

## 6. Các tham số chưa chốt (từ RISK_POLICY.md)

| Tham số | Mục đích | Trạng thái | Ghi chú |
|---|---|---|---|
| **limit_per_trade** | Tối đa % vốn rủi ro mỗi lệnh | ❓ Chưa chốt | Đề xuất 1-2% |
| **limit_portfolio** | Tối đa % vốn rủi ro tất cả position | ❓ Chưa chốt | Đề xuất 5-10% |
| **threshold_consecutive_losses** | Bao nhiêu lệnh thua liên tiếp trigger kill switch | ❓ Chưa chốt | Đề xuất 3-5 |
| **threshold_drawdown** | Bao nhiêu % drawdown trigger kill switch | ❓ Chưa chốt | Đề xuất 10-20% |
| **allow_duplicate_symbol** | Được phép 2 position cùng symbol không? | ❓ Chưa chốt | False (cấm) hay True (cho phép)? |

---

## 7. Ví dụ Risk Gateway Check

### 7.1 Happy Path: ALL PASS

```
Signal tới:
  symbol = EURUSD LONG
  risk_amount_pct = 1.5%
  entry = 1.0800, SL = 1.0700

Risk Gateway checks:
  1. Risk/trade: 1.5% <= 2% (limit) ✓ PASS
  2. Portfolio risk: current 2% + new 1.5% = 3.5% <= 5% (limit) ✓ PASS
  3. Kill switch: INACTIVE ✓ PASS
  4. Consecutive losses: 0 <= 3 (threshold) ✓ PASS
  5. Duplicate: no EURUSD position open ✓ PASS

Result: ✅ PASS
→ Signal được gửi tới Order Manager
```

### 7.2 Fail: Portfolio Risk Exceeded

```
Signal tới:
  symbol = GBP/USD SHORT
  risk_amount_pct = 2.5%
  
Trạng thái hiện tại:
  Portfolio risk = 3.5% (từ 2 position EURUSD + AUDUSD)
  limit_portfolio = 5%

Risk Gateway checks:
  1. Risk/trade: 2.5% <= 2% ✗ FAIL
     
Result: ❌ REJECT
Reason: "Risk per trade 2.5% exceeds limit 2%"
→ Signal không được gửi Order Manager
→ signal.status = DROPPED
```

### 7.3 Fail: Kill Switch Active

```
Signal tới:
  symbol = USDJPY
  risk_amount_pct = 1%
  
Trạng thái hiện tại:
  kill_switch_status = ACTIVE (kích hoạt do 5 lệnh thua liên tiếp trước đó)

Risk Gateway checks:
  1. Risk/trade: 1% <= 2% ✓ PASS
  2. Portfolio risk: 2% + 1% = 3% <= 5% ✓ PASS
  3. Kill switch: ACTIVE ✗ FAIL

Result: ❌ REJECT
Reason: "Kill switch activated"
→ Signal không được gửi Order Manager
→ Yêu cầu Project Owner xác nhận "reset kill switch" trước khi có signal mới được accept
```

### 7.4 Fail: Too Many Consecutive Losses → Auto Kill Switch

```
Trạng thái hiện tại:
  Consecutive losses = 3 (3 lệnh thua liên tiếp)
  threshold_losses = 3
  
Signal tới:
  risk_amount_pct = 1%

Risk Gateway checks:
  1. Risk/trade: 1% <= 2% ✓ PASS
  2. Portfolio risk: OK ✓ PASS
  3. Kill switch: INACTIVE (chưa kích hoạt) ✓ PASS
  4. Consecutive losses: 3 >= 3 ✗ FAIL

Result: ❌ REJECT + AUTO KILL SWITCH
Reason: "Consecutive losses (3) >= threshold (3)"
Action:
  - REJECT signal hiện tại
  - Set kill_switch_status = ACTIVE
  - Log: "Kill switch triggered automatically"
  - Alert Project Owner
  - Từ giờ, mọi signal mới sẽ REJECT ở check 3 (kill switch active)
```

---

## 8. Liên hệ với các file khác

**Input từ:**
- `execution/SIGNAL_QUEUE.md` → Signal cần kiểm tra
- `risk/RISK_POLICY.md` → Giới hạn rủi ro (% vốn, portfolio limit, consecutive losses, drawdown)
- `risk/KILL_SWITCH_RULES.md` → Điều kiện kích hoạt kill switch
- `risk/POSITION_SIZING.md` → Công thức tính risk_amount_pct (để validate signal)

**Output đi tới:**
- `execution/ORDER_MANAGER.md` → Signal đã qua Risk Gateway (PASS)
- `execution/AUDIT_LOG.md` → Ghi log check result (pass/reject, reason, timestamp)

**Tham chiếu:**
- `knowledge/MARKET_WIZARDS_LESSONS.md` → Nguyên tắc quản lý rủi ro (correlation, portfolio thinking)

---

## 9. Trạng thái và ghi chú

- **Thiết kế:** Đã chốt 5 check, luồng xử lý, cơ chế auto kill switch
- **Quan trọng:** Risk Gateway là NƠI DUY NHẤT chặn lệnh vì rủi ro — không có ngoại lệ
- **Chưa chốt:** Tất cả ngưỡng số (limit_per_trade, limit_portfolio, threshold_losses, threshold_drawdown, allow_duplicate_symbol)
- **Fail-safe:** Nếu nghi ngờ → REJECT (không "linh hoạt")
- **Tiếp theo:** Tích hợp với Order Manager (chi tiết trong ORDER_MANAGER.md)
