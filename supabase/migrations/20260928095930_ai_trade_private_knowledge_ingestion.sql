-- CWS AI Trade private research evidence ingestion.
-- CWS-generated replay outcomes/lessons remain QUARANTINED until provenance,
-- market-data reuse rights and independent human review are verified.
-- No production inference, broker execution, risk-gate or The5ers changes.
create table if not exists ai_trade.private_knowledge_ingestion_runs (
    source_key text primary key check (source_key ~ '^[A-Z0-9_]{8,120}$'),
    source_kind text not null check (source_kind in ('CWS_REPLAY_EVIDENCE', 'CWS_DISTILLED_KNOWLEDGE')),
    source_run_key text not null,
    rights_scope text not null check (rights_scope = 'INTERNAL_RESEARCH_ONLY'),
    rights_statement text not null,
    provenance jsonb not null check (jsonb_typeof(provenance) = 'object'),
    source_snapshot jsonb not null check (jsonb_typeof(source_snapshot) = 'object'),
    source_sha256 text not null check (source_sha256 ~ '^[a-f0-9]{64}$'),
    knowledge_version text not null unique check (knowledge_version ~ '^kv-replay-[a-f0-9]{20}$'),
    status text not null default 'QUARANTINED' check (status = 'QUARANTINED'),
    approved_for_training boolean not null default false check (approved_for_training = false),
    public_inference boolean not null default false check (public_inference = false),
    broker_orders boolean not null default false check (broker_orders = false),
    live_money_locked boolean not null default true check (live_money_locked = true),
    created_at timestamptz not null default now()
);
alter table ai_trade.private_knowledge_ingestion_runs enable row level security;
revoke all on ai_trade.private_knowledge_ingestion_runs from public, anon, authenticated;
grant select, insert on ai_trade.private_knowledge_ingestion_runs to service_role;

create or replace function ai_trade.prevent_private_knowledge_mutation()
returns trigger language plpgsql security invoker set search_path = ''
as $$
begin
    raise exception 'Private knowledge sources are immutable; append a new version';
end;
$$;
revoke all on function ai_trade.prevent_private_knowledge_mutation()
  from public, anon, authenticated, service_role;
drop trigger if exists prevent_private_knowledge_mutation on ai_trade.private_knowledge_ingestion_runs;
create trigger prevent_private_knowledge_mutation before update or delete
on ai_trade.private_knowledge_ingestion_runs for each row
execute function ai_trade.prevent_private_knowledge_mutation();

