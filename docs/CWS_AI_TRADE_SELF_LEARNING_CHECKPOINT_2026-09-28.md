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

`knowledge/self_learning/SOURCE_REGISTRY_V1.json` pins the three already-verified GitHub blobs (CWS Masterbook V3 **distilled**, practitioner registry, CWS 10-year backtest report), their rights scope and quarantine status. Only CWS-authored summaries/report text is covered by CWS_OWNED; third-party full books, 49-page EPUB and third-party raw market data are **not** ingested or relicensed. Git blob SHA-1 identifies the source; `stage_knowledge` independently creates the file SHA-256 once the verified repository source is available to the offline runner. No source was automatically approved or used to train model weights.

## 2026-09-28 continuation — fixed, pre-registered offline ML candidate code

- Added `src/self_learning/model.py` with a deterministic standard-library logistic baseline, pinned feature list/hyperparameters, train-only normalization, chronological splits and pre-OOS expanding walk-forward folds.
- Added `tests/self_learning/test_model.py`: deterministic candidate, source/version integrity, positive/negative license and cost gate, tamper rejection, abstention and zero broker orders.
- Updated `src/self_learning/pipeline.py`: dataset now carries its exact source metadata and declared 1x proxy cost; `dataset_version` hashes the full snapshot, and the candidate refuses mutated rows. 2x cost stress is actually applied to selected research returns.
- Pre-registered all details at `research/SELF_LEARNING_BASELINE_PREREG_2026-09-28.md`.
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

## 2026-09-28 — Supabase v9 xác minh

- GitHub source: `23b22ab8e1ab3a0c195895ad68fdd928cb1e95c1`; Supabase `cws-ai-trade-site` v9 ACTIVE; SHA-256 `046222b77d1520b45dba4e475d107e876b8961f307e245d6b24281f917cc8e1b`.
- Sửa đúng phép cộng lãi dương và lỗ âm theo từng vị thế trước khi gộp thành một dòng cho mỗi symbol. Kiểm thử hồi quy Node: 8/8 PASS trên fixture riêng; các trường thiếu trả null.
- Nâng bộ nhớ đệm static PWA lên `cws-ai-trade-static-v3`; live HTTP có dữ liệu thật cho 5 endpoint: health, HTML, JS danh mục, service worker và manifest.
- Python self-learning tests: 13/13 PASS trên unit fixtures; model trên dữ liệu thực vẫn chưa được huấn luyện.
- Sau triển khai `enabled=false`, `demo_send_enabled=false`, `risk_profile_approved=false` và giao diện vẫn thể hiện `MODEL_NOT_TRAINED`, `ABSTAIN`, `LOCKED`.
- Google Sites publication, Android device installation và APK chưa có bằng chứng kiểm thử hoàn thành.


## 2026-09-28 — Private EPUB and internal model-registry continuation

Source code added:
- `src/self_learning/epub_ingest.py`: EPUB3 ZIP integrity, size/traversal/doctype/manifest/spine checks; chapter-level source hashes, **private local quarantine** with immutable exclusive write, and a returned metadata-only manifest. Explicitly no training approval or broker route.
- `tests/self_learning/test_epub_ingest.py`: harmless HTML doctype compatibility and fail-closed negative tests.
- `research/CWS_ML_BTC_PRIVATE_BASELINE_PREREG_2026-09-28.md`: preregistered small research-only supervised baseline and strict provider rights restrictions; **not** a public/commercial data license.
- `supabase/migrations/20260928091859_ai_trade_private_ml_baseline_runs_v1.sql`: tracks the applied remote Supabase migration for an append-only, RLS-protected research registry.

Actual private book input was integrity-checked, its OPF author/title were verified, and its 31 extractable EPUB spine sections were staged to **private local quarantine** with source hashes. The full EPUB/chapter text was not committed to public GitHub, published in Google Sites, or used to train trading model weights. Staging does not establish rights clearance for any quoted third-party material. Local container quarantine is not claimed as durable cloud storage.

Offline evidence:
- `PYTHONPATH=. pytest -q tests/self_learning`: **20 passed** (pipeline, model candidate, EPUB validation).
- `node --test google-sites/cws-ai-trade/tests/portfolio.test.cjs`: **8 passed**, including 16-market universe, position-level gross gain/loss, mixed directions, missing fields and rejection of paper R as broker P/L.
- `python -m compileall -q src/self_learning` and default read-only `ABSTAIN/LOCKED` contract: PASS.
- Exact locally tested EPUB source/test Git blob SHA-1 independently matched the files fetched from GitHub after commit.
- Supabase confirmed private research registry RLS enabled, anon/authenticated SELECT denied and immutable mutation trigger present. The preregistered experiment was stored privately; external provider data, model artifact and evaluation are **not** redistributable public artifacts and are intentionally absent from this public checkpoint. **No model was promoted.**
- Read-only SQL after research confirmed runtime execution gates still disabled and order-intent count unchanged at zero.
- The public CWS Trading Engine stays fail-closed and read-only; no change to broker execution, kill-switch, Risk Engine or The5ers.

