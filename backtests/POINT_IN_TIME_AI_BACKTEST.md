# Point-in-Time AI Backtesting — Framework Kiểm chứng LLM/AI

> **Framework thiết kế kiểm chứng khách quan khả năng ra quyết định của LLM/AI trên dữ liệu lịch sử.**  
> Mục tiêu: Đánh giá xem AI có ra quyết định giao dịch hợp lý không khi **CHỈ được cấp dữ liệu tại từng thời điểm mô phỏng (point-in-time)**, triệt để chống look-ahead bias, và **so sánh kết quả với baseline rule-based** (Rule Engine từ `RULE_ENGINE.md`).

---

## 1. Mục tiêu

### 1.1 Động lực thiết kế

Một LLM/AI có thể đã "nhớ" sự kiện lịch sử thật từ dữ liệu huấn luyện:
- Biết trước diễn biến giá thật của EURUSD từ 2015-2025 (nếu dữ liệu đó trong training set)
- Biết trước COVID crash, Fed rate hike, dữ liệu kinh tế quan trọng
- "Suy luận" rằng "nhìn thấy pattern X → chắc chắn là Y"

**Framework này buộc AI phải ra quyết định dựa trên:**
- Dữ liệu point-in-time (chỉ quá khứ, không tương lai)
- Danh tính ẩn symbol (không dùng kiến thức đã biết về cặp tiền cụ thể)
- Thời gian ẩn (không suy luận sự kiện lịch sử)

### 1.2 Mục tiêu chính

1. **Kiểm chứng khách quan:** AI có ra quyết định tốt hơn/tương đương Rule Engine không?
2. **Đo rủi ro lừa dối:** Dùng dữ liệu point-in-time có loại bỏ được look-ahead bias không?
3. **Xác định giá trị AI:** Nếu AI tốt hơn, tốt bao nhiêu? Tạo thêm chi phí (API calls) không?
4. **Hạ tầng cho Giai đoạn 5:** Framework này là nền tảng để validate AI Scoring trước khi dùng thực tế.

---

## 2. Nguyên tắc Cốt Lõi — Chống Look-ahead Bias

### 2.1 Các nguồn rò rỉ thông tin tương lai + Cách chặn

| Nguồn rò rỉ | Mô tả | Cách chặn |
|---|---|---|
| **Nến hiện tại đang hình thành** | Giá intrabar hiện tại có thể gợi ý tương lai của nến | KHÔNG bao giờ gửi nến chưa đóng cho AI — chỉ gửi nến **ĐÃ ĐÓNG** tính đến timestamp mô phỏng hiện tại |
| **Danh tính symbol thật** | AI biết "EURUSD từ thường tăng sau ECB", "BTC thường spike trước halving" | **Ẩn tên symbol**: dùng mã hoá hoặc placeholder (ví dụ "ASSET_A", "ASSET_B") — AI không biết pair thật |
| **Ngày tháng thật** | AI suy luận "2020 là năm COVID", "tháng 3 Fed rate cut" → biết trước sự kiện | **Ẩn ngày tháng thật**: dùng offset tương đối (ví dụ "Ngày T+0", "Ngày T+45", "Ngày T+120") — AI chỉ biết thứ tự tương đối |
| **Tin tức/sự kiện lịch sử** | Dữ liệu đầu vào chứa "2008 financial crisis", "Fed tăng lãi suất" | **Loại bỏ triệt để**: không gửi bất kỳ thông tin sự kiện lịch sử, tin tức, hoặc background context nào liên quan tới giai đoạn dữ liệu |
| **Chỉ báo tính toán** | Nếu RSI tính từ dữ liệu tương lai (ví dụ "future RSI" dùng nến chưa đóng) | **Chỉ báo từ quá khứ:** RSI, EMA, SMA, MACD được tính từ những nến **ĐÃ ĐÓNG** tính đến timestamp hiện tại — không phải "future leak" |
| **Giá target/support** | AI biết "nếu giá lên tới 1.25 hôm nay, nó sẽ rebound ở 1.20" (biết trước support thật) | **Không gửi support/resistance "đã biết"**: chỉ gửi swing high/low được tính từ past data |

### 2.2 Nguyên tắc chi tiết

**Nguyên tắc 1: Chỉ dữ liệu quá khứ**
- Mỗi call tới LLM, chỉ được gửi dữ liệu từ timestamp T-∞ tới timestamp T (hiện tại mô phỏng)
- Không được gửi bất kỳ thông tin nào từ timestamp T+1 trở đi
- Bar/candle hiện tại (T) chỉ được gửi **nếu đã ĐÓNG** — nếu còn đang hình thành, chỉ gửi bar T-1

**Nguyên tắc 2: Ẩn danh symbol**
- Thay "EURUSD" → "ASSET_A" (hoặc "PAIR_001", "SYMBOL_UUID_xxx")
- Thay "BTC/USDT" → "ASSET_B" (hoặc "PAIR_002")
- AI không được biết identity thật của pair — để AI không dùng prior knowledge

**Nguyên tắc 3: Ẩn danh thời gian**
- Thay "2020-03-15" → "T-0", "T-1", "T-45" (offset từ ngày hôm nay)
- Thay "Tháng 3 2020" → "Tháng T+0"
- AI không thể suy luận "COVID crash ngày 2020-03-11" → không biết trước gì

