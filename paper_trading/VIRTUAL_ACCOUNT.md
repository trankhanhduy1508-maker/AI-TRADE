# Virtual Account — Quản lý Vốn Ảo

> **Tài liệu thiết kế Virtual Account (Tài khoản ảo)** cho Paper Trading Engine.
> Mô tả cách quản lý vốn ban đầu, equity, balance, unrealized/realized PnL, và
> các thay đổi trạng thái khi có lệnh mở/đóng. Virtual Account là "tài khoản ngân
> hàng" của hệ thống paper trading, ghi lại từng giao dịch và tính toán hiệu suất
> theo thời gian thực.

---

## 1. Định nghĩa

**Virtual Account** là một bản ghi dữ liệu đại diện cho một tài khoản giao dịch giả
lập, không liên kết tới sàn giao dịch thực. Nó lưu trữ:
- Vốn ban đầu (khởi tạo)
- Balance hiện tại (tiền mặt sẵn dùng)
- Equity = Balance + Unrealized PnL (giá trị tài khoản tại thời điểm hiện tại)
- Lịch sử các giao dịch (realized PnL)

---

## 2. Các trường dữ liệu (Data Model)

| Tên trường | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---|---|---|---|
| **account_id** | String/UUID | Bắt buộc | Định danh duy nhất cho tài khoản (ví dụ: `PT_001`) |
| **created_at** | Timestamp | Bắt buộc | Ngày/giờ khởi tạo tài khoản |
| **initial_capital** | Decimal (USD/unit) | Bắt buộc | Vốn ban đầu khi tạo tài khoản (không thay đổi) |
| **balance** | Decimal (USD/unit) | Bắt buộc | Tiền mặt hiện tại trong tài khoản (thay đổi khi có lệnh đóng) |
| **unrealized_pnl** | Decimal (USD/unit) | Bắt buộc | Tổng lợi/lỗ chưa thực hiện từ tất cả lệnh mở |
| **realized_pnl** | Decimal (USD/unit) | Bắt buộc | Tổng lợi/lỗ đã thực hiện từ tất cả lệnh đóng |
| **equity** | Decimal (USD/unit) | Tính toán | **equity = balance + unrealized_pnl** (giá trị tài khoản tại thời điểm hiện tại) |
| **positions_open** | Integer | Bắt buộc | Số lệnh đang mở hiện tại |
| **total_portfolio_risk** | Decimal (USD/%) | Bắt buộc | Tổng rủi ro danh mục đang mở (tham chiếu `risk/RISK_POLICY.md`) |
| **margin_used** | Decimal (%) | Tùy chọn | % margin đã dùng (nếu áp dụng leverage, hiện chưa chốt) |
| **last_update** | Timestamp | Bắt buộc | Lần update gần nhất (khi có lệnh mở, đóng, hoặc unrealized PnL thay đổi) |
| **status** | String (enum) | Bắt buộc | `ACTIVE` / `KILL_SWITCH` (nếu kill switch kích hoạt) |

---

## 3. Quy tắc cập nhật Account

### 3.1 Khi Virtual Order được FILLED (lệnh mở)

**Trạng thái thay đổi:**
- **balance**: Giảm đi = lệnh nhân vào entry (short) hoặc tăng (nếu áp dụng).
  - *Ghi chú hiện tại*: Chưa chốt cách tính balance khi order FILLED (liệu có
    khóa % balance cho rủi ro lệnh, hay cứ tính balance = balance - (SL khoảng cách
    × số lượng lệnh)?). Tạm định: **balance không thay đổi khi order FILLED**
    (chỉ tính khi lệnh đóng để realized PnL).
- **positions_open**: Tăng 1 (thêm 1 lệnh mở).
- **total_portfolio_risk**: Tăng = rủi ro lệnh mới (tính từ khoảng cách SL × số
  lượng).
- **unrealized_pnl**: Cập nhật (thêm 0 ban đầu nếu entry vừa fill, nhưng sau đó sẽ
  thay đổi khi giá dao động).
- **last_update**: Timestamp hiện tại.

### 3.2 Khi Position được cập nhật (giá dao động, unrealized PnL thay đổi)

**Trạng thái thay đổi:**
- **unrealized_pnl**: = Tổng (current_price - entry_price) × số_lượng cho từng
  position mở.
