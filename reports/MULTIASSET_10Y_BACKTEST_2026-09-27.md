# Multi-Asset 10-Year Backtest — 2026-09-27

## Kết luận ngắn

Đã có historical backtest cho 14 thị trường phổ biến:

Forex:
- EURUSD
- GBPUSD
- USDJPY
- AUDUSD
- USDCAD
- USDCHF
- NZDUSD

Cross-asset:
- BTCUSD
- ETHUSD
- XAUUSD / Gold
- USOIL / WTI
- US30 / Dow Jones
- NAS100 / Nasdaq 100
- US500 / S&P 500

Ba cặp EURUSD / GBPUSD / USDJPY đã có evidence 10 năm trước đó nên không chạy lại.

11 thị trường còn thiếu được chạy cloud trong continuation này:
- Supabase request #42: COMPLETE 11/11.
- không broker orders.
- research only.

ETH Yahoo chỉ có khoảng 8.88 năm nên không được gọi là 10-year PASS.
- CryptoCompare fallback request #43: FAIL HTTP 401.
- minimal source-only fix sang Coinbase Exchange public daily candles.
- request #45: COMPLETE.
- ETH coverage: 2016-05-18 → 2026-09-27 = 10.36 năm.
- Coinbase candles are public and no trading credential was used.

## Cách đọc backtest trong 30 giây

Đừng nhìn mỗi Full Sample Net R. Nó là phần dễ làm con người vui nhất và cũng dễ đánh lừa nhất.

Ưu tiên theo thứ tự:

1. **OOS Net R**
   - phần dữ liệu cuối không dùng làm warm-up/history ban đầu;
   - > 0 là tín hiệu tốt hơn;
   - < 0 nghĩa là strategy không giữ được hiệu quả trong đoạn chưa dùng trước đó.

2. **Walk-Forward Net R**
   - chia nhiều đoạn thời gian kế tiếp nhau;
   - càng nhiều fold dương càng có tính ổn định;
   - tổng WF âm là cảnh báo mạnh dù full sample đẹp.

3. **Positive folds**
   - ví dụ 4/5 nghĩa là 4 trong 5 đoạn test dương;
   - 0/5 thì rất yếu.

4. **Max Drawdown R**
   - đo đoạn sụt giảm lớn nhất theo đơn vị R;
   - càng lớn thì đường đi càng đau, dù cuối cùng tổng R có thể dương.

5. **Cost Mode**
   - RESEARCH_PROXY: đã có cost proxy nghiên cứu, vẫn chưa phải broker cost thật.
   - GROSS_ONLY: chưa trừ broker cost thật. Tuyệt đối không gọi đây là net profitability.

## TF-004 fixed methodology

- daily closed bars;
- time-series momentum lookback 20;
- initial stop lookback 5;
- trailing channel 20;
- one open position;
- stop-first ambiguity handling;
- chronological OOS 70/30;
- expanding-history walk-forward;
- no parameter retuning after results;
- no pyramiding.

## Kết quả 3 cặp đã có trước

| Market | Cost | OOS Net R | WF Net R | Positive folds | Ghi chú |
|---|---|---:|---:|---:|---|
| EURUSD | research proxy | +8.361 | -3.766 | 2/6 | OOS dương nhưng WF âm |
| GBPUSD | research proxy | -0.042 | -14.224 | 1/6 | yếu |
| USDJPY | research proxy | -1.029 | -1.262 | 3/6 | chưa ổn định |

Nguồn:
`reports/TF004_CLOUD_RISK_LAB_2026-09-27.md`

Lưu ý: historical lab cũ ghi 6 walk-forward folds. Continuation lab mới dùng 5 non-overlap folds. Vì vậy không nên so fold count cũ/mới như một phép xếp hạng tuyệt đối.

## Kết quả 11 thị trường mới

Các số dưới đây dùng cost multiplier 1x của từng market. Với GROSS_ONLY, 1x vẫn bằng gross vì cost thật chưa có.

