# IS/OOS and Cost Realism Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task.

**Goal:** Add chronological IS/OOS validation and explicit non-zero research cost assumptions without introducing capital-risk sizing or live execution.

**Architecture:** Keep the deterministic engine as the single simulator. Add an injectable `CostModel` that separates theoretical gross price PnL from net price PnL, and add a partition runner that warms the evaluator on all prior closed bars while allowing new entries only inside the requested IS or OOS interval. Use a fixed, versioned research cost profile per symbol; label it `UNVERIFIED` until broker-specific evidence exists.

**Tech Stack:** Python 3.12 standard library, pytest, existing CSV loader and stateful evaluator.

**Spec:** `backtests/BACKTEST_STANDARD.md`, `BACKTEST_ENGINE.md`, `auto_trade/MASTER_GOAL.md` validation ladder.

## Global Constraints

- Chronological partitions only; OOS bars cannot influence IS signals or parameters.
- Warm-up may use earlier closed bars, but OOS entries begin at the split index.
- Cost assumptions are explicit, non-zero research proxies and are not broker facts.
- Results remain price-unit/signal-only; no capital PnL, leverage, lot sizing, or hard-risk changes.
- Do not optimize parameters on the downloaded sample; the existing TF-001 spec remains fixed.
- No MT5/live code or credentials.

---

### Task 1: Define cost and partition contracts with failing tests

**Files:**
- Create: `tests/backtest/test_validation.py`
- Modify: `tests/backtest/test_engine.py`

**Interfaces:**
- `CostModel(spread_price, commission_price, slippage_price, swap_price_per_bar, profile_id)`.
- `run_backtest(..., cost_model=CostModel.zero())` preserves unit-test compatibility while real research runs pass a non-zero profile.
- `run_is_oos(bars, spec, evaluator_factory, split_index, cost_model)` returns separate IS/OOS `BacktestResult` values.

- [ ] **Step 1: Write cost accounting tests**

Create one deterministic trade with a known theoretical gross PnL and assert `Trade.gross_pnl_price`, `Trade.cost_price`, net `pnl_price`, and result metrics reconcile exactly.

- [ ] **Step 2: Write chronological partition tests**

Use an evaluator that records prefixes and emits signals after a known split. Assert the OOS evaluator sees only bars up to the current bar, no OOS trade has an entry before the split, and the IS result does not close a position using OOS bars.

- [ ] **Step 3: Run focused tests and confirm RED**

Run:

```powershell
python -m pytest -q -p no:cacheprovider tests/backtest/test_validation.py tests/backtest/test_engine.py
```

Expected: import failure because `CostModel` and `run_is_oos` do not exist yet.

### Task 2: Implement explicit cost accounting

**Files:**
- Create: `src/backtest/costs.py`
- Modify: `src/backtest/types.py`
- Modify: `src/backtest/engine.py`

**Interfaces:**
- `CostModel.zero() -> CostModel` is only a unit-test default.
- `CostModel.total(spread_price, holding_bars) -> float` returns spread + commission + swap; slippage is measured from theoretical versus executed prices in the engine.
- `Trade` records `gross_pnl_price`, net `pnl_price`, `cost_price`, and `holding_bars`.

- [ ] **Step 1: Implement validation and immutable cost model**

Reject negative costs and blank profile IDs. Keep zero available only for deterministic unit fixtures.

- [ ] **Step 2: Integrate gross/net reconciliation**

Compute theoretical exit-minus-entry PnL, executed PnL after slippage, explicit spread/commission/swap, and net PnL. Add aggregate gross PnL and total costs to metrics without changing existing keys.

- [ ] **Step 3: Run the cost tests GREEN**

Run the focused test file and existing engine tests. Confirm no hard risk policy file changes.

### Task 3: Implement chronological IS/OOS runner and CLI

**Files:**
- Create: `src/backtest/validation.py`
- Modify: `src/backtest/engine.py`
- Modify: `scripts/run_signal_backtest.py`

**Interfaces:**
- `run_backtest(..., signal_start_index=0, signal_end_index=None)` updates a stateful evaluator on every bar but accepts entries only in the requested interval.
- `run_is_oos(...)` uses a fresh evaluator for each partition, passes full prior history for warm-up, and sets OOS `signal_start_index=split_index`.
- CLI accepts `--split-fraction` and fixed cost arguments/profile, and prints IS/OOS results with the split timestamp.

- [ ] **Step 1: Add signal-window gating**

Discard pre-window signals while still invoking the evaluator so point-in-time cache state is warmed. Stop the IS run at the split and never use OOS bars to close IS results.

- [ ] **Step 2: Add the partition runner**

Validate `0 < split_index < len(bars)`, run IS on `[0, split_index)`, and run OOS on the full bar sequence with entries allowed from `split_index` onward.

- [ ] **Step 3: Add CLI reporting**

Print data range, split timestamp, cost profile, IS metrics, OOS metrics, and explicit `oos_status` (`PRELIMINARY` when trade count is below 30 or costs are unverified).

- [ ] **Step 4: Run focused and full tests GREEN**

Run the validation tests, then `python -m pytest -q -p no:cacheprovider tests`.

### Task 4: Run fixed-profile evidence and publish

**Files:**
- Create: `backtests/cost_profiles/research_fx_assumption_v1.json`
- Create: `backtests/TF001_FX_IS_OOS_2026-08-22.md`
- Modify: `research/EXPERIMENT_LOG.md`
- Modify: `research/HYPOTHESES.md`
- Modify: `auto_trade/CURRENT_STATUS.md`
- Modify: `reports/P1_DETERMINISTIC_BACKTEST_ENGINE_2026-08-22.md`

- [ ] **Step 1: Record the hypothesis before running the report**

Use existing H001 from `research/HYPOTHESES.md`; do not alter strategy parameters based on the first result. Record that this run tests the fixed TF-001 implementation across the chronological split.

- [ ] **Step 2: Run all six local datasets with the fixed profile**

Run three symbols × two intervals with a 70/30 chronological split. Record exact rows, split timestamp, costs, trade counts, net/gross PnL, max drawdown, and whether OOS meets the 30-trade preliminary threshold.

- [ ] **Step 3: Update evidence without overclaiming**

Mark OOS as preliminary when applicable. Do not call any result profitable or live-ready. Keep `UNVERIFIED` on the research proxy profile.

- [ ] **Step 4: Verify, commit, and push**

Run full tests, `git diff --check`, secret scan, inspect changed files, commit with `feat: add chronological oos cost model`, and push the existing branch.
