# MT5 Autonomous Position Management — V1

Ngày: 2026-09-26

## Goal

Biến execution layer từ "đặt được một lệnh" thành **quản lý trọn vòng đời vị thế** trên MetaTrader 5:

`signal -> risk gate -> entry -> protective SL -> optional TP -> monitor -> trail/partial/pyramid -> exit -> reconcile -> journal`

Live-money vẫn khóa. Spec này dành cho backtest, paper và MT5 DEMO cho tới khi live gate được Founder mở riêng.

## 1. Entry contract

Mọi order intent phải có:
- unique client order id;
- symbol;
- direction;
- volume;
- entry type;
- protective stop;
- exit model;
- strategy id;
- risk snapshot;
- timestamp/data freshness.

Không có protective stop hợp lệ -> reject trước broker.

## 2. Stop Loss

Nguyên tắc:
- SL là lớp bảo vệ bắt buộc.
- Sau khi position đã mở, SL **không bao giờ được nới theo hướng tăng rủi ro**.
- Long: stop mới chỉ được bằng hoặc cao hơn stop hiện tại.
- Short: stop mới chỉ được bằng hoặc thấp hơn stop hiện tại.
- Broker stop-level, digits, volume step và freeze-level phải được kiểm tra trước modify.
- Nếu state broker không chắc chắn -> không mở thêm risk.

## 3. Take Profit modes

Engine phải hỗ trợ ba mode tách biệt:

### FIXED_TP
Đóng theo target cố định đã được strategy spec định nghĩa.

### TRAILING_ONLY
Không có target cố định. Giữ vị thế cho tới trailing/structure/channel exit. Đây là mode gần nhất với "để lợi nhuận chạy".

### PARTIAL_THEN_TRAIL
Chốt một phần ở target đã định trước; phần còn lại chuyển sang trailing.

Tỷ lệ partial, R threshold và trailing lookback là tham số strategy/backtest, không phải quyết định tùy hứng của LLM.

## 4. Gồng lời

### LET_WINNER_RUN
Nếu position đang có lợi và chưa có exit signal:
- HOLD;
- ratchet stop theo rule;
- không chốt chỉ vì lợi nhuận "đã lớn".

### PYRAMID_WINNER
Cho phép add-on position chỉ khi:
- position hiện tại đang có lợi theo ngưỡng strategy;
- stop của vị thế cũ đã được bảo vệ theo policy;
- tổng portfolio risk sau add vẫn dưới hard limit;
- không vi phạm max adds;
- spread/data/connection/reconciliation đều hợp lệ.

Pyramiding phải có order id riêng và audit riêng.

### Cấm
- martingale;
- tăng lot sau lệnh thua để gỡ;
- thêm vị thế khi thesis đang sai;
- nới SL ra xa để tránh bị cắt.

## 5. Exit precedence

Thứ tự ưu tiên:
1. Kill switch / invalid state.
2. Protective SL.
3. Broker/risk emergency close.
4. Strategy invalidation / structure exit.
5. Fixed TP / partial TP.
6. Trailing stop update.
7. HOLD.

Nếu cùng một bar OHLC vừa chạm stop vừa chạm target mà không có tick sequence, backtest dùng policy bảo thủ `STOP_FIRST`.

## 6. MT5 operations cần có

Python adapter / MQL5 EA phải triển khai và test:
- market/pending order send;
- attach SL/TP;
- modify SL/TP;
- partial close;
- full close;
- read current positions;
- read pending orders;
- read history/deals;
- restart/reconnect;
- reconciliation;
- duplicate suppression;
- broker error mapping;
- audit log.

MetaQuotes Python API hỗ trợ `order_send()` với các field `sl`, `tp`, `position`; open positions đọc qua `positions_get()`. Mọi request vẫn phải broker-check và kiểm retcode.

## 7. State machine

`FLAT -> ENTRY_INTENT -> OPEN -> MANAGED -> EXIT_INTENT -> CLOSED`

Substate:
- `OPEN_PROTECTED`
- `OPEN_TRAILING`
- `OPEN_PARTIAL`
- `OPEN_PYRAMIDED`
- `RECONCILIATION_REQUIRED`
- `KILLED`

Bất kỳ restart/disconnect nào cũng chuyển sang `RECONCILIATION_REQUIRED` cho tới khi local state khớp broker.

## 8. AI boundary

LLM có thể:
- đọc knowledge;
- đề xuất hypothesis;
- giải thích signal;
- review journal.

LLM không được:
- tự tăng risk;
- tự bỏ SL;
- tự chọn lot ngoài Risk Engine;
- tự đổi exit mode giữa lệnh nếu strategy spec không cho phép;
- tự unlock live.

## 9. Definition of Done cho DEMO

Không coi là xong khi chỉ thấy order xuất hiện trên MT5.

Phải có evidence thật:
1. Entry DEMO.
2. SL/TP broker-side đúng.
3. Modify trailing stop.
4. Partial/full exit.
5. Restart terminal/process.
6. Reconcile position.
7. Duplicate order proof.
8. Kill-switch proof.
9. Journal đầy đủ.
10. Forward demo run không vi phạm risk policy.
