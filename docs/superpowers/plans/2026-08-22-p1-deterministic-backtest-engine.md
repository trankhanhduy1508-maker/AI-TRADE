# P1 Deterministic Backtest Engine Implementation Plan

> **For execution:** use `superpowers:executing-plans` and `superpowers:test-driven-development`.

**Goal:** Create the first deterministic, signal-only backtest path for the documented TF-001 strategy without introducing capital-risk assumptions or live MT5 behavior.

**Scope:** Machine-readable strategy configuration, dependency-injected signal evaluation, closed-bar-only event processing, conservative stop/target simulation, KPI calculation, and evidence-backed tests/reports. Historical-data performance claims remain blocked until lawful, reproducible OHLCV data is available.

**Step 1 — Define the contract with tests first**

- Add tests for strategy-spec loading and validation.
- Add tests proving closed-bar enforcement, no future-bar access, no overlapping positions, and deterministic same-bar stop-first behavior.
- Add KPI assertions for trade count, win rate, net price-unit PnL, and drawdown.
- Run the targeted tests and capture the expected RED state before implementation.

**Step 2 — Implement the smallest deterministic engine**

- Add immutable backtest/spec/trade result types.
- Implement JSON strategy-spec loading with explicit provenance and signal-only mode.
- Implement a backtest loop that exposes only the current/past bars to the evaluator, opens at a closed-bar close, evaluates exits only on later bars, and records conservative stop-first ambiguity.
- Keep the evaluator injectable; provide the TF-001 adapter through the existing rule engine without moving risk decisions into the signal layer.

**Step 3 — Verify and document boundaries**

- Run targeted tests, then the complete existing suite with cache disabled.
- Attempt a lawful reproducible historical-data fetch; if unavailable, record the exact blocker and do not call synthetic results a historical backtest.
- Update `auto_trade/CURRENT_STATUS.md` and add a dated P1 evidence report.

**Step 4 — Publish the verified increment**

- Review the diff for secrets, lookahead, risk-limit changes, and unsupported performance claims.
- Commit the P1 implementation and evidence, then push the existing branch.
