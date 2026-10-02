-- Internal-only immutable CWS replay quarantine; never trading approval or public model inference.

CREATE OR REPLACE FUNCTION ai_trade.quarantine_known_replay_run(p_run_key text)
 RETURNS text
 LANGUAGE plpgsql
 SET search_path TO ''
AS $function$
DECLARE
  r record;
  v_trades jsonb;
  v_lessons jsonb;
  v_count bigint;
  v_symbols bigint;
  v_unique bigint;
  v_bad bigint;
  v_lessons_count bigint;
  v_portfolio bigint;
  v_snapshot jsonb;
  v_hash text;
  v_key text;
BEGIN
  IF p_run_key IS NULL OR p_run_key !~ '^TF013A_REPLAY_10X14_[0-9]{8}$' THEN
    RAISE EXCEPTION 'Unsupported CWS replay run key';
  END IF;

  SELECT strategy_id, universe_size, target_trades_per_symbol,
         completed_trades, symbols_with_target
    INTO r FROM ai_trade.training_replay_runs WHERE run_key = p_run_key;
  IF NOT FOUND OR r.strategy_id <> 'TF-013A-FORWARD-DIVERSIFIED-TREND'
     OR r.universe_size <> 14 OR r.target_trades_per_symbol <> 10
     OR r.completed_trades <> 140 OR r.symbols_with_target <> 14 THEN
    RAISE EXCEPTION 'Replay run is absent or not completed under the frozen 14x10 protocol';
  END IF;

  SELECT count(*), count(DISTINCT symbol), count(DISTINCT (symbol, sequence_no)),
         count(*) FILTER (WHERE symbol IS NULL OR sequence_no IS NULL
              OR entry_ts IS NULL OR exit_ts IS NULL OR exit_ts <= entry_ts
              OR entry_price IS NULL OR entry_price <= 0
              OR exit_price IS NULL OR exit_price <= 0
              OR initial_stop IS NULL OR initial_stop <= 0
              OR r_10bps IS NULL OR r_20bps IS NULL
              OR lesson_code IS NULL OR exit_reason IS NULL),
         jsonb_agg(jsonb_build_object(
           'symbol',symbol,'asset_class',asset_class,'sequence_no',sequence_no,
           'direction',direction,'entry_ts',entry_ts,'exit_ts',exit_ts,
           'entry_price',entry_price,'exit_price',exit_price,'initial_stop',initial_stop,
           'gross_r',gross_r,'r_10bps',r_10bps,'r_20bps',r_20bps,
           'exit_reason',exit_reason,'lesson_code',lesson_code
         ) ORDER BY symbol,sequence_no)
    INTO v_count, v_symbols, v_unique, v_bad, v_trades
    FROM ai_trade.training_replay_trades WHERE run_key = p_run_key;

  IF v_count <> 140 OR v_symbols <> 14 OR v_unique <> v_count OR v_bad <> 0 OR
     EXISTS (SELECT 1 FROM ai_trade.training_replay_trades
             WHERE run_key = p_run_key GROUP BY symbol HAVING count(*) <> 10) THEN
    RAISE EXCEPTION 'Missing, duplicated or incomplete CWS replay trades';
  END IF;

  SELECT count(*), count(*) FILTER (WHERE scope='PORTFOLIO'),
         jsonb_agg(jsonb_build_object(
           'scope',scope,'symbol',symbol,'trade_count',trade_count,
           'wins',wins,'losses',losses,'net_r_10bps',net_r_10bps,
           'avg_r_10bps',avg_r_10bps,'max_loss_r',max_loss_r,
           'stop_exit_count',stop_exit_count,'reversal_exit_count',reversal_exit_count,
           'lesson',lesson
         ) ORDER BY scope,symbol NULLS LAST)
    INTO v_lessons_count, v_portfolio, v_lessons
    FROM ai_trade.training_replay_lessons WHERE run_key = p_run_key;
  IF v_lessons_count <> 15 OR v_portfolio <> 1 THEN
    RAISE EXCEPTION 'CWS replay evidence lessons are incomplete';
  END IF;

  v_snapshot := jsonb_build_object(
    'schema_version',1,'run_key',p_run_key,
    'strategy_id','TF-013A-FORWARD-DIVERSIFIED-TREND',
    'source_data_terms','UNVERIFIED',
    'source_provider_claim','Yahoo finance daily reference within CWS simulation',
    'cost_mode','RESEARCH_PROXY_10_20_BPS_NOT_BROKER_NET',
    'trades',v_trades,'lessons',v_lessons,
    'trade_count',v_count,'symbol_count',v_symbols,'lesson_count',v_lessons_count
  );
  v_hash := encode(extensions.digest(v_snapshot::text,'sha256'),'hex');

  SELECT source_key INTO v_key FROM ai_trade.private_knowledge_ingestion_runs
    WHERE source_kind = 'CWS_REPLAY_EVIDENCE'
      AND source_run_key = p_run_key
      AND source_sha256 = v_hash
      AND status = 'QUARANTINED'
      AND approved_for_training = false
      AND public_inference = false
      AND broker_orders = false
      AND live_money_locked = true
    LIMIT 1;
  IF FOUND THEN RETURN v_key; END IF;

  INSERT INTO ai_trade.private_knowledge_ingestion_runs (
    source_key, source_kind, source_run_key, rights_scope, rights_statement,
    provenance, source_snapshot, source_sha256, knowledge_version,
    status, approved_for_training, public_inference, broker_orders, live_money_locked
  ) VALUES (
    'CWS_REPLAY_' || upper(substr(v_hash,1,24)),
    'CWS_REPLAY_EVIDENCE', p_run_key, 'INTERNAL_RESEARCH_ONLY',
    'CWS replay derived from externally sourced market data; provider training/reuse rights unverified. Synthetic 10/20bps research cost; must remain unapproved.',
    jsonb_build_object('origin_schema','ai_trade',
      'origin_trades_table','training_replay_trades',
      'origin_lessons_table','training_replay_lessons',
      'source_run_key',p_run_key,
      'rights_evidence_status','UNVERIFIED',
      'evidence_scope','INTERNAL_RESEARCH_ONLY',
      'report_path','reports/AI_TRADE_RESEARCH_TO_FORWARD_2026-09-27.md'),
    v_snapshot, v_hash, 'kv-replay-' || substr(v_hash,1,20),
    'QUARANTINED',false,false,false,true
  ) ON CONFLICT DO NOTHING
    RETURNING source_key INTO v_key;

  IF v_key IS NULL THEN
    SELECT source_key INTO v_key FROM ai_trade.private_knowledge_ingestion_runs
      WHERE source_sha256 = v_hash AND source_kind = 'CWS_REPLAY_EVIDENCE'
        AND source_run_key = p_run_key;
  END IF;
  IF v_key IS NULL THEN
    RAISE EXCEPTION 'CWS immutable replay knowledge version collision';
  END IF;
  RETURN v_key;
