# Roadmap 7 Giai Đoạn — AI-TRADE

Lộ trình phát triển dự án AI-TRADE từ giai đoạn xây dựng nền tảng cho tới khi có khả năng giao dịch tự động trên thị trường thực. Mỗi giai đoạn có mục tiêu rõ ràng, deliverable cụ thể, và điều kiện để chuyển sang giai đoạn tiếp theo.

---

## GIAI ĐOẠN 1: KNOWLEDGE BASE (Hoàn tất)

**Mục tiêu:**
Xây dựng nền tảng kiến thức: các trường phái giao dịch, nguyên tắc, quy tắc, giả thuyết, và nền tảng rủi ro.

**Trạng thái:**
✅ Hoàn tất (hiện tại, Phase 1 research đã làm)

**Deliverables:**
- ✅ `README.md`, `PROJECT_CONTEXT.md`, `AGENTS.md`
- ✅ `knowledge/TREND_FOLLOWING.md`, `MARKET_WIZARDS_LESSONS.md`, `PRICE_ACTION_AND_MARKET_STRUCTURE.md`, `RSI_RESEARCH.md`, `VOLUME_RESEARCH.md`
- ✅ `knowledge/RESEARCH_SUMMARY.md` (12 trường phái)
- ✅ `knowledge/TRADING_SCHOOL_COMPARISON.md` (bảng so sánh)
- ✅ `knowledge/BEST_PRACTICES.md` (nguyên tắc tốt nhất)
- ✅ `knowledge/COMMON_FAILURES.md` (lỗi phổ biến)
- ✅ `knowledge/AI_DESIGN_PRINCIPLES.md` (kiến trúc AI)
- ✅ `risk/RISK_POLICY.md`, `risk/POSITION_SIZING.md`, `risk/KILL_SWITCH_RULES.md`
- ✅ `strategies/STRATEGY_TEMPLATE.md`, `TF_001_BREAKOUT_PULLBACK.md`, `TF_002_TRENDLINE_REACTION.md` (giả thuyết)
- ✅ `research/HYPOTHESES.md` (5 giả thuyết ban đầu)

**Điều kiện chuyển sang Giai đoạn 2:**
- Kiến thức đầy đủ 4 lĩnh vực: Trend Following, Price Action, Risk Management, Trading Wisdom
- Project Owner xác nhận framework "Trend Following + Market Structure + Volume" được chọn
- Có ít nhất 2 strategy template (TF_001, TF_002) được viết cụ thể

---

## GIAI ĐOẠN 2: RULE ENGINE (Bắt đầu)

**Mục tiêu:**
Chuẩn hóa các quy tắc thành code/pseudo-code, chuẩn bị cho việc lập trình thực tế. Không phải code production, mà code để **kiểm chứng logic** và **chuẩn bị backtest**.

**Thời gian ước tính:**
4-6 tuần

**Deliverables:**
- `src/rules/` — thư mục chứa các quy tắc dưới dạng pseudo-code hoặc pseudocode + unit test
  - `trend_detection.py` — xác định HH/HL/LH/LL từ OHLC
  - `breakout_detection.py` — phát hiện breakout hợp lệ (price action + volume)
  - `pullback_validation.py` — kiểm tra pullback hợp lệ
  - `trendline_reaction.py` — xác định trendline và phản ứng
  - `position_sizing.py` — tính khối lượng lệnh từ SL
  - `risk_checker.py` — kiểm tra vi phạm rủi ro
- Đơn vị test cho mỗi module (unit test)
- `src/ARCHITECTURE.md` — mô tả kiến trúc code

**Điều kiện chuyển sang Giai đoạn 3:**
- Tất cả module đều có unit test pass
- Code review được Project Owner xác nhận (logic đúng, không chứa bug rõ ràng)
- Sẵn sàng connect dữ liệu giá thật

---

## GIAI ĐOẠN 3: BACKTEST (4-8 tuần)

**Mục tiêu:**
Chạy backtest trên dữ liệu lịch sử để kiểm chứng từng giả thuyết và strategy. Mục tiêu không phải "thắng 100%" mà là **kiểm chứng xem strategy có logic hợp lý không**.

