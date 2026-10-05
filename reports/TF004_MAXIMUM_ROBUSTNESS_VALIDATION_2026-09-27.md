# TF-004 Maximum Robustness Validation — 2026-09-27

## Executive conclusion

**TF-004 is NOT validated for autonomous DEMO execution.**

This is a research conclusion, not a claim that every market/timeframe is untradeable.

The fixed TF-004 20/5/20 signal shows pockets of historical edge, but the evidence is not robust enough across execution assumptions, costs, markets, time scales, and forward evidence to justify broker execution.

No risk limit is approved by this report.
No broker order was sent.
Live/funded money remains hard locked.

## What was tested

The validation stack now includes:

1. Multi-market historical coverage.
2. Longest practical public daily history.
3. Chronological 70/30 OOS.
4. Expanding-history walk-forward.
5. 27-configuration parameter sensitivity:
   - momentum lookback: 10 / 20 / 40
   - initial stop: 3 / 5 / 10
   - trailing channel: 10 / 20 / 40
6. Cost stress:
   - 0x / 0.5x / 1x / 1.5x / 2x / 3x / 5x.
7. Six chronological regimes.
8. Start-date sensitivity:
   - 0 / 2 / 5 / 10-year offsets.
9. Time-scale aggregation:
   - 1D / 3D / 5D.
10. Monte Carlo bootstrap:
    - 2,000 deterministic resamples per market.
11. Execution timing stress:
    - close entry;
    - next-bar-open entry.
12. Stop execution stress:
    - stop-level fill;
    - gap-aware stop fill.
13. Winner-concentration stress:
    - remove best 1 trade;
    - remove best 3 trades;
    - cap winners at 10R;
    - cap winners at 5R.
14. Crypto data-source cross-check:
    - Yahoo vs Coinbase.
15. Intraday validation:
    - public 1H history;
    - approximate 4H aggregation;
    - OOS + walk-forward;
    - 27-parameter grid;
    - next-open + gap-aware execution.

## Daily historical coverage

| Market | Practical history |
|---|---:|
| EURUSD | 22.82y |
| GBPUSD | 22.82y |
| USDJPY | 29.91y |
| AUDUSD | 20.37y |
| USDCAD | 23.03y |
| USDCHF | 23.03y |
| NZDUSD | 22.82y |
| XAUUSD | 26.07y |
| USOIL | 26.09y |
| BTCUSD | 12.03y |
| ETHUSD | 10.36y |
| US30 | 34.73y |
| NAS100 | 40.98y |
| US500 | 98.74y |

This supersedes treating the earlier 10-year window as the maximum available evidence.

## Daily baseline versus conservative execution

Conservative execution means:
- signal from the completed bar;
- entry at next bar open;
- stop fill is gap-aware.

| Market | Cost mode | Baseline OOS | Baseline WF | Conservative OOS | Conservative WF |
|---|---|---:|---:|---:|---:|
| AUDUSD | RESEARCH_PROXY | -24.85R | -41.90R | -65.11R | -117.48R |
| BTCUSD | RESEARCH_PROXY | +9.73R | +52.58R | -3.91R | +36.67R |
| ETHUSD | GROSS_ONLY | +17.90R | +22.73R | +16.97R | +6.45R |
| EURUSD | RESEARCH_PROXY | +2.19R | -27.54R | -246.17R | -330.49R |
| GBPUSD | RESEARCH_PROXY | -12.99R | -24.69R | -244.06R | -416.16R |
| NAS100 | GROSS_ONLY | +13.17R | +21.10R | +13.35R | +11.36R |
| NZDUSD | GROSS_ONLY | -25.33R | -17.74R | -116.83R | -207.69R |
| US30 | GROSS_ONLY | -0.94R | +32.98R | -4.63R | -2.62R |
| US500 | GROSS_ONLY | +30.69R | +24.20R | +24.25R | +20.35R |
| USDCAD | GROSS_ONLY | -6.42R | +5.27R | -130.14R | -137.32R |
| USDCHF | GROSS_ONLY | +14.80R | +58.67R | -48.18R | -206.11R |
| USDJPY | RESEARCH_PROXY | -10.33R | -10.83R | -65.14R | -219.76R |
| USOIL | RESEARCH_PROXY | +13.97R | +15.24R | -3.38R | -5.37R |
| XAUUSD | RESEARCH_PROXY | +116.17R | +93.20R | -99.15R | -160.51R |

