"""MetaApi cloud market/runtime helpers."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
import math
from typing import Any

from src.execution.metaapi_cloud import MetaApiCloudAdapter, _get
from src.execution.risk import RiskContext
from src.execution.safety import SafetySnapshot
from src.rule_engine.types import Bar


_TIMEFRAME_SECONDS = {
    "1m": 60, "2m": 120, "3m": 180, "4m": 240, "5m": 300, "6m": 360,
    "10m": 600, "12m": 720, "15m": 900, "20m": 1200, "30m": 1800,
    "1h": 3600, "2h": 7200, "3h": 10800, "4h": 14400, "6h": 21600,
    "8h": 28800, "12h": 43200, "1d": 86400, "1w": 604800,
}


def _as_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    text = str(value).replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)


async def closed_bars(
    account: Any,
    *,
    symbol: str,
    timeframe: str,
    count: int,
    now: datetime | None = None,
) -> tuple[Bar, ...]:
    if timeframe not in _TIMEFRAME_SECONDS:
        raise ValueError(f"unsupported timeframe: {timeframe}")
    if count < 2:
        raise ValueError("count must be at least 2")
    records = await account.get_historical_candles(
        symbol=symbol,
        timeframe=timeframe,
        start_time=None,
        limit=min(1000, count + 1),
    )
    if not records:
        raise RuntimeError("MetaApi historical candles unavailable")
    current = now or datetime.now(timezone.utc)
    seconds = _TIMEFRAME_SECONDS[timeframe]
    parsed: list[Bar] = []
    for record in records:
        opened = _as_datetime(_get(record, "time"))
        # Historical endpoint may include the currently forming candle. Exclude it.
        if opened + timedelta(seconds=seconds) > current:
            continue
        parsed.append(
            Bar(
                timestamp=opened.astimezone(timezone.utc).isoformat(),
                open=float(_get(record, "open")),
                high=float(_get(record, "high")),
                low=float(_get(record, "low")),
                close=float(_get(record, "close")),
                volume=float(_get(record, "tickVolume", _get(record, "volume", 0.0)) or 0.0),
                closed=True,
            )
        )
    parsed.sort(key=lambda bar: bar.timestamp)
    return tuple(parsed[-count:])


def daily_pnl(connection: Any, *, magic: int, now: datetime | None = None) -> float:
    current = now or datetime.now(timezone.utc)
    start = current.astimezone(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    storage = connection.history_storage
    deals = storage.get_deals_by_time_range(start, current) or ()
    total = 0.0
    for deal in deals:
        if int(_get(deal, "magic", 0) or 0) != magic:
            continue
        for field in ("profit", "commission", "swap", "fee"):
            total += float(_get(deal, field, 0.0) or 0.0)
    return total


async def runtime_inputs_for_symbol(
    adapter: MetaApiCloudAdapter,
    *,
    symbol: str,
    own_open_positions: int,
    current_symbol_volume: float,
    daily_loss_value: float,
    max_tick_age_seconds: float,
    manual_pause: bool = False,
    risk_allowed: bool = False,
    reconciled: bool = False,
    state_known: bool = False,
    now: datetime | None = None,
) -> tuple[float, float, SafetySnapshot, RiskContext]:
    current = now or datetime.now(timezone.utc)
    bid, ask, tick_time = await adapter.quote(symbol)
    contract = await adapter.symbol_contract(symbol)
    spread_points = (ask - bid) / contract.point
    if tick_time is None:
        fresh = False
    else:
        tick_dt = _as_datetime(tick_time)
        age = (current - tick_dt).total_seconds()
        fresh = math.isfinite(age) and 0 <= age <= max_tick_age_seconds
    snapshot = SafetySnapshot(
        connected=True,
        data_fresh=fresh,
        state_known=state_known is True,
        reconciled=reconciled is True,
        risk_allowed=risk_allowed is True,
        manual_pause=manual_pause,
    )
    context = RiskContext(
        open_positions=own_open_positions,
        spread_points=spread_points,
        daily_loss=daily_loss_value,
        current_symbol_volume=current_symbol_volume,
    )
    return bid, ask, snapshot, context