END;
$function$;

CREATE OR REPLACE FUNCTION ai_trade.quarantine_completed_known_replays()
 RETURNS integer
 LANGUAGE plpgsql
 SET search_path TO ''
AS $function$
DECLARE
  r record;
  before_count integer;
  after_count integer;
BEGIN
  IF NOT pg_catalog.pg_try_advisory_xact_lock(pg_catalog.hashtext('cws_ai_trade_replay_quarantine_v1')) THEN
    RETURN 0;
  END IF;
  SELECT count(*) INTO before_count FROM ai_trade.private_knowledge_ingestion_runs
    WHERE source_kind='CWS_REPLAY_EVIDENCE';
  FOR r IN
    SELECT run_key FROM ai_trade.training_replay_runs
    WHERE run_key ~ '^TF013A_REPLAY_10X14_[0-9]{8}$'
      AND strategy_id='TF-013A-FORWARD-DIVERSIFIED-TREND'
      AND universe_size=14 AND target_trades_per_symbol=10
      AND completed_trades=140 AND symbols_with_target=14
    ORDER BY created_at ASC LIMIT 10
  LOOP
    PERFORM ai_trade.quarantine_known_replay_run(r.run_key);
  END LOOP;
  SELECT count(*) INTO after_count FROM ai_trade.private_knowledge_ingestion_runs
    WHERE source_kind='CWS_REPLAY_EVIDENCE';
  RETURN after_count - before_count;
END;
$function$;

REVOKE ALL ON FUNCTION ai_trade.quarantine_known_replay_run(text) FROM PUBLIC, anon, authenticated;

REVOKE ALL ON FUNCTION ai_trade.quarantine_completed_known_replays() FROM PUBLIC, anon, authenticated;

GRANT EXECUTE ON FUNCTION ai_trade.quarantine_known_replay_run(text) TO service_role;

GRANT EXECUTE ON FUNCTION ai_trade.quarantine_completed_known_replays() TO service_role;

SELECT cron.schedule('ai-trade-knowledge-quarantine-daily','45 3 * * *','SELECT ai_trade.quarantine_completed_known_replays();') WHERE NOT EXISTS (SELECT 1 FROM cron.job WHERE jobname='ai-trade-knowledge-quarantine-daily');

COMMENT ON FUNCTION ai_trade.quarantine_completed_known_replays() IS 'Bounded daily immutable quarantine for completed CWS replay evidence only. Never model promotion, public inference or broker execution.';
