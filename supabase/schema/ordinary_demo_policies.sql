create table ai_trade.ordinary_demo_policies (
 account_login bigint not null check(account_login>0),
 server text not null check(server='MetaQuotes-Demo'),
 policy jsonb not null check(policy->>'profile'='ORDINARY_MT5_DEMO'),
 approved boolean not null default false,
 approval_evidence text not null check(length(trim(approval_evidence))>0),
 updated_at timestamptz not null default now(),
 primary key(account_login,server)
);
alter table ai_trade.ordinary_demo_policies enable row level security;
revoke all on ai_trade.ordinary_demo_policies from public,anon,authenticated;
grant select on ai_trade.ordinary_demo_policies to service_role;
