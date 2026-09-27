"""Runtime conversion helpers for MetaApi cloud market data."""

from __future__ import annotations

from datetime import datetime, timezone
import math
from typing import Any

from src.execution.metaapi_cloud import MetaApiCloudAdapter
from src.execution.mt5_runtime import RuntimeMarketState
from src.rule_engine.types import Bar


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def collect_metaapi_market_state(
    adapter: MetaApiCloudAdapter,
    *,
    symbol: str,
    timeframe: str,
    count: int,
    magic: int,
) -> RuntimeMarketState:
    rows = adapter.historical_candles(symbol, timeframe, limit=count)
    if not rows:
        raise RuntimeError("MetaApi returned no historical candles")
    bars = tuple(
        Bar(
            timestamp=str(row["time"]),
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
            volume=float(row.get("tickVolume", row.get("volume", 0.0)) or 0.0),
            closed=True,
        )
        for row in sorted(rows, key=lambda item: str(item["time"]))
    )
    price = adapter.current_price(symbol)
    bid = float(price["bid"])
    ask = float(price["ask"])
    tick_time = _parse_time(str(price["time"]))
    contract = adapter.symbol_contract(symbol)
    spread_points = (ask - bid) / contract.tick_size
    if not math.isfinite(spread_points) or spread_points < 0:
        raise RuntimeError("invalid MetaApi spread")
    pnl = adapter.daily_pnl(magic=magic)
    return RuntimeMarketState(bars, bid, ask, spread_points, pnl, tick_time)