**Nguyên tắc 4: Loại bỏ context lịch sử**
- Không gửi "Fed ngành tăng lãi suất", "GDP giảm 20%", "bầu cử tổng thống"
- Không gửi "đây là thời kỳ high volatility", "đây là trend đầu năm"
- Nếu cần ghi chú gì cho AI biết, chỉ ghi "volatility cao/thấp" (không phải lý do tại sao)

**Nguyên tắc 5: Chỉ báo từ quá khứ được phép**
- RSI(14) tính từ 14 bar ĐÃ ĐÓNG trước T → được phép gửi
- EMA(50) tính từ 50 bar ĐÃ ĐÓNG trước T → được phép gửi
- Volume SMA(20) tính từ 20 bar ĐÃ ĐÓNG trước T → được phép gửi
- **KHÔNG phép:** Future-looking indicator, hoặc indicator dùng bar chưa đóng

---

## 3. Vòng Lặp Xử Lý Tuần Tự (Sequential Loop)

### 3.1 Sơ đồ tổng quát

```
Mô phỏng bắt đầu
    ↓
═══════════════════════════════════════════════════════════════
    Bước 1: OBSERVE (Cấp dữ liệu point-in-time)
    ├─ Hệ thống xác định timestamp mô phỏng hiện tại = T
    ├─ Chuẩn bị dữ liệu từ -∞ tới T (ĐÃ ĐÓNG)
    ├─ Ẩn danh symbol, ngày tháng, sự kiện
    ├─ Tính chỉ báo từ quá khứ (RSI, EMA, Volume SMA, ...)
    ├─ Gửi cho AI + Rule Engine cùng 1 bộ dữ liệu
    └─ Ghi log: "Observe [T], dữ liệu gửi = {...}"
    ↓
    Bước 2: DECIDE (AI + Rule Engine ra quyết định độc lập)
    ├─ AI (qua 1 trong các prompt ở prompts/) đưa ra quyết định
    │   ├─ Reasoning: Tại sao AI chọn hành động này?
    │   ├─ Output: [BUY / SELL / HOLD / WAIT / REJECT]
    │   ├─ Nếu có lệnh: Entry price, Stop Loss, Target
    │   └─ Ghi log: "AI Decision = {...}, Reasoning = {...}"
    │
    ├─ Rule Engine (RULE_ENGINE.md) ra quyết định riêng
    │   ├─ Áp dụng 10 rule tuần tự
    │   ├─ Output: [TRADE / WAIT / REJECT], Setup Score 0-100
    │   └─ Ghi log: "Rule Decision = {...}, Score = {...}"
    │
    └─ So sánh: AI vs Rule (ghi lại)
    ↓
    Bước 3: EXECUTE (Thực thi quyết định trong mô phỏng)
    ├─ Nếu AI → BUY/SELL:
    │   ├─ Virtual Order (từ Paper Trading Engine)
    │   ├─ Giả lập slippage/spread
    │   ├─ Kiểm tra Risk Gateway (rủi ro có vượt không?)
    │   ├─ Nếu pass → Position OPEN, ghi log fill price
    │   └─ Nếu fail → ghi log rejection reason
    │
    ├─ Nếu Rule → TRADE:
    │   ├─ Tương tự AI (Virtual Order + Risk Gateway)
    │   └─ Ghi log riêng biệt
    │
    ├─ Mở Position (nếu orders fill)
    │   ├─ Entry price = fill price thực tế (không giá ideal)
    │   ├─ Stop Loss, Target
    │   ├─ Unrealized PnL update
    │   └─ Ghi log: "Position OPEN = {...}"
    │
    └─ Khoảng thời gian: Execute = quá trình fill + risk check (< 1 mô phỏng bar, giả lập)
    ↓
    Bước 4: REVEAL NEXT DATA (Tiến sang timestamp tiếp theo)
    ├─ Khoảng thời gian này (từ sau Execute tới trước Observe bước tiếp theo)
    ├─ Hệ thống không gửi dữ liệu "trong tương lai" cho AI
    ├─ Ai KHÔNG được "sửa quyết định" ở bước này — quyết định ở Execute đã khoá
    ├─ Position được monitor (SL/TP hit?, RULE_010 exit?)
    ├─ Ghi log: "Position CLOSED = {...}" nếu exit
    ├─ Update Virtual Account
    └─ Tiến sang T+1
    ↓
    Lặp lại từ Bước 1 tới hết dữ liệu test
```

### 3.2 Chi tiết 4 bước

**Bước 1: OBSERVE (Cấp dữ liệu point-in-time)**

