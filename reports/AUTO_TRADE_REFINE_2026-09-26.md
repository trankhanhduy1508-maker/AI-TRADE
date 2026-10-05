# Auto Trade Refine — 2026-09-26

## Founder request

Refine AI Trade theo hai trục:
1. Knowledge First, ưu tiên sách do người thành công thật sự viết; đặc biệt Peter Lynch / *One Up on Wall Street*.
2. MT5 tự động đặt lệnh và quản lý đầy đủ SL, TP, trailing/gồng lời và pyramiding có kiểm soát.

## Repo finding

Nhánh `codex/p0-covel-knowledge-audit` chứa nhiều implementation/evidence hơn nhánh `codex/mt5-demo-execution-proof`: deterministic backtest, IS/OOS, walk-forward, risk engine, recovery, MQL5 EA, Android control contract và MT5 adapter code-verified.

Vì vậy refinement được ghi vào nhánh giàu evidence này; không tạo lại foundation.

## Changes

- Thêm `knowledge/KNOWLEDGE_INGESTION_POLICY.md`.
- Thêm `knowledge/PRACTITIONER_BOOK_CORPUS.md`.
- Thêm `execution/MT5_AUTONOMOUS_POSITION_MANAGEMENT.md`.
- Đổi knowledge priority trong `auto_trade/MASTER_GOAL.md`: practitioner-first, track-record provenance, Peter Lynch core corpus; Covel chuyển thành secondary synthesis/cross-check.
- Ghi decision mới vào `DECISIONS.md`.
- Cập nhật current status theo checkpoint 2026-09-26.

## Important boundary

Không có full lawful copy của *One Up on Wall Street* trong source hiện tại, nên không claim đã ingest toàn bộ sách. Chỉ ingest public/verified facts và distilled principles có provenance cho tới khi lawful source xuất hiện.

MT5 live-money vẫn khóa. Current code có demo safety boundary, risk/recovery và MQL5 EA; lifecycle management cần runtime DEMO evidence cho modify SL, partial exit, reconnect/reconciliation và duplicate suppression.