**Thời gian ước tính:**
4-8 tuần (phụ thuộc độ phức tạp + số lần tối ưu)

**Deliverables:**
- Dữ liệu giá cho ít nhất 3 cặp/asset (ví dụ: EUR/USD, GBP/USD, BTC/USDT)
- Ít nhất 2 timeframe (ví dụ: D1, H4)
- Backtest khoảng thời gian tối thiểu 1-2 năm lịch sử
- `backtests/RESULTS_TF_001_*.md` — kết quả chi tiết cho mỗi pair/timeframe
- `backtests/RESULTS_TF_002_*.md` — tương tự
- `research/EXPERIMENT_LOG.md` — ghi lại mỗi lần backtest chạy
- Cập nhật `strategies/TF_001_BREAKOUT_PULLBACK.md`, `TF_002_TRENDLINE_REACTION.md` với kết quả backtest

**Các giả thuyết cần kiểm chứng (từ `research/HYPOTHESES.md`):**
- H001: Pullback sau breakout cho R:R tốt hơn vào ngay
- H002: Trendline từ điểm thứ 3 có giá trị giao dịch
- H003: RSI làm bộ lọc cải thiện kỳ vọng (nếu áp dụng)
- H004: Volume tăng ở breakout giảm false break
- H005: False break trendline + volume thấp là signal ngược (nếu áp dụng)

**Điều kiện chuyển sang Giai đoạn 4:**
- Ít nhất 1 strategy (TF_001 hoặc TF_002) có backtest result pass (kỳ vọng dương trên ít nhất 1 pair/timeframe)
- Hoặc: cả 2 strategy fail nhưng nguyên nhân rõ ràng (ví dụ: "pullback quá ít trên EUR/USD", "trendline không được tôn trọng trên BTC H4") → điều chỉnh strategy, backtest lại
- Có ít nhất 100+ lệnh backtest để kết quả có ý nghĩa thống kê

**Lưu ý:**
- Không được bịa số liệu — chạy code, lưu lại kết quả
- Mỗi backtest phải ghi rõ: dữ liệu (pair, timeframe, khoảng), tham số (N-bar breakout, ATR multiplier), kết quả (số lệnh, tỷ lệ %, PnL)
- Nếu phát hiện lỗi logic trong code → fix, backtest lại (không fix "số liệu")

---

## GIAI ĐOẠN 4: PAPER TRADE (4-12 tuần)

**Mục tiêu:**
Giao dịch trên **dữ liệu thực tế live** nhưng **không có tiền thật** (paper trade / simulator). Mục tiêu kiểm chứng chiến lược hoạt động trên dữ liệu chưa "nhìn thấy" và xác nhận không có vấn đề kỹ thuật.

**Thời gian ước tính:**
4-12 tuần (phụ thuộc tần suất signal, thị trường volatility)

**Deliverables:**
- Kết nối dữ liệu live (ví dụ: API từ sàn giao dịch)
- Paper trading engine (code mô phỏng giao dịch mà không có tiền thật)
- Đầy đủ logging: mỗi signal, mỗi lệnh, mỗi exit được ghi lại
- `research/EXPERIMENT_LOG.md` được cập nhật liên tục
- Báo cáo paper trading hàng tuần: số lệnh, PnL, drawdown

**Chiến lược được test:**
- TF_001 + TF_002 kết hợp (nếu cả 2 pass backtest)
- Hoặc chỉ strategy nào pass backtest (nếu chỉ 1 pass)

**Điều kiện chuyển sang Giai đoạn 5:**
- Paper trade chạy liên tục ít nhất 2-4 tuần
- Kết quả paper trade **không khác quá lớn** so với backtest (cho phép sai margin 10-20% do slippage, spread)
- Không phát hiện bug kỹ thuật lớn (missed signal, calculation error, crash)
- Project Owner xác nhận OK để vào giai đoạn AI Scoring

**Lưu ý:**
- Nếu phát hiện lỗi trong chiến lược (không phải code) → quay về Giai đoạn 3 để backtest lại
- Nếu paper trading kém hơn backtest quá nhiều (< 50% PnL backtest) → điều tra nguyên nhân, fix, backtest lại

---

