# Current Status — AI-TRADE

## Documentation Foundation

✅ README.md

✅ AGENTS.md

✅ PROJECT_CONTEXT.md

✅ DECISIONS.md

✅ CURRENT_STATUS.md (file này)

---

## Knowledge

✅ TREND_FOLLOWING.md

✅ MARKET_WIZARDS_LESSONS.md

✅ PRICE_ACTION_AND_MARKET_STRUCTURE.md

✅ RSI_RESEARCH.md

✅ VOLUME_RESEARCH.md

---

## Strategies

✅ STRATEGY_TEMPLATE.md

✅ TF_001_BREAKOUT_PULLBACK.md (giả thuyết, chưa backtest)

✅ TF_002_TRENDLINE_REACTION.md (giả thuyết, chưa backtest)

---

## Risk

✅ RISK_POLICY.md

✅ POSITION_SIZING.md

✅ KILL_SWITCH_RULES.md

---

## Research

✅ HYPOTHESES.md

✅ EXPERIMENT_LOG.md (rỗng, chưa có thử nghiệm nào chạy thật)

✅ FAILURE_CASES.md (rỗng, chưa có ca thất bại nào ghi nhận)

---

## Backtests

✅ BACKTEST_STANDARD.md

✅ RESULTS_TEMPLATE.md (chưa có kết quả backtest thật nào điền vào)

---

## Prompts

✅ MARKET_ANALYST.md

✅ TRADE_CRITIC.md

✅ POST_TRADE_REVIEWER.md

---

## Chưa làm (theo đúng giới hạn PROJECT_CONTEXT.md)

⬜ Kết nối dữ liệu giá thật (lịch sử hoặc real-time).

⬜ Chạy backtest thật cho TF_001/TF_002 — hiện 2 chiến lược mới ở mức giả thuyết.

⬜ Code trong `src/` — thư mục hiện rỗng, chưa có dòng code nào.

⬜ Kết nối tài khoản giao dịch thật — KHÔNG làm ở giai đoạn này.

⬜ Bot đặt lệnh thật — KHÔNG làm ở giai đoạn này.

⬜ Huấn luyện model — KHÔNG làm ở giai đoạn này.

---

## Research Phase 01

✅ RESEARCH_SUMMARY.md — Tóm tắt 12 trường phái giao dịch

✅ TRADING_SCHOOL_COMPARISON.md — Bảng so sánh chi tiết theo 10 tiêu chí

✅ BEST_PRACTICES.md — 6 lĩnh vực best practices, 17 nguyên tắc vàng

✅ COMMON_FAILURES.md — 9 nhóm lỗi phổ biến, phòng tránh & bảng tóm tắt

✅ AI_DESIGN_PRINCIPLES.md — Nguyên tắc thiết kế AI, kiến trúc đề xuất (Trend Following + Market Structure + Volume)

✅ ROADMAP.md (gốc repo) — Lộ trình 7 giai đoạn từ Knowledge Base tới Live Trading

✅ reports/RESEARCH_PHASE_01.md — Báo cáo hoàn tất Phase 01

**Trạng thái:** ✅ Phase 01 Complete — Sẵn sàng cho Phase 02 (Rule Engine)

---

## Rule Engine Phase (Phase 02)

✅ RULE_ENGINE.md — Kiến trúc tổng thể, Decision Flow (10 bước), Scoring System (0-100)

✅ rule_engine/RULE_001_TREND.md — Xác định xu hướng HH/HL hoặc LH/LL

✅ rule_engine/RULE_002_MARKET_STRUCTURE.md — Cấu trúc thị trường hợp lệ

✅ rule_engine/RULE_003_BREAKOUT.md — Phá vỡ hợp lệ (body ratio, close vượt hẳn)

✅ rule_engine/RULE_004_PULLBACK.md — Hồi giá hợp lệ sau breakout

✅ rule_engine/RULE_005_VOLUME.md — Volume xác nhận (SMA20 comparison)

✅ rule_engine/RULE_006_RSI.md — RSI bias (phân kỳ, quá mua/bán)

✅ rule_engine/RULE_007_EMA.md — EMA bias (filter xu hướng dài hạn)

✅ rule_engine/RULE_008_RISK.md — Risk/Reward và Stop Loss validation

✅ rule_engine/RULE_009_LIQUIDITY.md — Thanh khoản thị trường

✅ rule_engine/RULE_010_EXIT.md — Quy tắc thoát lệnh (SL, trailing, exit signal)

✅ rule_engine/RULE_CONFLICTS.md — Xung đột giữa rule, thứ bậc ưu tiên

✅ rule_engine/RULE_ENGINE_CHECKLIST.md — QA Checklist cho từng rule

✅ reports/RULE_ENGINE_PHASE_REPORT.md — Audit Rule Engine, đề xuất cải tiến

**Trạng thái:** ✅ Phase 02 Complete (Thiết kế) — Sẵn sàng cho Phase 03 (Coding + Backtest)

---

## Point-in-Time AI Backtesting

✅ `backtests/POINT_IN_TIME_AI_BACKTEST.md` — Framework kiểm chứng LLM/AI qua dữ liệu point-in-time, chống look-ahead bias, logging append-only, so sánh với Rule Engine baseline

**Trạng thái:** ✅ Thiết kế xong, chưa triển khai/chạy thật

