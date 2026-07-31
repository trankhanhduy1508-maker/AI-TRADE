# Backtest Engine — Kiến trúc và Luồng Xử lý

> **Tài liệu thiết kế Backtest Engine của AI-TRADE.**  
> Mô tả đầy đủ kiến trúc hệ thống backtest, luồng xử lý dữ liệu từ Market Data → Performance Analysis,  
> các module chính, quy trình đánh giá chiến lược từ giả thuyết tới kết luận kiểm chứng.  
> Tuân thủ `backtests/BACKTEST_STANDARD.md` (no look-ahead bias, no overfitting, no cherry-picking).

---

## 1. Kiến trúc Backtest Engine tổng thể

### 1.1 Định nghĩa

Backtest Engine là **hệ thống mô phỏng giao dịch lịch sử** để kiểm chứng giả thuyết chiến lược.  
Nó không là bot thật, không gửi lệnh ra sàn. Nhiệm vụ duy nhất: đánh giá xem chiến lược  
đã định nghĩa trong `strategies/*.md` có tạo ra tín hiệu hợp lệ, quản lý rủi ro tốt,  
và có kỳ vọng dương hay không trên dữ liệu lịch sử.

### 1.2 Các thành phần chính

| Thành phần | Vai trò | Người/Đội phụ trách | Kết quả |
|---|---|---|---|
| **Data Ingestion** | Lấy OHLCV, tick data, session info, timezone từ nguồn bên ngoài | Human (lập trình viên) | Dữ liệu thô, lưu vào kho dữ liệu |
| **Data Validation** | Kiểm tra đầy đủ, không có lỗ hổng, định dạng đúng | Engine | Báo cáo lỗi/cảnh báo |
| **Data Cleaning** | Loại bỏ dữ liệu sai, xử lý outlier, căn chỉnh timezone | Engine | Dữ liệu sạch |
| **Indicator Calculation** | Tính EMA, RSI, Volume SMA (nếu chiến lược cần) | Engine | Cached indicators |
| **Rule Engine** | Áp dụng 10 rule từ `RULE_ENGINE.md` trên từng nến | Engine (quy tắc xác định sẵn) | Scoring 0-100, signal: TRADE/WAIT/REJECT |
| **Signal Generator** | Phát hành tín hiệu LONG/SHORT khi Score >= 80 (ngưỡng đề xuất) | Engine | Trade signals với entry/SL/TP |
| **Position Simulator** | Mô phỏng vào lệnh, xử lý giá thực tế trong nến | Engine | Position open/close history |
| **Risk Manager** | Kiểm tra rủi ro danh mục, quản lý Position Sizing theo `risk/POSITION_SIZING.md` | Engine | Reject lệnh nếu vượt limit |
| **Trade Logger** | Ghi log toàn bộ giao dịch: entry, exit, PnL, drawdown | Engine | Trade journal (CSV/JSON) |
| **Performance Analyzer** | Tính tất cả KPI: Win Rate, Expectancy, Sharpe, Sortino, Calmar, Max DD... | Engine | Bảng KPI |
| **Report Generator** | Tổng hợp kết quả thành báo cáo dễ đọc, so sánh in-sample vs out-of-sample | Engine | HTML/MD report |

---

## 2. Luồng dữ liệu chi tiết (Data Flow)

