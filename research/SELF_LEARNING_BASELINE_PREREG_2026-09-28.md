# CWS AI Trade — ML Baseline Preregistration (research only)

2026-09-28. Applies only to a separately rights-cleared, immutable closed-bar OHLC dataset.
This protocol is frozen BEFORE any real-data candidate is fit or OOS is inspected.

- Target: positive next-bar OPEN-to-CLOSE price return after explicitly declared research-only round-trip cost. This is NOT a realizable filled trade, actual spread/slippage/swap, broker-net profit or forecasting of a live account.
- Inputs available at the close of bar t only: return close(t)/close(t-1)-1; range [high(t)-low(t)]/open(t). Nothing from bar t+1 may enter a feature.
- Time-ordered train/validation/holdout = 60/20/20, one sample purged at both boundaries for a one-bar label horizon. No random splits. Keep the final 20% OOS sealed until the candidate is frozen.
- Candidate: pure-Python logistic regression with standardization fit on TRAIN only; deterministic zero-initialized feature weights, intercept initialized to training log odds; 600 full-batch gradient epochs, learning rate .12, L2 .03, normalized feature clipping 8.
- Baseline comparator: training-prevalence probability, not a selectively tuned profitable strategy.
- Metrics: Brier, log loss, number of selected research observations, theoretical next-open-to-close return sum after 1x and 2x proxy cost. No metric counts as a broker trade or actual P/L.
- Research abstain threshold .55 is fixed before looking at OOS. Public/production inference must return ABSTAIN even if an unapproved candidate is trained.
- Walk-forward: three expanding folds on development data only (50%, 60%, 70% training fraction; following ~10% test with minimum 40 points), retrained per fold. The final sealed OOS is excluded from all fold fitting and parameter choices.
- Source gate: verified data-provider use rights, source version/hash, timestamp, market/timeframe and actual closed-bar integrity. Third-party books are not numerical market data. Synthetic fixtures test code only.
- Deployment: NONE. No automatic promotion, no order endpoints, no DEMO/LIVE gating changes. A new independently approved model/feature version and genuine forward evidence are mandatory before any production integration.

Known current blocker: the 140 training replay trades in Supabase are the **latest ten per market**, derived from Yahoo daily market history; they are selection-biased and are NOT 300+ fully sourced contiguous licensed OHLC bars. Do not relabel or use them as the approved numeric dataset.
