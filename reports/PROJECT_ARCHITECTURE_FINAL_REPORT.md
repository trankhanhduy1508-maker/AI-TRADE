# Báo Cáo Kiến Trúc Cuối Cùng — AI-TRADE

**Ngày:** 01/08/2026  
**Trạng thái:** Thiết kế hoàn tất, chưa code  
**Giai đoạn:** Phase 2 (Rule Engine) + Phase 3-4-5 (kiến trúc) hoàn tất

---

## 1. Tổng Quan Kiến Trúc Hệ Thống

### 1.1 Sơ đồ Kiến Trúc Toàn Hệ Thống

```
┌─────────────────────────────────────────────────────────────────┐
│                       KNOWLEDGE BASE                             │
│  (Trend Following, Price Action, Volume, Risk Management...)    │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────────┐
│                     RISK POLICY (Luật cứng)                      │
│  (% rủi ro/lệnh, % danh mục, kill switch rules, v.v.)           │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────────┐
│                      RULE ENGINE                                 │
│  10 Rules (Trend, Structure, Breakout, Pullback, Volume, RSI,   │
│  EMA, Risk, Liquidity, Exit) → Setup Score (0-100)              │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ↓
            Trade Signal (score >= 80 đề xuất)
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ↓                             ↓
  ┌──────────────┐         ┌──────────────────────┐
  │   Execution   │         │  Point-in-Time AI    │
  │   Engine      │         │  Backtesting        │
  │               │         │  (Framework chứng    │
  │ • Signal      │         │   minh AI)           │
  │   Queue       │         │                      │
  │ • Risk        │         │ • Ẩn danh symbol/ngày
  │   Gateway     │         │ • Locked OOS         │
  │ • Order       │         │ • Walk-Forward       │
  │   Manager     │         │ • So sánh AI vs Rule │
  │ • Position    │         │   baseline           │
  │   Manager     │         │                      │
  │ • Audit Log   │         └──────────────────────┘
  └──────┬───────┘
         │
    ┌────┴────┐
    │          │
    ↓          ↓
┌─────────────────────────┐  ┌──────────────────────────┐
│  Paper Trading          │  │  Live Trading (Giai 7)   │
│  (Giai đoạn 4)          │  │  (tương lai, khi ready)  │
│                         │  │                          │
│ • Virtual Account       │  │ • Real Broker Adapter    │
│ • Virtual Order         │  │   (MT5, Binance, IB...)  │
│ • Position             │  │ • Kill Switch (thủ/tự)   │
│ • Trade Journal        │  │ • Real-time Monitoring   │
│ • Periodic Review      │  │ • Daily PnL Report       │
│ • Performance          │  │                          │
│   Dashboard            │  │                          │
└──────┬────────────────┘  └──────────┬─────────────────┘
       │                              │
       └──────────────┬───────────────┘
                      │
                      ↓
        ┌─────────────────────────────┐
        │   TRADE JOURNAL +           │
        │   RESEARCH LOGGING          │
        │                             │
        │ • Mỗi lệnh đóng            │
        │ • Mỗi phiên giao dịch      │
        │ • Failure cases            │
        │ • Experiments             │
        └──────────────┬──────────────┘
                       │
                       ↓
        ┌─────────────────────────────┐
        │   PERFORMANCE TRACKING      │
        │                             │
        │ • KPI (win rate, expectancy,│
        │   Sharpe, max DD)           │
        │ • Dashboard                 │
        │ • Periodic Review           │
        │   (Daily/Weekly/Monthly)    │
        └─────────────────────────────┘
```

### 1.2 Luồng Dữ Liệu Chi Tiết

**Trade Signal Journey:**
1. Rule Engine phát hiện setup → phát hành Trade Signal (score >= 80)
2. Execution Engine (Signal Queue) nhận signal
3. Risk Gateway kiểm tra 5 điều kiện rủi ro → PASS hoặc REJECT
4. Order Manager (nếu PASS) → tạo order, tính khối lượng
5. Broker Adapter (Paper hoặc Real) → gửi lệnh
6. Position Manager → theo dõi position, monitor SL/TP/exit rule
7. Position CLOSED → Trade Journal ghi lại + Periodic Review check
8. Kết quả → Performance Dashboard + Research Logging