```
Đầu vào:
  - Timestamp mô phỏng hiện tại: T
  - Dữ liệu OHLCV từ T-∞ tới T (ĐÃ ĐÓNG)

Xử lý:
  1. Tách dữ liệu thành 2 bộ
     ├─ Bộ cho AI: Ẩn danh symbol + ngày, chỉ OHLCV + chỉ báo
     └─ Bộ cho Rule Engine: Ẩn danh nhưng có swap symbol (để track)
  
  2. Tính chỉ báo từ quá khứ (T-1 trở lại):
     ├─ RSI(14 chưa chốt, cần Project Owner)
     ├─ EMA(chưa chốt)
     ├─ Volume SMA(20 đề xuất)
     ├─ Swing High/Low (N=2 hoặc 3, chưa chốt)
     └─ Các chỉ báo khác theo strategy
  
  3. Nén dữ liệu thành JSON/dict:
     {
       "timestamp_relative": "T+45",
       "price_data": [
         {"close": 1.0950, "high": 1.0970, "low": 1.0940, "open": 1.0945, "volume": 120000},
         {"close": 1.0948, "high": 1.0955, "low": 1.0935, "open": 1.0948, "volume": 95000},
         ...
       ],
       "indicators": {
         "rsi_14": 65.2,
         "ema_50": 1.0920,
         "volume_sma_20": 105000,
         "swing_high": 1.0975,
         "swing_low": 1.0910
       }
     }
  
  4. Gửi cho AI + Rule Engine

Đầu ra:
  - Dữ liệu point-in-time (ẩn danh symbol/ngày)
  - Các chỉ báo tính từ quá khứ
```

**Bước 2: DECIDE (AI + Rule Engine ra quyết định)**

```
AI Decision:
  Input: Dữ liệu point-in-time từ OBSERVE
  
  Prompt gửi tới LLM:
  ├─ (Từ prompts/MARKET_ANALYST.md hoặc TRADE_CRITIC.md)
  ├─ Mô tả cấu trúc thị trường hiện tại (swing, trend, ...)
  ├─ Liệt kê điều kiện setup (từ strategies/TF_001 hoặc TF_002)
  ├─ Yêu cầu: "Bạn có nên vào lệnh BUY/SELL không? Tại sao?"
  └─ Ràng buộc: "KHÔNG dự đoán tương lai. Chỉ dùng dữ liệu đã cho."
  
  Output từ LLM:
  {
    "decision": "BUY" | "SELL" | "HOLD" | "WAIT" | "REJECT",
    "confidence": 0.0-1.0,  # LLM tự đánh giá độ tự tin
    "reasoning": "text...",  # Tại sao? (ghi đầy đủ để audit)
    "entry_price": 1.0950,   # Nếu BUY/SELL
    "stop_loss": 1.0910,     # Nếu có lệnh
    "target_price": 1.1000,  # Nếu có lệnh (tùy chọn)
    "risk_pct": 2.0          # % rủi ro (nếu có lệnh)
  }
  
  Ghi log đầy đủ: timestamp mô phỏng, input đầy đủ gửi cho LLM, output đầy đủ từ LLM, LLM model version.

Rule Engine Decision:
  Input: Dữ liệu point-in-time từ OBSERVE
  
  Quy trình:
  ├─ RULE_001: Có xu hướng? → UP/DOWN/NEUTRAL
  ├─ RULE_002: Có cấu trúc? → VALID/INVALID
  ├─ RULE_003: Có breakout? → YES/NO/WEAK
  ├─ RULE_004: Có pullback? → VALID/INVALID/WAITING
  ├─ RULE_005: Volume xác nhận? → STRONG/NORMAL/WEAK
  ├─ RULE_006: RSI bias? → BULLISH/BEARISH/NEUTRAL
  ├─ RULE_007: EMA bias? → UP_BIAS/DOWN_BIAS/NEUTRAL
  ├─ RULE_008: Risk/Reward OK? → ACCEPTABLE/UNACCEPTABLE
  ├─ RULE_009: Thanh khoản? → GOOD/FAIR/POOR
  └─ Tính Setup Score (0-100)
  
  Output:
  {
    "decision": "TRADE" | "WAIT" | "REJECT",
    "score": 85,  # 0-100, từ tất cả rule
    "rules_passed": [001, 002, 003, ...],
    "rules_failed": [008],
    "entry_price": 1.0950,  # Nếu TRADE
    "stop_loss": 1.0910,
    "target_price": 1.1000,
    "reasoning": "text..."  # Tóm tắt
  }
  
  Ghi log đầy đủ: score, rule results, quyết định cuối.

So sánh AI vs Rule:
  {
    "agreement": true | false,  # AI và Rule có cùng quyết định?
    "ai_decision": "BUY",
    "rule_decision": "TRADE",
    "ai_confidence": 0.78,
    "rule_score": 85,
    "divergence_reason": "..."  # Nếu khác nhau
  }
```

**Bước 3: EXECUTE (Thực thi quyết định)**

```
Nếu AI/Rule quyết định BUY/SELL (hoặc TRADE):
  1. Virtual Order
     ├─ Entry price = giá close hiện tại (hoặc giá AI/Rule đề xuất)
     ├─ Giả lập slippage (ví dụ ±2 pips)
     ├─ Giả lập spread (ví dụ 2 pips)
     └─ Fill price = entry_price ± slippage/spread
  
  2. Risk Gateway kiểm tra (từ risk/RISK_POLICY.md)
     ├─ Check 1: (PnL tiềm năng nếu SL hit) <= % rủi ro/lệnh?
     ├─ Check 2: Tổng rủi ro portfolio <= limit?
     ├─ Check 3: Kill switch active?
     ├─ Check 4: Consecutive losses < threshold?
     ├─ Check 5: Không có position cùng symbol?
     └─ Nếu fail bất kỳ check → REJECT, ghi log rejection reason
  
  3. Nếu PASS tất cả:
     ├─ Position OPEN
     ├─ Ghi log: "position_opened = {...}"
     ├─ Entry price = fill price (không ideal price)
     ├─ Stop Loss = rule định
     ├─ Target (nếu có)
     ├─ Risk amount = (entry - SL) × quantity
     └─ Unrealized PnL = 0 (mới mở)
  
  4. Nếu FAIL:
     ├─ Ghi log: "order_rejected = {...}"
     ├─ Không mở position
     └─ Tiếp tục theo dõi

Ghi log chi tiết: order_id, signal_id (từ AI/Rule), entry price, SL, TP, fill price, slippage, risk amount, rejection reason (nếu có).
```

