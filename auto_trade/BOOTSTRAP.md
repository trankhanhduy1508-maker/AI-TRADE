# AI AUTO TRADE — BOOTSTRAP

Dùng file này để bắt đầu mọi phiên Codex/AI làm Auto Trade.

## Read first

1. `AGENTS.md`
2. `PROJECT_CONTEXT.md`
3. `DECISIONS.md`
4. `CURRENT_STATUS.md`
5. `auto_trade/MASTER_GOAL.md`
6. `auto_trade/CURRENT_STATUS.md`
7. Các file knowledge/risk/code liên quan trực tiếp task hiện tại.

Không ground toàn repo nếu task không cần.

## Operating rule

- Repo/evidence hiện tại là source of truth.
- Dùng Superpowers/skills liên quan trước khi hành động nếu môi trường có hỗ trợ.
- Knowledge First theo `knowledge/KNOWLEDGE_INGESTION_POLICY.md`: ưu tiên practitioner có track record kiểm chứng; Peter Lynch là core corpus, Covel/Schwager là secondary/cross-check.
- Không tuyên bố đã học toàn bộ sách nếu source chưa đủ.
- STABLE FIRST -> MINIMUM CHANGE -> VERIFY -> REWRITE LAST.
- Tự xử lý routine blocker; không hỏi Founder các quyết định kỹ thuật nhỏ.
- Không tự thay đổi hard risk limits.
- Chưa unlock live-money trading.
- Mọi thay đổi phải test/verify trước khi báo DONE.

## Current priority

Đọc `auto_trade/CURRENT_STATUS.md` và thực hiện ưu tiên cao nhất chưa hoàn thành.

Ưu tiên hiện tại: tiếp tục practitioner-first ingestion + map claim thành hypothesis, sau đó hoàn thiện MT5 DEMO full lifecycle theo `execution/MT5_AUTONOMOUS_POSITION_MANAGEMENT.md`.

Sau đó tiếp tục goal, không dừng chỉ để hỏi những gì repo đã trả lời được.
