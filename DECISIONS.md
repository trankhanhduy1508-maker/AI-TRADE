# Official Decisions — AI-TRADE

Trường phái giao dịch

Reaction, không dự đoán cảm tính.

Trend Following.

Price Action và cấu trúc thị trường là dữ liệu chính.

---

Vai trò chỉ báo

Volume, EMA, RSI chỉ dùng để xác nhận.

Không dùng RSI kiểu máy móc "quá mua thì bán, quá bán thì mua".

Không coi trendline chạm là đủ điều kiện vào lệnh.

---

Quản lý rủi ro

Quan trọng hơn tỷ lệ thắng.

Mọi giới hạn rủi ro là luật cứng, không do LLM tự quyết định.

Bắt buộc có kill switch.

Thua lỗ liên tiếp/drawdown vượt ngưỡng → bắt buộc tạm dừng và đánh giá lại.

---

Kết nối thật

Chưa kết nối tài khoản giao dịch thật.

Chưa viết bot đặt lệnh thật.

Chưa tự ý huấn luyện model.

---

Tổng quát hoá chiến lược

Không có chiến lược nào mặc định hiệu quả ở mọi thị trường/timeframe — mỗi chiến
lược phải ghi rõ phạm vi đã kiểm chứng.

---

Ngôn ngữ và bản quyền

Toàn bộ tài liệu viết bằng tiếng Việt.

Không chép nguyên văn sách/khóa học có bản quyền — chỉ tổng hợp bằng ngôn ngữ riêng.

Không khẳng định chiến lược nào chắc chắn sinh lời.

---

Kiến trúc AI Trading (Phase 01 Research)

Lõi chính: Trend Following + Market Structure (HH/HL, BOS/CHoCH)

Xác nhận: Volume (breakout volume > SMA), Price Action (breakout quality), EMA bias (filter)

Nền tảng rủi ro: Market Wizards principles (cut loss fast, let profit run, discipline)

Không dùng: SMC, Wyckoff, Al Brooks, Minervini (reversal) — quá phức tạp hoặc không phù hợp

---

Nguyên tắc thiết kế AI (Phase 01)

1. Reaction, không prediction — chỉ vào khi dữ liệu đã xảy ra
2. Trend Following, không reversal — theo xu hướng xác nhận, không bắt đảo
3. Price Action/Market Structure quyết định → chỉ báo xác nhận
4. Volume/EMA xác nhận, không chính — luôn sau cấu trúc giá
5. Quản lý rủi ro > tỷ lệ thắng — cắt lỗ nhanh, để lợi chạy
6. Không tổng quát chiến lược → backtest riêng mỗi pair/timeframe
7. AI không tự quyết định rủi ro — mọi limit từ RISK_POLICY.md

---

Roadmap 7 giai đoạn (Phase 01)

Phase 1: Knowledge Base ✅ (hoàn tất)
Phase 2: Rule Engine (4-6w) — code quy tắc + unit test
Phase 3: Backtest (4-8w) — chạy backtest 100+ lệnh
Phase 4: Paper Trade (4-12w) — live trading không tiền thật 2-4w
Phase 5: AI Scoring (4-8w) — LLM phân tích, confirm, cảnh báo
Phase 6: Machine Learning (6-16w) — optimize tham số, train model
Phase 7: Live Trading (∞) — account thật, phụ thuộc Project Owner confirm

---

Phát triển

MVP tài liệu trước, tránh over-engineering.

Không xóa file có sẵn khi thêm nội dung mới.

Phase 01 complete, ready for Phase 02 (Rule Engine).

---

Kiến trúc Rule Engine (Phase 02 Design)

Decision Flow: 10 bước tuần tự (Trend → Structure → Breakout → Pullback → Volume → R/R → SL → Portfolio Risk → Score → Signal).

Các điều kiện reject cứng (không thương lượng): Không trend, không structure, không breakout, false break, R/R < 1.0, không SL, vượt portfolio limit, kill switch.

