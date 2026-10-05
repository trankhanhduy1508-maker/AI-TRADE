-- Only read-only feed credential hashes; keys belong in private runtime config.
create table if not exists ai_trade.paper_feed_readers (
  id text primary key,
  key_hash text not null unique,
  enabled boolean not null default true,
  created_at timestamptz not null default now()
);
alter table ai_trade.paper_feed_readers enable row level security;
revoke all on ai_trade.paper_feed_readers from public, anon, authenticated;
