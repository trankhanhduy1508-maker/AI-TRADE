create extension if not exists pgcrypto;

create table if not exists ai_trade.mt5_demo_credentials (
  id integer primary key default 1 check (id = 1),
  login bigint not null,
  server text not null default 'MetaQuotes-Demo',
  email text,
  password_cipher bytea not null,
  investor_password_cipher bytea,
  is_demo boolean not null default true check (is_demo = true),
  verified boolean not null default false,
  account_type integer,
  balance numeric,
  currency text,
  leverage integer,
  trade_allowed boolean,
  created_at timestamptz not null default now(),
  verified_at timestamptz,
  updated_at timestamptz not null default now()
);

revoke all on ai_trade.mt5_demo_credentials from anon, authenticated;

comment on table ai_trade.mt5_demo_credentials is
  'Encrypted MetaQuotes-Demo credentials only. Live/funded credentials are forbidden.';
