# CWS ML research preregistration — internal-only BTC-USD baseline

Date: 2026-09-28. Repository branch: codex/p0-covel-knowledge-audit.
This protocol is frozen **before reading model scores**; no parameter retuning against OOS.

## Source and legal boundary

- Provider: Coinbase Exchange public REST candles, product BTC-USD, granularity 86400 seconds, UTC; request historical bars from 2025-08-01 through 2026-09-27 inclusive, with overlapping bounded fetch windows.
- Access terms: https://www.coinbase.com/en-au/legal/market_data (updated 2026-08-07). Use solely for **CWS internal research**; no publication/redistribution of raw data, derived works, model weights, predictions or private evaluation to outside end-users. This is **NOT a license for the proposed public/commercial CWS Trading Web App**. A separate approved commercial/redistribution license or independently lawful source is mandatory before product use.
- Exclude the currently forming UTC 2026-09-28 candle. Reject duplicate, non-UTC daily, missing, nonfinite, nonsensical and incomplete candles; require at least 300.
- Record UTC data range, provider endpoint, normalization version, immutable dataset digest, cost assumption and verified code commit SHA. Keep raw snapshot and model artifact private in the unexposed ai_trade schema with RLS where supported; never in a public Git repository or a public browser.

## Fixed experiment

- Task: predict whether the next daily open-to-close BTC-USD return exceeds an explicit 10-bps **research friction proxy**. Not broker cost, executable fill, MT5 P/L or a recommendation to trade.
- Features: prior close-to-close return and **current already-closed** bar range / open; predict only after current bar closes. Next-bar prices are labels, never features.
- Model: the already committed src/self_learning/model.py deterministic two-feature L2-logistic baseline, 600 epochs, learning rate 0.12, L2 0.03, max z-score magnitude 8 and fixed probability threshold 0.55. No GPT/API dependency for scoring.
- Chronological train/validation/OOS: 60/20/20 with one-bar purge at boundaries. Fit mean/std on train only. OOS must remain sealed until the model and metrics are frozen.
- Development-only expanding walk-forward: training portions 50%, 60%, 70% of the combined development data; evaluate immediately subsequent 40 samples each, purging one boundary sample.
- Compare Brier score against constant **training prevalence**, report log loss, count/positive labels, selected-sample 10-bps proxy return and an additional 10-bps stress (20-bps total). Do not label these paper, broker net, capital returns, precision of an approved signal or deployed model.
- If model fails source, rights, feature causality, OOS, uncertainty/calibration or sample gates, status remains CANDIDATE_NOT_APPROVED or REJECTED. Even favorable metrics do not permit automatic deployment/promotion.
- Do not touch the pre-existing runtime_config, broker adapter, Risk Engine, The5ers or kill switch. Keep public inference ABSTAIN and live money LOCKED.

## Evaluation evidence requirements

At least three checks: (1) input/license/provenance/chronology check, (2) model and negative-path unit tests plus OOS/walk-forward evaluation, (3) source-code and private model-registry readback with unchanged Supabase execution-gate state. Do not claim actual Android QA or Google Sites publish without device/browser evidence.