Scoring System: 0-100, 10 rule (001-009) với điểm max khác nhau. Ngưỡng vào lệnh >= 80 (đề xuất, cần backtest xác nhận).

Priority rank: Price Action/Structure > Risk > Volume > Indicators (RSI, EMA, Liquidity).

Rule Conflicts: Khi xung đột, priority cao thắng. Giải quyết bằng giảm điểm, không reject tùy tiện.

10 Rule: RULE_001 Trend, RULE_002 Structure, RULE_003 Breakout, RULE_004 Pullback, RULE_005 Volume, RULE_006 RSI, RULE_007 EMA, RULE_008 Risk, RULE_009 Liquidity, RULE_010 Exit.

Rule 010 (Exit) áp dụng SAU khi vào lệnh, khác 001-009 là xác định vào lệnh.

---

Tham số chưa chốt (cần Project Owner)

R/R minimum: Đề xuất 1.5, cần backtest xác nhận.

Scoring threshold: Đề xuất 80/100, cần backtest xác nhận.

Body ratio breakout: Đề xuất 60%, cần backtest xác nhận.

SMA period volume: Đề xuất 20, cần chốt cụ thể.

EMA period bias: Chưa chốt (50? 100? 200?), strategy phải define rõ.

Swing high/low period (N): Chưa chốt, tuỳ timeframe (2-3 suggested).

% rủi ro/lệnh, % drawdown max, số lệnh thua liên tiếp: Chưa chốt trong RISK_POLICY.md.

---

Paper Trading Engine (Giai đoạn 4)

Phân tách Virtual Account, Virtual Order, Position, Trade Journal, Periodic Review, Performance Dashboard để tách biệt hoàn toàn với Execution Engine thật.

Virtual Account là "ngân hàng" ảo: balance, equity, unrealized PnL, positions_open, total_portfolio_risk được quản lý riêng biệt.

Virtual Order mô phỏng execution: thêm slippage/spread giả định, kiểm tra Risk Gateway (5 checks), FILLED hoặc REJECTED.

Position trong paper trading: đơn giản hơn Execution Engine, chỉ theo dõi entry, SL, target, unrealized PnL, exit khi SL/TP hit hoặc exit rule.

Trade Journal = ghi lại chi tiết lệnh đóng (entry/exit, PnL, R multiple, hold time) + rule breakdown — input cho POST_TRADE_REVIEWER prompt.

Periodic Review (Daily/Weekly/Monthly): kiểm tra kill switch, PnL, KPI so backtest, signal quality — foundation cho quyết định tiếp tục/pause/debug.

Performance Dashboard: tái sử dụng KPI từ backtests/KPI_STANDARD.md, display live + historical, so sánh vs backtest expectation.

---

Execution Engine (Giai đoạn 4 + 7)

Một Execution Engine duy nhất hỗ trợ cả Paper Trading (giai đoạn 4) và Live Trading (giai đoạn 7) thông qua Broker Adapter Interface.

Signal Queue → Risk Gateway → Order Manager → Broker Adapter → Position Manager + Audit Log (8 thành phần).

Risk Gateway là CỔNG CHẶN RỦI RO DUY NHẤT: 5 checks (risk/trade, portfolio risk, kill switch, consecutive losses, no duplicate symbol) — không ngoại lệ, không linh hoạt.

Order Manager: tạo order từ signal đã qua Risk Gateway, tính khối lượng (từ position sizing formula), gửi qua Broker Adapter, đảm bảo idempotency (order_id duy nhất).

Broker Adapter Interface: định nghĩa hành vi bắt buộc (place_order, cancel_order, get_position, get_balance...) mà BẤT KỲ broker nào phải implement — hiện tại chỉ Paper Adapter, tương lai có MT5 Adapter, Binance Adapter, IB Adapter v.v.

Position Manager: theo dõi position đang mở, monitor exit conditions (SL/TP hit, RULE_010 exit signal), cập nhật portfolio_risk_current cho Risk Gateway.

