create table if not exists ai_trade.mt5_session_e2e_probe (
  id smallint primary key check (id = 1),
  raw_token text not null,
  created_at timestamptz not null default now(),
  expires_at timestamptz not null
);
alter table ai_trade.mt5_session_e2e_probe enable row level security;
revoke all on table ai_trade.mt5_session_e2e_probe from anon, authenticated;
comment on table ai_trade.mt5_session_e2e_probe is
  'Ephemeral QA-only opaque session token. Never stores MT5 passwords or provider secrets.';