**AI Backtesting Journey (Giai đoạn 5):**
1. Point-in-Time Framework nhận dữ liệu quá khứ (ẩn danh symbol/ngày)
2. Gửi cùng dữ liệu cho cả AI + Rule Engine
3. AI quyết định (via LLM) + Rule Engine quyết định (riêng)
4. Cả 2 quyết định qua Risk Gateway (double-check)
5. Thực thi ảo (Virtual Order + Position)
6. Ghi log đầy đủ (AI reasoning, rule score, fill price, PnL, exit)
7. Tiến sang timestamp tiếp theo (quyết định không thay đổi)
8. Lặp tới hết dữ liệu test → So sánh KPI (AI vs Rule baseline)

---

## 2. Kết Quả Audit: Phát Hiện & Sửa Chữa

### 2.1 Trùng Lặp Phát Hiện

**Loại 1: Không phải trùng lặp nguyên văn, nhưng overlap khái niệm**

| File 1 | File 2 | Tình huống | Quyết định |
|---|---|---|---|
| `paper_trading/VIRTUAL_ORDER.md` | `execution/ORDER_MANAGER.md` | Cả 2 xử lý order: virtual (sim) vs thực (exec) | ✅ Giữ cả 2 — khác tầng kiến trúc, không trùng |
| `paper_trading/POSITION.md` | `execution/POSITION_MANAGER.md` | Cả 2 theo dõi position: ảo vs thực | ✅ Giữ cả 2 — POSITION là đơn giản (sim), POSITION_MANAGER là production-grade |
| `paper_trading/TRADE_JOURNAL.md` | `research/EXPERIMENT_LOG.md` | TRADE_JOURNAL ghi lệnh, EXPERIMENT_LOG ghi phiên | ✅ Khác phạm vi, giữ cả 2 |

**Kết luận:** Không tìm thấy trùng lặp nguyên văn. Các file có overlap nhỏ nhưng phục vụ mục đích khác nhau ở các tầng kiến trúc khác nhau.

---

### 2.2 Mâu Thuẫn Phát Hiện

| Mâu thuẫn | File | Nguyên nhân | Sửa chữa |
|---|---|---|---|
| Trạng thái order khác nhau | VIRTUAL_ORDER vs ORDER_MANAGER | Hệ thống khác nhau (virtual vs exec) → cách gọi tên khác | ✅ Đã ghi chú trong EXECUTION_ENGINE.md mục 4.3 giải thích sự khác biệt |
| Tham chiếu `PAPER_TRADING_ENGINE.md` nằm trong folder | `execution/EXECUTION_ENGINE.md` line 105 | File tham chiếu không rõ vị trí (root? folder?) | ✅ Đã ghi chú: "PAPER_TRADING_ENGINE.md nằm trong paper_trading/ hoặc được dùng từ root" |
| Số lệnh thua liên tiếp trigger kill switch | RISK_GATEWAY.md, RISK_POLICY.md | Cả 2 nói "chưa chốt số" nhưng không có sự không nhất quán rõ ràng | ✅ Ghi chú: "Chưa chốt, cần Project Owner confirm (đề xuất 3-5)" |

**Kết luận:** Không tìm thấy mâu thuẫn lớn. Một số chỗ chưa rõ ràng về vị trí file/tham số, nhưng không phải lỗi logic.

---

### 2.3 Phần Còn Thiếu

| Mục | Trạng thái | Ghi chú |
|---|---|---|
| `rule_engine/RULE_010_EXIT.md` | ✅ Tồn tại | Đã có sẵn từ Phase 02 (151 dòng, đầy đủ nội dung) — **lần audit trước ghi nhầm là "chưa viết", đã đính chính** |
| `execution/SIGNAL_QUEUE.md` | ✅ Tồn tại | Đã tạo trong phiên này |
| `execution/RETRY_TIMEOUT_POLICY.md` | ✅ Tồn tại | Đã tạo trong phiên này |
| `execution/ERROR_HANDLING.md` | ✅ Tồn tại | Đã tạo trong phiên này |
| `risk/POSITION_SIZING.md` | ✅ Tồn tại | Tồn tại từ lâu |
| `backtests/POINT_IN_TIME_AI_BACKTEST.md` | ✅ Tạo trong phiên trước | Hoàn tất |