### Important interpretation

Only three daily markets keep both OOS and walk-forward positive under the conservative next-open + gap-aware model:
- ETHUSD
- NAS100
- US500

All three are currently **GROSS_ONLY**.

Therefore there is currently **no broker-cost-aware market with both conservative OOS and conservative walk-forward positive**.

This is the key reason the historical evidence does not validate broker execution.

## Parameter sensitivity

The 27-configuration sweep was used as a stability test, not as a winner-selection search.

Examples:
- BTCUSD: 18/27 combinations had both OOS and WF positive.
- ETHUSD: 26/27.
- NAS100: 26/27.
- US500: 25/27.
- AUDUSD: 0/27.
- NZDUSD: 0/27.
- GBPUSD: 6/27.

Strong parameter neighborhoods are useful evidence, but they do not override missing broker costs or execution-timing failure.

No parameter from this sweep was promoted.

## Cost sensitivity

For RESEARCH_PROXY markets, cost stress extended to 5x.

Examples:
- BTC baseline OOS + WF remained positive through the research 5x cost stress under the optimistic close-entry model.
- USOIL remained positive in both only through approximately 1.5x.
- EURUSD / GBPUSD / USDJPY did not retain both-positive baseline evidence.
- GROSS_ONLY markets are unaffected by this test because their cost profile is zero; their 5x result must not be misrepresented as cost robustness.

## Regime and start-date sensitivity

The strategy is materially regime-dependent.

Examples:
- BTC: 4/6 positive chronological regimes and 4/4 positive start offsets.
- ETH: 6/6 regimes and 4/4 start offsets.
- NAS100: 6/6 regimes and 4/4 start offsets.
- US500: 5/6 regimes and 4/4 start offsets.
- GBPUSD: 0/6 regimes and 0/4 start offsets.
- AUDUSD: 2/6 regimes and 0/4 start offsets.
- NZDUSD: 2/6 regimes and 0/4 start offsets.

Again, ETH/NAS100/US500 remain gross-only.

## Monte Carlo

Each market used 2,000 deterministic bootstrap resamples of historical trade R.

Selected examples:
- ETH: probability of negative total R in bootstrap ≈ 0.4%; p95 max DD ≈ 16.20R.
- NAS100: ≈ 2.6%; p95 DD ≈ 36.29R.
- US500: ≈ 0.2%; p95 DD ≈ 44.31R.
- BTC: ≈ 17.1%; p95 DD ≈ 54.57R.
- EURUSD: ≈ 68.7%; p95 DD ≈ 101.50R.
- GBPUSD: ≈ 96.5%; p95 DD ≈ 90.01R.
- AUDUSD: ≈ 94.8%; p95 DD ≈ 82.41R.

Monte Carlo only resamples observed trade outcomes. It cannot model unknown future structural breaks.

## Winner-concentration stress

Some apparently strong historical results depend heavily on rare large winners.

### Gold

Baseline OOS:
- total: +116.17R;
- best single trade: +112.57R;
- without best trade: +3.60R;
- without best 3 trades: -14.22R;
- cap winners at 5R: -5.65R.

Under next-open + gap-aware execution:
- OOS: -99.15R;
- WF: -160.51R.

Therefore the headline +116R is not robust evidence.

### Bitcoin

Baseline OOS:
- total: +9.73R;
- best trade: +9.11R;
- without best trade: +0.62R;
- without best 3: -13.60R.

This is consistent with trend-following's reliance on large winners, but it also demonstrates concentration risk.

### US500