Audit Log: append-only, ghi tất cả sự kiện (signal received, risk check, order created/sent/filled, position opened/closed) — bắt buộc cho live trading, bảo vệ audit trail.

Error Handling + Retry Policy: phân loại lỗi (kỹ thuật/nghiệp vụ/dữ liệu), retry kỹ thuật theo backoff exponential, không retry nghiệp vụ.

AI không tự quyết định rủi ro: mọi lệnh AI đề xuất vẫn phải qua Risk Gateway 5 checks, Risk Gateway có quyền reject nếu vi phạm RISK_POLICY.md.

---

Point-in-Time AI Backtesting (Framework Kiểm chứng)

Mục đích: Kiểm chứng khách quan khả năng AI ra quyết định giao dịch hợp lý trên dữ liệu lịch sử, hoàn toàn chống look-ahead bias.

Chống look-ahead bias triệt để: Ẩn danh symbol thật, ẩn danh thời gian thật, loại bỏ thông tin sự kiện lịch sử, chỉ cấp dữ liệu point-in-time (quá khứ tính đến timestamp mô phỏng hiện tại).

Vòng lặp tuần tự: Observe (cấp data) → Decide (AI + Rule ra quyết định riêng) → Execute (mô phỏng) → Reveal next data (tiến sang timestamp tiếp theo, không được sửa quyết định).

Locked Out-of-Sample: Dữ liệu test được khoá từ đầu, chỉ chạy 1 lần, không optimize prompt rồi chạy lại trên đúng bộ OOS đó.

Walk-Forward: Áp dụng phương pháp WFA (từ WALK_FORWARD_GUIDE.md), chia dữ liệu thành các window in-sample/OOS cuộn tiến theo thời gian.

Logging append-only: Ghi đầy đủ mỗi bước (observe, AI decision, rule decision, execute, position close) với timestamp, input/output LLM, fill price, PnL — không sửa/xóa để audit sau.

So sánh Rule-based baseline: Chạy song song AI + Rule Engine trên cùng dữ liệu point-in-time, ghi lại cả 2 quyết định tại mỗi bước, tính KPI (win rate, expectancy, max DD, Sharpe, agreement rate, false alarm rate) để so sánh giá trị AI.

AI vẫn qua Risk Gateway: Framework này chỉ KIỂM CHỨNG AI, không phải cho AI tự quyết định rủi ro. Mọi lệnh AI đề xuất vẫn phải qua 5 risk checks từ RISK_GATEWAY.md, Risk Gateway có quyền reject nếu vi phạm RISK_POLICY.md.

---

Rule Engine Code (Phase 2 Code, MVP)

Bắt đầu code thật (Python, `src/rule_engine/`) từ đặc tả `rule_engine/*.md` — 10 rule + orchestrator scoring, 103 unit/integration test PASS thật.

Direction đề xuất phải khớp trend thật: RULE_001 tự phát hiện xu hướng từ dữ liệu (không nhận direction làm input). Nếu hướng giao dịch đề xuất (`direction` truyền vào `evaluate_setup()`) không khớp xu hướng RULE_001 phát hiện được (hoặc xu hướng NEUTRAL) → reject ngay, đúng nguyên tắc "không giao dịch ngược xu hướng chính".

Liquidity (RULE_009) dùng tham số tạm: Chưa có nguồn spread/order-book thật, `evaluate_setup()` nhận `spread_pips`/`depth_ok` làm tham số có giá trị mặc định "tạm ổn" — caller (Data Loader/Backtest Engine sau này) phải truyền dữ liệu thật khi có, không dùng mặc định cho quyết định thật.

Chỉ dùng Python standard library ở Phase 2 Code — chưa cần pandas/numpy, vì mục tiêu là kiểm chứng logic, không phải hiệu năng xử lý dữ liệu lớn (sẽ xét lại khi tới Data Loader/Backtest Engine với dữ liệu thật).