**Kết luận:** Tất cả file được tham chiếu đều tồn tại. Không có rule nào còn thiếu trong `rule_engine/`.

---

### 2.4 Chuẩn Hoá Cấu Trúc Thư Mục

**Pattern Hiện Tại:**
- Pattern A (Overview ở ROOT + chi tiết trong folder):
  - `RULE_ENGINE.md` (root) + `rule_engine/` (chi tiết) ✅
  - `BACKTEST_ENGINE.md` (root) + `backtests/` (chi tiết) ✅

- Pattern B (Overview TRONG folder):
  - `paper_trading/PAPER_TRADING_ENGINE.md` ← không nhất quán
  - `execution/EXECUTION_ENGINE.md` ← không nhất quán

**Quyết định:** 
- ⚠️ **Khuyến nghị di chuyển** `paper_trading/PAPER_TRADING_ENGINE.md` → `PAPER_TRADING_ENGINE.md` (root)
- ⚠️ **Khuyến nghị di chuyển** `execution/EXECUTION_ENGINE.md` → `EXECUTION_ENGINE.md` (root)
- **Lý do:** Nhất quán với Pattern A (RULE_ENGINE, BACKTEST_ENGINE cũng là engines, nên overview nên ở root)
- **Tác động:** Cần cập nhật lại mọi tham chiếu ở CURRENT_STATUS.md, DECISIONS.md, ROADMAP.md, AGENTS.md nếu có

**Tuy nhiên:** Vì đây là file MỚI TẠO TRONG PHI~N NÀY (không phải file cũ), và việc di chuyển sẽ cần cập nhật nhiều tham chiếu, **tôi SẼ KHÔNG thực hiện di chuyển** (để tránh thay đổi không cần thiết) nếu không rõ ràng yêu cầu. Thay vào đó, **ghi chú rõ trong báo cáo này**.

**Tên file:** Tất cả file .md đều theo UPPER_SNAKE_CASE ✅ nhất quán.

---

## 3. Chuẩn Hoá Áp Dụng

### 3.1 Cấu Trúc Thư Mục

✅ **Được áp dụng:**
- Tất cả file mới có HEADER (blockquote mô tả tài liệu)
- Tất cả file có liên hệ (liệt kê tham chiếu ở cuối)
- Tất cả file có trạng thái (thiết kế/chưa chốt/tiếp theo)

⚠️ **Khuyến nghị (chưa áp dụng):**
- Di chuyển `PAPER_TRADING_ENGINE.md` và `EXECUTION_ENGINE.md` lên root (để nhất quán)

### 3.2 Naming Convention

✅ Tất cả file .md sử dụng `UPPER_SNAKE_CASE`

### 3.3 Tính Nhất Quán

✅ Được áp dụng:
- Tất cả file paper_trading/ tham chiếu tới các file risk/, execution/ đúng cách
- Tất cả file execution/ tham chiếu tới RISK_POLICY.md, KILL_SWITCH_RULES.md đúng cách
- Tất cả file reference tới DECISIONS.md, RULE_ENGINE.md, ROADMAP.md đúng cách

---

## 4. Danh Sách TẤT CẢ Tham Số Chưa Chốt

### 4.1 Risk Policy Thông Số

| Tham số | File | Mục đích | Đề xuất | Ưu tiên |
|---|---|---|---|---|
| **% rủi ro/lệnh** | `risk/RISK_POLICY.md` | Max risk per trade | 1% hoặc 2% | ⭐⭐⭐ Ngay |
| **% rủi ro danh mục** | `risk/RISK_POLICY.md` | Max portfolio risk | 5% hoặc 10% | ⭐⭐⭐ Ngay |
| **Số lệnh thua liên tiếp** | `risk/KILL_SWITCH_RULES.md` | Trigger auto kill switch | 3 hoặc 5 | ⭐⭐⭐ Ngay |
| **% drawdown max** | `risk/KILL_SWITCH_RULES.md` | Trigger auto kill switch | 10% hoặc 20% | ⭐⭐⭐ Ngay |
| **Cho phép duplicate symbol** | `execution/RISK_GATEWAY.md` (check 5) | 1 position/symbol? hay nhiều? | False (cấm) | ⭐⭐ Sau |

