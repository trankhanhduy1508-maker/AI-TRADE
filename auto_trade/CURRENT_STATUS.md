# AI AUTO TRADE — CURRENT STATUS

## North Star

✅ `auto_trade/MASTER_GOAL.md` — autonomous Trend Following + MT5 + Android control.

✅ `auto_trade/BOOTSTRAP.md` — short session bootstrap.

✅ `AGENTS.md` — Superpowers/skill discipline + autonomy + verification rules.

## Current Priority

**P3 - INDEPENDENT STRATEGY VALIDATION - IN PROGRESS (TF-003 PRELIMINARY)**

P0 knowledge audit, P1 deterministic engine work, and P2 chronological IS/OOS
cost-accounting work are complete at their current evidence boundaries. TF-003
is now the independent comparison baseline; it has not passed validation.

**P0 — TREND FOLLOWING KNOWLEDGE AUDIT — COMPLETE (CODE VERIFIED)**

Trước khi mở rộng MT5/execution, audit `knowledge/TREND_FOLLOWING.md` và các knowledge hiện có theo Michael W. Covel `Trend Following`, ưu tiên Fifth Edition.

Yêu cầu:
- xác định source nào thực sự đã có;
- không tuyên bố đã ingest full book nếu chưa có full lawful copy;
- bổ sung provenance cho từng nhóm kiến thức;
- tách book/author knowledge khỏi engineering derivation;
- map kiến thức thành strategy concepts có thể kiểm chứng/backtest;
- không chép dài nguyên văn nội dung có bản quyền.

### P0 evidence

- `knowledge/COVEL_TREND_FOLLOWING_PROVENANCE.md` là registry nguồn + claim
  matrix. Nó ghi rõ Fifth Edition metadata/preview có thể kiểm chứng, nhưng repo
  chưa có full lawful copy nên chưa gắn `VERIFIED_FROM_BOOK` cho claim nội dung.
- `knowledge/TREND_FOLLOWING.md` đã được chuẩn hóa theo các nhãn provenance và
  tách author material, primary research, implementation derivation, unverified.
- `reports/P0_COVEL_TREND_FOLLOWING_AUDIT_2026-08-22.md` ghi evidence ledger,
  gap và acceptance checklist.
- `python -m pytest -q -p no:cacheprovider tests` → **155 passed**.
- Kiểm tra required paths, provenance labels, internal links và `git diff --check`
  đã đạt. Đây là code/documentation verification, chưa phải backtest hay
  production/live evidence.

### P0 boundary

- Không đổi `risk/RISK_POLICY.md`, không chốt hard risk limits.
- Không thêm MT5/live-order code, không mở live-money trading.
- Không claim AI-TRADE đã chứng minh profitability; strategy-specific backtest
  vẫn là bước sau.

## P0 Historical Next Autonomous Action

P0 đã được audit và chuẩn hóa; bước kế tiếp là viết machine-readable strategy
spec rồi mới backtest theo validation ladder trong `MASTER_GOAL.md`.

Các hạng mục cũ trong root `CURRENT_STATUS.md` vẫn là backlog/evidence hiện hữu, nhưng **không được ưu tiên hơn P0 này** cho đến khi knowledge audit được cập nhật rõ ràng.

## P1 evidence

- `strategies/TF_001_BREAKOUT_PULLBACK.json` defines the first machine-readable
  contract. It remains `SIGNAL_ONLY`; market/timeframe and cost model are
  explicitly `UNVERIFIED`.
- `src/backtest/` implements closed-bar-only evaluation, no future-bar exposure,
  one-open-position simulation, conservative `STOP_FIRST` ambiguity handling,
  transparent end-of-data open-position state, and price-unit KPIs.
- `tests/backtest/` covers the contract and invariants; the full suite is now
  **166 passed** with `python -m pytest -q -p no:cacheprovider tests`.
- `src/rule_engine/incremental.py` and the stateful backtest adapter now cache
  confirmed point-in-time swings. Prefix parity passed and full 1H runs over
  12k+ bars complete in about 1.35-2.35 seconds per symbol.
- `scripts/fetch_yahoo_chart.py` successfully fetched 3 FX pairs at 1D and 1H
  for local research. Data is not committed because this public research feed
  is not a broker execution feed.
- The dated P1 report records data quality, smoke results, runtime limitation,
  and the boundary between engine verification and strategy evidence.

### Current P1 boundary

- No capital PnL, leverage, lot sizing, hard risk limit, MT5 execution, or live
  trading was added.
- Full 1H runs now complete after incremental caching, but remain full-sample
  diagnostics only; IS/OOS, realistic costs, and capital-risk PnL are still
  unverified.

### Historical pre-cache P1 boundary

- No capital PnL, leverage, lot sizing, hard risk limit, MT5 execution, or live
  trading was added.
- Full 1D TF-001 runs produced zero qualifying trades on the downloaded sample;
  this is not a profitability claim.
- Full 1H TF-001 runs exposed an O(n²) runtime bottleneck in the current rule
  engine adapter and were stopped; bounded 1H smoke runs are recorded only as
  diagnostic evidence, not out-of-sample validation.

## P2 evidence - IS/OOS and cost realism

- `src/backtest/costs.py` now separates theoretical gross price PnL from net
  price-unit PnL after explicit spread, commission, slippage, and swap proxies.
- `src/backtest/validation.py` runs chronological 70/30 IS/OOS partitions with
  warm-up history and OOS entry gating.
- `backtests/TF001_FX_IS_OOS_2026-08-22.md` records all six runs. Daily data had
  no qualifying trades; all three hourly OOS samples were net negative after
  the fixed `UNVERIFIED` research cost profile.
- Cost/partition tests pass and the complete repository suite is now **168
  passed** with `python -m pytest -q -p no:cacheprovider tests`.
- H001 remains unvalidated. No parameter tuning was performed after observing
  the result.

## P3 evidence - independent time-series momentum baseline

- `strategies/TF_003_TIME_SERIES_MOMENTUM.json` defines a separate price-only
  time-series momentum evaluator. Its 20-bar lookback, five-bar stop window,
  and fixed target are implementation derivations, not Covel book parameters.
- `src/strategies/time_series_momentum.py` uses only closed-bar history and
  excludes the signal bar from the stop window. Unit tests cover lookback,
  direction, stop geometry, and unclosed-bar rejection.
- `backtests/TF003_FX_IS_OOS_2026-08-22.md` records all six fixed runs. Three
  OOS partitions were positive and three negative after the declared fixed
  `UNVERIFIED` research cost proxy; all six ended with an open position at the
  data boundary.
- The full suite is now **172 passed** with
  `python -m pytest -q -p no:cacheprovider tests`.
- H006 remains unvalidated. No retuning was performed after observing the
  result, and no MT5/demo execution was added.

## Next Autonomous Action

Keep H001 and H006 unvalidated. Research a broker/demo data path and specify a
separate channel/trailing-exit engine capability so the next comparison can
test “let profits run” without silently changing either existing result.
Repeat validation with broker-specific costs before any MT5-demo expansion.

## Live Trading Gate

🔒 Live-money trading vẫn khóa theo `PROJECT_CONTEXT.md`.

Goal dài hạn có MT5 autonomous execution, nhưng giai đoạn hiện tại chỉ research/backtest/paper/demo theo governance.
