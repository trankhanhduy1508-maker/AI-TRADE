# AI AUTO TRADE — CURRENT STATUS

## North Star

✅ `auto_trade/MASTER_GOAL.md` — autonomous Trend Following + MT5 + Android control.

✅ `auto_trade/BOOTSTRAP.md` — short session bootstrap.

✅ `AGENTS.md` — Superpowers/skill discipline + autonomy + verification rules.

## Current Priority

**P4 - EXIT-MODEL AND DATA-QUALITY VALIDATION - IN PROGRESS (TF-004 PRELIMINARY)**

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

## P4 evidence - channel-trailing exit comparison

- `src/backtest/spec.py` and `src/backtest/engine.py` now support explicit
  `FIXED_RR` (backward-compatible default) and `CHANNEL_TRAILING` exits.
  Channel stops ratchet only from preceding bars and produce no fixed target.
- Regression tests preserve the existing fixed-target behavior; new tests
  verify optional targets, prior-bar-only channel calculation, and monotonic
  ratcheting.
- `backtests/TF004_FX_IS_OOS_2026-08-22.md` records six fixed runs. Two OOS
  partitions were positive and four negative after the `UNVERIFIED` research
  cost proxy; all six ended with an open position.
- H007 remains unvalidated. Hourly trade counts increased materially; this is
  recorded as an observation, not a tuning instruction.
- The full suite was **174 passed** immediately after the exit-model code;
  execution tests require a fresh full-suite verification before commit.

## P5 evidence - MT5 safety boundary (no live/demo activation)

- `src/execution/mt5_adapter.py` adds a dependency-injected MT5 boundary with
  `DISABLED` default, hard-locked `LIVE`, `order_check()` before
  `order_send()`, return-code mapping, and persistent SQLite client-intent
  deduplication.
- `execution/MT5_ADAPTER_IMPLEMENTATION.md` records official MetaQuotes API
  evidence and the exact boundary. No MetaTrader package, terminal, account,
  credential, or broker-specific data was added.
- Four execution tests pass with a fake terminal. Real MT5/demo, reconnect,
  reconciliation, independent risk engine, kill switch, and Android control
  remain unverified workstreams.
- The full suite is now **178 passed** with
  `python -m pytest -q -p no:cacheprovider tests`.

## P6 evidence - recovery, reconciliation, and kill switch contracts

- `src/execution/recovery.py` blocks new risk after disconnect and only clears
  the block after exact local/broker position reconciliation.
- `src/execution/safety.py` persists a kill switch in SQLite; missing state is
  active by default. The safety gate blocks unknown state, stale data,
  disconnects, unreconciled positions, manual pause, and an independent risk
  policy rejection.
- Seven execution tests pass for reconnect gating, mismatch blocking,
  fail-closed unknown state, and persistent kill-switch activation/reset.
- The complete suite is now **181 passed** with
  `python -m pytest -q -p no:cacheprovider tests`.
- A fresh full-suite verification is required before this milestone is
  committed; no demo/live execution was enabled.

## P7 evidence - safety-gated execution handoff

- `src/execution/coordinator.py` now evaluates the independent safety gate
  before calling any broker adapter. Active kill switch and risk-policy blocks
  are tested to prevent adapter calls; an explicitly cleared DEMO gate passes
  the result through without modifying it.
- This is a local contract test only. It does not create an account, connect a
  terminal, choose hard risk limits, or enable live money.
- The complete suite is now **184 passed** with
  `python -m pytest -q -p no:cacheprovider tests`.

## P8 evidence - append-only audit state

- `src/execution/audit.py` persists ordered SQLite audit events and rejects
  sensitive field names before writing. The coordinator records blocked and
  submitted outcomes when an audit log is supplied.
- Execution tests now cover persistence across reopen, sensitive-field
  rejection, and coordinator block-event capture.
- A fresh full-suite verification is required before commit; this remains
  local contract evidence, not broker/demo execution evidence.
- The complete suite is now **187 passed** with
  `python -m pytest -q -p no:cacheprovider tests`.

## P9 evidence - fixed walk-forward robustness

- `src/backtest/validation.py` and `scripts/run_walk_forward.py` provide fixed
  expanding-history, non-overlapping OOS folds without parameter selection.