**Bước 4: REVEAL NEXT DATA (Tiến sang timestamp tiếp theo)**

```
Sau khi Execute khoá quyết định:
  1. Monitor vị trí mở (nếu có):
     ├─ Cập nhật giá market hiện tại
     ├─ Tính unrealized PnL
     ├─ Kiểm tra: SL hit? TP hit? RULE_010 exit signal?
     └─ Nếu hit → position CLOSED, ghi log
  
  2. Update Virtual Account:
     ├─ Balance = Balance_old + realized PnL (nếu có lệnh đóng)
     ├─ Equity = Balance + unrealized PnL (từ các position mở)
     └─ Ghi log: "account_updated = {...}"
  
  3. Tiến sang timestamp tiếp theo:
     ├─ T = T + 1 (tăng 1 bar)
     ├─ Chuẩn bị dữ liệu cho bar tiếp theo
     └─ Quay lại Bước 1 (OBSERVE)

Điểm quan trọng:
  - AI KHÔNG được "sửa quyết định" ở bước này
  - Quyết định ở Execute đã fixed (khoá)
  - Chỉ có exit rules (SL, TP, RULE_010) được phép tác động sau này
```

---

## 4. Locked Out-of-Sample & Walk-Forward

### 4.1 Định nghĩa Out-of-Sample bị khoá

**Out-of-Sample "bị khoá"** nghĩa là:
- Dữ liệu được đặt riêng ra **từ đầu**, không dùng để tune prompt/strategy
- Chỉ dùng 1 lần duy nhất để đánh giá AI
- Sau khi chạy xong, không quay lại sửa prompt rồi chạy lại trên đúng bộ dữ liệu OOS đó

**Mục đích:** Tránh overfitting prompt — AI/prompt có thể tune "quá tốt" cho 1 bộ dữ liệu nhất định, nhưng fail trên dữ liệu mới.

### 4.2 Walk-Forward áp dụng

Framework này **phải sử dụng Walk-Forward Analysis** (xem `backtests/WALK_FORWARD_GUIDE.md`):

```
Dữ liệu tổng: 2015-2020 (6 năm)

Window 1:
  In-sample (tune prompt):    2015-2016
  Out-of-sample (test AI):    2017 (LOCKED)

Window 2:
  In-sample (tune prompt):    2015-2017 (có thể điều chỉnh prompt dựa trên 2017 kết quả)
  Out-of-sample (test AI):    2018 (LOCKED)

Window 3:
  In-sample (tune prompt):    2015-2018
  Out-of-sample (test AI):    2019 (LOCKED)

Window 4:
  In-sample (tune prompt):    2015-2019
  Out-of-sample (test AI):    2020 (LOCKED)

Kết quả cuối: Gộp tất cả OOS (2017, 2018, 2019, 2020) → WFA result
```

**Nguyên tắc:**
1. **Mỗi OOS window chạy 1 lần duy nhất** — không optimize trên đó rồi chạy lại
2. **Có thể điều chỉnh prompt** sau khi xem kết quả từ window trước, nhưng **KHÔNG được chạy lại** trên window đó
3. **Tuy nhiên:** Có thể thiết lập "prompt version V1, V2, V3" nếu muốn thử prompt khác nhau trên **cùng 1 OOS window**, miễn là ghi rõ "Test V1 vs V2 trên cùng OOS 2017"

### 4.3 Ghi log Walk-Forward

```
window_id: 1
in_sample_period: 2015-01-01 to 2016-12-31
out_of_sample_period: 2017-01-01 to 2017-12-31 [LOCKED]
prompt_version: MARKET_ANALYST_V1
ai_model: gpt-4-turbo-2024-04-09

in_sample_result:
  ai_trades: 120
  ai_win_rate: 53%
  ai_expectancy: 1.85 pips

out_of_sample_result: [LOCKED - chỉ chạy 1 lần]
  ai_trades: 45
  ai_win_rate: 51%
  ai_expectancy: 1.62 pips
  rule_expectancy: 1.78 pips (baseline so sánh)
  ai_vs_rule_agreement: 62%
```

---

## 5. Logging Đầy Đủ (Append-Only)

### 5.1 Mục đích logging

- **Reproducibility:** Tái lập được toàn bộ quá trình backtest
- **Audit trail:** Kiểm chứng AI có "gian lận" (look-ahead) không
- **Comparison:** So sánh AI vs Rule trên **chính xác cùng 1 bộ dữ liệu**, bằng chứng rõ ràng
- **Debugging:** Nếu AI quyết định sai, có thể xem đầu vào/đầu ra chính xác là gì

### 5.2 Log Format (Append-Only, không sửa/xóa sau khi ghi)

