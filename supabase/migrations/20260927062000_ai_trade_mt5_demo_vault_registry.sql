create table if not exists ai_trade.mt5_demo_accounts (
  account_login bigint primary key,
  server text not null,
  account_type text not null default 'DEMO' check (account_type='DEMO'),
  password_secret_id uuid not null,
  investor_password_secret_id uuid,
  source text not null,
  source_run_id text,
  created_at timestamptz not null default now(),
  last_verified_at timestamptz,
  is_active boolean not null default true
);

revoke all on ai_trade.mt5_demo_accounts from anon, authenticated;

create or replace function ai_trade.upsert_mt5_demo_account(
  p_login bigint,
  p_server text,
  p_password text,
  p_investor_password text,
  p_source text,
  p_source_run_id text
) returns void
language plpgsql
security definer
set search_path = ai_trade, vault, public
as $$
declare
  v_password_name text := 'AI_TRADE_MT5_DEMO_PASSWORD_' || p_login::text;
  v_investor_name text := 'AI_TRADE_MT5_DEMO_INVESTOR_PASSWORD_' || p_login::text;
  v_password_id uuid;
  v_investor_id uuid;
begin
  if p_login <= 0 or coalesce(p_server,'')='' or coalesce(p_password,'')='' then
    raise exception 'invalid demo account payload';
  end if;

  select id into v_password_id from vault.secrets where name=v_password_name;
  if v_password_id is null then
    v_password_id := vault.create_secret(
      p_password,
      v_password_name,
      'AI-TRADE MT5 DEMO master password',
      null
    );
  else
    perform vault.update_secret(
      v_password_id,
      p_password,
      v_password_name,
      'AI-TRADE MT5 DEMO master password',
      null
    );
  end if;

  if coalesce(p_investor_password,'')<>'' then
    select id into v_investor_id from vault.secrets where name=v_investor_name;
    if v_investor_id is null then
      v_investor_id := vault.create_secret(
        p_investor_password,
        v_investor_name,
        'AI-TRADE MT5 DEMO investor password',
        null
      );
    else
      perform vault.update_secret(
        v_investor_id,
        p_investor_password,
        v_investor_name,
        'AI-TRADE MT5 DEMO investor password',
        null
      );
    end if;
  end if;

  insert into ai_trade.mt5_demo_accounts(
    account_login,server,account_type,password_secret_id,
    investor_password_secret_id,source,source_run_id,last_verified_at,is_active
  ) values(
    p_login,p_server,'DEMO',v_password_id,v_investor_id,
    p_source,p_source_run_id,now(),true
  )
  on conflict(account_login) do update set
    server=excluded.server,
    password_secret_id=excluded.password_secret_id,
    investor_password_secret_id=excluded.investor_password_secret_id,
    source=excluded.source,
    source_run_id=excluded.source_run_id,
    last_verified_at=now(),
    is_active=true;
end;
$$;

revoke all on function ai_trade.upsert_mt5_demo_account(bigint,text,text,text,text,text) from public;