### 2.1 Kiến trúc tổng thể

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. MARKET DATA (OHLCV, Tick, Session, Timezone, Spread)        │
│    từ nguồn bên ngoài (API, CSV, database)                     │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. DATA VALIDATION                                              │
│    ✓ Đầy đủ (không lỗ hổng)  ✓ Định dạng  ✓ Range hợp lệ      │
│    ✓ Không duplicate  ✓ Timestamp nhất quán                    │
│    → Reject nếu lỗi, báo cáo chi tiết                          │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. DATA CLEANING                                                │
│    • Xử lý outlier (giá quá cao/quá thấp)                      │
│    • Căn chỉnh timezone (convert all to UTC)                   │
│    • Xử lý session boundary (không trading lúc chợ đóng)      │
│    • Xử lý missing candle (gap, holiday)                       │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. INDICATOR CALCULATION (Cached)                               │
│    • EMA(50), EMA(100), EMA(200) — nếu chiến lược dùng        │
│    • RSI(14) với input = Close                                 │
│    • Volume SMA(20)                                            │
│    • ATR (nếu tính stop loss động)                             │
│    → Cache để tránh tính lặp lại                               │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. RULE ENGINE (Tuần tự từ RULE_ENGINE.md)                    │
│    • RULE_001: Trend (HH/HL or LH/LL)                          │
│    • RULE_002: Market Structure (VALID)                        │
│    • RULE_003: Breakout (body ratio, close > level)            │
│    • RULE_004: Pullback (tiếp tục theo dõi setup)             │
│    • RULE_005: Volume (xác nhận)                               │
│    • RULE_006: RSI (bias)                                      │
│    • RULE_007: EMA (filter)                                    │
│    • RULE_008: Risk (R/R >= 1.5, SL valid)                    │
│    • RULE_009: Liquidity (spread, depth)                       │
│    → Scoring 0-100, reject conditions                          │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. SIGNAL GENERATOR                                             │
│    IF Score >= 80 (ngưỡng đề xuất):                            │
│      → Phát hành TRADE signal (LONG hoặc SHORT)                │
│      → Kèm entry/SL/TP levels từ RULE_008                      │
│    ELSE:                                                        │
│      → WAIT (score < 80 nhưng >= 50: theo dõi tiếp)           │
│      → REJECT (score < 50 hoặc reject conditions)              │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. POSITION SIMULATOR (Xử lý từng nến)                        │
│    Khi có TRADE signal (LONG/SHORT):                           │
│    • Entry: Close price của nến hiện tại (hoặc next open)     │
│    • Stop Loss: Level định sẵn (từ RULE_008)                  │
│    • Take Profit: Level định sẵn                              │
│    • Kiểm tra nến tiếp theo:                                   │
│      - Chạm SL? → Close position, ghi PnL                     │
│      - Chạm TP? → Close position, ghi PnL                     │
│      - Xảy ra EXIT signal (RULE_010)? → Close, ghi PnL        │
│      - Tiếp tục hold                                          │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. RISK MANAGER                                                 │
│    Trước mỗi vào lệnh:                                         │
│    • Tính khối lượng (position size) từ POSITION_SIZING.md    │
│    • Kiểm tra tổng rủi ro danh mục (từ RISK_POLICY.md)       │
│    • Kiểm tra tương quan giữa các vị trí mở                   │
│    IF rủi ro vượt limit:                                       │
│      → REJECT lệnh, ghi log                                    │
│    ELSE:                                                        │
│      → Cho phép vào lệnh                                       │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 9. TRADE LOGGER                                                 │
│    Ghi toàn bộ giao dịch (CSV/JSON):                            │
│    • Timestamp, pair, timeframe                                │
│    • Direction (LONG/SHORT), Entry price                       │
│    • Stop Loss, Take Profit                                    │
│    • Exit price, Exit reason, PnL, Return %                   │
│    • Entry drawdown, Exit drawdown                             │
│    • Cumulative PnL, Drawdown%                                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 10. PERFORMANCE ANALYZER                                        │
│     Tính KPI (xem backtests/KPI_STANDARD.md):                 │
│     • Win Rate, Profit Factor, Expectancy                     │
│     • Max Drawdown, Relative DD                               │
│     • Sharpe, Sortino, Calmar Ratio                           │
│     • Recovery Factor, Consecutive Wins/Losses                │
│     → In-sample vs Out-of-sample (nếu có split)              │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 11. REPORT GENERATOR                                            │
│     • Xuất báo cáo HTML/MD (xem BACKTEST_REPORT_TEMPLATE.md)  │
│     • Bảng KPI tóm tắt                                        │
│     • Equity curve + Drawdown chart                           │
│     • Trade list: tất cả giao dịch, entry/exit reason         │
│     • Phân tích dãy lỗ, dãy thắng                             │
│     • So sánh in-sample / out-of-sample                       │
│     • Kết luận: chiến lược có giá trị không?                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Giải thích chi tiết từng bước

#### Bước 1: Market Data
**Input:**  
- OHLCV (Open, High, Low, Close, Volume) của từng nến
- Tick Data (tùy chọn, cho độ chính xác cao hơn)
- Session info (giờ mở/đóng chợ)
- Timezone (UTC, EST, JST...)
- Spread, Commission, Swap

**Output:** Dữ liệu thô, lưu vào database/cache

**Tại sao cần:**  
Mọi quyết định giao dịch phải dựa trên dữ liệu thật, không được sáng tạo ra.

---

#### Bước 2: Data Validation
**Input:** Dữ liệu thô từ bước 1

