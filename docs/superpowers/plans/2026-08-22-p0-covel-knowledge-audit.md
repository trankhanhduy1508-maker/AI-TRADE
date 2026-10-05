# P0 Covel Trend Following Knowledge Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Audit and upgrade the canonical Trend Following knowledge base with traceable provenance, while keeping book/author claims separate from engineering and backtest choices.

**Architecture:** `knowledge/TREND_FOLLOWING.md` remains the canonical conceptual summary. A separate provenance registry records source identity, evidence level, claim scope, and implementation derivation. No MT5, live execution, hard risk limit, or model-training behavior changes in P0.

**Tech Stack:** Markdown, repository-local validation scripts/pytest, Git, authoritative public web sources from Michael Covel and primary research papers.

**Spec:** `auto_trade/MASTER_GOAL.md` and `auto_trade/CURRENT_STATUS.md`

## Global Constraints

- P0 must complete before MT5/execution expansion.
- Do not claim full-book ingestion without a full lawful copy.
- Use provenance labels: `VERIFIED_FROM_BOOK`, `VERIFIED_FROM_AUTHOR`, `VERIFIED_FROM_PRIMARY_RESEARCH`, `IMPLEMENTATION_DERIVATION`, `UNVERIFIED`.
- Do not copy long copyrighted passages; summarize in original Vietnamese.
- Do not change hard risk limits or unlock live-money trading.
- Keep the deterministic research/backtest boundary and distinguish evidence levels.

---

### Task 1: Provenance registry and audit report

**Files:**
- Create: `knowledge/COVEL_TREND_FOLLOWING_PROVENANCE.md`
- Create: `reports/P0_COVEL_TREND_FOLLOWING_AUDIT_2026-08-22.md`
- Create: `docs/superpowers/plans/2026-08-22-p0-covel-knowledge-audit.md`

**Interfaces:**
- Consumes: `auto_trade/MASTER_GOAL.md`, `auto_trade/CURRENT_STATUS.md`, existing `knowledge/*.md`, official Covel source pages/PDF, primary research papers.
- Produces: a source registry and claim matrix that later knowledge edits can reference without inventing numeric parameters.

- [ ] Record lawful source availability, including Fifth Edition bibliographic metadata and the absence of a full lawful book copy in the workspace.
- [ ] Map the required domains (reaction, price, entries/exits, loss/profit asymmetry, sizing/volatility, portfolio, behavior, scientific testing, crisis behavior, evaluation) to provenance labels and source URLs.
- [ ] Mark repo-specific HH/HL, BOS/CHoCH, EMA, volume, thresholds, and timeframe choices as implementation derivations or unverified until independently tested.
- [ ] Record audit gaps and the exact next evidence needed.

### Task 2: Canonical Trend Following knowledge upgrade

**Files:**
- Modify: `knowledge/TREND_FOLLOWING.md`
- Modify: `knowledge/AI_DESIGN_PRINCIPLES.md`
- Modify: `knowledge/MARKET_WIZARDS_LESSONS.md`

**Interfaces:**
- Consumes: `knowledge/COVEL_TREND_FOLLOWING_PROVENANCE.md`.
- Produces: Vietnamese canonical prose with inline provenance references and explicit separation between author philosophy, research evidence, and repository implementation.

- [ ] Replace unsupported or overly broad claims with scoped statements that identify whether they are Covel author material, primary research, repo policy, or an unverified hypothesis.
- [ ] Add a deterministic concept map: observed market data -> trend qualification -> entry/exit rule -> independent risk gate -> evaluation, without assigning Covel ownership to repo parameters.
- [ ] Preserve the existing architecture and safety boundary; do not add MT5 or live-order code.
- [ ] Add an explicit non-claim section covering no guarantee of profitability, market/timeframe non-generalization, and no full-book ingestion claim.

### Task 3: Verification and status synchronization

**Files:**
- Modify: `auto_trade/CURRENT_STATUS.md`
- Test: repository Markdown/provenance validation commands and the existing pytest suite.

**Interfaces:**
- Consumes: Tasks 1-2 outputs and fresh test results.
- Produces: current-only status describing what is verified, what remains unknown, and the next P1 action.

- [ ] Validate every provenance label, source URL, internal path, and required domain mapping.
- [ ] Run the repository tests and record the exact command/result; distinguish code-verified documentation checks from runtime or trading evidence.
- [ ] Update status only after verification, leaving live-money trading locked.
- [ ] Commit the P0 changes and push the isolated branch; verify the remote branch points to the commit.
