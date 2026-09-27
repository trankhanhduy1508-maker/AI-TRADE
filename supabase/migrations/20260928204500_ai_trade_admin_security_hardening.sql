create table if not exists ai_trade.dashboard_symbol_specs (
  market text primary key,
  broker_symbol text,
  supported boolean not null default false,
  description text,
  digits integer,
  contract_size numeric,
  tick_size numeric,
  tick_value numeric,
  currency_base text,
  currency_profit text,
  currency_margin text,
  calc_mode integer,
  source text not null,
  observed_at timestamptz not null default now(),
  details jsonb not null default '{}'::jsonb
);

do $$
declare r record;
begin
  for r in
    select c.relname
    from pg_class c
    join pg_namespace n on n.oid=c.relnamespace
    where n.nspname='ai_trade' and c.relkind='r'
  loop
    execute format('alter table ai_trade.%I enable row level security',r.relname);
    execute format('revoke all on table ai_trade.%I from anon, authenticated',r.relname);
    execute format('drop policy if exists %I on ai_trade.%I','deny_api_access',r.relname);
    execute format(
      'create policy %I on ai_trade.%I for all to anon, authenticated using (false) with check (false)',
      'deny_api_access',r.relname
    );
  end loop;
end $$;

revoke usage on schema ai_trade from anon, authenticated;