**Kiểm tra:**
- Mỗi nến có đủ 5 phần tử (O, H, L, C, V)?
- H >= L, H >= O, H >= C, L <= O, L <= C?
- Volume >= 0?
- Timestamp tăng đơn điệu (không ngược thời gian)?
- Không có gap lớn không mong muốn (chỉ gap session)?
- Close và Open của nến kế tiếp liên tiếp hay có lỗ hổng?

**Output:**  
- ✅ Data VALID: tiếp tục bước 3
- ❌ Data INVALID: báo cáo lỗi cụ thể, không xử lý tiếp

**Khi nào gây lỗi backtest:**  
Nếu bỏ qua validation, có thể xuất hiện "lỗ hổng dữ liệu" tạo ra tín hiệu ảo.

---

#### Bước 3: Data Cleaning
**Input:** Dữ liệu hợp lệ từ bước 2

**Xử lý:**
1. **Outlier:** Nếu giá nhảy > X% so với close trước (ví dụ 10%), cần xác nhận có phải gap hay lỗi dữ liệu
2. **Timezone:** Convert tất cả timestamp về UTC (hoặc 1 timezone chung) để tránh nhầm lẫn
3. **Session boundary:** Nếu timeframe là 4H mà chợp đóng 17:00, dãy nến 16:00-17:00 sẽ ngắn, cần ghi chú
4. **Missing candle:** Nếu session gap (weekend, holiday), đừng tính nhầm thành "downtrend"
5. **Duplicate data:** Nếu lấy từ 2 nguồn, loại bỏ record trùng

**Output:** Dữ liệu sạch

---

#### Bước 4: Indicator Calculation
**Input:** Dữ liệu sạch

**Tính toán (cache để tránh tính lặp):**
- EMA: nếu chiến lược dùng RULE_007 (EMA bias)
- RSI: nếu chiến lược dùng RULE_006 (RSI)
- Volume SMA: nếu chiến lược dùng RULE_005 (volume confirmation)
- ATR: nếu dùng tính stop loss động

**Output:** Mỗi indicator có 1 cột data (indexed by timestamp)

**Tại sao cache:** Tránh tính lặp lại 100 lần khi backtest 100 lệnh.

---

#### Bước 5: Rule Engine
**Input:** Dữ liệu sạch + indicators

**Luồng (tuần tự):**  
Áp dụng 10 quy tắc từ `RULE_ENGINE.md` trên từng nến:
1. RULE_001 (Trend): có xu hướng (HH/HL) không? → Score điểm, có thể reject nếu không trend
2. RULE_002 (Structure): cấu trúc hợp lệ (VALID) không?
3. RULE_003 (Breakout): có breakout (body ratio, close) không?
4. ...
5. RULE_008 (Risk): R/R >= 1.5, SL hợp lệ?
6. RULE_009 (Liquidity): spread, depth OK?

**Output:**  
- Score 0-100 (tổng điểm từ 9 rule, rule 10 là exit — áp dụng sau)
- Reject conditions: reject cứng nếu không trend, không structure, R/R < 1.0, vv
- Decision: TRADE (score >= 80), WAIT (50-79), REJECT (< 50 hoặc reject conds)

---

#### Bước 6: Signal Generator
**Input:** Score từ Rule Engine

**Logic:**
```
IF Score >= 80 (ngưỡng đề xuất, cần backtest confirm):
    → Phát hành TRADE signal
    → Kèm direction (LONG/SHORT)
    → Kèm entry/SL/TP từ RULE_008
ELSE IF 50 <= Score < 80:
    → WAIT (tiếp tục theo dõi)
ELSE:
    → REJECT (không vào lệnh)
```

**Output:** Trade signal (LONG/SHORT) + entry/SL/TP, hoặc WAIT/REJECT

---

#### Bước 7: Position Simulator
**Input:** Trade signal, market data tiếp theo

**Xử lý từng nến:**
1. **Entry:** Close price của nến hiện tại (hoặc open nến tiếp theo, tùy quy định)
2. **Hold:** Kiểm tra nến tiếp theo:
   - High >= TP? → Close at TP → PnL = (TP - Entry) * Qty
   - Low <= SL? → Close at SL → PnL = (SL - Entry) * Qty
   - RULE_010 EXIT signal? → Close at market (close price) → PnL
   - Tiếp tục hold
3. **Exit:** Ghi lại exit price, exit reason, PnL

**Output:** Trade history (mỗi giao dịch: entry, exit, PnL)

---

#### Bước 8: Risk Manager
**Input:** Trade signal từ Signal Generator

