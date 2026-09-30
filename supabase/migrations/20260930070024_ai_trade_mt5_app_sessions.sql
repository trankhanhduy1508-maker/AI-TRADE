create table if not exists ai_trade.mt5_app_sessions (
  token_hash text primary key check (token_hash ~ '^[0-9a-f]{64}$'),
  account_login bigint not null,
  server text not null check (server = 'MetaQuotes-Demo'),
  trade_permission text not null check (trade_permission in ('TRADING_ALLOWED','READ_ONLY')),
  remember boolean not null default false,
  created_at timestamptz not null default now(),
  expires_at timestamptz not null,
  revoked_at timestamptz,
  last_seen_at timestamptz not null default now()
);
alter table ai_trade.mt5_app_sessions enable row level security;
revoke all on table ai_trade.mt5_app_sessions from anon, authenticated;
create index if not exists mt5_app_sessions_expiry_idx
  on ai_trade.mt5_app_sessions (expires_at)
  where revoked_at is null;
comment on table ai_trade.mt5_app_sessions is
  'Opaque DEMO MT5 app sessions only. Never stores broker passwords or provider secrets.';
