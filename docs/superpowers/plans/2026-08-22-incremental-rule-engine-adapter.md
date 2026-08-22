# Incremental Rule-Engine Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task.

**Goal:** Remove the O(n²) trend/structure rescans from the TF-001 backtest adapter while preserving the existing point-in-time rule semantics.

**Architecture:** Add a stateful `PointInTimeRuleCache` that confirms a swing only after its configured right-hand bars exist, exactly matching the existing strict swing comparisons. Extend the existing scoring/market-structure interfaces with optional cached features, preserving all current callers. Use a stateful `RuleEngineSignalEvaluator` in the CLI; keep the public stateless adapter for compatibility.

**Tech Stack:** Python 3.12 standard library, existing `Bar`/`RuleResult` contracts, pytest, cProfile for evidence.

**Spec:** `auto_trade/MASTER_GOAL.md` validation ladder and `backtests/BACKTEST_ENGINE.md` closed-bar/no-lookahead requirements.

## Global Constraints

- Only closed bars may influence a signal.
- A swing is usable only after its right-hand confirmation window is present.
- Signal generation remains separate from capital-risk sizing and hard risk limits.
- Existing public rule-engine APIs remain backward compatible.
- No live MT5 code, credentials, account access, or risk-policy changes.
- Evidence must distinguish parity/performance verification from strategy profitability.

---

### Task 1: Lock parity requirements with failing tests

**Files:**
- Create: `tests/rule_engine/test_incremental_features.py`
- Modify: `tests/backtest/test_engine.py`

**Interfaces:**
- The tests will import `PointInTimeRuleCache` and `RuleEngineSignalEvaluator` after their contracts are defined.

- [ ] **Step 1: Write the failing parity test**

```python
def test_incremental_features_match_full_scan_at_every_closed_bar():
    cache = PointInTimeRuleCache(n=2)
    for index in range(len(bars)):
        history = tuple(bars[: index + 1])
        cached = cache.update(history)
        direct_trend = trend_detection.evaluate(list(history), n=2)
        assert cached.trend_result == direct_trend
        direct_levels = market_structure._find_last_swing_levels(list(history), n=2)
        assert cached.swing_levels == direct_levels
```

- [ ] **Step 2: Add a no-future-confirmation test**

Use a center bar that becomes a strict swing only when its two right-hand bars arrive. Assert the cache does not expose it before that bar count and does expose it afterwards.

- [ ] **Step 3: Add an adapter parity test**

Run a short deterministic fixture through the stateful adapter and a fresh full-scan adapter at each prefix. Assert direction, stop, target, and score are identical whenever either adapter emits a signal.

- [ ] **Step 4: Run the new tests and confirm RED**

Run:

```powershell
python -m pytest -q -p no:cacheprovider tests/rule_engine/test_incremental_features.py tests/backtest/test_engine.py
```

Expected: collection or import failure because the new cache/evaluator contracts do not exist yet.

### Task 2: Implement point-in-time cached trend and structure features

**Files:**
- Create: `src/rule_engine/incremental.py`
- Modify: `src/rule_engine/market_structure.py`

**Interfaces:**
- `PointInTimeRuleCache(n: int = 2)` stores only confirmed swing values and counters.
- `PointInTimeRuleCache.update(history: Sequence[Bar]) -> CachedRuleFeatures` accepts the append-only prefixes supplied by `run_backtest`.
- `CachedRuleFeatures.trend_result: RuleResult` and `.swing_levels: tuple[float | None, float | None]` are the reusable features.
- `market_structure.evaluate(..., swing_levels=None)` uses supplied levels when present and preserves old full-scan behavior when omitted.

- [ ] **Step 1: Implement the minimal cache**

When a new bar arrives, confirm candidate index `len(history) - n - 1`. Compare it strictly against `n` bars on both sides, append confirmed highs/lows, update HH/HL/LH/LL counters, and derive the same status/score/reject/detail fields as `trend_detection.evaluate`.

- [ ] **Step 2: Implement cached structure levels**

Update the latest confirmed swing high/low only when the newly confirmed candidate qualifies. Return `(None, None)` until the existing full scan would return no levels.

- [ ] **Step 3: Add the optional structure-level fast path**

Change only the internal level lookup branch in `market_structure.evaluate`; the status, score, rejection, and detail logic must remain unchanged.

- [ ] **Step 4: Run parity tests and the existing rule-engine suite**

Run the focused tests first, then `python -m pytest -q -p no:cacheprovider tests/rule_engine`.

### Task 3: Integrate the cache without changing signal semantics

**Files:**
- Modify: `src/rule_engine/scoring.py`
- Modify: `src/backtest/engine.py`
- Modify: `scripts/run_signal_backtest.py`

**Interfaces:**
- `evaluate_setup(..., trend_result=None, swing_levels=None)` accepts optional cached features while preserving all existing positional arguments.
- `RuleEngineSignalEvaluator` owns one `PointInTimeRuleCache` and implements `__call__(history, spec) -> Signal | None`.
- `rule_engine_signal(history, spec)` remains available as a stateless compatibility wrapper.

- [ ] **Step 1: Add optional scoring inputs**

Use the supplied trend result instead of invoking RULE_001 and pass supplied swing levels into RULE_002. All downstream rules, thresholds, spread input, and signal-only boundaries remain unchanged.

- [ ] **Step 2: Add stateful evaluator and switch the CLI**

The CLI creates one `RuleEngineSignalEvaluator` per backtest run, ensuring cache state is monotonic and never shared across instruments/timeframes.

- [ ] **Step 3: Run the adapter parity test RED/GREEN cycle**

Confirm the test written in Task 1 fails before integration and passes after it. Run the full repository suite after the focused tests pass.

### Task 4: Benchmark and document the milestone

**Files:**
- Modify: `reports/P1_DETERMINISTIC_BACKTEST_ENGINE_2026-08-22.md`
- Modify: `auto_trade/CURRENT_STATUS.md`

- [ ] **Step 1: Run fresh benchmarks**

Run 1H bounded 1,000-bar and full 12k-bar smoke commands for all three downloaded research files. Record wall time, rows, trades, open-position state, and any data-cleaning counts. Do not label them OOS or profitability evidence.

- [ ] **Step 2: Verify no-lookahead and API compatibility**

Run the full suite, inspect `git diff --check`, scan changed files for secrets, and compare the cached/full adapter outputs on the same prefixes.

- [ ] **Step 3: Update status and report**

Record the measured runtime change, parity result, remaining OOS/cost-realism gap, and next priority. Keep risk policy and live gate unchanged.

- [ ] **Step 4: Commit and push**

```powershell
git add src/rule_engine/incremental.py src/rule_engine/market_structure.py src/rule_engine/scoring.py src/backtest/engine.py scripts/run_signal_backtest.py tests/rule_engine/test_incremental_features.py tests/backtest/test_engine.py auto_trade/CURRENT_STATUS.md reports/P1_DETERMINISTIC_BACKTEST_ENGINE_2026-08-22.md docs/superpowers/plans/2026-08-22-incremental-rule-engine-adapter.md
git commit -m "perf: cache point-in-time rule engine features"
git push origin HEAD:codex/p0-covel-knowledge-audit
```
