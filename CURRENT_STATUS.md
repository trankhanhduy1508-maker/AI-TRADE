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

## Data Loader — Code (MVP Task 2)

✅ `src/data_loader/` — `csv_loader.py` (đọc CSV → `list[Bar]`, dùng chung `Bar` với Rule Engine), `validator.py` (Bước 2 Data Validation theo BACKTEST_ENGINE.md), `cleaner.py` (Bước 3 Data Cleaning: sort/dedupe/outlier detection), `pipeline.py` (ghép luồng đầy đủ)

✅ `tests/data_loader/` — 52 test + fixture CSV nhỏ (dữ liệu giả lập để test code, không phải dữ liệu thị trường thật) — **52/52 PASS thật**, tổng cộng **155/155 test toàn repo PASS**

**Trạng thái:** ✅ Code xong, test pass thật. Vẫn CHƯA có nguồn dữ liệu giá lịch sử thật (API/CSV thật từ sàn) — đây là điều kiện cần cho MVP Task 3 (Backtest Engine) chạy backtest thật, KHÔNG phải blocker của Data Loader (Data Loader chỉ là code đọc/làm sạch dữ liệu, hoạt động với bất kỳ CSV đúng định dạng nào).

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


---

## 2026-10-02 — Render minimal policy + Android MT5 recovery

- Render governance đã chốt: Render làm ít việc nhất có thể; không dùng filesystem Render làm file/state storage bền vững. Xem `docs/CWS_RENDER_MINIMAL_USAGE_POLICY_2026-10-02.md`.
- Render Free AutoTrade thin proxy đã LIVE và stateless; Supabase vẫn là source of truth.
- MT5 session backend REAL DEMO E2E: PASS (connect -> account -> disconnect), order_send=false, orders_sent=0.
- Android MT5 fix source HEAD evidence: `a35999c8c62e6bc2632f301aa755bec1f4182845`.
- Android source QA: PASS.
- Android device smoke: PASS.
- Android DEMO APK build: PASS.
- APK SHA-256: `ff20a195d4acb3ca809d1075798727105aea098441c87550d2f440e71a979601`.
- Founder physical Android + real credential E2E trên APK mới: NOT_YET_PASS.
- AutoTrade DEMO order execution: DISABLED / NOT_YET_PASS.
- Live money: LOCKED.
- VNext không xây lại engine; tiếp tục từ `ai-trade-mt5-session` + `ai-trade-tick`. Xem `research/CWS_AUTOTRADE_ANDROID_MT5_VNEXT_2026-10-02.md`.

- Supabase MT5 session v6 hiện trả blocker AutoTrade cụ thể cho Android và xác nhận `render_required=false`.


---

## 2026-10-02 — MT5 Android exact-credential diagnosis + clipboard fix

- DEMO credential đã được test trực tiếp trên PC qua pinned pymt5: 4/4 handshake variants LOGIN_CODE=0.
- Cùng credential qua full CWS backend: connect/account/account/disconnect đều PASS; DEMO + TRADING_ALLOWED; order_send=false; orders_sent=0.
- Root cause còn lại của lần Android fail: manual-entry mismatch dù độ dài login/password đúng; không bắt Founder gõ lại.
- Android HEAD `f9934031564079836bdaa88f0b580fb3638c310f` thêm `DÁN TỪ MT5`, xử lý clipboard in-memory, không persist credential.
- APK v0.5.0-demo.
- GitHub build run `36992239724`: PASS.
- Source-only QA run `36992239765`: PASS.
- Device smoke run `36992239775`: PASS.
- Protocol probe run `36992244610`: PASS.
- APK SHA-256: `67c7fd155d0d3cf03a2276cddda4194e7fa6f0085c88c09c9c17add5a5539920`.
- Physical Android clipboard + real DEMO connect on v0.5.0-demo: NOT_YET_PASS.
- Live money remains LOCKED; order execution remains fail-closed.
- Chi tiết: `research/CWS_AUTOTRADE_MT5_ANDROID_CLIPBOARD_FIX_2026-10-02.md`.


---

## 2026-10-02 — MT5 direct Android recovery

- Root cause narrowed: same Founder-authorized DEMO credential returns login code 0 on PC direct protocol in 5 independent variants, while Supabase cloud path returned broker code 3 after 3 retries.
- Stop asking Founder to repeatedly retype credential for cloud-handshake diagnosis.
- Android direct login implemented: APK -> MetaQuotes WebTerminal protocol directly; password is memory-only and is not sent to Supabase in the new login path.
- Direct Android HEAD: `949d9bae07cfbb0b3b03e4eb1a4ec0933c18b2fc`.
- Source QA: PASS, run `36993594745`.
- DEMO APK build: PASS, run `36993594339`.
- Device smoke: PASS, run `36993594344`.
- Protocol probe: PASS, run `36993597889`.
- APK SHA-256: `ca9d63a41ed1ef3333ca27f1b637440b52e1415c8fa5d5220137dea708549e07`.
- Physical Android direct broker login on v0.6.0-demo-direct: NOT_YET_PASS.
- AutoTrade: OFF; live money: LOCKED; orders_sent remains 0.
- Detail: `research/CWS_AUTOTRADE_MT5_DIRECT_ANDROID_RECOVERY_2026-10-02.md`.


---

## 2026-10-02 — MT5 login root cause + pymt5 fallback

