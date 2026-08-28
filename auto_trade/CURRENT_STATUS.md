# AI AUTO TRADE — CURRENT STATUS

## North Star

✅ `auto_trade/MASTER_GOAL.md` — autonomous Trend Following + MT5 + Android control.

✅ `auto_trade/BOOTSTRAP.md` — short session bootstrap.

✅ `AGENTS.md` — Superpowers/skill discipline + autonomy + verification rules.

## Current Priority

**P0 — VERIFIED MT5 DEMO EXECUTION PROOF**

Ngày 2026-08-28, Founder đã cho phép test có kiểm soát trên tài khoản DEMO.
Live-money vẫn khóa tuyệt đối.

Đã hoàn thành trong nhánh `codex/mt5-demo-execution-proof`:
- Ground canonical repo `trankhanhduy1508-maker/AI-TRADE` và đọc đúng source-of-truth.
- Cài official `MetaTrader5` Python package vào runtime Python cục bộ.
- Thêm DEMO-only account guard, append-only journal và deterministic idempotency key.
- Thêm native Python MT5 adapter: initialize → account guard → symbol/tick → order_check → order_send.
- Unit tests: `5 passed`.

Runtime blocker hiện tại: `mt5.initialize()` trả `(-10003, 'IPC initialize failed, MetaTrader 5 x64 not found')` vì host chưa có MT5 terminal. Official installer download bị policy supply-chain chặn; chưa có terminal/account session để đặt lệnh, audit, close, reconnect hoặc chứng minh no-duplicate.

Khi terminal xuất hiện, thứ tự bắt buộc là: verify DEMO context → tick → order_check → một lệnh tối thiểu → audit → close → restart/reconnect → reconcile → duplicate-order proof → forward demo validation.

Trước khi mở rộng MT5/execution, audit `knowledge/TREND_FOLLOWING.md` và các knowledge hiện có theo Michael W. Covel `Trend Following`, ưu tiên Fifth Edition.

Yêu cầu:
- xác định source nào thực sự đã có;
- không tuyên bố đã ingest full book nếu chưa có full lawful copy;
- bổ sung provenance cho từng nhóm kiến thức;
- tách book/author knowledge khỏi engineering derivation;
- map kiến thức thành strategy concepts có thể kiểm chứng/backtest;
- không chép dài nguyên văn nội dung có bản quyền.

## Next Autonomous Action

Agent đọc `auto_trade/BOOTSTRAP.md`, dùng Superpowers/skills liên quan, rồi thực hiện P0 đến khi gặp blocker thật sự.

Các hạng mục cũ trong root `CURRENT_STATUS.md` vẫn là backlog/evidence hiện hữu, nhưng **không được ưu tiên hơn P0 này** cho đến khi knowledge audit được cập nhật rõ ràng.

## Live Trading Gate

🔒 Live-money trading vẫn khóa theo `PROJECT_CONTEXT.md`.

Goal dài hạn có MT5 autonomous execution, nhưng giai đoạn hiện tại chỉ research/backtest/paper/demo theo governance.
