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
