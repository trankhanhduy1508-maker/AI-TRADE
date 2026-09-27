create table if not exists ai_trade.mt5_demo_mailbox (
  id integer primary key default 1 check (id = 1),
  provider text not null default 'mail.tm' check (provider = 'mail.tm'),
  address text not null,
  password_cipher bytea not null,
  provider_account_id text,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

revoke all on ai_trade.mt5_demo_mailbox from anon, authenticated;

comment on table ai_trade.mt5_demo_mailbox is
  'Service-owned temporary mailbox for MetaQuotes DEMO verification only. Password is pgcrypto-encrypted.';