**Tham số chưa chốt:**
- LLM model cụ thể (Claude 3.5 Sonnet? GPT-4?)
- Phiên bản prompt AI
- Cơ chế ẩn danh symbol/ngày (placeholder ASSET_A/ASSET_B hay UUID?)
- Chỉ báo gửi cho AI (OHLCV thô hay kèm RSI/EMA?)
- Dữ liệu test (pair, timeframe, khoảng thời gian)
- Chi phí LLM (estimate API calls)

---

## Paper Trading Engine

✅ `paper_trading/PAPER_TRADING_ENGINE.md` — Kiến trúc tổng thể

✅ `paper_trading/VIRTUAL_ACCOUNT.md` — Quản lý vốn ảo

✅ `paper_trading/VIRTUAL_ORDER.md` — Mô phỏng execution

✅ `paper_trading/POSITION.md` — Theo dõi lệnh mở

✅ `paper_trading/TRADE_JOURNAL.md` — Ghi lại chi tiết lệnh đóng

✅ `paper_trading/PERIODIC_REVIEW.md` — Daily/Weekly/Monthly review

✅ `paper_trading/PERFORMANCE_DASHBOARD.md` — Tính KPI, hiển thị hiệu suất

**Trạng thái:** ✅ Thiết kế xong, chưa code — Sẵn sàng cho Giai đoạn 4 (Paper Trade)

---

## Execution Engine

✅ `execution/EXECUTION_ENGINE.md` — Kiến trúc tổng thể, 8 thành phần

✅ `execution/SIGNAL_QUEUE.md` — Hàng đợi signal từ Rule Engine

✅ `execution/RISK_GATEWAY.md` — Cổng kiểm tra rủi ro (5 checks)

✅ `execution/ORDER_MANAGER.md` — Tạo và gửi lệnh

✅ `execution/POSITION_MANAGER.md` — Theo dõi position mở

✅ `execution/RETRY_TIMEOUT_POLICY.md` — Quy tắc retry & timeout

✅ `execution/ERROR_HANDLING.md` — Phân loại lỗi, quyết định hành động

✅ `execution/AUDIT_LOG.md` — Ghi log append-only

✅ `execution/BROKER_ADAPTER_INTERFACE.md` — Interface đa broker

**Trạng thái:** ✅ Thiết kế xong, chưa code — Hỗ trợ cả Giai đoạn 4 (Paper) + Giai đoạn 7 (Live)

---

## Rule Engine — Code (Phase 2 Code, MVP)

✅ `src/rule_engine/` — 10 module RULE_001-010 + `scoring.py` (orchestrator Decision Flow + Setup Score) bằng Python thuần (standard library only)

✅ `tests/rule_engine/` — 103 unit test + integration test (không mock RULE_001-005), chạy `python -m pytest tests/rule_engine/ -v` — **103/103 PASS thật**

✅ `src/ARCHITECTURE.md` — mô tả kiến trúc code, luồng dữ liệu `evaluate_setup()`

**Môi trường:** Python 3.14.6 đã cài cục bộ trên máy (trước đó chưa có runtime nào — đã cài để có thể code+test thật).

**Trạng thái:** ✅ Code xong, test pass thật — Rule Engine sẵn sàng dùng cho Data Loader/Backtest Engine tiếp theo. Chưa test với dữ liệu giá thật (chưa có Data Loader).

**Giới hạn đã biết:**
- RULE_009 (Liquidity) chưa có nguồn spread/order-book thật — `evaluate_setup()` nhận `spread_pips`/`depth_ok` làm tham số tùy chọn (mặc định giả định "tạm ổn"), caller cần truyền dữ liệu thật khi có.
- Tham số rủi ro (`rr_min=1.5` và các ngưỡng khác) là giá trị đề xuất, chưa được Project Owner chốt chính thức.

---

## Next Task (Priority)

### Urgent (1-2 tuần):

1. **Project Owner confirm kiến trúc Paper Trading + Execution Engine:**
   - 7 thành phần Paper Trading Engine (Virtual Account, Order, Position, Trade Journal, Review, Dashboard)?
   - 8 thành phần Execution Engine (Signal Queue, Risk Gateway, Order Manager, Position Manager, Retry/Timeout, Error Handling, Audit Log, Broker Adapter)?
   - Broker Adapter Interface cho đa sàn tương lai?

2. **Chốt tham số cụ thể (từ RISK_POLICY.md, EXECUTION_ENGINE.md):**
   - % rủi ro/lệnh (1%? 2%?)
   - % rủi ro danh mục (5%? 10%?)
   - Số lệnh thua liên tiếp trigger kill switch (3? 5?)
   - % drawdown max trigger kill switch (10%? 20%?)
   - Cho phép duplicate position same symbol (True/False)?

3. **Chốt tham số Point-in-Time AI Backtesting:**
   - LLM model cụ thể (Claude 3.5 Sonnet? GPT-4 Turbo?)
   - Phiên bản prompt AI
   - Cơ chế ẩn danh symbol/ngày
   - Chỉ báo gửi cho AI (OHLCV thô? hay kèm chỉ báo?)
   - Dữ liệu test (pair, timeframe, khoảng)
   - Chi phí LLM estimate

### Medium (2-4 tuần):

4. **Chuẩn bị dữ liệu:** Chọn 2-3 cặp tiền, 1-2 timeframe, lấy 1-2 năm dữ liệu lịch sử

### Long-term (4-8 tuần):

5. **Phase 3 (Code + Backtest):** 
   - Viết code Python lập trình Rule Engine (src/rule_engine.py)
   - Unit test từng rule
   - Chạy backtest TF_001 + TF_002 với Rule Engine + Point-in-Time AI Backtesting
