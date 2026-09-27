drop view if exists ai_trade.forward_validation_readiness;

create view ai_trade.forward_validation_readiness as
select
  s.strategy_id,
  s.evaluation_state,
  s.closed_trades,
  s.elapsed_days,
  s.markets_with_trades,
  s.positive_markets,
  s.net_r_10bps,
  s.expectancy_r_10bps,
  s.profit_factor_r_10bps,
  s.max_drawdown_r_10bps,
  s.return_to_drawdown_10bps,
  s.net_r_20bps,
  s.market_positive_contribution_dominance,
  s.flagged_bars,
  s.entry_without_visible_stop,
  s.gates,
  s.created_at as evaluated_at,
  false::boolean as broker_orders,
  true::boolean as live_money_locked,
  false::boolean as account_risk_approved
from ai_trade.forward_evaluation_snapshots s
where s.id = (
  select s2.id
  from ai_trade.forward_evaluation_snapshots s2
  where s2.strategy_id=s.strategy_id
  order by s2.created_at desc,s2.id desc
  limit 1
);

revoke all on ai_trade.forward_validation_readiness from anon,authenticated;