| Market | Coverage | Cost mode | OOS Net R | OOS Exp R | OOS PF | OOS DD R | WF +folds | WF Net R |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| AUDUSD | 10.74y | RESEARCH_PROXY | -15.920 | -0.497 | 0.197 | 16.186 | 0/5 | -27.803 |
| USDCAD | 10.74y | GROSS_ONLY | -3.332 | -0.101 | 0.805 | 7.860 | 0/5 | -19.725 |
| USDCHF | 10.73y | GROSS_ONLY | +18.942 | +0.729 | 2.615 | 4.484 | 3/5 | +24.337 |
| NZDUSD | 10.74y | GROSS_ONLY | -15.257 | -0.412 | 0.316 | 15.302 | 0/5 | -37.992 |
| XAUUSD | 10.72y | RESEARCH_PROXY | +8.299 | +0.251 | 1.339 | 13.224 | 2/5 | +10.837 |
| BTCUSD | 10.74y | RESEARCH_PROXY | +14.007 | +0.305 | 1.500 | 13.999 | 2/5 | +8.458 |
| ETHUSD | 10.36y | GROSS_ONLY | +17.905 | +0.578 | 2.120 | 4.967 | 4/5 | +22.727 |
| USOIL | 10.72y | RESEARCH_PROXY | +10.279 | +0.447 | 1.988 | 5.402 | 3/5 | +4.446 |
| US30 | 10.72y | GROSS_ONLY | +8.318 | +0.333 | 1.870 | 4.035 | 2/5 | -3.844 |
| NAS100 | 10.72y | GROSS_ONLY | -1.214 | -0.043 | 0.932 | 7.433 | 3/5 | +1.208 |
| US500 | 10.72y | GROSS_ONLY | +7.656 | +0.284 | 1.515 | 5.643 | 3/5 | +8.964 |

## Cách hiểu kết quả này

Có một số market cho cả OOS và WF dương trong historical research:
- USDCHF
- XAUUSD
- BTCUSD
- ETHUSD
- USOIL
- US500

Nhưng đây không phải danh sách được phép trade hay ranking promotion.

Lý do:
- USDCHF, ETHUSD, US500 là GROSS_ONLY.
- XAUUSD, BTCUSD, USOIL mới có research cost proxy, chưa phải broker-aligned cost.
- historical result không thay thế forward paper.
- broker spread / commission / swap / margin / tick value chưa được gắn cho actual DEMO account.
- risk profile vẫn chưa Founder-approved.

US30 là ví dụ dễ nhớ:
- OOS dương +8.318R;
- nhưng WF tổng âm -3.844R.
=> nhìn OOS một mình có thể khiến ta tưởng strategy ổn trong khi tính ổn định theo thời gian chưa đạt.

NAS100 là ví dụ ngược:
- OOS âm -1.214R;
- WF tổng hơi dương +1.208R.
=> evidence mâu thuẫn, chưa đủ để promote.

AUDUSD / NZDUSD là ví dụ rõ:
- OOS âm mạnh;
- 0/5 fold dương;
- WF âm mạnh.
=> historical evidence hiện không ủng hộ TF-004 trên hai market này.

## Runtime evidence

Supabase Edge Function:
`ai-trade-multiasset-backtest`

Current deployed version after fixes:
v3.

Request #42:
- COMPLETE
- 11/11 successful
- Yahoo research daily data
- no broker orders

Request #43:
- ETH CryptoCompare fallback
- FAIL: CRYPTOCOMPARE_HTTP_401
- not counted as PASS

Request #45:
- ETH Coinbase Exchange public daily candles
- COMPLETE
- coverage 10.36 years
- 112 full-sample trades
- OOS: +17.905R
- WF: +22.727R
- 4/5 positive folds
- GROSS_ONLY

Persistent evidence:
`ai_trade.backtest_runs`

## Boundary

Backtest coverage is now broad enough to say:
**14-market ~10-year historical research coverage exists.**

It is NOT enough to say:
- profitable in live conditions;
- safe to trade;
- broker-net profitable;
- risk profile approved;
- The5ers execution approved.

Next evidence layer, when requested, is broker-aligned DEMO / forward validation rather than more repetition of the same historical backtest.
