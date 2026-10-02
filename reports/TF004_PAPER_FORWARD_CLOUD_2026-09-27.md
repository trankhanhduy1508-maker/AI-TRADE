# TF-004 Paper-Forward Cloud — 2026-09-27

## Trạng thái

**ACTIVE / INITIALIZED — chưa phải performance PASS.**

Paper-forward đã được triển khai hoàn toàn trên cloud, không dùng PC và không gửi broker order.

Runtime:
- AppDeploy app: `ai-trade-cloud-vpwo6l`
- mode: `PAPER_ONLY`
- brokerOrders: `false`
- pyramiding: `false`
- cron: `paper-forward`
- cadence: `15 */6 * * *` UTC
- handler: `paperForwardCronHandler`

## Workflow

Mỗi vòng:
1. tải Yahoo daily closed bars cho EURUSD=X, GBPUSD=X, USDJPY=X;
2. bỏ current/incomplete UTC day;
3. chỉ xử lý bars mới hơn checkpoint đã lưu;
4. TF-004 signal: close so với close 20 bars trước;
5. initial stop: prior 5 bars;
6. one open paper position;
7. 20-bar channel trailing;
8. STOP_FIRST;
9. lưu paper entry/exit và R vào AppDeploy DB;
10. không gọi MetaApi/broker.

State được giới hạn:
- tối đa 200 closed paper trades mỗi symbol;
- tối đa 40 recent events;
- checkpoint `lastProcessed` chống xử lý lại sau restart.

## Initialization evidence

Manual cloud-to-cloud initialization:
- Supabase pg_net request id: `29`
- HTTP: `200`
- generatedAt: `2026-09-27T03:26:47.264Z`
- mode: `PAPER_ONLY`
- brokerOrders: `false`
- pyramiding: `false`

Initial states:

| Symbol | Last processed | Position | Trades | Net R | Event |
|---|---|---|---:|---:|---|
| EURUSD=X | 2026-09-26T19:04:57Z | none | 0 | 0 | WARMED |
| GBPUSD=X | 2026-09-24T23:00:00Z | none | 0 | 0 | WARMED |
| USDJPY=X | 2026-09-26T04:21:09Z | none | 0 | 0 | WARMED |

Event detail cho cả ba:
`Forward-only start; no historical trades backfilled`.

Đây là hành vi đúng: journal bắt đầu từ checkpoint hiện tại thay vì giả lập quá khứ rồi gọi đó là forward evidence.

## Safety

- Live-money vẫn hard locked.
- MetaApi/MT5 secrets chưa bind.
- Paper-forward không có broker-order path.
- Winner pyramiding đã bị disable sau negative historical validation.
- Hard risk profile vẫn `FAIL_CLOSED`; không có founder-approved spread/daily-loss/portfolio hard number mới.

## Data limitations

- Yahoo là research proxy, không phải broker execution feed.
- Cost profile vẫn `UNVERIFIED`.
- Paper-forward này đánh giá behavior của strategy từ thời điểm khởi tạo trở đi; không thay thế broker DEMO execution evidence.
- Chưa có future closed paper trade, vì vậy chưa được ghi performance PASS.

## Gate tiếp theo

Tích lũy closed future bars/trades tự động. Chỉ sau khi có forward sample đủ nghĩa mới so sánh:
- expectancy R;
- max DD R;
- loss streak;
- stability giữa ba pair;
- historical vs forward drift.

Không promote hard risk number hoặc broker execution chỉ vì journal đã khởi tạo thành công.