### 4.2 Thông Số Point-in-Time AI Backtesting

| Tham số | File | Mục đích | Đề xuất | Ưu tiên |
|---|---|---|---|---|
| **LLM model** | `backtests/POINT_IN_TIME_AI_BACKTEST.md` (mục 9) | AI phân tích | Claude 3.5 Sonnet / GPT-4 Turbo | ⭐⭐⭐ Ngay |
| **Phiên bản prompt AI** | `backtests/POINT_IN_TIME_AI_BACKTEST.md` | Prompt version | MARKET_ANALYST_V1 (chưa viết) | ⭐⭐⭐ Ngay |
| **Cơ chế ẩn danh symbol** | `backtests/POINT_IN_TIME_AI_BACKTEST.md` (mục 2.1) | Chống look-ahead bias | ASSET_A/B hay UUID? | ⭐⭐⭐ Ngay |
| **Ẩn danh ngày tháng** | `backtests/POINT_IN_TIME_AI_BACKTEST.md` (mục 2.1) | Chống look-ahead bias | T-offset (T+0=cuối test) | ⭐⭐⭐ Ngay |
| **Chỉ báo gửi cho AI** | `backtests/POINT_IN_TIME_AI_BACKTEST.md` (mục 3.1) | Input complexity | OHLCV thô? hay + RSI/EMA? | ⭐⭐ Sau |
| **Dữ liệu test** | `backtests/POINT_IN_TIME_AI_BACKTEST.md` (mục 9) | Dataset | EUR/USD, GBP/USD, BTC; D1, H4; 6+ năm | ⭐⭐⭐ Ngay |
| **Chi phí LLM** | `backtests/POINT_IN_TIME_AI_BACKTEST.md` (mục 9) | Budget | Chưa estimate | ⭐⭐ Sau |

### 4.3 Thông Số Rule Engine & Strategy

| Tham số | File | Mục đích | Hiện tại | Ưu tiên |
|---|---|---|---|---|
| **R/R minimum** | `DECISIONS.md` | Trade accept condition | 1.5 (đề xuất) | ⭐ Chưa chốt |
| **Scoring threshold** | `DECISIONS.md` | Setup accept condition | 80 (đề xuất) | ⭐ Chưa chốt |
| **Body ratio breakout** | `DECISIONS.md` | Breakout quality | 60% (đề xuất) | ⭐ Chưa chốt |
| **SMA period volume** | `DECISIONS.md` | Volume confirmation | 20 (đề xuất) | ⭐ Chưa chốt |
| **EMA period bias** | `rule_engine/RULE_007_EMA.md` | Trend filter | Chưa chốt (strategy define) | ⭐ Chưa chốt |
| **N-bar swing high/low** | `strategies/TF_001.md`, `TF_002.md` | Structure define | N=2 hoặc 3? | ⭐ Chưa chốt |

### 4.4 Thông Số Execution Engine

| Tham số | File | Mục đích | Đề xuất | Ưu tiên |
|---|---|---|---|---|
| **account_capital** | `execution/ORDER_MANAGER.md` | Position sizing | Từ Project Owner | ⭐⭐⭐ Ngay |
| **order_type** | `execution/ORDER_MANAGER.md` | MARKET hay LIMIT | MARKET (đề xuất) | ⭐ Sau |
| **time_in_force** | `execution/ORDER_MANAGER.md` | GTC hay IOC/FOK | GTC (đề xuất) | ⭐ Sau |
| **Retry max times** | `execution/RETRY_TIMEOUT_POLICY.md` | Retry attempt limit | 3 (đề xuất) | ⭐ Sau |
| **Timeout (giây)** | `execution/RETRY_TIMEOUT_POLICY.md` | Wait broker response | 30s (đề xuất) | ⭐ Sau |
| **Backoff strategy** | `execution/RETRY_TIMEOUT_POLICY.md` | Retry spacing | Exponential (đề xuất) | ⭐ Sau |

### 4.5 Thông Số Paper Trading