Baseline OOS:
- total: +30.69R;
- without best trade: +20.45R;
- without best 3: +5.66R.

This is less concentrated than gold, but remains gross-only.

## Crypto data-source cross-check

### BTC 2016 → 2026

Yahoo:
- OOS ≈ +14.01R
- WF ≈ +8.46R
- positive folds: 2/5

Coinbase:
- OOS ≈ +13.93R
- WF ≈ +7.54R
- positive folds: 2/5

The signs and magnitudes are close, reducing concern that the BTC historical result is purely a Yahoo-feed artifact.

### ETH matched window 2017-11-09 → 2026-09-27

Yahoo:
- OOS ≈ +19.05R
- WF ≈ +35.24R
- positive folds: 5

Coinbase:
- OOS ≈ +16.62R
- WF ≈ +31.39R
- positive folds: 4

The two feeds agree directionally on the matched historical window.

ETH remains gross-only for broker-cost purposes.

## Intraday validation

Public Yahoo 1H history returned roughly:
- FX: 12,000 bars;
- crypto: 16,800 bars;
- gold/oil: 13,873 bars;
- US indices: 3,344 bars.

Observed window:
approximately 2024-10-27/28 through 2026-09-25/27.

4H is an approximate aggregation of returned trading-hour bars.

### Conservative 1H

No market with a research cost proxy produced both positive conservative OOS and conservative WF.

Examples:
- BTC: OOS -10.81R, WF +24.09R.
- EURUSD: both strongly negative.
- GBPUSD: both strongly negative.
- USDJPY: both strongly negative.
- Gold: both strongly negative.
- Oil: both strongly negative.

The very large negative R values in several FX 1H runs expose a structural issue:
a signal computed at close can carry a prior stop into the next-open entry with a very small effective stop distance. In R-normalized terms this produces extreme loss geometry.

This is not a reason to invent a minimum stop threshold after seeing the result. It is evidence that TF-004's execution contract is incomplete.

### Conservative approximate 4H

The only both-positive examples were:
- ETH: OOS +7.05R, WF +1.07R.
- USDCAD: OOS +14.59R, WF +4.16R.

Both are GROSS_ONLY.

No research-cost-aware market passed both conservative OOS and WF on 4H.

## What the tests falsified

The following stronger claims are not supported:

- "TF-004 is broadly robust across popular markets."
- "The 10-year positive markets are enough to enable DEMO."
- "Close-entry results survive realistic next-open execution."
- "Gold's large historical R is broadly distributed."
- "Current public-data results establish broker-net profitability."
- "A hard risk profile can be derived from this historical evidence."

## Current evidence boundary

Historical backtesting is now extensive enough to expose the dominant weaknesses of the current method.

The remaining blockers are not solved by repeating more variants of the same historical test:

1. execution semantics need a preregistered redesign;
2. actual broker symbol/cost/margin/tick-value evidence is missing;
3. forward paper journal has not accumulated a meaningful closed-trade sample;
4. The5ers written automation approval is still unverified;
5. risk profile remains unapproved.

## Research decision

**TF-004 remains a research baseline. No promotion to autonomous DEMO.**

Do not retune TF-004 after seeing these results and then call the retuned result independent validation.

A future strategy revision should receive a new preregistered ID/spec and rerun the same validation ladder from the beginning.

## Runtime evidence

Supabase functions:
- `ai-trade-multiasset-backtest` v5
- `ai-trade-robustness-lab` v2
- `ai-trade-intraday-validation` v1

Persistent tables:
- `ai_trade.backtest_runs`
- `ai_trade.robustness_runs`

Robustness batches:
- FX A: COMPLETE 4/4
- FX B + Gold: COMPLETE 4/4
- Crypto + Oil: COMPLETE 3/3
- Indices: COMPLETE 3/3

Execution-realism V2 batches:
- 4/4 COMPLETE

Intraday batches:
- 14/14 COMPLETE

Broker orders:
- false

Live/funded:
- hard locked
