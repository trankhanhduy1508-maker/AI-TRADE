# CWS AI Trade — Self-Learning Research Checkpoint

Date: 2026-09-28
Branch: codex/p0-covel-knowledge-audit
Starting handoff checkpoint: 6ba79fdc7395419a2511ae4e54eb689ff2c38b5e

## Verified grounding

- Read the canonical Founder intent, Web App handoff, Masterbook V3 distilled, research corpus, Google Sites/Web App README, and the multi-asset report.
- Supabase project oziktadfeenydvgobudr reports ACTIVE_HEALTHY. Edge Function cws-ai-trade-site reports ACTIVE v7; presence is **not** a substitute for a fresh HTTP or Android-device test.
- Read-only SQL against ai_trade.runtime_config confirmed: enabled=false, demo_send_enabled=false, risk_profile_approved=false. No execution, risk or The5ers setting was changed.
- ai_trade.training_replay_trades contains 140 historical replay trades (2019-10-02 through 2026-09-23). This is **not** a versioned, approved closed-bar OHLCV training dataset.
- 14-market historical backtest reports exist. Reported GROSS_ONLY and RESEARCH_PROXY metrics must not be represented as realized broker-net performance.
- Google Drive search for "Trading Masterbook", "AI TRADE" and "Trading" returned no available file. The public distilled Markdown is **not** the complete Founder EPUB.
- Google Sites owned by Founder is not verified as published. Source README already reports PWA v7; actual Android install/offline end-to-end remains pending.

## Implemented in this checkpoint

Files:
- src/self_learning/pipeline.py
- src/self_learning/__init__.py
- tests/self_learning/test_pipeline.py

Research-only offline gates:
1. Stage licensed, source-hashed text metadata in exclusive-write QUARANTINED records. Each item records source path, rights reference, license, kind, timestamp, market, timeframe and evidence level. No automatic approval or production promotion.
2. Validate closed chronological OHLC bars and source/cost provenance. Fail closed on duplicate times, invalid prices, incomplete bars, unknown rights or missing cost assumption.
3. Construct versioned research-only dataset; features use information at closed bar t; label uses the NEXT bar's open-to-close return after an explicit research cost assumption. Do not call the result broker-net P/L.
4. Chronological train/validation/OOS partitions with one-sample purge at each boundary for the one-bar label horizon. No random shuffle.
5. Default inference contract returns MODEL_NOT_TRAINED, ABSTAIN and LOCKED. It contains no broker/order route.

## Test evidence and limitations

Command in an isolated cloud/container workspace reproducing the committed source and tests:
PYTHONPATH=. python -m pytest -q tests/self_learning/test_pipeline.py

Result: **9 passed**. Tests exercise synthetic fixtures **only** to test validation, chronology, quarantine, missing values and fail-closed behavior. No simulated fixture result is a model performance result. GitHub CI and production deployment were not run by these tests.

**BLOCKED: model training, calibrated scores, OOS/WF model evaluation and paper-trading comparison** until an actual licensed OHLCV snapshot with price provider, complete timestamps, version and cost evidence is available and validated. Do not use replay trade count as a substitute for bar-level provenance. No candidate model artifact or production model was created.

**PENDING: fresh live HTTP/Android visual verification**, Google Sites publication with authorized editing session, broker-aligned transaction-cost evidence, independently approved model and paper-forward evidence. The Edge Function was not redeployed by this change.

## Next exact action

Ingest a genuinely permitted closed-bar OHLCV snapshot with an explicit rights/reference and cost profile, then build a fixed chronological research dataset and separately train a lightweight candidate. Pre-register baseline, OOS, walk-forward and costs before inspecting holdout results. Keep production inference ABSTAIN and all execution gates locked until independently approved.

## Source registry linked

\`knowledge/self_learning/SOURCE_REGISTRY_V1.json\` pins the three already-verified GitHub blobs (CWS Masterbook V3 **distilled**, practitioner registry, CWS 10-year backtest report), their rights scope and quarantine status. Only CWS-authored summaries/report text is covered by CWS_OWNED; third-party full books, 49-page EPUB and third-party raw market data are **not** ingested or relicensed. Git blob SHA-1 identifies the source; \`stage_knowledge\` independently creates the file SHA-256 once the verified repository source is available to the offline runner. No source was automatically approved or used to train model weights.

## 2026-09-28 continuation — fixed, pre-registered offline ML candidate code

- Added \`src/self_learning/model.py\` with a deterministic standard-library logistic baseline, pinned feature list/hyperparameters, train-only normalization, chronological splits and pre-OOS expanding walk-forward folds.
- Added \`tests/self_learning/test_model.py\`: deterministic candidate, source/version integrity, positive/negative license and cost gate, tamper rejection, abstention and zero broker orders.
- Updated \`src/self_learning/pipeline.py\`: dataset now carries its exact source metadata and declared 1x proxy cost; \`dataset_version\` hashes the full snapshot, and the candidate refuses mutated rows. 2x cost stress is actually applied to selected research returns.
- Pre-registered all details at \`research/SELF_LEARNING_BASELINE_PREREG_2026-09-28.md\`.
- Offline unit tests use explicitly synthetic TEST-market fixture bars to verify computation; these fixtures are **not evidence of trading or model profitability**.
- Actual model weights on real data: **BLOCKED until source license, immutable licensed OHLC series, and cost provenance have been independently verified**. Yahoo-derived last-ten-per-market replay results are inadequate for this specific bar-level baseline.
- Public website and PWA deployment remain unchanged by this Python research-code commit; model status stays NOT_TRAINED/ABSTAIN. All existing execution controls stay locked.

## 2026-09-28 — verified Supabase PWA v8 read-only UI

- Github source commit: `7798cc4abe4ad6a1e5adabc30e3267b120170765`. Manual deploy of `cws-ai-trade-site` returned ACTIVE v8, function bundle SHA-256 `b6f7ad751142d6e8ff5042bb2820d7e946f44a0318ea4aff006d3016c0ea6bf6`.
- Pre-deploy check: v7 live edge source matched GitHub v7 bundle; GitHub v8 changed only bundled `index.html`. `styles.css`, `portfolio.js`, `app.js`, `pwa.js`, `sw.js`, manifest, icon code and Deno configuration unchanged.
- Post-deploy independent Supabase function readback: ACTIVE v8 with source that includes `MODEL_NOT_TRAINED`; independent live HTML fetch confirms `MODEL_NOT_TRAINED`, `CHƯA HUẤN LUYỆN`, `ABSTAIN · Gate: LOCKED` in the CWS Trading Engine read-only panel.
- Four live HTTP GETs had no fetch errors: health (publicReadOnly=true/liveMoneyLocked=true), app HTML, PWA manifest, portfolio.js. No Android physical-device test was performed.
- Python research tests rerun: **13 passed**, `python -m compileall -q src/self_learning` passed. Tests are **synthetic fixture validation only**. NO model was trained on real licensed market OHLCV, no real-data OOS/WF/paper results and no broker-net claim.
- Supabase read-only SQL after deployment: `enabled=false; demo_send_enabled=false; risk_profile_approved=false`.
- Financial data rights remain an actual blocker to real ML training: FRED and broker/redistributor datasets cannot be assumed available for CWS model training solely because their prices can be downloaded; sample provider GitHub MIT software licenses do not independently establish rights over underlying broker-fed data. Do not turn an unverified market feed into `PERMISSION_GRANTED`.
- Google Site Founder publish, Android hardware QA, APK build/signing and real-data candidate evaluation remain unverified; this checkpoint only marks completed, independently tested surfaces as PASS.
