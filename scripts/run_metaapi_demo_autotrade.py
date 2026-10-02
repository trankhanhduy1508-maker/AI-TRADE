"""Compatibility entrypoint for the one supported MetaApi cloud runner.

The old REST/transport adapter was removed. Never invoke a stale execution
backend or turn a command-line flag into DEMO order authorization.
"""
from __future__ import annotations

import argparse
import asyncio
import os


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol")
    parser.add_argument("--timeframe")
    parser.add_argument("--strategy")
    parser.add_argument("--poll-seconds", type=float)
    parser.add_argument("--max-spread-points", type=float)
    parser.add_argument("--max-daily-loss-demo", type=float)
    parser.add_argument("--max-tick-age-seconds", type=float)
    parser.add_argument("--state-dir")
    parser.add_argument("--exit-mode", choices=("TRAILING_ONLY", "FIXED_TP", "PARTIAL_THEN_TRAIL"))
    parser.add_argument("--max-pyramid-adds", type=int)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--enable-demo-send", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.enable_demo_send:
        print("CONFIG_BLOCKED: compatibility CLI cannot authorize DEMO orders; "
              "use the canonical runner only after server-side approval evidence")
        return 78
    mapping = {
        "symbol": "AI_TRADE_SYMBOL",
        "timeframe": "AI_TRADE_TIMEFRAME",
        "strategy": "AI_TRADE_STRATEGY",
        "poll_seconds": "AI_TRADE_POLL_SECONDS",
        "max_spread_points": "AI_TRADE_MAX_SPREAD_POINTS",
        "max_daily_loss_demo": "AI_TRADE_MAX_DAILY_LOSS_DEMO",
        "max_tick_age_seconds": "AI_TRADE_MAX_TICK_AGE_SECONDS",
        "state_dir": "AI_TRADE_STATE_DIR",
        "exit_mode": "AI_TRADE_EXIT_MODE",
        "max_pyramid_adds": "AI_TRADE_MAX_PYRAMID_ADDS",
    }
    for setting, env_name in mapping.items():
        value = getattr(args, setting)
        if value is not None:
            os.environ[env_name] = str(value)
    os.environ["AI_TRADE_ONCE"] = "YES" if args.once else "NO"
    os.environ["AI_TRADE_ENABLE_DEMO_SEND"] = "NO"
    from scripts.run_metaapi_cloud_autotrade import main as run_current
    return asyncio.run(run_current())


if __name__ == "__main__":
    raise SystemExit(main())
