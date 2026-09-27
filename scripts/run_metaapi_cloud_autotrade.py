"""24/7 cloud-native AI-TRADE runner using MetaApi. No Windows PC required."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
import sys


async def main() -> int:
    token = os.getenv("METAAPI_TOKEN", "").strip()
    account_id = os.getenv("METAAPI_ACCOUNT_ID", "").strip()
    if not token or not account_id:
        print("CONFIG_BLOCKED: METAAPI_TOKEN and METAAPI_ACCOUNT_ID are required", flush=True)
        return 78

    from metaapi_cloud_sdk import MetaApi

    from src.backtest.spec import load_strategy_spec
    from src.execution.cloud_auto_engine import CloudAutoTradeConfig, CloudAutoTradeEngine
    from src.execution.metaapi_cloud import MetaApiCloudAdapter
    from src.execution.metaapi_runtime import closed_bars, daily_pnl, runtime_inputs_for_symbol
    from src.execution.position_lifecycle import ExitMode
    from src.execution.position_state import PositionStateStore
    from src.execution.risk import IndependentRiskEngine, RiskLimits
    from src.execution.safety import KillSwitchStore, SafetyGate
    from src.strategies.time_series_momentum import TimeSeriesMomentumEvaluator

    symbol = os.getenv("AI_TRADE_SYMBOL", "EURUSD").strip()
    timeframe = os.getenv("AI_TRADE_TIMEFRAME", "15m").strip()
    strategy_path = os.getenv(
        "AI_TRADE_STRATEGY", "strategies/TF_004_TIME_SERIES_CHANNEL.json"
    )
    state_dir = Path(os.getenv("AI_TRADE_STATE_DIR", "/data/ai-trade"))
    state_dir.mkdir(parents=True, exist_ok=True)
    allow_send = os.getenv("AI_TRADE_ENABLE_DEMO_SEND", "").upper() == "YES"
    poll_seconds = max(5.0, float(os.getenv("AI_TRADE_POLL_SECONDS", "30")))
    max_tick_age = float(os.getenv("AI_TRADE_MAX_TICK_AGE_SECONDS", "120"))
    max_spread = float(os.getenv("AI_TRADE_MAX_SPREAD_POINTS", "30"))
    max_daily_loss = float(os.getenv("AI_TRADE_MAX_DAILY_LOSS_DEMO", "10"))
    max_pyramid_adds = max(0, int(os.getenv("AI_TRADE_MAX_PYRAMID_ADDS", "0")))
    once = os.getenv("AI_TRADE_ONCE", "").upper() == "YES"

    api = MetaApi(token)
    account = await api.metatrader_account_api.get_account(account_id=account_id)
    connection = account.get_streaming_connection()
    adapter = MetaApiCloudAdapter(
        account,
        connection,
        allow_order_send=allow_send,
        ledger_path=state_dir / "cloud_order_intents.sqlite",
    )
    await adapter.connect()
    await connection.subscribe_to_market_data(symbol)

    spec = load_strategy_spec(strategy_path)
    if spec.signal_model != "TIME_SERIES_MOMENTUM":
        raise RuntimeError("cloud runner currently requires TIME_SERIES_MOMENTUM")

    kill = KillSwitchStore(state_dir / "kill_switch.sqlite")
    if kill.is_active() and allow_send:
        kill.deactivate("explicit AI_TRADE_ENABLE_DEMO_SEND=YES cloud start")
    position_state = PositionStateStore(state_dir / "positions.sqlite")
    risk = IndependentRiskEngine(
        RiskLimits(
            max_volume=0.01,
            max_open_positions=1,
            max_spread_points=max_spread,
            max_daily_loss=max_daily_loss,
            max_total_volume_per_symbol=0.01 * (1 + max_pyramid_adds),
        )
    )
    evaluator = TimeSeriesMomentumEvaluator()
    engine = CloudAutoTradeEngine(
        config=CloudAutoTradeConfig(
            strategy_id=spec.strategy_id,
            symbol=symbol,
            exit_mode=ExitMode(os.getenv("AI_TRADE_EXIT_MODE", "TRAILING_ONLY")),
            reward_risk=spec.reward_risk,
            trailing_lookback=spec.exit_lookback_bars,
            max_pyramid_adds=max_pyramid_adds,
        ),
        adapter=adapter,
        gate=SafetyGate(kill),
        risk_engine=risk,
        state=position_state,
        signal_evaluator=lambda history: evaluator(history, spec),
    )

    last_bar = None
    try:
        while True:
            owned = await engine.reconcile_owned_positions()
            bars = await closed_bars(
                account,
                symbol=symbol,
                timeframe=timeframe,
                count=max(50, spec.lookback_bars + spec.exit_lookback_bars + 5),
            )
            if not bars:
                print("NO_ACTION no closed bars", flush=True)
            elif bars[-1].timestamp != last_bar:
                pnl = daily_pnl(connection, magic=engine.config.magic)
                bid, ask, snapshot, context = await runtime_inputs_for_symbol(
                    adapter,
                    symbol=symbol,
                    own_open_positions=len(owned),
                    current_symbol_volume=sum(p.volume for p in owned),
                    daily_loss_value=pnl,
                    max_tick_age_seconds=max_tick_age,
                )
                outcome = await engine.on_closed_bar(
                    bars,
                    bid=bid,
                    ask=ask,
                    snapshot=snapshot,
                    risk_context=context,
                )
                print(
                    f"{bars[-1].timestamp} {symbol} {outcome.status} {outcome.detail}",
                    flush=True,
                )
                last_bar = bars[-1].timestamp
            if once:
                break
            await asyncio.sleep(poll_seconds)
    finally:
        position_state.close()
        kill.close()
        await adapter.close()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
