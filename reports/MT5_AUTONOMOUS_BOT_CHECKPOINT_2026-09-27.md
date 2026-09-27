# MT5 Autonomous Bot — Code-Verified Checkpoint 2026-09-27

## Kết quả đã hoàn thành

Autonomous DEMO path hiện có đầy đủ các lớp code:

`closed MT5 bar -> signal evaluator -> SafetyGate -> IndependentRiskEngine -> MT5BrokerAdapter -> broker`

Position lifecycle:

`OPEN -> protective SL -> optional TP -> trailing -> partial -> drop TP -> winner pyramiding -> full close -> restart/reconcile -> duplicate suppression`

Các điểm đã implement:
- MT5 DEMO-only account guard; LIVE vẫn hard-locked.
- broker contract preflight, stop distance, volume step.
- broker-side SL/TP.
- read-only `positions_get()` không phụ thuộc quyền gửi lệnh.
- modify SL/TP bằng `TRADE_ACTION_SLTP`.
- partial/full close bằng opposite `TRADE_ACTION_DEAL` + position ticket.
- trailing stop không được nới theo hướng tăng risk.
- partial volume tự chuẩn hóa theo broker volume grid.
- `TRAILING_ONLY`, `FIXED_TP`, `PARTIAL_THEN_TRAIL`.
- winner-only pyramiding; martingale/averaging-down không có path.
- total symbol volume cap cho pyramiding.
- persistent order intent ledger chống duplicate qua restart.
- persistent lifecycle state cho partial/pyramid/last stop.
- broker-authoritative reconciliation sau restart.
- runner `scripts/run_mt5_demo_autotrade.py`: closed bars, tick freshness, spread, daily PnL theo magic, one-bar-once loop.

## Local verification

Sandbox verification của patch hiện hành:
- `python -m py_compile src/execution/*.py scripts/run_mt5_demo_autotrade.py` -> PASS.
- targeted execution/risk/runtime regression suite -> **36 passed**.

Đây là CODE VERIFIED, không phải broker runtime PASS.

## Official MT5 API cross-check

MetaQuotes current docs xác nhận:
- `positions_get()` đọc position theo symbol/ticket.
- `TRADE_ACTION_SLTP` dùng để thay đổi Stop Loss / Take Profit của position.
- `order_send()` nhận `position` ticket khi thay đổi/đóng vị thế.
- `copy_rates_from_pos()` có bar index 0 là current bar; runner dùng start_pos=1 để loại bar chưa đóng.
- `history_deals_get()` cung cấp deal history; runtime chỉ cộng PnL/commission/swap/fee của đúng magic bot.

## Runtime evidence blocker

Đã thử hai đường Windows:
1. CWS PC Commander -> MCP SSE probe 404.
2. Remote Desktop Commander -> MAY086/MAY087/MAY088 đều `offline` tại thời điểm kiểm tra.

Do không có Windows host online, chưa thể chứng minh:
- MT5 terminal initialize thật;
- account DEMO thật;
- order_check/order_send broker thật;
- SL/TP/partial/trailing broker-side thật;
- restart/reconcile với broker thật.

Không đánh dấu runtime PASS giả.

## Gate tiếp theo khi Windows online

Chạy:
`python scripts/run_mt5_demo_autotrade.py --symbol EURUSD --timeframe M15 --once`

Sau khi monitor pass và xác minh account DEMO:
`python scripts/run_mt5_demo_autotrade.py --symbol EURUSD --timeframe M15 --enable-demo-send --once`

Sau one-shot runtime evidence mới bật loop 24/7. Live-money vẫn khóa.