Nguyên tắc tương tự `execution/AUDIT_LOG.md`:

```
[ISO8601 wall-clock timestamp] [Event Type] [Details as JSON]

Ví dụ:
2025-08-01T14:32:45.123Z [observe_start] {"window": 1, "timestamp_relative": "T+45", "symbol_ident": "ASSET_A", "bar_count": 150}
2025-08-01T14:32:46.456Z [ai_decision_request] {"prompt_version": "MARKET_ANALYST_V1", "model": "claude-3-5-sonnet-20241022", "input_tokens": 2145, "timestamp_ms": 1123}
2025-08-01T14:32:51.789Z [ai_decision_response] {"decision": "BUY", "confidence": 0.78, "reasoning": "...", "entry": 1.0950, "sl": 1.0910, "output_tokens": 456, "latency_ms": 5333}
2025-08-01T14:32:52.012Z [rule_decision] {"decision": "TRADE", "score": 85, "rules_passed": [1,2,3,4,5,6,7,8], "rules_failed": [], "entry": 1.0950, "sl": 1.0910}
2025-08-01T14:32:52.100Z [decide_compare] {"agreement": true, "ai_decision": "BUY", "rule_decision": "TRADE", "ai_confidence": 0.78, "rule_score": 85}
2025-08-01T14:32:52.234Z [risk_check_start] {"order_id": "AI_WIN1_ORD001", "signal_id": "AI_WIN1_SIG001", "entry": 1.0950, "sl": 1.0910, "target": 1.1000}
2025-08-01T14:32:52.345Z [risk_check_1_passed] {"order_id": "AI_WIN1_ORD001", "risk_per_trade": 2.0, "limit": 2.5, "status": "PASS"}
2025-08-01T14:32:52.356Z [risk_check_2_passed] {"order_id": "AI_WIN1_ORD001", "portfolio_risk": 5.2, "limit": 10.0, "status": "PASS"}
2025-08-01T14:32:52.367Z [risk_check_passed_all] {"order_id": "AI_WIN1_ORD001", "checks": 5}
2025-08-01T14:32:52.480Z [virtual_order_executed] {"order_id": "AI_WIN1_ORD001", "entry_ideal": 1.0950, "slippage_pips": 1, "spread_pips": 2, "fill_price": 1.0953, "fill_time_ms": 200}
2025-08-01T14:32:52.500Z [position_opened] {"position_id": "AI_WIN1_POS001", "entry": 1.0953, "sl": 1.0910, "target": 1.1000, "quantity": 100000, "risk_amount": 4300}
2025-08-01T14:32:52.600Z [execute_complete] {"bar_index": 45, "ai_order_count": 1, "rule_order_count": 1}
2025-08-01T14:33:15.234Z [position_monitoring] {"position_id": "AI_WIN1_POS001", "current_price": 1.0968, "unrealized_pnl": 1500, "update_time": "T+45"}
... (many more monitoring updates)
2025-08-01T14:35:00.000Z [position_closed] {"position_id": "AI_WIN1_POS001", "close_reason": "TP_HIT", "close_price": 1.1000, "realized_pnl": 4700, "realized_pnl_pct": 109.3, "bars_held": 3}
2025-08-01T14:35:00.100Z [reveal_next_data] {"bar_index": 46, "account_balance": 104700, "equity": 104700, "open_positions": 0}
... (lặp lại cho bar tiếp theo)
```

### 5.3 Log fields bắt buộc mỗi bước

**OBSERVE:**
- wall-clock timestamp
- bar index / timestamp relative (T+N)
- symbol identity (ẩn danh)
- OHLCV data range
- Indicators computed (RSI, EMA, Volume SMA, Swing levels)

**DECIDE (AI):**
- wall-clock timestamp
- prompt version / AI model
- Full input sent to LLM (tất cả prompt + data)
- Full output from LLM (raw JSON/text)
- AI decision (BUY/SELL/HOLD/WAIT/REJECT)
- Confidence, reasoning
- Entry/SL/Target (nếu có)
- Latency, token count (input/output)

**DECIDE (Rule):**
- wall-clock timestamp
- Rule results (RULE_001 tới RULE_009)
- Setup Score (0-100)
- Rule decision (TRADE/WAIT/REJECT)
- Entry/SL/Target (nếu có)
- Reasoning / quy tắc nào fail

**DECIDE (Compare):**
- wall-clock timestamp
- AI decision vs Rule decision
- Agreement (Y/N)
- Divergence reason (nếu khác nhau)

**EXECUTE:**
- wall-clock timestamp
- order_id (AI_WINX_ORDYYY, RULE_WINX_ORDYYY)
- Risk check results (tất cả 5 check)
- Fill price (ideal vs actual)
- Slippage / spread
- Position opened / rejected
- Position ID (nếu opened)

**REVEAL NEXT DATA:**
- wall-clock timestamp
- Bar index
- Positions closed (reason, PnL)
- Account state (balance, equity)

---

## 6. So Sánh với Rule-based Baseline

### 6.1 Cách chạy song song