- `backtests/TF003_TF004_WALK_FORWARD_2026-08-22.md` records twelve strategy /
  symbol / timeframe cases. Only two had positive sums of closed-trade fold
  nets; EURUSD 1H had zero positive folds for both strategies.
- This strengthens the evidence that TF-003/TF-004 have not passed robust
  cross-market/timeframe validation. Costs and data remain unverified.
- The complete suite is now **188 passed** with
  `python -m pytest -q -p no:cacheprovider tests`.

## P10 evidence - Android/control-plane state contract

- `src/control_plane/state.py` provides persistent fail-closed pause/kill state
  and a provider-neutral public `RuntimeHealth` snapshot for a future Android
  client. New installations are paused and kill-switched by default.
- `monitoring/ANDROID_CONTROL_CONTRACT.md` records the public shape and the
  remaining authentication/MT5/runtime gates. No network endpoint or remote
  command path is active.
- This is local contract evidence only; the absent MT5 runtime and broker/demo
  account remain external blockers for live telemetry validation.
- The complete suite is now **191 passed** with
  `python -m pytest -q -p no:cacheprovider tests`.

## P11 evidence - deterministic paper execution path

- `src/execution/paper_adapter.py` now provides a network-free deterministic
  fill adapter using the same persistent duplicate ledger as the MT5 boundary.
- `paper_trading/IMPLEMENTATION_STATUS.md` records the exact local evidence
  and remaining paper gates. An end-to-end test confirms paper order -> safety
  gate -> audit log flow.
- No broker, terminal, credentials, realistic-fill claim, or live-money path
  was added.
- The complete suite is now **194 passed** with
  `python -m pytest -q -p no:cacheprovider tests`.

## P12 evidence - paper mark-to-market and exits

- `PaperBrokerAdapter.process_tick()` now handles deterministic bid/ask
  mark-to-market for long and short positions, closes at declared SL/TP, and
  applies `STOP_FIRST` when both are touched.
- Paper tests cover long stop-first, short target, duplicate protection, and
  the safety-gated audit path. This remains offline simulation, not broker
  evidence.
- The complete suite is now **196 passed** with
  `python -m pytest -q -p no:cacheprovider tests`.

## P13 evidence - official MT5 runtime installation and boundary probe

- Official `mt5setup.exe` was downloaded from the MetaTrader-linked CDN and
  verified with a valid `MetaQuotes Ltd.` Authenticode signature before the
  unattended install to an isolated temporary portable directory.
- The installed terminal is build `6140`; the official Python package is
  `MetaTrader5==5.0.6090`. The terminal starts and completes MQL5 compilation.
- Read-only Python initialization with explicit and auto-discovered terminal
  paths returned `(-10005, 'IPC timeout')`; no order API was called. The
  package/terminal boundary is therefore **unvalidated**, not demo evidence.
- Detailed evidence and official references are in
  `execution/MT5_RUNTIME_VALIDATION_2026-08-22.md`. No account, credential,
  broker server, or live-money capability was added.

## P13 verification

- Runtime evidence is based on fresh installer signature, terminal version,
  terminal log, and Python probe output.
- The full project suite remains **196 passed** from the previous milestone;
  no production strategy or execution code changed in P13.

## P14 evidence - native MQL5 TF-003 boundary

- Added `mql5/Experts/AITradeTrendFollowingEA.mq5`, a deterministic closed-bar
  breakout implementation with ATR stop/target and a fixed `DemoLots` cap.
- The EA is demo-locked by default and requires explicit demo enablement,
  exact demo account mode, terminal connection, terminal trade permission,
  input validation, and spread validation before `CTrade::Buy/Sell`.
- TDD/static contract tests pass for default lock, gate ordering, closed-bar
  data, fixed lot cap, and absence of direct `OrderSend`.
- Official MetaEditor build 6140 compilation produced **0 errors, 0 warnings**
  under X64 Regular. This validates syntax/compile only; the EA has not been
  attached to a chart, connected to an account, or allowed to submit a demo
  order.
- Details are in `execution/MQL5_NATIVE_EA_IMPLEMENTATION.md`.

## P15 evidence - native fail-closed operations hooks

- Added independent common-file kill switch and entry-pause checks to the
  native EA. Missing flags remain active/paused by default; only explicit
  `DISARMED` and `RESUMED` values clear those controls.
