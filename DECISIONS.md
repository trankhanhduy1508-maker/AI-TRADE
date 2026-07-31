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
