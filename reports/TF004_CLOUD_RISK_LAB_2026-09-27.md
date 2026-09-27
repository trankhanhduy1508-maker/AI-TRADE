# TF-004 Cloud Risk Lab — 2026-09-27

## Kết luận

**RISK PROFILE = FAIL_CLOSED.**

Risk Lab không tìm được bằng chứng đủ mạnh để hợp thức hóa bốn hard limit đang còn bỏ trống:

- `MAX_SPREAD_POINTS`: chưa chốt.
- `MAX_DAILY_LOSS_DEMO`: chưa chốt.
- `MAX_PYRAMID_ADDS`: chưa chốt.
- `MAX_TOTAL_VOLUME_DEMO`: chưa chốt.

Không được biến các giá trị tạm từng xuất hiện trong code thành Founder-approved risk policy.

## Phương pháp

Runtime: AppDeploy cloud, không dùng PC.

Nguồn dữ liệu:
- Yahoo chart daily research proxy.
- Window: 2016-01-01 đến bar UTC hoàn tất gần nhất.
- EURUSD=X: 2,794 bars, last bar 2026-09-26.
- GBPUSD=X: 2,793 bars, last bar 2026-09-24.
- USDJPY=X: 2,794 bars, last bar 2026-09-26.

Strategy cố định:
- TF-004-TIME-SERIES-CHANNEL.
- momentum lookback: 20 bars.
- initial stop lookback: 5 bars.
- trailing channel: 20 bars.
- one open position.
- STOP_FIRST.
- Không retune sau khi thấy kết quả.

Validation:
- OOS chronological 70/30.
- Walk-forward expanding history: 50% initial / 10% non-overlap test windows.
- Cost stress: 0x / 1x / 1.5x / 2x.
- Cost proxy 1x dùng đúng research assumptions cũ, provenance `UNVERIFIED`.

## Baseline 1x cost proxy

| Pair | OOS trades | OOS net R | OOS expectancy R | OOS PF R | OOS max DD R | Max loss streak | WF positive folds | WF net R sum | WF worst DD R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| EURUSD | 30 | +8.361 | +0.279 | 1.570 | 6.214 | 5 | 2/6 | -3.766 | 11.541 |
| GBPUSD | 36 | -0.042 | -0.001 | 0.998 | 14.561 | 10 | 1/6 | -14.224 | 9.635 |
| USDJPY | 30 | -1.029 | -0.034 | 0.939 | 6.384 | 4 | 3/6 | -1.262 | 6.699 |

EURUSD có OOS dương nhưng walk-forward âm. GBPUSD và USDJPY baseline đều không đạt net-R stability.

## Cost stress

### 0x research costs

| Pair | OOS net R | WF net R sum |
|---|---:|---:|
| EURUSD | +10.407 | +3.096 |
| GBPUSD | +2.450 | -10.080 |
| USDJPY | -0.017 | +0.193 |

Ngay cả khi giả định **không có spread, commission, slippage và swap**, ba cặp vẫn không đồng thời vượt OOS + walk-forward.

### Highest cost multiplier với cả OOS và WF dương

- EURUSD: 0x.
- GBPUSD: none.
- USDJPY: none.

Điều này không phải broker spread tolerance. Nó chỉ mô tả sensitivity của research proxy.

## Vì sao chưa thể suy hard risk number

1. Yahoo data không phải broker execution feed.
2. Cost profile là price-unit proxy chưa broker-verified.
3. Backtest đo R theo entry-to-stop, không có account balance, leverage, lot-value hay margin model.
4. Daily-loss bằng tiền không thể suy từ signal-only R mà không bịa capital-risk mapping.
5. Historical engine cố định này chưa mô phỏng pyramiding, nên không có evidence để đặt max adds hoặc max total volume.
6. Cross-pair stability fail ngay cả trước khi thêm broker friction thật.

## Gate

- Không bind MetaApi/MT5 DEMO credentials vào execution runtime từ evidence này.
- Không unlock DEMO execution bằng hard risk number tự suy đoán.
- Live money tiếp tục hard locked.
- Technical DEMO lot cap 0.01 không được coi là Founder-approved capital risk policy.

## Evidence path

Cloud endpoint:
`GET /api/research/tf004-risk`

AppDeploy app:
`ai-trade-cloud-vpwo6l`

Endpoint runtime probe qua Supabase pg_net:
- HTTP 200.
- final probe request id: 27.
- generatedAt: `2026-09-27T03:18:41.991Z`.
- candidate status: `FAIL_CLOSED`.

## Next research work

Tiếp tục ở paper/research layer:
1. forward paper journal không gửi broker order;
2. broker-aligned spread/slippage/commission/swap evidence khi có DEMO credentials;
3. capital-normalized risk model tách khỏi strategy selection;
4. pyramiding phải có backtest riêng, không suy từ non-pyramid TF-004;
5. chỉ tạo hard risk proposal sau khi các gate trên có evidence.
