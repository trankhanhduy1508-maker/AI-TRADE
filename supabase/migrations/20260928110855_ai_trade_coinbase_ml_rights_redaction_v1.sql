-- Legal compliance correction, 2026-09-28.
-- Coinbase Market Data Terms updated 2026-08-07 prohibit training ANY ML model
-- with Coinbase Market Data, even for internal use, absent prior written consent.
-- Authority: https://www.coinbase.com/legal/market_data, section 3(5).
-- This is an atomic, one-row emergency redaction of a rejected candidate,
-- NOT model promotion or disabling risk/broker gates.
--
-- Preserve a metadata-only tombstone while removing source rates, fitted
-- weights, predictions and performance metrics. Preserve only a model ID
-- for historical audit and leave status REJECTED.
ALTER TABLE ai_trade.private_ml_baseline_runs
  DROP CONSTRAINT private_ml_baseline_runs_rights_scope_check;
ALTER TABLE ai_trade.private_ml_baseline_runs
  ADD CONSTRAINT private_ml_baseline_runs_rights_scope_check
  CHECK (rights_scope IN ('INTERNAL_RESEARCH_ONLY','PROHIBITED_FOR_ML'));

DO $redact$
DECLARE
  prior record;
  replacement jsonb;
  modified integer;
BEGIN
  SELECT experiment_key,provider,rights_scope,status,model_version,
         source_sha256,source_snapshot,model_artifact,evaluation,
         public_inference,broker_orders,live_money_locked
  INTO prior
  FROM ai_trade.private_ml_baseline_runs
  WHERE experiment_key='BTC_USD_D1_INTERNAL_BASELINE_20260928_V1'
  FOR UPDATE;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'Coinbase research row missing, do not silently skip compliance redaction';
  END IF;

  IF prior.rights_scope='PROHIBITED_FOR_ML' THEN
    IF prior.status <> 'REJECTED' OR prior.source_snapshot->>'redacted' <> 'true'
       OR prior.model_artifact->>'redacted' <> 'true'
       OR prior.evaluation->>'redacted' <> 'true' THEN
      RAISE EXCEPTION 'Coinbase row already marked prohibited but raw/derived data may remain';
    END IF;
    RETURN;
  END IF;

  IF prior.provider <> 'Coinbase Exchange'
     OR prior.rights_scope <> 'INTERNAL_RESEARCH_ONLY'
     OR prior.status <> 'REJECTED'
     OR prior.model_version <> 'mc1-9fe3562afdd3be27d9f2'
     OR prior.source_sha256 <> '96ed4c2009fc7c48449e833803739aae15a4317b25afafc04a45b667f11712b9'
     OR prior.public_inference <> false
     OR prior.broker_orders <> false
     OR prior.live_money_locked <> true
     OR jsonb_typeof(prior.source_snapshot->'raw') <> 'array'
     OR jsonb_array_length(prior.source_snapshot->'raw') <> 423
     OR prior.model_artifact->'model' IS NULL
     OR prior.evaluation->'oos' IS NULL
  THEN
    RAISE EXCEPTION 'Coinbase record unexpected: abort rather than redact another experiment';
  END IF;

  replacement := jsonb_build_object(
    'redacted',true,
    'provider','Coinbase Exchange',
    'ml_training_permitted',false,
    'reason_code','COINBASE_MARKET_DATA_ML_USE_REQUIRES_PRIOR_WRITTEN_CONSENT',
    'official_terms','https://www.coinbase.com/legal/market_data',
    'terms_version','2026-08-07',
    'source_observations_retained',0,
    'previous_source_digest','96ed4c2009fc7c48449e833803739aae15a4317b25afafc04a45b667f11712b9'
  );

  -- Transactional, tightly scoped exception to append-only rule. Re-enable
  -- the exact immutability trigger before committing. On failure all rolls back.
  EXECUTE 'ALTER TABLE ai_trade.private_ml_baseline_runs DISABLE TRIGGER prevent_private_ml_mutation';

  UPDATE ai_trade.private_ml_baseline_runs
     SET rights_scope='PROHIBITED_FOR_ML',
         source_snapshot=replacement,
         source_sha256=encode(extensions.digest(replacement::text,'sha256'),'hex'),
         model_artifact=jsonb_build_object(
           'redacted',true,'weights_removed',true,'usable',false,
           'reason_code','TRAINING_RIGHTS_NOT_ESTABLISHED'),
         evaluation=jsonb_build_object(
           'redacted',true,'derived_metrics_removed',true,'usable',false)
   WHERE experiment_key='BTC_USD_D1_INTERNAL_BASELINE_20260928_V1'
     AND source_sha256='96ed4c2009fc7c48449e833803739aae15a4317b25afafc04a45b667f11712b9';

  GET DIAGNOSTICS modified=ROW_COUNT;
  IF modified <> 1 THEN
    RAISE EXCEPTION 'Coinbase redaction affected % rows instead of one', modified;
  END IF;
  EXECUTE 'ALTER TABLE ai_trade.private_ml_baseline_runs ENABLE TRIGGER prevent_private_ml_mutation';
END
$redact$;

COMMENT ON TABLE ai_trade.private_ml_baseline_runs IS
 'Immutable private research registry. Coinbase model BTC_USD_D1_INTERNAL_BASELINE_20260928_V1 is metadata-only legal-redaction tombstone, prohibited for ML absent prior written provider consent. All inference and broker orders disabled.';