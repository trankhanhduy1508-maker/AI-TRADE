alter table ai_trade.prop_program_config
  add column if not exists automation_approval_evidence text,
  add column if not exists automation_approval_verified_at timestamptz;

alter table ai_trade.runtime_config
  add column if not exists risk_profile_approval_evidence text,
  add column if not exists risk_profile_approved_at timestamptz,
  add column if not exists max_total_volume_demo numeric;

alter table ai_trade.prop_program_config
  drop constraint if exists prop_program_config_approval_evidence_check,
  add constraint prop_program_config_approval_evidence_check
  check (
    not automation_approval_verified
    or (
      nullif(btrim(automation_approval_evidence),'') is not null
      and automation_approval_verified_at is not null
    )
  );

alter table ai_trade.runtime_config
  drop constraint if exists runtime_config_risk_approval_evidence_check,
  add constraint runtime_config_risk_approval_evidence_check
  check (
    not risk_profile_approved
    or (
      nullif(btrim(risk_profile_approval_evidence),'') is not null
      and risk_profile_approved_at is not null
      and max_total_volume_demo is not null
      and max_total_volume_demo > 0
    )
  );

drop view ai_trade.bootcamp_readiness;

create view ai_trade.bootcamp_readiness as
select
  p.provider,
  p.program,
  p.phase,
  p.initial_balance,
  p.initial_balance * (1 + p.profit_target_pct) as target_balance,
  p.initial_balance * (1 - p.max_loss_pct) as loss_floor,
  p.automation_approval_verified,
  p.enabled as execution_enabled,
  r.risk_profile_approved,
  r.demo_send_enabled,
  (
    nullif(btrim(p.automation_approval_evidence),'') is not null
    and p.automation_approval_verified_at is not null
  ) as automation_approval_evidence_present,
  (
    nullif(btrim(r.risk_profile_approval_evidence),'') is not null
    and r.risk_profile_approved_at is not null
  ) as risk_profile_evidence_present,
  (r.max_total_volume_demo is not null and r.max_total_volume_demo > 0)
    as max_total_volume_demo_configured,
  case
    when not p.automation_approval_verified
      or nullif(btrim(p.automation_approval_evidence),'') is null
      or p.automation_approval_verified_at is null
      then 'BLOCKED_APPROVAL'
    when not r.risk_profile_approved
      or nullif(btrim(r.risk_profile_approval_evidence),'') is null
      or r.risk_profile_approved_at is null
      or r.max_total_volume_demo is null
      or r.max_total_volume_demo <= 0
      then 'BLOCKED_RISK_PROFILE'
    when not p.enabled then 'BLOCKED_EXECUTION_DISABLED'
    when not r.demo_send_enabled then 'BLOCKED_DEMO_SEND_DISABLED'
    else 'ELIGIBLE_FOR_DEMO_PREFLIGHT'
  end as readiness
from ai_trade.prop_program_config p
cross join ai_trade.runtime_config r
where p.provider='THE5ERS' and r.id=1;
