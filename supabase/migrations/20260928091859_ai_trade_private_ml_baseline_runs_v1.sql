-- Applied in Supabase project oziktadfeenydvgobudr as remote migration
-- 20260928091859_ai_trade_private_ml_baseline_runs_v1.
-- Append-only, non-exposed internal research; never a production trading model.
create table if not exists ai_trade.private_ml_baseline_runs (
  experiment_key text primary key,
  provider text not null,
  rights_scope text not null check (rights_scope = 'INTERNAL_RESEARCH_ONLY'),
  source_url text not null,
  source_snapshot jsonb not null,
  source_sha256 text not null check (source_sha256 ~ '^[0-9a-f]{64}$'),
  model_artifact jsonb not null,
  evaluation jsonb not null,
  model_version text not null unique,
  code_commit_sha text not null check (code_commit_sha ~ '^[0-9a-f]{40}$'),
  status text not null default 'CANDIDATE_NOT_APPROVED'
    check (status in ('CANDIDATE_NOT_APPROVED', 'REJECTED')),
  public_inference boolean not null default false check (public_inference = false),
  broker_orders boolean not null default false check (broker_orders = false),
  live_money_locked boolean not null default true check (live_money_locked = true),
  created_at timestamptz not null default now()
);
alter table ai_trade.private_ml_baseline_runs enable row level security;
revoke all on ai_trade.private_ml_baseline_runs from public, anon, authenticated;
grant select, insert on ai_trade.private_ml_baseline_runs to service_role;
create or replace function ai_trade.prevent_private_ml_mutation()
returns trigger language plpgsql security invoker set search_path = ''
as $$
begin
  raise exception 'Private ML research runs are immutable; insert a new experiment key';
end;
$$;
revoke all on function ai_trade.prevent_private_ml_mutation() from public, anon, authenticated, service_role;
drop trigger if exists prevent_private_ml_mutation on ai_trade.private_ml_baseline_runs;
create trigger prevent_private_ml_mutation before update or delete
on ai_trade.private_ml_baseline_runs for each row
execute function ai_trade.prevent_private_ml_mutation();