| Tham số | File | Mục đích | Hiện tại | Ưu tiên |
|---|---|---|---|---|
| **Slippage/Spread** | `paper_trading/VIRTUAL_ORDER.md` (mục 5.4) | Execution realism | Chưa chốt (cần per-pair) | ⭐⭐ Sau |
| **Tần suất update price** | `paper_trading/POSITION.md` (mục 6.1) | Real-time hay per-minute? | Chưa chốt | ⭐ Sau |
| **Initial capital paper** | `paper_trading/VIRTUAL_ACCOUNT.md` | Starting balance | Chưa chốt (ví dụ 10K?) | ⭐⭐ Sau |
| **Format lưu trữ journal** | `paper_trading/TRADE_JOURNAL.md` (mục 8) | JSON/CSV/DB? | File-based (đề xuất) | ⭐ Sau |
| **Review timezone** | `paper_trading/PERIODIC_REVIEW.md` (mục 8) | EOD time | Chưa chốt (UTC? local?) | ⭐ Sau |

---

## 5. Rủi Ro Còn Lại

### 5.1 Rủi Ro Dữ Liệu

| Rủi ro | Tác động | Mức độ | Giảm thiểu |
|---|---|---|---|
| **Chưa có dữ liệu giá thật** | Không thể backtest, paper trade, live trading | ⭐⭐⭐ Cao | Lấy dữ liệu (Phase 3 priority) |
| **Look-ahead bias AI backtest** | AI kết quả tốt nhưng chỉ vì "nhìn trước" | ⭐⭐⭐ Cao | Tuân thủ Point-in-Time framework strict (ẩn symbol/ngày, locked OOS) |
| **Slippage assumption sai** | Paper trade kết quả khác backtest quá | ⭐⭐ Trung | Compare paper vs backtest, adjust slippage nếu > 30% |

### 5.2 Rủi Ro Kiến Trúc/Thiết Kế

| Rủi ro | Tác động | Mức độ | Giảm thiểu |
|---|---|---|---|
| **Tham số rủi ro chưa chốt** | Position sizing, kill switch sai → account mất | ⭐⭐⭐ Cao | Project Owner PHẢI chốt trước code (NGAY) |
| **Overlap Paper Trading vs Execution** | Confusing, code redundant | ⭐ Thấp | Ghi chú rõ: Paper là simulation, Execution là production |
| **Overfitting Strategy** | TF_001, TF_002 backtest tốt nhưng live fail | ⭐⭐⭐ Cao | Tuân thủ Walk-Forward Analysis, locked OOS, mỗi OOS chỉ chạy 1 lần |

### 5.3 Rủi Ro Vận Hành

| Rủi ro | Tác động | Mức độ | Giảm thiểu |
|---|---|---|---|
| **Chi phí LLM cao** | Backtest 1000+ lệnh × 2 prompts = hóa đơn API lớn | ⭐⭐ Trung | Estimate trước, start nhỏ (1 pair, 1 TF, 6 tháng) |
| **Chưa có code** | Mọi thứ còn là giả thuyết, chưa chạy thật | ⭐⭐⭐ Cao | Bắt đầu code Phase 3 NGAY (Rule Engine), test từng module |
| **Chưa integrate broker thật** | Paper trade mô phỏng có thể khác live | ⭐⭐ Trung | Test Broker Adapter Interface cẩn thận, mock nhiều scenario |

---

## 6. Đánh Giá: "Sẵn Sàng Code Chưa?"

### Câu Trả Lời: **CÓ, nhưng CÓ ĐIỀU KIỆN**

### 6.1 Phần Sẵn Sàng

✅ **Kiến trúc / Thiết kế:**
- Rule Engine: ✅ Hoàn tất (10 rules, decision flow, scoring system)
- Paper Trading Engine: ✅ Hoàn tất (7 thành phần, state machine)
- Execution Engine: ✅ Hoàn tất (8 thành phần, interface)
- Point-in-Time AI Backtesting: ✅ Framework rõ ràng (4 bước, logging spec)
- Tất cả mối quan hệ giữa module: ✅ Rõ ràng, có document