The private provider license has a personal/internal research boundary and does **not** authorize making that provider's data or derived model available through a public/commercial Web App. Provider terms and permissions must be checked separately for any production use. The model, if any, cannot be represented as broker-net profitable or live validated.

No Google Sites publish, Android install E2E or APK completion is asserted in this checkpoint.


## 2026-09-28 — ECB reference-rate real-data research and reproducibility

This is an internal, NON-EXECUTABLE research continuation. It does not supersede a broker-price model, forward-paper evidence, or any execution/risk approval.

- The protocol and fixed rejection thresholds were committed **before** opening/evaluating the complete source: `research/CWS_ML_ECB_REFERENCE_V1_PREREG_2026-09-28.md`, protocol commit `2c6ed583173f4f050d85362b63491df02a02ce90`.
- Independently retrieved five bounded windows of the ECB Data Portal's `EXR.D.USD.EUR.SP00.A` official EUR/USD reference-rate series. Validated 954 unique, chronologically ordered published observations from 2023-01-02 through 2026-09-25, consistent overlaps, reference series/currency/status and original official rate strings. ECB reference rates are **informational, not executable broker prices**. Attribute `Source: ECB statistics.`; no third-party rights are assumed.
- Created 948 causal one-reference-step samples; fit a genuine deterministic two-feature logistic research model on 568 historical train observations; evaluated 189 validation and 189 sealed OOS observations, plus three development-only walk-forward folds. Research-only fictional 10/20-bps cost proxy was used, not broker-net costs or paper P/L.
- The real ECB research model was **REJECTED under frozen preregistered gates**: insufficient selected OOS observations and failed doubled-cost research stress. No threshold, features or rejection gate was retuned after inspecting OOS. The previous BTC internal model also remains REJECTED. No approved production model exists.
- Source observations, dataset/model weights and private evaluation were persisted only to a private local research workspace and immutable RLS-protected `ai_trade.private_ml_baseline_runs` on Supabase as `ECB_EURUSD_REFERENCE_BASELINE_20260928_V1`. The external-provider observations, model weights and private evaluation are **not committed to this public GitHub repository or served by CWS Web App**.
- The model's official source/data/code hashes, immutable snapshot and preregistration commit were independently read back. Stored research artifact is `REJECTED`, `public_inference=false`, `broker_orders=false`, `live_money_locked=true`, `ABSTAIN/LOCKED`.
- Added `scripts/run_ecb_reference_research.py` and `tests/self_learning/test_reference_reproduction.py`, an offline GPT-independent reproduction runner pinned to the independently verified source digest and exact original model Git blob. The runner refuses changed input, changed model code, output inside the repository, symlinked private destination or overwrite of immutable artifacts. It never calls a broker.
- Hardening of `src/self_learning/epub_ingest.py` now restricts the private book quarantine directory to `0700`, files to `0600`, rejects symlinks and removes partial writes; original staged book/chapter material was also made private locally.
- Test evidence: 29/29 Python self-learning tests (synthetic fixtures only), 8/8 Node portfolio tests; actual independently sourced ECB model trained/evaluated separately and reproducibly through the pinned offline runner. The offline reproduction returned the exact original research model/dataset version and REJECTED state. No unit fixture was presented as market evidence.

### Triple-check evidence

1. Source and causal dataset: official ECB CSV fields, 954 original observations, date bounds, duplicate conflicts, frozen source/dataset SHA-256, sealed chronology, exact original model Git blob.
2. Independent evaluation and regression: original Python model and independent JavaScript parity check agreed to numerical tolerance on the real source; Python/Node tests passed; all OOS/WF and predeclared negative gates respected. Reproduction runner replayed the real private experiment and refused modified/fake source.
3. Persistent runtime/security: Supabase readback confirmed source_snapshot SHA-256, 954 stored original observations, exactly 3 WF folds, REJECTED evaluation, model/prereg code references, RLS, no public/authenticated SELECT and immutable update/delete trigger. Final read-only runtime check: `enabled=false`, `demo_send_enabled=false`, `risk_profile_approved=false`, and 0 broker order intents.