- **equity**: = balance + unrealized_pnl (tính lại).
- **last_update**: Timestamp hiện tại.

### 3.3 Khi Position được CLOSED (lệnh đóng)

**Trạng thái thay đổi:**
- **realized_pnl**: Tăng thêm PnL của lệnh vừa đóng (= PnL_position).
- **balance**: Tăng thêm = realized_pnl từ lệnh vừa đóng.
- **positions_open**: Giảm 1.
- **total_portfolio_risk**: Giảm = rủi ro lệnh vừa đóng.
- **unrealized_pnl**: Cập nhật lại = tổng unrealized PnL từ các lệnh còn lại mở.
- **equity**: = balance + unrealized_pnl (tính lại).
- **last_update**: Timestamp hiện tại.

### 3.4 Khi Kill Switch kích hoạt

**Trạng thái thay đổi:**
- **status**: = `KILL_SWITCH`.
- Không tạo lệnh mới (Virtual Order sẽ REJECT ngay).
- Các lệnh đang mở vẫn được theo dõi, nhưng không auto-close (chỉ wait cho Project
  Owner decide).
- Periodic Review sẽ cảnh báo.

---

## 4. Ví dụ minh họa (Bảng số liệu giả định)

### Scenario: Một phiên paper trade với 3 lệnh

**Khởi tạo:**
| Trường | Giá trị |
|---|---|
| initial_capital | 10,000 USD |
| balance | 10,000 USD |
| unrealized_pnl | 0 USD |
| realized_pnl | 0 USD |
| equity | 10,000 USD |
| positions_open | 0 |
| total_portfolio_risk | 0 USD |

**Sau khi Lệnh 1 được FILLED (entry = 100, SL = 98, số lượng = 100 units, rủi ro =
2%):**
| Trường | Giá trị |
|---|---|
| balance | 10,000 USD (chưa thay đổi) |
| unrealized_pnl | 0 USD (entry vừa fill) |
| realized_pnl | 0 USD |
| equity | 10,000 USD |
| positions_open | 1 |
| total_portfolio_risk | 200 USD (2% × 10,000) |

**Giá di chuyển: entry = 100 → current = 102 (profit $2/unit × 100 = $200):**
| Trường | Giá trị |
|---|---|
| balance | 10,000 USD |
| unrealized_pnl | +200 USD |
| realized_pnl | 0 USD |
| equity | 10,200 USD |
| positions_open | 1 |
| total_portfolio_risk | 200 USD |

**Lệnh 1 được CLOSED (exit = 102, PnL = +200 USD):**
| Trường | Giá trị |
|---|---|
| balance | 10,200 USD (tăng 200) |
| unrealized_pnl | 0 USD (lệnh 1 đã close) |
| realized_pnl | +200 USD |
| equity | 10,200 USD |
| positions_open | 0 |
| total_portfolio_risk | 0 USD |

**Lệnh 2 được FILLED (entry = 105, SL = 103, số lượng = 80, rủi ro = 2% × 10,200
= $204):**
| Trường | Giá trị |
|---|---|
| balance | 10,200 USD |
| unrealized_pnl | 0 USD |
| realized_pnl | 200 USD |
| equity | 10,200 USD |
| positions_open | 1 |
| total_portfolio_risk | 204 USD |

**Giá: entry = 105 → current = 104 (loss $1/unit × 80 = -$80):**
| Trường | Giá trị |
|---|---|
| balance | 10,200 USD |
| unrealized_pnl | -80 USD |
| realized_pnl | 200 USD |
| equity | 10,120 USD |
| positions_open | 1 |
| total_portfolio_risk | 204 USD |

**Lệnh 2 được CLOSED (exit = 104, PnL = -80 USD):**
| Trường | Giá trị |
|---|---|
| balance | 10,120 USD |
| unrealized_pnl | 0 USD |
| realized_pnl | 120 USD (200 - 80) |
| equity | 10,120 USD |
| positions_open | 0 |
| total_portfolio_risk | 0 USD |

---

## 5. Liên hệ với Risk Policy

- **Tổng rủi ro danh mục** (`total_portfolio_risk`) phải **<= giới hạn danh mục**
  từ `risk/RISK_POLICY.md` (hiện chưa chốt con số, ví dụ: 5% vốn).