✅ **Foundation:**
- Knowledge base: ✅ Đầy đủ (kiến thức, strategy template, quy tắc tốt)
- Risk policy: ✅ Có từ từ lâu, structure đúng
- Strategy: ✅ 2 strategy (TF_001, TF_002) định nghĩa rõ

✅ **Có thể code ngay những phần:**
- Rule Engine logic (các hàm trend detection, breakout, volume...) — không phụ thuộc rủi ro
- Rule engine decision flow (10 bước tuần tự) — không phụ thuộc số liệu
- Data parsing (OHLCV) — không phụ thuộc architecture quyết định
- Audit Log framework — không phụ thuộc tham số
- Unit test cho từng rule — không phụ thuộc live data

### 6.2 Phần Chưa Sẵn Sàng

❌ **Chưa chốt tham số cốt lõi:**
- % rủi ro/lệnh: ??? (1% hay 2%)
- % drawdown max: ??? (10% hay 20%)
- Số lệnh thua liên tiếp: ??? (3 hay 5)
- **→ Position sizing không thể code "thật" (chỉ code scaffolding)**
- **→ Kill switch không thể activate "thật" (chỉ code placeholder)**

❌ **Chưa có dữ liệu:**
- Không có dữ liệu giá lịch sử
- **→ Backtest không chạy được (Phase 3 blocked)**
- **→ Paper trading không thể bắt đầu (Phase 4 blocked)**

❌ **Một số chi tiết chưa hoàn thiện:**
- AI prompt (`prompts/MARKET_ANALYST.md` đã có, nhưng phiên bản "khoá" cụ thể dùng cho Point-in-Time backtest — ví dụ gắn tag `MARKET_ANALYST_V1` — chưa được chốt/đóng băng) → cần chốt trước khi chạy AI backtesting thật

❌ **Chưa test thực tế:**
- Tất cả kiến trúc là hypothetical (chưa code)
- Assumption slippage, market condition: chưa validate

### 6.3 Lộ Trình Khuyến Nghị

**Tuần 1: Chốt Tham Số (NGAY)**
```
[Week 1] Project Owner xác nhận:
  ✅ % rủi ro/lệnh = 1% (example)
  ✅ % danh mục = 5%
  ✅ Số lệnh thua = 3
  ✅ % drawdown = 15%
  ✅ account_capital = 10,000 USD
  ✅ Dữ liệu test = EUR/USD, GBP/USD; D1, H4; 2015-2025
```

**Tuần 2-3: Viết Tài Liệu Chi Tiết**
```
[Week 2-3]
  ✅ RULE_010_EXIT.md (exit rule detail)
  ✅ MARKET_ANALYST_V1.md (AI prompt cho backtesting)
  ✅ Lấy dữ liệu (2-3 pair, 6+ năm)
```

**Tuần 4-6: Code Phase 3 (Backtest)**
```
[Week 4-6]
  ✅ Code Rule Engine (rule_001.py... rule_010.py)
  ✅ Unit test từng rule
  ✅ Data loader (OHLCV parser)
  ✅ Backtest engine (từ BACKTEST_ENGINE.md)
  ✅ Chạy backtest TF_001 + TF_002
```

**Tuần 7-10: Code Phase 4 (Paper Trade)**
```
[Week 7-10]
  ✅ Virtual Account, Virtual Order, Position (paper_trading/)
  ✅ Paper Broker Adapter
  ✅ Trade Journal + Periodic Review
  ✅ Performance Dashboard
  ✅ Test paper trading 2-4 tuần
```

**Tuần 11-14: Code Phase 5 (AI Backtesting)**
```
[Week 11-14]
  ✅ Point-in-Time backtest framework
  ✅ Integrate AI (LLM calls) + Rule Engine
  ✅ Locked OOS + Walk-Forward
  ✅ So sánh KPI (AI vs Rule)
  ✅ Report kết quả
```

---

## 7. Đề Xuất Các Bước Tiếp Theo

### 7.1 Ưu Tiên Cao (Tuần 1-2)

1. **[Tuần 1] Project Owner chốt tham số rủi ro:**
   - Meeting ngắn 30 min, confirm: % risk/trade, portfolio risk max, kill switch threshold
   - **Impact:** Không confirm → không thể code position sizing, kill switch → backed chưa có ý nghĩa