**Kiểm tra trước mỗi lệnh:**
1. **Position Size:** Từ signal, tính khối lượng dựa trên POSITION_SIZING.md
2. **Portfolio Risk:** Tổng rủi ro của tất cả vị trí mở có vượt `risk/RISK_POLICY.md` không?
3. **Correlation:** Các vị trí có tương quan cao (cùng cặp, cùng hướng)? Tính gộp rủi ro.

**Decision:**
- Nếu OK → cho phép Position Simulator vào lệnh
- Nếu vượt limit → REJECT, không vào lệnh, ghi log

**Output:** ACCEPT / REJECT

---

#### Bước 9: Trade Logger
**Input:** Mỗi giao dịch từ Position Simulator

**Ghi log (CSV/JSON):**
```
timestamp_entry, pair, timeframe, direction, entry_price, 
stop_loss, take_profit, quantity,
timestamp_exit, exit_price, exit_reason,
pnl, return_pct,
cum_pnl, max_dd_% (peak to trough khi còn position)
```

**Output:** Trade journal (file CSV/JSON hoặc database)

---

#### Bước 10: Performance Analyzer
**Input:** Trade journal từ Trade Logger

**Tính toán KPI (xem `backtests/KPI_STANDARD.md`):**
- Win Rate, Profit Factor, Expectancy
- Max Drawdown, Relative DD
- Sharpe, Sortino, Calmar
- Recovery Factor, Consecutive Wins/Losses
- Return on Account % (ROA)
- Profit Factor, Win/Loss Ratio

**Output:** Bảng KPI (dạng số)

**Bật lên In-sample vs Out-of-sample:**  
Nếu dữ liệu được split (ví dụ 2015-2018 = in-sample để điều chỉnh tham số,  
2019-2020 = out-of-sample để test), tính riêng KPI cho mỗi phần.

---

#### Bước 11: Report Generator
**Input:** KPI + Trade journal + Market data

**Xuất báo cáo:**
- HTML hoặc Markdown (template xem `backtests/BACKTEST_REPORT_TEMPLATE.md`)
- Bảng KPI tóm tắt
- Equity curve (cumulative PnL theo thời gian)
- Drawdown curve (peak-to-trough %)
- Trade list (tất cả giao dịch chi tiết)
- Phân tích dãy lỗ dài nhất, dãy thắng dài nhất
- So sánh in-sample vs out-of-sample (nếu có)
- **Kết luận:** Chiến lược có giá trị (>= điều kiện thành công) không?

**Output:** Báo cáo dễ đọc, dễ so sánh, không suy diễn quá mức

---

## 3. Hệ thống phát hiện lỗi (Error Detection & Prevention)

### 3.1 Look Ahead Bias (Nhìn về phía trước)

**Định nghĩa:** Sử dụng dữ liệu tương lai (chưa xảy ra) để xác nhận tín hiệu quá khứ.

**Ví dụ sai:**
- Tại thời điểm T, dùng High của nến T+1 để xác nhận setup tại T (lỗ dữ liệu từ tương lai).
- Vẽ trendline dựa trên swing high/low xác nhận sau (sau khi biết rồi), rồi tính có breakout trendline không.

**Cách phát hiện:**
- Kiểm tra: tại mỗi thời điểm quyết định vào lệnh, có dùng dữ liệu nào > timestamp hiện tại?
- Trace luồng input của Rule Engine: tất cả input phải là dữ liệu <= timestamp entry.

**Cách phòng tránh:**
- **Quy tắc cứng:** Tại mỗi nến T, chỉ được dùng dữ liệu từ nến T trước đó (T-1, T-2, ...).
- **Validation code:** Đặt assert tại vị trí tính score, kiểm tra max(timestamp indicator) <= timestamp entry.

---

### 3.2 Survivorship Bias (Thiên lệch sống sót)

**Định nghĩa:** Chỉ backtest trên cặp/thị trường đã tồn tại tới nay, bỏ qua cặp đã biến mất.

**Ví dụ sai:**
- Backtest EURUSD, GBPUSD (cặp lớn, chắc chắn tồn tại), bỏ qua cặp emerging đã delisted hoặc collapsed.
- Kết quả: chiến lược chỉ "tốt" vì backtest trên những cặp sống sót.

**Cách phát hiện:**
- Liệt kê tất cả cặp/thị trường đã backtest.
- So sánh: có những cặp nào bị loại ra (tuyên bố không có dữ liệu)?
- Nếu cặp bị loại là những cặp yếu hoặc thua lỗ, có khả năng là survivorship bias.