- **Nếu total_portfolio_risk + rủi ro lệnh mới > giới hạn**:
  → Virtual Order sẽ REJECT (Risk Gateway block).
- Mỗi lệnh mới phải check điều kiện này trước khi được FILLED.

---

## 6. Reset / Khởi tạo Account cho mỗi phiên Paper Trade

### 6.1 Khi bắt đầu một phiên paper trade mới

```
1. Tạo account_id mới (ví dụ: PT_20260801_001)
2. Khởi tạo:
   - created_at = ngày/giờ hiện tại
   - initial_capital = vốn được chỉ định (ví dụ: 10,000 USD)
   - balance = initial_capital
   - unrealized_pnl = 0
   - realized_pnl = 0
   - equity = initial_capital
   - positions_open = 0
   - total_portfolio_risk = 0
   - status = ACTIVE
   - last_update = now()
```

### 6.2 Trong suốt phiên

- Cập nhật real-time mỗi khi có sự thay đổi (order FILLED, position price updated,
  position CLOSED, etc.).
- Lưu snapshot của account state định kỳ (ví dụ: hàng giờ) để audit/review sau.

### 6.3 Kết thúc phiên / Tạo báo cáo

- Snapshot cuối cùng của Virtual Account được dùng để tính hiệu suất phiên
  (PnL %, win rate, max drawdown...).
- Tham chiếu `backtests/KPI_STANDARD.md` để tính các chỉ số.

---

## 7. Cấu trúc lưu trữ dữ liệu

*Ghi chú: Hiện tại là thiết kế tài liệu, không phải code. Khi implement:*

**Tùy chọn 1: JSON/YAML file**
```yaml
account_id: PT_20260801_001
created_at: 2026-08-01T09:00:00Z
initial_capital: 10000.00
balance: 9950.00
unrealized_pnl: 150.00
realized_pnl: 100.00
equity: 10100.00
positions_open: 1
total_portfolio_risk: 200.00
status: ACTIVE
last_update: 2026-08-01T14:30:00Z
```

**Tùy chọn 2: Database table**
```
Table: virtual_accounts
- id (PRIMARY KEY)
- account_id (UNIQUE)
- initial_capital (DECIMAL)
- balance (DECIMAL, updated real-time)
- unrealized_pnl (DECIMAL, computed)
- realized_pnl (DECIMAL, cumulative)
- equity (DECIMAL, computed = balance + unrealized_pnl)
- positions_open (INTEGER)
- total_portfolio_risk (DECIMAL)
- status (ENUM: ACTIVE, KILL_SWITCH)
- created_at, last_update (TIMESTAMP)
```

---

## 8. Liên hệ với các file khác

- **`risk/RISK_POLICY.md`** → Giới hạn portfolio risk cần check khi cập nhật
  `total_portfolio_risk`.
- **`risk/POSITION_SIZING.md`** → Công thức tính số lượng lệnh từ vốn và SL, ảnh
  hưởng tới rủi ro.
- **`paper_trading/VIRTUAL_ORDER.md`** → Khi Virtual Order FILLED, cập nhật
  `positions_open` và `total_portfolio_risk`.
- **`paper_trading/POSITION.md`** → Cập nhật `unrealized_pnl` mỗi khi Position price
  thay đổi.
- **`paper_trading/TRADE_JOURNAL.md`** → Khi Position CLOSED, ghi thông tin vào
  journal, cập nhật `realized_pnl`.
- **`paper_trading/PERFORMANCE_DASHBOARD.md`** → Dùng Virtual Account data để tính
  KPI (ROA%, Sharpe, max drawdown...).

---

## 9. Trạng thái và ghi chú

- **Thiết kế**: Hoàn tất cấu trúc dữ liệu, quy tắc cập nhật, ví dụ minh họa.
- **Chưa chốt**: Cách tính balance khi order FILLED (liệu có "lock" vốn không?),
  leverage policy (nếu áp dụng).
- **Cần Project Owner review**: Xác nhận initial_capital mỗi phiên, chính sách margin
  (nếu có).
- **Tiếp theo**: Viết VIRTUAL_ORDER.md (mô phỏng execution), POSITION.md (theo dõi
  lệnh mở), TRADE_JOURNAL.md (ghi chi tiết).