The public PWA is still read-only with no approved model and no direct broker execution. Google Sites actual Founder publish, Android-device install/offline E2E, signed APK, legitimate broker-executable data/cost alignment, OOS-qualified model and **real future paper evidence** remain unverified; these are not declared PASS.

## 2026-09-28 — Supabase PWA v10: model không được duyệt, không phụ thuộc AppDeploy

- GitHub Web App source: `773722edc6055936b592025cd628f2db14fe76db`; Supabase Edge Function `cws-ai-trade-site` **v10 ACTIVE**, deployment digest `cf6c0ba8166ff1348e0bf69728666e001fde5a729d8ff086e2565168376557ab`.
- Điều chỉnh thông báo UI từ “chưa huấn luyện” sang **`MODEL_NOT_APPROVED`**, vì nghiên cứu nội bộ đã thực sự train nhưng hai candidate bị loại, không có model production. Tín hiệu sản phẩm tiếp tục `ABSTAIN` và `LOCKED`.
- Loại liên kết Founder Secure AppDeploy cũ khỏi Web App. Hướng dẫn nhập JSON chỉ đọc không còn phụ thuộc phiên đăng nhập tên miền cũ. Footer ghi rõ Google Sites **chưa xuất bản** thay vì gọi bản web hiện hành là Google Sites.
- Nâng cache static PWA lên `cws-ai-trade-static-v4`; chỉ có `index.html` và `sw.js` thay đổi trong bundle so với v9; không chỉnh bộ tính 16 cặp, Lot/P&L, biểu đồ, EPUB hay broker.
- Ba lớp kiểm tra: (1) GitHub index/worker trùng chính xác bundle, so với deployed v9 trước khi sửa; (2) deployed v10 source đọc lại trùng chính xác GitHub bundle, HTTP live GET health/HTML/worker/manifest không lỗi, HTML thể hiện `MODEL_NOT_APPROVED`, `ABSTAIN · Gate: LOCKED`, không còn AppDeploy; footer live xác nhận `Google Sites chưa xuất bản`; (3) SQL sau triển khai: `enabled=false`, `demo_send_enabled=false`, `risk_profile_approved=false`, order intents = 0, hai private model vẫn không có public inference.
- Kiểm thử hồi quy không đổi mã nguồn Python/portfolio: **29/29 Python** và **8/8 Node** PASS; không gọi các bài fixture là kết quả thị trường.
- **Không khẳng định** Android Chrome cài/khởi động offline E2E trên điện thoại, Google Sites Founder đã publish, hoặc APK đã build/ký. Chưa có model đủ chuẩn OOS, broker-net cost và forward paper để mở sản phẩm trading.

## 2026-09-28 — Android debug APK đã build và đối chiếu ba lớp

- Source Android WebView read-only được bổ sung trên nhánh duy nhất; cloud build [run 36407451446](https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36407451446) **SUCCESS** với Android Lint, assembleDebug và apksigner v2. Lỗi lint của lần đầu về back gesture Android 13+ đã được sửa tối thiểu và build lại.
- APK debug SHA-256 `2506f856b1b258386b2509cbafc0138397d4de93a3f27200555c2f6cd46c0d99`; ZIP artifact GitHub `10962564442`, SHA-256 `13fccb6dd97637e2ebd1e2e4af46f666745d18c0918577d096935fbd4123aab6`. Đã tải lại và kiểm chứng ZIP/ APK hash độc lập, archive CRC và Android DEX/Manifest. Ký bằng **Android Debug**, chỉ dành cho QA, không phải release APK/ký sản phẩm.
- Kiểm tra lớp 1: mã nguồn trên GitHub, HTTPS allowlist, SSL fail-closed, khóa thực thi không thay đổi. Lớp 2: Android cloud lint/compile/apksigner + 29 Python / 8 Node tests. Lớp 3: artifact tải lại khớp hash build; Web App Supabase v10 readback khớp GitHub bundle; runtime SQL xác minh live-money lock, 0 broker intents, hai mô hình nghiên cứu vẫn REJECTED.
- Google Sites chưa publish được dưới tài khoản Founder; chưa có test APK trên điện thoại Android thực, kênh ký release lâu dài, OOS-approved trading model hay future forward-paper evidence. Không gọi các mục này PASS. Source/book/market-data private không được phát hành qua APK/web.
- Tình trạng quarantine knowledge replay: migration private, immutable, RLS đã áp dụng nhưng chưa ghi thành công snapshot replay vào bảng; một thao tác ghi bị công cụ chặn, do đó không đánh dấu hoàn tất. Hai model riêng vẫn ở private registry, trạng thái REJECTED.