**Cách phòng tránh:**
- **Công khai:** Ghi rõ cặp/thị trường nào đã backtest, nó còn active không, và nó có dữ liệu năm bao nhiêu.
- **Bổ sung:** Nếu có thể, backtest thêm trên cặp emerging hoặc cặp đã delisted (nếu có dữ liệu).

---

### 3.3 Data Leakage (Rò rỉ dữ liệu)

**Định nghĩa:** Huấn luyện/tối ưu tham số dùng thông tin từ tập test, hoặc tham số lọc được chọn sau khi biết kết quả.

**Ví dụ sai:**
- Backtest 2015-2020, sau đó điều chỉnh tham số R/R từ 1.5 → 2.0 vì thấy kết quả 1.5 có 1 chuỗi lỗ dài → Điều chỉnh này dùng "kiến thức" từ toàn bộ 2015-2020, không phải từ quy tắc trước.
- Chọn "chiến lược này tốt nhất" dựa trên kết quả backtest, nhưng quyết định chọn là sau khi xem kết quả (chứ không trước).

**Cách phát hiện:**
- Xem timeline: khi nào tham số được chốt? Trước hay sau khi backtest?
- Kiểm tra: có bao nhiêu tham số được thử (grid search)? Nếu thử 100+ biến thể, cơ hội overfitting cao.

**Cách phòng tránh:**
- **Quy tắc cứng:** Tham số phải được chốt TRƯỚC khi backtest, từ rule engine design (`RULE_ENGINE.md`).
- **In-sample vs Out-of-sample:** Điều chỉnh tham số chỉ trên in-sample, test kết quả trên out-of-sample chưa từng thấy.

---

### 3.4 Overfitting (Quá khớp)

**Định nghĩa:** Tham số được tối ưu quá tốt trên 1 bộ dữ liệu nhất định, nhưng không tổng quát hóa.

**Ví dụ sai:**
- Điều chỉnh EMA period từ 50 → 37 → 62 chỉ vì in-sample 2015-2018 cho kết quả tốt nhất với 37.
- Out-of-sample 2019-2020 với EMA 37 cho kết quả tệ, nhưng không phát hiện.

**Dấu hiệu nhận biết:**
- In-sample Sharpe Ratio = 2.5, Out-of-sample = 0.8 (chênh lệch > 2x).
- In-sample Win Rate = 65%, Out-of-sample = 45%.
- Consecutive Losses: in-sample max 3, out-of-sample max 8.

**Cách phòng tránh:**
- **Out-of-sample test bắt buộc:** không được coi kết quả in-sample là chính thức.
- **Walk Forward Analysis:** Chia dữ liệu thành các window liên tiếp, tối ưu trên window N, test trên window N+1.
- **Bootstrap / Monte Carlo:** Đảo xáo lại chuỗi PnL để kiểm tra độ ổn định.

---

### 3.5 Curve Fitting (Khớp đường cong)

**Định nghĩa:** Chọn tham số để phù hợp với "hình dạng" lịch sử, chứ không phải vì nó có cơ sở logic.

**Ví dụ sai:**
- "Thấy trong dữ liệu 2015-2018, RSI quay từ 70 xuống luôn có pullback", nên set rule "nếu RSI từ 75 → 65 trong 2 nến → vào lệnh".
- Quy tắc này "khớp" dữ liệu lịch sử nhưng không có cơ sở gì ngoài coincidence.

**Cách phát hiện:**
- Kiểm tra: quy tắc này có cơ sở logic không? Hay chỉ là "nó xảy ra ở quá khứ"?
- Test: quy tắc này có tổng quát trên nhiều thị trường/timeframe không? Hay chỉ tốt trên 1 cặp.

**Cách phòng tránh:**
- **Nguyên tắc:** Nếu không có lý do logic (từ `RULE_ENGINE.md`, `strategies/*.md`), không tạo quy tắc mới.
- **Cross-market test:** Nếu quy tắc "tốt" trên EURUSD, thử trên GBPUSD, AUDJPY xem có tốt không.

---

### 3.6 Duplicate Trades (Giao dịch trùng)

**Định nghĩa:** Cùng setup được xử lý 2 lần, hoặc 2 tín hiệu gần nhau được coi là tín hiệu riêng biệt.

**Ví dụ sai:**
- Nến T có breakout → phát hành TRADE signal LONG
- Nến T+1 (giá vẫn cao, structure vẫn same) → phát hành TRADE signal LONG lại
- → Ghi nhận 2 giao dịch thay vì 1 setup.