## GIAI ĐOẠN 5: AI SCORING (4-8 tuần)

**Mục tiêu:**
Tích hợp LLM/AI để **phân tích, xác nhận, phản biện** các signal trước khi ra tín hiệu giao dịch. AI không tự quyết định rủi ro, chỉ cung cấp phân tích và cảnh báo bổ sung.

**Thời gian ước tính:**
4-8 tuần

**Deliverables:**
- `src/ai/` — thư mục chứa các prompt + logic AI
  - `market_analyst.py` — AI phân tích setup, xác nhận có vẻ hợp lệ không
  - `trade_critic.py` — AI phản biện setup, tìm điểm yếu
  - `risk_reviewer.py` — AI kiểm tra rủi ro (warning nếu vi phạm)
  - `post_trade_analyzer.py` — AI phân tích lệnh đóng để rút kinh nghiệm
- `prompts/` được cập nhật với các prompt chính thức cho AI (prompt chuẩn)
- Test case với các scenario (setup hợp lệ, setup sai, market shock...)
- Báo cáo hiệu suất AI: confirmation rate, false alarm rate, value added

**AI sẽ:**
- ✅ Phân tích "tại sao setup này hợp lệ?" (ghi lại reasoning)
- ✅ Cảnh báo "setup này thiếu điều kiện X, cẩn thận"
- ✅ Kiểm tra rủi ro "portfolio risk > limit, không thể vào lệnh"
- ✅ Tổng hợp ngày đã giao dịch

**AI KHÔNG:**
- ❌ Tự quyết định mức rủi ro (luật cứng từ `risk/RISK_POLICY.md`)
- ❌ Tự nới lỏng giới hạn thua lỗ
- ❌ Bỏ qua kill switch
- ❌ Dự đoán thị trường sắp đảo chiều

**Điều kiện chuyển sang Giai đoạn 6:**
- AI scoring chạy 2-4 tuần, kiểm chứng AI không thêm false alarm quá
- AI confirmation rate > 80% (setup AI confirm lại là setup thật)
- Project Owner xác nhận AI analysis hữu ích

---

## GIAI ĐOẠN 6: MACHINE LEARNING (6-16 tuần)

**Mục tiêu:**
Áp dụng ML để **tối ưu hóa tham số** (N-bar breakout, ATR multiplier, EMA period...) hoặc **nhận biết pattern** (CNN cho "bar quality"). Không phải thay thế rule-based system, mà bổ sung.

**Thời gian ước tính:**
6-16 tuần (phụ thuộc độ phức tạp model)

**Các ứng dụng ML có thể:**
1. **Hyperparameter optimization (RL):**
   - Input: quy tắc strategy + dữ liệu giá
   - Agent: tự động tìm N-bar tối ưu, ATR multiplier...
   - Reward: PnL, Sharpe ratio
   - Output: tối ưu tham số mà không overfitting

2. **Pattern recognition (CNN/LSTM):**
   - Input: ảnh chart (nến, trendline, swing)
   - Model: CNN phân loại "bull bar strong" vs "bull bar weak", "quality breakout" vs "false break"
   - Output: score 0-1 cho mỗi setup
   - Áp dụng: thêm vào xác nhận AI ở Giai đoạn 5

3. **Regime detection (LSTM/HMM):**
   - Input: dữ liệu giá + indicator
   - Model: phát hiện "thị trường trend" vs "thị trường range" vs "high volatility"
   - Output: filter strategy thích hợp cho từng regime

**Deliverables:**
- `src/ml/` — thư mục chứa model training + inference
  - `hyperparameter_optimizer.py` — RL tối ưu tham số
  - `bar_quality_classifier.py` — CNN phân loại nến
  - `regime_detector.py` — LSTM phát hiện regime (nếu áp dụng)
- `ml_models/` — thư mục lưu trained model + checkpoint
- Backtest lại với optimal parameters tìm được
- So sánh: backtest với rule-only vs backtest với ML bổ sung

**Điều kiện chuyển sang Giai đoạn 7:**
- ML optimization pass: hyperparameter tối ưu không overfitting (out-of-sample test)
- Hoặc: CNN classifier > 70% accuracy trên test set
- Paper trade ML version 1-2 tuần để kiểm chứng
- Project Owner xác nhận ready cho live trading