- Added a common append-only native audit CSV. New entries are blocked if the
  audit sink cannot be opened; order intent and result are recorded around the
  `CTrade` call.
- Native contract tests now pass **5 passed** and fresh MetaEditor build 6140
  compilation remains **0 errors, 0 warnings** under X64 Regular.
- This is still compile/static evidence only. No demo account, chart attach,
  broker connection, or order submission occurred.

## P16 evidence - native persistent signal reservation

- Added a per-symbol/timeframe Global Variable reservation keyed by the closed
  signal bar. The reservation occurs before `CTrade::Buy/Sell` and is retained
  through ambiguous failures, preventing blind duplicate submission after a
  terminal/process restart.
- Native contract tests now pass **6 passed** and fresh MetaEditor build 6140
  compilation remains **0 errors, 0 warnings** under X64 Regular.
- This remains compile/static evidence only; no account or broker order was
  used.

## P17 evidence - isolated fail-closed tester attempt

- Added `mql5/tester/AITradeTrendFollowingEA_FAIL_CLOSED.ini` with
  `AllowLiveTrading=0`, remote/cloud agents disabled, and the EA's default
  `EnableDemoTrading=false`. The config contains only a synthetic offline
  tester profile marker, not a broker credential.
- Two isolated official terminal copies read the config and started build 6140,
  but Strategy Tester refused to start with
  `tester not started because the account is not specified`.
- No `/login` argument, password, account credential, chart attachment, EA
  tick, order check, or order send was attempted. This is a verified external
  account-context blocker, not demo evidence.
- Continue independent workstreams; do not claim MT5 demo execution until a
  lawful demo account context is supplied outside the repository.

## P18 evidence - independent Python risk engine

- Added `src/execution/risk.py` with explicit hard limits for volume, open
  positions, spread, daily loss, finite market context, and directional SL/TP.
- `ExecutionCoordinator` now invokes the engine before `adapter.submit()` when
  configured; missing risk context and rejected risk decisions are fail-closed
  and auditable.
- Targeted risk/coordinator tests pass **12 passed**. Full-suite verification is
  required before commit, and this work does not change any hard risk limit or
  enable live execution.
- Details are in `execution/RISK_ENGINE_IMPLEMENTATION.md`.

## P19 evidence - local control-plane command audit

- `ControlPlaneState` now persists every local pause, resume, and kill
  activation in `control_events` with command, `LOCAL` source, note, and UTC
  timestamp. Empty pause/kill reasons are rejected.
- `read_events()` exposes a provider-neutral audit shape for a future
  authenticated Android API; no network endpoint or remote control path was
  enabled.
- Control-plane tests now pass **5 passed** for this module. Full-suite
  verification is required before commit.

## P20 evidence - persistent recovery state

- `PersistentRecoveryState` now stores connection/reconciliation gates in a
  SQLite row with UTC update time. A new process reads prior state for
  evidence but resets its runtime gate fail-closed; it does not inherit
  permission to open risk unless it reconnects and records exact reconciliation.
- Disconnect persists `connected=false` and `reconciled=false`; a restored
  connection only records the reconciliation result supplied by the caller.
- `is_stale()` exposes a deterministic UTC freshness check for heartbeat
  monitoring and rejects invalid age/time inputs.
- Recovery tests pass **5 passed**, including persistence across reopen,
  fail-closed reset after disconnect, and stale-heartbeat detection.
  Full-suite verification is required before this milestone is committed.
- This remains local state evidence. Broker reconciliation, MT5 demo forward
  trading, crash/restart behavior in a real terminal, and 24/7 reliability
  remain unverified.

## Next Autonomous Action

Keep H001, H006, and H007 unvalidated. Continue MT5 reliability work through a
native MQL5, safety-gated demo boundary and real-runtime discovery plus
reconnect/reconciliation, risk, kill-switch, and monitoring contracts while
seeking a lawful broker/demo data path. Do not infer demo or live readiness
from the Founder login statement, preliminary strategy results, or terminal
installation alone.

## Live Trading Gate

🔒 Live-money trading vẫn khóa theo `PROJECT_CONTEXT.md`.

Goal dài hạn có MT5 autonomous execution, nhưng giai đoạn hiện tại chỉ research/backtest/paper/demo theo governance.