**Cách phát hiện:**
- Xem Trade Journal: có 2 entry liên tiếp cùng direction, cùng cấp giá không?
- So sánh: entry nến T và entry nến T+1, setup có giống không?

**Cách phòng tránh:**
- **Quy tắc:** Nếu có vị trí LONG mở, không phát hành tín hiệu LONG mới cho tới khi vị trí cũ đóng.
- **Check code:** Kiểm tra Signal Generator có kiểm tra position status (is_open) trước khi phát signal không.

---

### 3.7 Missing Candle (Nến thiếu)

**Định nghĩa:** Dữ liệu bị lỗ hổng (weekend, holiday, server down), nhưng không được xử lý rõ ràng.

**Ví dụ sai:**
- Friday 17:00 close = 1.0900, Monday 9:00 open = 1.0950 (gap weekend)
- Backtest tính high Friday = 1.0900, low Friday = 1.0880 (không có dữ liệu weekend)
- Tính swing: high Friday là swing high? Hay bị gap ảnh hưởng?

**Cách phát hiện:**
- Kiểm tra: timestamp nào có gap > 1 session (ví dụ > 24h nhưng không phải weekend)?
- Xem Trade Journal: có trade nào bị exit lỗi vì "high" của nến weekend không?

**Cách phòng tránh:**
- **Data Cleaning step:** Xác định session boundary (9:00-17:00 Forex, 14:30-21:00 Stock...), bỏ dữ liệu ngoài session.
- **Logging:** Ghi log nếu phát hiện gap lớn, yêu cầu human review.

---

### 3.8 Wrong Timezone (Timezone sai)

**Định nghĩa:** Dữ liệu từ 2 nguồn khác nhau, timezone khác, nhưng không convert về chung.

**Ví dụ sai:**
- Source 1: dữ liệu GMT (mở 9:00 GMT, đóng 17:00 GMT)
- Source 2: dữ liệu EST (mở 14:00 EST = 9:00 GMT, đóng 22:00 EST = 17:00 GMT, nhưng ghi EST)
- Nhân phức hợp 2 nguồn: "Mở 9:00 GMT + 14:00 EST = sao không trùng?"

**Cách phát hiện:**
- Kiểm tra: timezone của source là gì?
- Nếu combine 2 source: convert về chung timezone, rồi kiểm tra có bị offset không.

**Cách phòng tránh:**
- **Step 1 Data Cleaning:** Convert tất cả timestamp về 1 timezone chung (UTC).
- **Logging:** Ghi rõ "timestamp ban đầu: X timezone → converted to UTC: Y".

---

### 3.9 Invalid Spread (Spread không hợp lệ)

**Định nghĩa:** Spread được giả định < thực tế, hoặc spread thay đổi (ví dụ trước news).

**Ví dụ sai:**
- Giả định spread = 2 pips (typical), nhưng trước ngày công bố lãi suất, spread = 10 pips.
- Signal Generator không check spread, phát hành entry lệnh, nhưng thực tế trade thêm 8 pips chi phí.

**Cách phát hiện:**
- So sánh: giả định spread vs spread thực tế (từ dữ liệu bid-ask).
- Nếu có tick data: tính spread từ bid-ask, không giả định.

**Cách phòng tránh:**
- **Data source:** Nếu có, dùng tick data (bid-ask) thay vì OHLCV (chỉ close/open).
- **Risk Manager:** Kiểm tra spread thực tế trước entry, nếu spread > ngưỡng → reject entry.

---

### 3.10 Invalid R/R (Risk/Reward không hợp lệ)

**Định nghĩa:** R/R được tính sai, hoặc không thực hiện được R/R lý thuyết.

**Ví dụ sai:**
- Lý thuyết: entry 1.1000, SL 1.0950 (50 pips), TP 1.1100 (100 pips) → R/R = 1:2
- Thực tế: giá lên tới 1.1080, không tới 1.1100 (TP), rồi rơi xuống 1.0950 (SL) → R/R thực tế = 1:1, không phải 1:2.

**Cách phát hiện:**
- Xem Trade Journal: R/R lý thuyết vs R/R thực tế có khác?
- Nếu R/R thực tế < R/R lý thuyết quá nhiều lần: signal generator có sai không?

**Cách phòng tránh:**
- **Lý thuyết:** Tính R/R dựa trên level lý thuyết (entry/SL/TP từ setup), ghi rõ.
- **Thực tế:** Tính R/R thực tế từ actual exit price, so sánh với lý thuyết.
- **Logging:** Ghi cả 2, để phân tích sai lệch.

---

## 4. KPI (Key Performance Indicators)

