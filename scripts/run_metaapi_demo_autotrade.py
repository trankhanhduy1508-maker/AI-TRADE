"""Cloud-only autonomous DEMO runner using MetaApi instead of a Windows MT5 terminal."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import sys
import time


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="EURUSD")
    parser.add_argument("--timeframe", default="15m")
    parser.add_argument("--strategy", default="strategies/TF_004_TIME_SERIES_CHANNEL.json")
    parser.add_argument("--region", default=os.getenv("METAAPI_REGION", "new-york"))
    parser.add_argument("--poll-seconds", type=float, default=10.0)
    parser.add_argument("--bars", type=int, default=250)
    parser.add_argument("--max-spread-points", type=float, default=30.0)
    parser.add_argument("--max-daily-loss-demo", type=float, default=10.0)
    parser.add_argument("--max-tick-age-seconds", type=float, default=120.0)
    parser.add_argument("--state-dir", default=".runtime/metaapi_demo")
    parser.add_argument(
        "--exit-mode",
        choices=["TRAILING_ONLY", "FIXED_TP", "PARTIAL_THEN_TRAIL"],
        default="TRAILING_ONLY",
    )
    parser.add_argument("--max-pyramid-adds", type=int, default=0)
    parser.add_argument("--enable-demo-send", action="store_true")
    parser.add_argument("--once", action="store_true")
    return parser


def main() -> int:
    args = _parser().parse_args()

    from src.backtest.spec import load_strategy_spec
    from src.execution.auto_engine import AutoTradeConfig, DemoAutoTradeEngine
    from src.execution.coordinator import ExecutionCoordinator
    from src.execution.metaapi_cloud import MetaApiCloudAdapter, MetaApiCloudConfig
    from src.execution.metaapi_runtime import collect_metaapi_market_state
    from src.execution.mt5_runtime import runtime_risk_context, runtime_snapshot
    from src.execution.position_controller import PositionActionCoordinator
    from src.execution.position_lifecycle import ExitMode, PositionLifecycleManager
    from src.execution.position_state import PositionStateStore
    from src.execution.risk import IndependentRiskEngine, RiskLimits
    from src.execution.safety import KillSwitchStore, SafetyGate
    from src.strategies.time_series_momentum import TimeSeriesMomentumEvaluator

    token = os.getenv("METAAPI_TOKEN", "").strip()
    account_id = os.getenv("METAAPI_ACCOUNT_ID", "").strip()
    if not token or not account_id:
        raise SystemExit("METAAPI_TOKEN and METAAPI_ACCOUNT_ID are required runtime secrets")
    if args.poll_seconds < 1:
        raise SystemExit("poll-seconds must be >= 1")

    state_dir = Path(args.state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    spec = load_strategy_spec(args.strategy)
    if spec.signal_model != "TIME_SERIES_MOMENTUM":
        raise SystemExit("cloud runner currently requires TIME_SERIES_MOMENTUM")

    adapter = MetaApiCloudAdapter(
        MetaApiCloudConfig(
            account_id=account_id,
            token=token,
            region=args.region,
            client_base_url=os.getenv("METAAPI_CLIENT_BASE_URL") or None,
            market_base_url=os.getenv("METAAPI_MARKET_BASE_URL") or None,
        ),
        ledger_path=state_dir / "order_intents.sqlite",
        allow_order_send=args.enable_demo_send,
    )
    adapter.connect()  # hard-fails on a non-DEMO account

    kill = KillSwitchStore(state_dir / "kill_switch.sqlite")
    if kill.is_active() and args.enable_demo_send:
        kill.deactivate("explicit cloud DEMO runner start")

    risk = IndependentRiskEngine(
        RiskLimits(
            max_volume=0.01,
            max_open_positions=1,
            max_spread_points=args.max_spread_points,
            max_daily_loss=args.max_daily_loss_demo,
            max_total_volume_per_symbol=0.01 * (1 + max(0, args.max_pyramid_adds)),
        )
    )
    state = PositionStateStore(state_dir / "positions.sqlite")
    entry = ExecutionCoordinator(adapter, SafetyGate(kill), risk_engine=risk)
    controller = PositionActionCoordinator(PositionLifecycleManager(adapter), state)
    evaluator = TimeSeriesMomentumEvaluator()
    config = AutoTradeConfig(
        strategy_id=spec.strategy_id,
        symbol=args.symbol,
        exit_mode=ExitMode(args.exit_mode),
        reward_risk=spec.reward_risk,
        trailing_lookback=spec.exit_lookback_bars,
        max_pyramid_adds=max(0, args.max_pyramid_adds),
    )
    engine = DemoAutoTradeEngine(
        config=config,
        adapter=adapter,
        entry=entry,
        positions=controller,
        state=state,
        signal_evaluator=lambda history: evaluator(history, spec),
    )

    last_bar = None
    try:
        while True:
            owned = engine.reconcile_owned_positions()
            market = collect_metaapi_market_state(
                adapter,
                symbol=args.symbol,
                timeframe=args.timeframe,
                count=args.bars,
                magic=config.magic,
            )
            bar_id = market.bars[-1].timestamp
            if bar_id != last_bar:
                snapshot = runtime_snapshot(
                    market=market,
                    now=datetime.now(timezone.utc),
                    reconciled=True,
                    max_tick_age_seconds=args.max_tick_age_seconds,
                    risk_allowed=True,
                )
                context = runtime_risk_context(
                    own_open_positions=len(owned),
                    market=market,
                    current_symbol_volume=sum(position.volume for position in owned),
                )
                outcome = engine.on_closed_bar(
                    market.bars,
                    bid=market.bid,
                    ask=market.ask,
                    snapshot=snapshot,
                    risk_context=context,
                )
                print(f"{bar_id} {args.symbol} {outcome.status} {outcome.detail}", flush=True)
                last_bar = bar_id
            if args.once:
                break
            time.sleep(args.poll_seconds)
    except KeyboardInterrupt:
        return 0
    finally:
        state.close()
        kill.close()
        adapter.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
