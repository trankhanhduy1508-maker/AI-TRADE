create table if not exists ai_trade.training_arena_watch (
 strategy_id text not null, symbol text not null, asset_class text not null,
 status text not null, last_signal text, last_bar_ts timestamptz,
 updated_at timestamptz not null default now(), primary key(strategy_id,symbol)
);
alter table ai_trade.training_arena_watch enable row level security;
revoke all on ai_trade.training_arena_watch from public,anon,authenticated;
