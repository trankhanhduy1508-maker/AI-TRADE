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

## Next Task

1. Thu thập dữ liệu giá lịch sử cho ít nhất 1 cặp/thị trường + 1 timeframe cụ thể
   để bắt đầu backtest TF_001.
2. Chạy backtest thật theo `backtests/BACKTEST_STANDARD.md`, điền kết quả vào
   `backtests/RESULTS_TEMPLATE.md`, ghi nhận vào `research/EXPERIMENT_LOG.md`.
3. Sau khi có kết quả backtest thật đầu tiên, đánh giá lại TF_001 trước khi làm
   tiếp TF_002.
