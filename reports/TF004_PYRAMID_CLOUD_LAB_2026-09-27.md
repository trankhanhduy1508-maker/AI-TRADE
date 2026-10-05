# TF-004 Winner-Pyramiding Cloud Lab — 2026-09-27

## Kết luận

**NO_PYRAMID_PROMOTION.**

Một lần add-on position theo rule production research đã làm kết quả xấu hơn trên cả EURUSD, GBPUSD và USDJPY trong OOS/walk-forward. Vì vậy không có evidence để promote `max_pyramid_adds=1` vào risk policy.

Đây là research result, không phải lời khuyên giao dịch và không unlock DEMO/live.

## Rule được test

Pyramid variant chỉ được add khi:
- position hiện tại đang lời;
- stop cũ đã bảo vệ ít nhất hòa vốn;
- momentum 20-bar vẫn cùng hướng;
- tối đa 1 add;
- add tại close của closed bar;
- channel trailing 20-bar tiếp tục quản lý toàn position.

Normalization:
- tổng PnL của các legs chia cho original entry-to-stop risk;
- đây là research R metric, không phải account return.

Cost:
- baseline research proxy 1x cũ;
- provenance `UNVERIFIED`.

Data:
- Yahoo daily proxies;
- 2016-01-01 → last completed UTC day;
- OOS chronological 70/30;
- walk-forward expanding 50/10.

## EURUSD

### Không pyramid
- OOS net: +8.361R
- OOS max DD: 6.214R
- WF net sum: -3.766R
- WF worst DD: 11.541R

### 1 add
- OOS net: +8.357R
- OOS max DD: 8.641R
- OOS adds: 12
- max loss streak: 11
- WF net sum: -11.613R
- WF worst DD: 13.782R
- WF adds: 23

Delta:
- OOS net: -0.004R
- OOS DD: +2.427R
- WF net: -7.847R
- WF DD: +2.241R

## GBPUSD

### Không pyramid
- OOS net: -0.042R
- OOS max DD: 14.561R
- WF net sum: -14.224R
- WF worst DD: 9.635R

### 1 add
- OOS net: -12.197R
- OOS max DD: 17.041R
- OOS adds: 9
- max loss streak: 12
- WF net sum: -28.777R
- WF worst DD: 10.729R
- WF adds: 16

Delta:
- OOS net: -12.155R
- OOS DD: +2.480R
- WF net: -14.553R
- WF DD: +1.094R

## USDJPY

### Không pyramid
- OOS net: -1.029R
- OOS max DD: 6.384R
- WF net sum: -1.262R
- WF worst DD: 6.699R

### 1 add
- OOS net: -7.592R
- OOS max DD: 12.372R
- OOS adds: 11
- max loss streak: 7
- WF net sum: -5.131R
- WF worst DD: 9.959R
- WF adds: 18

Delta:
- OOS net: -6.563R
- OOS DD: +5.988R
- WF net: -3.869R
- WF DD: +3.260R

## Gate

- `max_pyramid_adds=1` không được promote.
- Pyramiding phải mặc định disabled trong research/execution policy cho tới khi có một hypothesis mới được preregister và vượt OOS + walk-forward + broker-cost validation.
- Không dùng kết quả này để suy ra max total volume hoặc daily-loss money limit.

## Evidence

Cloud endpoint:
`GET /api/research/tf004-pyramid`

Probe:
- HTTP 200.
- Supabase pg_net request id: 28.
- generatedAt: `2026-09-27T03:21:54.810Z`.
- conclusion: `NO_PYRAMID_PROMOTION`.