**Chi tiết xem:** `backtests/KPI_STANDARD.md`

Các KPI quan trọng:
- Net Profit, Gross Profit, Gross Loss
- Win Rate, Expectancy, Profit Factor
- Max Drawdown, Relative Drawdown
- Sharpe Ratio, Sortino Ratio, Calmar Ratio
- Average Win, Average Loss, Risk/Reward
- Consecutive Wins, Consecutive Losses
- Recovery Factor

**Nguyên tắc:** Không tin 1 KPI một mình — luôn xem tổng bộ KPI cùng lúc.  
Ví dụ: Win Rate 70% + Expectancy âm = chiến lược thua lỗ (lỗ giao dịch lớn hơn lợi giao dịch).

---

## 5. Quy trình kiểm thử (Testing Procedures)

### 5.1 In-Sample Testing
**Mục đích:** Confirm giả thuyết + điều chỉnh tham số (nếu cần).

**Thực hiện:**
- Chạy backtest trên khoảng thời gian định sẵn (ví dụ 2015-2018).
- Nếu giả định không match kết quả, sửa giả định hoặc rule.
- Ghi nhận KPI in-sample.

**Lưu ý:** Không điều chỉnh tham số quá nhiều, tránh overfitting.

### 5.2 Out-of-Sample Testing
**Mục đích:** Xác nhận kết quả in-sample có tổng quát không.

**Thực hiện:**
- Chạy backtest trên khoảng thời gian **chưa từng thấy** (ví dụ 2019-2020).
- So sánh KPI out-of-sample vs in-sample.
- Nếu sai lệch > 30%, có khả năng overfitting.

### 5.3 Walk Forward Analysis
**Mục đích:** Kiểm tra khi điều chỉnh tham số liên tục (rolling window).

**Thực hiện:**
- Chia dữ liệu: Window 1 (2015-2016 in-sample) → test on 2017 (out-of-sample)
- Chia dữ liệu: Window 2 (2015-2017 in-sample) → test on 2018 (out-of-sample)
- Gộp kết quả từ tất cả window.
- KPI Walk Forward = kết quả gộp từ all out-of-sample window.

**Chi tiết:** xem `backtests/WALK_FORWARD_GUIDE.md`

### 5.4 Monte Carlo Simulation
**Mục đích:** Kiểm tra độ ổn định của sequence (chuỗi) PnL.

**Thực hiện:**
- Lấy tất cả trade (entry-exit PnL) từ backtest.
- Đảo xáo lại chuỗi trade (shuffle trades), recalculate equity curve + drawdown.
- Lặp N lần (ví dụ 1000 lần).
- Kiểm tra: trong các lần shuffle này, Max Drawdown có bao nhiêu % worse?

**Chi tiết:** xem `backtests/MONTE_CARLO_GUIDE.md`

---

## 6. Khả năng mở rộng (Scalability)

### 6.1 Thêm chiến lược mới
1. Viết file `strategies/TF_NNN_*.md` (giả thuyết + quy tắc)
2. Chạy Backtest Engine với tham số: strategy = TF_NNN, market = ?, timeframe = ?
3. Engine sẽ apply 10 rule từ `RULE_ENGINE.md` (chung cho tất cả chiến lược)
4. Xuất báo cáo, update `research/EXPERIMENT_LOG.md`

**Dễ/khó:** Dễ — engine thiết kế để chạy bất kỳ chiến lược nào (chỉ khác tham số entry/SL/TP).

### 6.2 Thêm thị trường mới
1. Lấy dữ liệu lịch sử (OHLCV) của thị trường mới
2. Chạy Data Validation + Cleaning
3. Chạy Backtest Engine trên chiến lược hiện có
4. Xuất báo cáo, ghi nhận "chiến lược TF_001 trên AUDJPY: tốt/tệ"

**Dễ/khó:** Dễ — chỉ cần dữ liệu.

### 6.3 Thêm timeframe mới
1. Lấy dữ liệu hiện tại ở timeframe mới (ví dụ 1H → 4H → 1D)
2. Chạy Backtest Engine
3. Ghi nhận "TF_001 trên 4H: tốt/tệ" (khác 1H)

**Dễ/khó:** Dễ — chỉ đổi timeframe.

### 6.4 Backtest nhiều thị trường cùng lúc
**Kiến trúc:** Chạy Engine tuần tự hoặc song song (parallel):
- Sequential: Market 1 → Market 2 → Market 3 (chậm)
- Parallel: Market 1, 2, 3 cùng lúc (nhanh, cần quản lý resource)