**Cùng 1 bộ dữ liệu point-in-time:**
1. Hệ thống chuẩn bị dữ liệu tại timestamp T
2. Gửi cho **cả 2:** AI + Rule Engine (chính xác cùng dữ liệu)
3. Ghi lại **cả 2** quyết định: AI decision, Rule decision, entry price, SL, TP
4. Mô phỏng execute **cả 2** quyết định (nếu cả 2 quyết định vào lệnh)
5. Ghi lại **cả 2** kết quả: fill price, PnL, exit reason

### 6.2 Bảng so sánh tóm gọn (mỗi bar / hàng tuần / hàng tháng)

```
Timestamp | AI Decision | Rule Decision | Agreement? | AI Entry | Rule Entry | AI PnL | Rule PnL | Notes
---------|---|---|---|---|---|---|---|---
T+45 | BUY | TRADE | ✓ | 1.0950 | 1.0950 | +470 | +420 | Cùng entry, AI tốt hơn
T+46 | HOLD | WAIT | ✓ | - | - | - | - | Cùng không vào
T+47 | BUY | REJECT | ✗ | 1.0960 | - | -150 | N/A | AI vào lệnh thua, Rule đúng reject
T+48 | HOLD | TRADE | ✗ | - | 1.0970 | - | +380 | Rule phát hiện setup, AI miss
```

### 6.3 KPI so sánh (từ `backtests/KPI_STANDARD.md`)

Tính các KPI sau cho **cả AI và Rule**, rồi so sánh:

| KPI | AI | Rule | Diff | Ghi chú |
|---|---|---|---|---|
| **Total trades** | 120 | 132 | -12 (AI ít vào hơn) | AI conservative? |
| **Win Rate %** | 52.5% | 51.2% | +1.3pp | AI tốt hơn chút ít |
| **Expectancy (pips/trade)** | 1.85 | 1.78 | +0.07 | AI tốt hơn 4% |
| **Gross Profit** | 1500 | 1420 | +80 | AI lợi nhiều hơn |
| **Gross Loss** | 920 | 880 | -40 | AI lỗ ít hơn |
| **Profit Factor** | 1.63 | 1.61 | +0.02 | Gần như nhau |
| **Max Drawdown %** | 12.5% | 12.8% | +0.3pp | AI rủi ro ít hơn |
| **Sharpe Ratio** | 1.45 | 1.38 | +0.07 | AI ổn định hơn |
| **Agreement Rate** | N/A | 65% | N/A | AI + Rule cùng quyết định 65% lần |
| **False Alarm Rate** | N/A | 8.3% | N/A | AI vào lệnh mà Rule reject: 8.3% tổng AI trades |
| **Missed Opportunity Rate** | N/A | 7.6% | N/A | Rule phát hiện setup mà AI miss: 7.6% tổng Rule trades |

### 6.4 Kết luận so sánh

```
Kết luận: AI có giá trị hơn Rule Engine không?

Tiêu chí:
✓ Expectancy > Rule: AI tốt hơn
✓ Win Rate > Rule: AI tốt hơn
✓ Max DD < Rule: AI an toàn hơn
? Profit Factor gần nhau: không có lợi thế rõ
? Agreement < 80%: Cảnh báo AI decision khác rule quá nhiều

Quyết định:
- Nếu AI tốt hơn trên nhiều tiêu chí: ACCEPT → tiếp tục AI Scoring ở Giai đoạn 5
- Nếu AI tệ hơn hoặc gần như nhau: Có thể REJECT → Rule Engine đủ, không cần AI phức tạp
- Nếu AI miss quá nhiều cơ hội: Cần review prompt / AI reasoning
```

---

## 7. Ranh Giới & Vai Trò AI

### 7.1 Điều AI được phép

✅ Phân tích cấu trúc thị trường (trend, breakout, pullback)  
✅ Xác nhận setup hợp lệ (theo `strategies/TF_00x.md`)  
✅ Phản biện setup (tìm điểm yếu, xem có false break không)  
✅ Cảnh báo rủi ro (ví dụ "drawdown cao, cẩn thận")  
✅ Tính toán entry/SL/TP (dựa trên quy tắc đã định)  

### 7.2 Điều AI KHÔNG được phép

❌ Tự quyết định % rủi ro → từ `risk/POSITION_SIZING.md`, cứng  
❌ Nới lỏng giới hạn thua lỗ → Kill Switch từ `risk/KILL_SWITCH_RULES.md`, cứng  
❌ Bỏ qua Risk Gateway → Tất cả lệnh phải qua 5 checks  
❌ Dự đoán "chắc chắn" sắp lên/xuống → Chỉ dựa dữ liệu hiện tại  
❌ Thay đổi Strategy/Prompt ngầm → Phải rõ ràng, log đầy đủ  

### 7.3 Cách áp dụng ranh giới

**AI decision = Đề xuất, không phải Lệnh cuối:**
1. AI đề xuất: "BUY tại 1.0950, SL 1.0910, Target 1.1000"
2. Risk Gateway kiểm tra: Rủi ro OK không?
3. Nếu OK → Execute Virtual Order
4. Nếu FAIL → Reject, ghi log (AI không tự override)

**Nếu AI vi phạm Rule (ví dụ R/R < 1.0):**
- Risk Gateway block (lệnh không được fill)
- Ghi log: "Risk check failed: R/R < 1.0"
- AI KHÔNG được "argue" hoặc "override"

---

## 8. Liên Hệ Với Các File Khác

