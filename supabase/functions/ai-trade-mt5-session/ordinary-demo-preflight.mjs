// Read-only evaluation. This function never authorizes or submits an order.
export function ordinaryDemoPreflight(context = {}) {
  context = context && typeof context === 'object' ? context : {};
  const session = context.session ?? {}, config = context.config ?? {}, policy = context.policy ?? {};
  const broker = context.broker ?? {}, controls = context.controls ?? {};
  const blockers = [];
  const fraction = value => typeof value === 'number' && Number.isFinite(value) && value > 0 && value <= 1;
  const login = String(session.account_login ?? '');
  if (!login || session.server !== 'MetaQuotes-Demo' || session.trade_permission !== 'TRADING_ALLOWED') blockers.push('SESSION_NOT_TRADABLE');
  if (config.enabled !== true) blockers.push('RUNTIME_DISABLED');
  if (config.demo_send_enabled !== true) blockers.push('DEMO_SEND_DISABLED');
  if (context.providerConfigured !== true) blockers.push('PROVIDER_NOT_READY');
  const approved = policy.profile === 'ORDINARY_MT5_DEMO' && policy.approved === true
    && String(policy.account_login ?? '') === login && policy.server === session.server
    && typeof policy.approval_evidence === 'string' && policy.approval_evidence.trim().length > 0
    && fraction(policy.max_trade_risk_fraction) && fraction(policy.max_portfolio_risk_fraction)
    && policy.max_portfolio_risk_fraction >= policy.max_trade_risk_fraction
    && fraction(policy.max_drawdown_fraction)
    && Number.isInteger(policy.max_consecutive_losses) && policy.max_consecutive_losses > 0
    && typeof policy.max_total_volume === 'number' && Number.isFinite(policy.max_total_volume) && policy.max_total_volume > 0;
  if (!approved) blockers.push('RISK_NOT_APPROVED');
  if (!(broker.verified === true && broker.fresh === true && broker.mode === 'DEMO'
    && String(broker.login ?? '') === login && broker.server === session.server
    && broker.tradeAllowed === true && broker.readOnly === false)) blockers.push('BROKER_STATE_UNVERIFIED');
  if (controls.known !== true) blockers.push('CONTROL_STATE_UNKNOWN');
  if (controls.kill_active !== false || controls.paused !== false) blockers.push('EXECUTION_PAUSED');
  if (controls.reconciled !== true) blockers.push('RECONCILIATION_REQUIRED');
  if (config.strategy_id !== 'TF-013A-FORWARD-DIVERSIFIED-TREND' || context.strategyValidated !== true) blockers.push('STRATEGY_NOT_VALIDATED');
  if (context.executionLaneImplemented !== true) blockers.push('EXECUTION_LANE_UNAVAILABLE');
  return {profile:'ORDINARY_MT5_DEMO',prop_approval_required:false,preflight_ready:blockers.length === 0,
    blockers,order_send_enabled:false,orders_sent:0,live_money_locked:true};
}