---

## GIAI ĐOẠN 7: LIVE TRADING (Phụ thuộc quyết định Project Owner)

**Mục tiêu:**
Giao dịch trên **tài khoản thật** với **tiền thật**. Điều này chỉ được phép khi tất cả 6 giai đoạn trước đã pass và Project Owner rõ ràng xác nhận.

**Thời gian ước tính:**
Không xác định (phụ thuộc Project Owner)

**Deliverables:**
- Kết nối API sàn giao dịch (real account)
- Kill switch thủ công + tự động (bắt buộc)
- Real-time monitoring + alerts
- Daily PnL report
- Tham số trading bắt đầu nhỏ (tối thiểu position size)

**Điều kiện bắt đầu:**
- ✅ Giai đoạn 1-6 hoàn tất, kết quả đạt kỳ vọng
- ✅ Project Owner xác nhận rõ ràng (không "ngầm hiểu")
- ✅ Tài khoản đã chuẩn bị (vốn đủ, sàn đã chọn, API test OK)
- ✅ Kill switch cơ chế được test (thủ công và tự động)
- ✅ Monitoring system chạy 24/7

**Điều kiện tạm dừng:**
- Drawdown vượt ngưỡng đã định (từ `risk/RISK_POLICY.md`)
- Thua N lệnh liên tiếp (từ `risk/KILL_SWITCH_RULES.md`)
- Phát hiện bug / anomaly trong code
- Bất kỳ lý do nào do Project Owner quyết định

**Điều kiện kết thúc:**
- Project Owner ra lệnh dừng
- Hoặc: đạt mục tiêu lợi nhuận/cuộc sống của project

---

## BẢNG TÓMS TẮT ROADMAP

| Giai đoạn | Mục tiêu | Thời gian | Deliverables | Pass Condition |
|---|---|---|---|---|
| 1 | Knowledge Base | ✅ Hoàn tất | 11 file tài liệu | Kiến thức đầy đủ 4 lĩnh vực |
| 2 | Rule Engine | 4-6w | Code pseudo + unit test | Module test pass |
| 3 | Backtest | 4-8w | Backtest result 100+ lệnh | Strategy pass ≥1 pair/TF |
| 4 | Paper Trade | 4-12w | Live paper trading 2-4w | PnL ±10-20% so với backtest |
| 5 | AI Scoring | 4-8w | AI phân tích + confirm | AI confirm rate > 80% |
| 6 | Machine Learning | 6-16w | ML optimization + training | Out-of-sample test pass |
| 7 | Live Trading | ∞ | Real account + kill switch | Project Owner confirm + tài khoản ready |

---

## THÍCH ỨNG ROADMAP

Roadmap này là **blueprint**, có thể điều chỉnh:

**Nếu giai đoạn N fail:**
- Quay lại giai đoạn N-1, xem xét lại assumptions
- Fix strategy / code / hypothesis
- Backtest lại

**Nếu muốn bỏ qua giai đoạn nào:**
- Ví dụ: bỏ qua giai đoạn 6 (ML), đi thẳng giai đoạn 7 (rule-only live trading)
- Được phép, nhưng cần xác nhận từ Project Owner

**Nếu muốn thêm giai đoạn:**
- Ví dụ: giai đoạn 3.5 "Sensitivity Analysis" (kiểm tra strategy với drawdown extreme)
- Được phép, phải xác định rõ mục tiêu + pass condition

---

## GHI CHÚ QUAN TRỌNG

1. **Không skip**, không "chuyên" tắt một giai đoạn chỉ vì muốn nhanh
2. **Dữ liệu thật**, không bịa — mỗi kết quả phải có code/log chứng minh
3. **Project Owner là người duyệt**, không phải AI tự quyết định chuyển giai đoạn
4. **Kill switch bắt buộc từ giai đoạn 7**, nên dự phòng từ giai đoạn 2-3
5. **Kỷ luật quan trọng hơn tỷ lệ thắng** — một hệ thống tuân thủ tuyệt đối 40% win có giá trị hơn 60% win nhưng cảm tính

