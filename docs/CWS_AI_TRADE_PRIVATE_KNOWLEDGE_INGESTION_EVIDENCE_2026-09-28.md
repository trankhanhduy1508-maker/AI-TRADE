# CWS AI Trade — Private knowledge ingestion runtime evidence

Date: 2026-09-28 (UTC). Branch: `codex/p0-covel-knowledge-audit`.
Project: Supabase `oziktadfeenydvgobudr`; schema `ai_trade`.
Scope: private versioned research input **only**, not production ML, not broker execution.

## Actual sources, rights and immutable versions

The already-applied migration `supabase/migrations/20260928095930_ai_trade_private_knowledge_ingestion.sql` provisions the append-only `ai_trade.private_knowledge_ingestion_runs` table. Two **actual** source snapshots were inserted without fabricating observations:

| Source | Exact provenance | Content retained privately | knowledge_version | source_snapshot SHA-256 | Status |
|---|---|---|---|---|---|
| CWS Masterbook V3 distilled | `knowledge/CWS_TRADING_MASTERBOOK_V3_DISTILLED_2026-09-28.md`, Git blob `116368dcf74e70fe502d993aa8acae92612f2c47` | CWS-authored public distilled Markdown (not the complete EPUB) and provenance | `kv-replay-8264dd7dc006e7710fe4` | `8264dd7dc006e7710fe4d397dc38e53b8dac3baed19e342439246f6891acf40c` | QUARANTINED |
| CWS TF-013A replay | `ai_trade.training_replay_trades` and `ai_trade.training_replay_lessons`, run `TF013A_REPLAY_10X14_20260927` | Exact snapshot of 140 existing replay trades, 14 symbols and 15 existing CWS-generated lessons | `kv-replay-71b0a99b8ccf3534a2e9` | `71b0a99b8ccf3534a2e99552486a27c0638afe98934bb7c71e026879a7d5d853` | QUARANTINED |

The Masterbook source is CWS's already-public **distilled** writing; it does not establish rights over referenced third-party full books. The replay derives from an external Yahoo-based price feed whose reuse/training rights have **not** been independently cleared. Both rows explicitly declare INTERNAL_RESEARCH_ONLY and `approved_for_training=false`. This checkpoint **does not** mark either source as approved or count replay outcomes as new trades. Cost-adjusted replay R is a synthetic research proxy, not actual broker P/L. Neither source is exposed through public Google Sites or the CWS Trading Web App.

## Three independent verifications

1. **Provenance/integrity.** GitHub file was fetched at the verified exact source blob. Database readback confirmed two source keys, exact original run key, 140/14/15 replay counts and both `source_sha256 = SHA256(source_snapshot::text)` checks true. Distilled Markdown was not misidentified as the full EPUB.
2. **Private append-only access.** `ai_trade.private_knowledge_ingestion_runs` has RLS enabled, `anon` and `authenticated` have no SELECT, and the `prevent_private_knowledge_mutation` trigger is enabled. Unsafe row count (`approved_for_training OR public_inference OR broker_orders OR NOT live_money_locked OR status != 'QUARANTINED'`) is **zero**. No rights review was bypassed.
3. **Unchanged execution.** Live runtime `enabled=false`, `demo_send_enabled=false`, `risk_profile_approved=false`, zero broker order intents. The two existing research models remain **REJECTED**; zero model registry rows permit public inference or broker orders.

The evidence is from actual Supabase SQL readback after insert, not a unit-test fixture. Two separate SQL negative tests attempted same-value UPDATE and DELETE inside exception-checked blocks; both operations were rejected by the immutable trigger, and post-test readback retained exactly two valid quarantined records. Do not convert QUARANTINED to APPROVED, claim commercially licensed data, publish proprietary snapshots or unlock broker/risk/The5ers gates without the separately established evidence/approval process.

## Private owner Drive copies (not public application deployment)