- Founder DEMO credential tested directly on PC with pinned pymt5: 4/4 login handshake variants PASS (LOGIN_CODE=0).
- Android/Supabase raw verifier evidence: 3 attempts, broker_login_code=3, input lengths intact.
- Root issue narrowed to raw Deno/npm-ws verifier path, not credential entry.
- New Free Render service `cws-mt5-verify-free`: stateless, no storage, no DB, no polling, auto-deploy OFF.
- Vault -> Render pymt5 -> MetaQuotes E2E: PASS / DEMO_VERIFIED.
- `ai-trade-mt5-demo-validate` runtime v6: raw verifier first, Render pymt5 fallback only after direct login rejection.
- Existing REAL_DEMO_SESSION_E2E regression: PASS.
- Live money: LOCKED.
- AutoTrade orders: still fail-closed / orders_sent=0.
- Full evidence: `research/CWS_AUTOTRADE_MT5_LOGIN_PYMT5_FALLBACK_CHECKPOINT_2026-10-02.md`.

---

## 2026-10-02 — Deterministic engine + DEMO handoff

- Founder chốt runtime trading không dùng LLM làm trading brain; AI chỉ nghiên cứu/backtest/audit/cải tiến code.
- Tiếp tục reuse TF-013A deterministic engine; không xây brain mới.
- Supabase cron forward-shadow/reconcile/evaluate/training-arena đang ACTIVE; run 2026-10-02 đều succeeded.
- Training arena snapshot: 14/14 paper positions open, 9 floating-R dương, 5 âm, aggregate floating R xấp xỉ +0.475652R; đây là paper evidence, không phải broker fills.
- True-forward lane vẫn COLLECTING: 0 closed forward trades, 0 flagged bars, 0 entry thiếu visible stop; không bypass promotion gate.
- Supabase deployed `ai-trade-mt5-demo-bootstrap` v6 có direct MetaQuotes create/verify path và `open_demo_temp`; GitHub/local source có khả năng stale so với deployed runtime, phải sync safety-forward trước khi sửa/deploy.
- Chưa claim new-account broker DEMO order PASS; live/funded money tiếp tục HARD LOCKED.
- Handoff: `research/CWS_AUTOTRADE_DETERMINISTIC_ENGINE_DEMO_HANDOFF_2026-10-02.md`.
- New-chat prompt: `prompts/CWS_AUTOTRADE_CHAT_MOI_DETERMINISTIC_ENGINE_2026-10-02.md`.


---

## 2026-10-02 — MT5 new DEMO phone-verification blocker

- Supabase deployed `ai-trade-mt5-demo-bootstrap` v6 đã được mirror byte-for-byte về GitHub ở commit `c286e5fdcfedd64149f393cac8eebd4f3e2b2480`; không deploy source cũ đè runtime mới.
- Runtime transport probe: `TRANSPORT_READY`, MetaQuotes WebTerminal build `6231`, WebSocket ready, AES key length 32; `brokerOrders=false`, `liveMoneyLocked=true`.
- `open_demo_temp` đã chạy thật đến MetaQuotes nhưng dừng fail-closed: `TEMP_MAIL_DEMO_OPEN_BLOCKED` -> `VERIFICATION_PROBE_FAILED`, broker code `1`.
- `ai_trade.mt5_demo_credentials` vẫn 0 row: chưa có DEMO mới được tạo/verify; không được gọi PASS.
- Protocol byte layout cmd 27/40/30 của v6 khớp pinned `cloudQuant/pymt5@e7b5a8d28201879576e6cd22a39b9ea8677d4ee1`; upstream pymt5 HEAD hiện vẫn cùng implementation và chỉ ghi nhận re-verify build 5687.
- MetaTrader 5 Help hiện yêu cầu First name, Second name, Email và **Phone ở định dạng quốc tế** khi mở account. Runtime v6 đang để phone field trống trong opening payload, nên đây là blocker có bằng chứng phù hợp với broker validation code 1.
- Không bịa số điện thoại, không dùng SMS/identity bypass, không dùng temporary phone, không fake OTP/CAPTCHA.
- Supabase connector đã chặn attempt deploy patch thử nghiệm; deployed runtime vẫn v6 nguyên trạng.
- AutoTrade DEMO broker execution: NOT_YET_PASS. TF-013A engine không đổi. Promotion gate không bypass. Live/funded money HARD LOCKED.
- Evidence chi tiết: `research/CWS_AUTOTRADE_MT5_DEMO_PHONE_VERIFICATION_BLOCKER_2026-10-02.md`.


## 2026-10-05 — Web + MT5 thử nghiệm

- Web/PWA riêng tư đã publish; form Login/Password/Server nối MT5 session v9.
- Readback broker DEMO đã liên kết: PASS read-only; chưa có web password-login E2E, chưa có broker order.
- Forward v2 chặn state vị thế hỏng, sửa JSON double encoding; 7 state hỏng chưa phục hồi.
- 28 test đúng phạm vi PASS; portable build PASS; không gọi full-suite PASS.
- DEMO auto trade vẫn OFF: provider chưa ready, risk chưa duyệt, max total volume NULL; live money LOCKED.
- Chi tiết: research/CWS_AUTOTRADE_WEB_MT5_CHECKPOINT_2026-10-05.md.


## 2026-10-05 — Knowledge → deterministic research, no LLM runtime

- Nạp 12 nguyên tắc Masterbook V3 có source/hash vào machine-readable rules package.
- Bộ research gọi lại R2 chronological walk-forward; không thay TF-013A production.
- 20 Python test PASS + CLI E2E synthetic PASS: 12 claims loaded, 2 folds, llm_calls=0, orders_sent=0, promotion=NOT_APPROVED, costs MODELED_ONLY.
- Không claim edge/real-market net profitability; chưa thêm cloud cron hoặc broker send.
- Handoff: research/CWS_AUTOTRADE_AUTONOMOUS_RULES_2026-10-05.md.