**Output:** Bảng so sánh KPI giữa các market (pivot table style).

---

## 7. Quyết định thiết kế chính

| Quyết định | Lựa chọn | Lý do |
|---|---|---|
| **Scoring ngưỡng vào lệnh** | >= 80/100 (đề xuất) | Cân bằng giữa chính xác cao (>90 = quá cứng) vs linh hoạt (< 70 = quá nhiều false signal) |
| **Entry timing** | Close price nến hiện tại | Thực tế, không look-ahead |
| **In-sample vs Out-of-sample** | Bắt buộc (quy tắc cứng) | Tránh overfitting |
| **Walk Forward** | Nên làm (tùy chọn) | Kiểm tra khả năng điều chỉnh tham số liên tục |
| **Monte Carlo** | Nên làm (tùy chọn) | Kiểm tra độ ổn định sequence |
| **Min trades for conclusion** | >= 30 (nếu từ đơn vị > 30, tốt hơn) | < 30 = too noisy statistically |
| **Timezone** | UTC (chung) | Tránh nhầm lẫn |
| **Spread** | Actual (từ tick data) hoặc giả định thực tế | Không giả định 0 |
| **Slippage** | Giả định tối thiểu (ví dụ 1 pip) | Thực tế luôn có slippage |

---

## 8. Workflow kiểm chứng chiến lược (từ giả thuyết → kết luận)

1. **Ghi giả thuyết** → `research/HYPOTHESES.md`
   - Giả thuyết: "Breakout + volume xác nhận = trend strong"
   - Điều kiện kiểm chứng: breakout body > 60%, volume > SMA20, không false break

2. **Thiết kế rule** → `strategies/TF_NNN.md` + `RULE_ENGINE.md`
   - Quy tắc entry, SL, TP, exit cụ thể

3. **Chạy Backtest Engine**
   - Data: 2015-2018 (in-sample)
   - Output: KPI, trade journal, báo cáo

4. **Kiểm tra in-sample KPI**
   - Win Rate >= 45%?
   - Expectancy > 0?
   - Max DD <= 20%?
   - Nếu không → Quay lại bước 2, sửa rule

5. **Chạy out-of-sample**
   - Data: 2019-2020 (out-of-sample)
   - So sánh KPI với in-sample
   - Sai lệch > 30%? → Có khả năng overfitting

6. **Walk Forward (tùy chọn)**
   - Xác nhận khả năng điều chỉnh tham số

7. **Monte Carlo (tùy chọn)**
   - Xác nhận độ ổn định sequence

8. **Cập nhật kết luận**
   - `research/HYPOTHESES.md`: "Được kiểm chứng / Bị bác bỏ"
   - Nếu được kiểm chứng: thêm vào danh sách chiến lược có giá trị
   - Nếu bị bác bỏ: ghi nhận vào `research/FAILURE_CASES.md`

---

## 9. Giới hạn và giả định

- **Dữ liệu quá khứ ≠ tương lai:** Backtest dựa trên dữ liệu lịch sử, không đảm bảo hiệu suất tương lai.
- **Spread/Slippage giả định:** Thực tế có thể khác (tránh, news, weekend).
- **Lỏng rủi ro:** Không mô phỏng stop order không được fill (quá volatile), nếu cần, phải adjust risk manager.
- **Lệnh fill tức thời:** Giả định entry/exit tại price đã định, thực tế market order có slippage.
- **Không mô phỏng tâm lý:** Backtest không thể bắt được "panic selling" hoặc "euphoria buying".

---

## 10. Tham chiếu

- `RULE_ENGINE.md` — 10 quy tắc scoring
- `strategies/TF_*.md` — Giả thuyết + quy tắc từng chiến lược
- `risk/RISK_POLICY.md`, `risk/POSITION_SIZING.md` — Quản lý rủi ro
- `backtests/BACKTEST_STANDARD.md` — Chuẩn backtest (no look-ahead, no overfitting, no cherry-picking)
- `backtests/KPI_STANDARD.md` — Định nghĩa KPI
- `backtests/WALK_FORWARD_GUIDE.md` — Walk Forward Analysis
- `backtests/MONTE_CARLO_GUIDE.md` — Monte Carlo Simulation
- `backtests/BACKTEST_CHECKLIST.md` — QA Checklist trước khi tin kết quả
- `research/EXPERIMENT_LOG.md` — Ghi nhận tất cả backtest đã chạy
- `research/FAILURE_CASES.md` — Ghi nhận các ca thất bại, để học hỏi
