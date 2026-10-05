# CWS ML — ECB EUR/USD reference-rate experiment, pre-registered

Protocol date: 2026-09-28. Scope: research-only, **not executable FX trading**.

## Origin, rights and intended scope

Official source: ECB Statistical Data Warehouse/Data Portal, series \`EXR/D.USD.EUR.SP00.A\`, daily EUR/USD reference rates, https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?startPeriod=2023-01-01&endPeriod=2026-09-25&format=csvdata

License/usage review:
- https://www.ecb.europa.eu/stats/ecb_statistics/governance_and_quality_framework/html/usage_policy.en.html : the ESCB permits free commercial and noncommercial reuse of its *public ESCB statistics*, subject to accurate attribution and not modifying the original statistics. Third-party data are explicitly excluded absent permission.
- https://www.ecb.europa.eu/services/using-our-site/disclaimer/html/index.en.html and https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html : reference rates are informational and not suitable execution prices.
- This experiment uses only an official ECB **reference-rate statistic**; do not claim its derivations, a trained model, an execution feed or every API series are commercially cleared without separate compliance review. Do not redistribute the original data on Google Sites/Android.

Fetch the immutable historical window 2023-01-01 through 2026-09-25 inclusive, \`format=csvdata\`. The current 2026-09-28 unpublished/unfinished ECB reference observation is excluded. Record response hashes, official source URL, retrieval time, original reference dates, source metadata and observations under a private project-controlled audit store. No private data or model weights in public GitHub.

## Objective and causality

Forecast the next **published ECB reference-rate observation's** positive return *after a fictional 10-bps research friction*. This is **not** the price or P/L of an executable trade. Use reference-rate close-to-close changes, not fabricated OHLC bars.

At observation \`t\`, using only the already published reference rates through \`t\`:
- \`lagged_reference_return = P[t] / P[t-1] - 1\`
- \`mean_abs_5_reference_returns = mean(abs(P[j]/P[j-1] - 1))\` over the five latest already published changes ending at t.
- Label \`target_next_reference_net_return = P[t+1] / P[t] - 1 - 0.001\`.
- \`target_positive_after_proxy = int(target_next_reference_net_return > 0)\`.

Require >= 400 real published observations; strictly increasing dates, valid finite positive values, no conflicting duplicates, USD/EUR daily ECB series only. Closed observations may skip weekends and documented non-publication days; fail if duplicate, future, malformed or time-reversed.

## Frozen baseline and validation

- Deterministic standard-library logistic regression, 2 features, train-only z-score normalization, max absolute z=8, L2=0.03, learning rate=0.12, 600 epochs, intercept initialized to train prevalence log-odds.
- Probability selection threshold fixed at 0.55. No threshold tuning using holdout.
- Train/validation/OOS = chronological 60/20/20 and purge one observation at each boundary, for the one-step-ahead target. Initial model fits training only. Never train on validation/OOS.
- Three expanding development-only walk-forward folds: training fractions 50%, 60%, 70% of train+validation; one-sample purge, next 40 observations as test per fold, all before sealed OOS.
- Report row counts, timespan, class balance, Brier vs training-prevalence Brier, log loss, 10-bps research-only selected-sample proxy returns and another 10-bps cost-stress. Do not call these paper trades, broker-net P/L or actual performance.
- Fixed reject gates: data/provenance invalid; OOS Brier **not strictly below** naïve train-prevalence Brier; fewer than **2 of 3** development-only walk-forward folds with Brier improvement over their own training-prevalence baseline; fewer than **5 OOS selected observations**; or OOS selected-sample return sum after **20-bps total** research friction not strictly positive. No threshold, features, cost or parameters may be changed after observing results. Even a favorable candidate cannot auto-promote: next gate requires a separate execution-aligned, approved feed and true forward paper validation.

## Irreversible safety boundaries and triple check

No trade route, AppDeploy, GPT inference dependency, broker/risk/The5ers edits or live-money unlock. Model output remains a private \`CANDIDATE_NOT_APPROVED\` / \`REJECTED\` research artifact; the public Web App continues to return \`ABSTAIN\` and \`LOCKED\`. No production inference from ECB reference-rate model.

Before a checkpoint: (1) independent source and license/causality checks; (2) deterministic and negative-path tests followed by OOS/WF only after the protocol is committed; (3) read back private registry, GitHub source/checkpoint, and Supabase safety gates. If an externally verifiable right is ambiguous, limit this experiment to internal research only.