The original **Founder CWS Trading Masterbook EPUB** and the **debug-QA Android APK** were copied into separate private owner-only Google Drive folders under `CWS AI TRADE`. Google Drive readback reported `shared=false` and only the owner permission, and returned 1,707,675-byte EPUB and 11,887-byte APK.

The original local files were hashed and CRC/integrity checked before upload. Independently re-downloaded Drive bytes matched **exactly**:
- EPUB SHA-256 `c7d1ef5cca95217e67ec1764cf0b9cbc14ad1fa30cfa542717d0fe3373b5b00a`;
- QA APK SHA-256 `2506f856b1b258386b2509cbafc0138397d4de93a3f27200555c2f6cd46c0d99`.

The APK corresponds to the GitHub Android debug workflow for commit `8b2642013526dd9448ed1a2e39b9ebe82e369f69`, which completed Gradle lint/assemble and an APK Signature Scheme v2 verification with an **ephemeral debug certificate**. Drive storage is a private QA convenience, not release-signature stability, device QA, Play Store publication or production readiness. Private Drive file IDs and full EPUB contents are intentionally omitted from this public checkpoint.

## Automated replay quarantine (bounded, fail-closed)

Applied Supabase migration `20260928102300_ai_trade_known_replay_quarantine_cron_v1` and committed the exact SQL as `supabase/migrations/20260928102300_ai_trade_known_replay_quarantine_cron_v1.sql`. Added two internal `SECURITY INVOKER` functions:

- `ai_trade.quarantine_known_replay_run(text)` accepts **only** the preregistered TF-013A 14-symbol / 10-trade replay run format. It checks the completed run, trade counts, unique symbol/sequence pairs, entry/exit time/price bounds and all 15 original lesson records; builds a source-pinned JSONB snapshot and SHA-256 version. It deduplicates identical snapshots and creates an **additional immutable version** if an existing run's underlying evidence later changes. Stored data remain internal research with provider rights **UNVERIFIED**, `approved_for_training=false`, `public_inference=false`, `broker_orders=false` and `live_money_locked=true`.
- `ai_trade.quarantine_completed_known_replays()` takes a transaction-scoped advisory lock, processes at most ten completed eligible runs and reports the number of newly quarantined versions. A new Supabase Cron job `ai-trade-knowledge-quarantine-daily` runs `45 3 * * *` UTC. No network calls, external subscriptions, live orders, model retraining or approval occur in this job.

### Independent acceptance gates

1. **Input and deterministic versioning:** `quarantine_known_replay_run('TF013A_REPLAY_10X14_20260927')` was invoked twice and returned the **same** existing `CWS_REPLAY_TF013A_20260927_V1` row; both bounded-scanner invocations returned `newly_quarantined=0`. An unknown/future run was explicitly **rejected** with the expected incomplete-run exception. Source count remained two; hashes and all quarantine flags independently verified.
2. **Actual remote runtime:** Supabase migration history contains `20260928102300_ai_trade_known_replay_quarantine_cron_v1`. `cron.job` readback shows job ID 10, schedule `45 3 * * *`, `active=true` and command exactly `SELECT ai_trade.quarantine_completed_known_replays();`. This confirms the job is configured; it does **not** claim that a future scheduled run has executed.
3. **Security and GitHub readback:** `anon` and `authenticated` cannot execute either function; `service_role` can invoke the reviewed ingest function. GitHub migration source readback matched the committed 7,520-character SQL. The unrelated execution flags remain `enabled=false`, `demo_send_enabled=false`, `risk_profile_approved=false`, with **zero order intents**. RLS-without-public-policy on the private immutable table is intentional fail-closed behavior, not a public read policy.

This automates **quarantine/version collection only**. It cannot use unverified Yahoo-derived research as an approved training dataset, convert simulated R into realized broker P/L, automatically promote the two rejected models or satisfy the still-required future forward-paper/broker-cost evidence.