2. **[Tuần 1-2] Lấy dữ liệu giá lịch sử:**
   - Chọn 2-3 pair (EUR/USD, GBP/USD ít nhất)
   - 2 timeframe (D1, H4)
   - 6+ năm dữ liệu (2015-2025 nếu có)
   - **Impact:** Backtest không chạy được nếu chưa có dữ liệu

### 7.2 Ưu Tiên Trung (Tuần 3-4)

4. **[Tuần 3] Chốt phiên bản "khoá" của AI Prompt (gắn tag MARKET_ANALYST_V1):**
   - `rule_engine/RULE_010_EXIT.md` đã có sẵn — không cần viết lại, chỉ cần review cùng Project Owner ở bước audit rule engine
   - Dựa trên prompts/MARKET_ANALYST.md hiện tại
   - Draft chi tiết: input (OHLCV + indicators), output (BUY/SELL/HOLD + reasoning), constraints (no look-ahead)
   - Test với dữ liệu dummy
   - **Impact:** AI backtesting không chạy nếu prompt chưa rõ

5. **[Tuần 3-4] Confirm Point-in-Time Backtesting Tham Số:**
   - LLM model: Claude 3.5 Sonnet hay GPT-4?
   - Ẩn danh symbol: ASSET_A/B hay UUID?
   - Chỉ báo: OHLCV + RSI/EMA hay chỉ OHLCV?
   - **Impact:** Code backtest framework phụ thuộc tham số này

### 7.3 Ưu Tiên Thấp (Tuần 5+)

6. **[Tuần 5+] Confirm tiêu chí "AI tốt hơn":**
   - Expectancy cao 5% là pass? hay cần 10%+?
   - Tiêu chí decision của Phase 5
   - **Impact:** Không impact code, nhưng guide decision

7. **[Tuần 5+] Confirm Execution Engine Details:**
   - order_type (MARKET hay LIMIT?)
   - time_in_force (GTC hay IOC?)
   - retry strategy (exponential backoff period?)
   - **Impact:** Detail implementation Execution Engine, không block Phase 3

---

## 8. Kết Luận

### 8.1 Tóm Tắt

✅ **Kiến trúc:** Hoàn tất, toàn diện, nhất quán  
✅ **Tài liệu:** 30+ file thiết kế, structured, cross-reference clear  
⚠️ **Tham số:** 20+ tham số chưa chốt, liệt kê rõ trong mục 4  
⚠️ **Dữ liệu:** Chưa có, cần lấy  
❌ **Code:** 0 lines (đúng như planned — giai đoạn thiết kế, không code)  

### 8.2 Sẵn Sàng Code?

**CÓ, nhưng tuần 1 PHẢI chốt rủi ro tham số, nếu không:**
- Position sizing không thể code "thật" (chỉ code placeholder)
- Kill switch không thể activate "thật" (chỉ code placeholder)
- Backtest kết quả vô ích (không biết % risk/trade → không tính được PnL thực)

**Có thể code NGAY (không phụ thuộc tham số):**
- Rule Engine logic (rule 001-010)
- Data loader (OHLCV parser)
- Audit Log framework
- Unit test infrastructure

### 8.3 Bước Tiếp Theo Khẩn Cấp

```
[Tuần 1 - Ngay lập tức]
1. Project Owner chốt: % risk/trade, % portfolio, kill switch, account capital, dữ liệu test
2. Lấy dữ liệu (EUR/USD, GBP/USD, D1/H4, 6+ năm)

[Tuần 2-3]
3. Chốt phiên bản "khoá" của prompt (gắn tag MARKET_ANALYST_V1) dựa trên prompts/MARKET_ANALYST.md hiện có
4. Confirm Point-in-Time parameters (LLM, ẩn danh, indicators)

[Tuần 4+]
5. Bắt đầu Phase 3 (Code Rule Engine + Backtest)
```

---

**Báo Cáo Kiểm Toàn Kiến Trúc Kết Thúc**

**Trạng thái cuối:** ✅ **Sẵn sàng cho Phase 3 (Code), với điều kiện project owner chốt rủi ro tham số tuần 1**