**Thiết kế framework này:**
- `backtests/BACKTEST_STANDARD.md` — Chuẩn backtest (chống self-deception)
- `backtests/WALK_FORWARD_GUIDE.md` — Walk-Forward Analysis (phòng overfitting)
- `backtests/KPI_STANDARD.md` — Định nghĩa KPI (so sánh AI vs Rule)

**Input: Các prompt AI sẽ test:**
- `prompts/MARKET_ANALYST.md` — Phân tích setup
- `prompts/TRADE_CRITIC.md` — Phản biện setup
- `prompts/POST_TRADE_REVIEWER.md` — Phân tích lệnh đã đóng

**Baseline: Rule Engine để so sánh:**
- `RULE_ENGINE.md` — 10 rule, Decision Flow, Scoring System
- `strategies/TF_001_BREAKOUT_PULLBACK.md` — Strategy 1 (rule-based)
- `strategies/TF_002_TRENDLINE_REACTION.md` — Strategy 2 (rule-based)

**Execution & Risk:**
- `execution/AUDIT_LOG.md` — Format ghi log append-only
- `execution/RISK_GATEWAY.md` — 5 risk checks (bắt buộc)
- `paper_trading/PAPER_TRADING_ENGINE.md` — Virtual Order, Position, Account simulation
- `risk/RISK_POLICY.md` — Giới hạn rủi ro (% per trade, portfolio %, drawdown max)
- `risk/KILL_SWITCH_RULES.md` — Quy tắc dừng khẩn cấp

**Quyết định kiến trúc:**
- `DECISIONS.md` — Nguyên tắc (Reaction, Trend Following, Risk Priority, AI không tự quyết định rủi ro)
- `ROADMAP.md` — Giai đoạn 3 (Backtest) + Giai đoạn 5 (AI Scoring) — framework này là hạ tầng chung

---

## 9. Tham Số Chưa Chốt

| Tham số | Ảnh hưởng | Đề xuất | Tình trạng | Cần Project Owner |
|---|---|---|---|---|
| **LLM model** | Chất lượng AI decision | Claude 3.5 Sonnet? GPT-4 Turbo? | Chưa chốt | ✅ Cần confirm |
| **Prompts version** | Chất lượng AI reasoning | Bắt đầu từ MARKET_ANALYST_V1 | Chưa chốt | ✅ Cần draft + iterate |
| **Symbol ẩn danh — cơ chế** | Chống look-ahead bias | Mapping table (thật → mã hoá UUID) hoặc placeholder alphabet (ASSET_A, ASSET_B) | Chưa chốt | ✅ Cần chọn |
| **Ngày ẩn danh — offset** | Chống look-ahead bias | T-offset (T+0 = ngày cuối test, T-N = ngày cũ hơn) | Chưa chốt | ✅ Cần confirm |
| **Chỉ báo gửi cho AI** | Độ phức tạp input | OHLCV + RSI + EMA + Volume SMA + Swing levels? Hay chỉ OHLCV thô? | Chưa chốt | ✅ Cần quyết định |
| **Slippage/Spread** | Độ thực tế của kết quả | Slippage ±2 pips, Spread 2 pips (ví dụ EUR/USD) | Đề xuất | ✅ Cần confirm theo pair |
| **Walk-Forward window** | Số lượng OOS test | In-sample 2 năm, Out-of-sample 1 năm (từ WALK_FORWARD_GUIDE.md) | Đề xuất | ✅ Cần confirm |
| **Dữ liệu test** | Độ phù hợp | Ít nhất 1-2 pair, 1-2 timeframe, 6+ năm dữ liệu (nếu xài WFA) | Chưa chốt | ✅ Cần lấy data |
| **Số lệnh tối thiểu** | Ý nghĩa thống kê | Ít nhất 100 lệnh (từ BACKTEST_STANDARD.md) | Đề xuất | ✅ Cần confirm |
| **Chi phí LLM** | Budget & feasibility | Nếu test 100+ lệnh × 2 prompts (AI + theo dõi) × bao nhiêu tokens? | Chưa tính | ✅ Cần estimate |
| **Giải thích quyết định AI** | Logging detail | Toàn bộ reasoning text? Hay summary? | Đề xuất: toàn bộ | ✅ Cần confirm |

---

## 10. Trạng Thái và Ghi Chú

### 10.1 Trạng thái hiện tại

✅ **Thiết kế xong:** Framework kiến trúc hoàn chỉnh, các bước rõ ràng, logging spec, so sánh KPI  
⬜ **Chưa triển khai:** Không viết code, không chạy backtest thực tế, không gọi LLM  

### 10.2 Các điểm CHƯA CHỐT cần Project Owner xác nhận

1. **LLM model cụ thể**: Claude 3.5 Sonnet? GPT-4? Có budget để gọi API bao nhiêu lần?
2. **Phiên bản prompt**: Bắt đầu từ MARKET_ANALYST.md revision nào? Có cần custom thêm?
3. **Cơ chế ẩn danh symbol/ngày**: Dùng placeholder (ASSET_A, ASSET_B) hay mapping UUID?
4. **Chỉ báo gửi cho AI**: Chỉ OHLCV thô hay kèm RSI/EMA/Volume?
5. **Dữ liệu test**: Pair nào? Timeframe nào? Khoảng thời gian bao lâu? (Ảnh hưởng tới chi phí & thời gian)
6. **Tiêu chí "AI tốt hơn"**: Expectancy cao 5% là tốt hơn? Hay cần cao 10%+?
7. **Scheduling**: Khi nào chạy backtest? Liên tục iterate prompt hay run 1 lần?

### 10.3 Tiếp theo sau thiết kế

**Tuần 1-2 (Preparation):**
1. Project Owner confirm tất cả tham số ở mục 10.2
2. Lấy dữ liệu lịch sử (pair, timeframe, khoảng)
3. Draft prompt AI cụ thể

**Tuần 3-6 (Implementation & Run):**
4. Code framework point-in-time backtest (Python hoặc JS)
5. Integrate Virtual Order + Risk Gateway + Audit Log
6. Chạy backtest 1 lần với AI + Rule
7. Tính KPI, so sánh, viết báo cáo

**Tuần 7-8 (Review & Decision):**
8. Project Owner review kết quả
9. Quyết định: AI có giá trị không? Tiếp tục Giai đoạn 5 (AI Scoring) không?

### 10.4 Rủi ro thiết kế

- **Look-ahead bias vẫn có thể xảy ra nếu:** Dữ liệu OHLCV "bị rò rỉ" future info (ví dụ future high dùng làm entry condition), hoặc chỉ báo bị tính sai
  - **Cách giảm rủi ro:** Kiểm tra kỹ formula chỉ báo, unit test, compare backtest vs paper trade
  
- **AI có thể "gian lận" qua prompt:** Nếu prompt chứa thông tin ẩn tương lai (ví dụ "ngày này là Fed announcement, AI biết trước")
  - **Cách giảm rủi ro:** Review prompt kỹ, test prompt trên dữ liệu dummy, xem reasoning của AI
  
- **Chi phí LLM cao:** Nếu test 1000+ lệnh × bao nhiêu tokens/lệnh → hóa đơn API lớn
  - **Cách giảm rủi ro:** Estimate chi phí trước, start nhỏ (1 pair, 1 timeframe, 6 tháng), scale lên nếu OK

---

## Phụ lục A: Ví dụ Mock Data Point-in-Time

```json
{
  "backtest_window": 1,
  "timestamp_relative": "T+45",
  "timestamp_wall_clock": "2025-08-01T14:32:45Z",
  "symbol_ident": "ASSET_A",  // Thực là EURUSD nhưng ẩn danh
  "ohlcv_data": [
    {
      "bar": -5,
      "open": 1.0920, "high": 1.0935, "low": 1.0915, "close": 1.0930, "volume": 98000
    },
    {
      "bar": -4,
      "open": 1.0930, "high": 1.0950, "low": 1.0925, "close": 1.0948, "volume": 112000
    },
    {
      "bar": -3,
      "open": 1.0948, "high": 1.0960, "low": 1.0940, "close": 1.0955, "volume": 105000
    },
    {
      "bar": -2,
      "open": 1.0955, "high": 1.0970, "low": 1.0950, "close": 1.0965, "volume": 118000
    },
    {
      "bar": -1,
      "open": 1.0965, "high": 1.0975, "low": 1.0958, "close": 1.0970, "volume": 125000
    },
    {
      "bar": 0,  // Current (ĐÃ ĐÓNG)
      "open": 1.0970, "high": 1.0985, "low": 1.0960, "close": 1.0980, "volume": 130000
    }
  ],
  "indicators": {
    "rsi_14": 68.5,
    "ema_50": 1.0940,
    "ema_200": 1.0880,
    "volume_sma_20": 110000,
    "swing_high_2bar": 1.0985,
    "swing_low_2bar": 1.0960,
    "trend": "UP"
  },
  "notice": "Tất cả dữ liệu ở trên là quá khứ tính đến bar=0. Không có thông tin tương lai. Symbol ẩn danh, ngày ẩn danh."
}
```

---

## Phụ lục B: Ví dụ AI Decision Log

```json
{
  "event_type": "ai_decision_response",
  "timestamp": "2025-08-01T14:32:51.789Z",
  "request_id": "AI_WIN1_REQ001",
  "model": "claude-3-5-sonnet-20241022",
  "prompt_version": "MARKET_ANALYST_V1",
  
  "input_tokens": 2145,
  "output_tokens": 456,
  "latency_ms": 5333,
  
  "ai_decision": {
    "action": "BUY",
    "confidence": 0.78,
    "reasoning": "Xu hướng tăng rõ ràng (swing high 1.0985 > swing high trước, close 1.0980 > 1.0970). Volume tăng (130k > avg 110k). EMA bias UP (close trên EMA 50). Cấu trúc pullback không rõ ràng nhưng breakout có xác nhận. Risk/Reward không tính trong phân tích này (để Risk Gateway xử lý). Kết luận: Setup hợp lệ để vào BUY.",
    "entry_price": 1.0980,
    "stop_loss": 1.0910,
    "target_price": 1.1050,
    "risk_pct": 2.0,
    "r_multiple": 2.3
  },
  
  "warnings": [
    "Pullback pattern không rõ, có thể entry sẽ high risk.",
    "Volume tăng nhưng không quá cao, có thể breakout yếu."
  ],
  
  "full_response": "... (raw text từ LLM) ..."
}
```

---

