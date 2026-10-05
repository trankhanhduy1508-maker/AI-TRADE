"""Runtime data bridge for autonomous MT5 DEMO trading."""

from dataclasses import dataclass
from datetime import datetime, timezone
import math
from typing import Any

from src.execution.risk import RiskContext
from src.execution.safety import SafetySnapshot
from src.rule_engine.types import Bar


@dataclass(frozen=True)
class RuntimeMarketState:
    bars: tuple[Bar, ...]
    bid: float
    ask: float
    spread_points: float
    daily_pnl: float
    tick_time: datetime


def _value(record: Any, name: str) -> Any:
    try:
        return record[name]
    except (KeyError, TypeError, IndexError):
        return getattr(record, name)


def closed_bars(mt5: Any, symbol: str, timeframe: int, count: int) -> tuple[Bar, ...]:
    if count < 2:
        raise ValueError("count must be at least 2")
    records = mt5.copy_rates_from_pos(symbol, timeframe, 1, count)
    if records is None or len(records) == 0:
        raise RuntimeError(f"copy_rates_from_pos failed: {mt5.last_error()}")
    bars = []
    for row in records:
        try:
            epoch = float(_value(row, "time"))
            prices = tuple(float(_value(row, name)) for name in ("open", "high", "low", "close"))
            volume = float(_value(row, "tick_volume"))
            if (not math.isfinite(epoch) or epoch <= 0 or not epoch.is_integer()
                    or not all(math.isfinite(v) and v > 0 for v in prices)
                    or not math.isfinite(volume) or volume < 0
                    or prices[1] < max(prices[0], prices[2], prices[3])
                    or prices[2] > min(prices[0], prices[1], prices[3])):
                raise ValueError("invalid broker bar")
            timestamp = datetime.fromtimestamp(int(epoch), timezone.utc).isoformat()
        except (AttributeError, KeyError, TypeError, ValueError, OverflowError, OSError) as exc:
            raise RuntimeError("BROKER_BAR_INVALID") from exc
        bars.append(Bar(timestamp=timestamp, open=prices[0], high=prices[1],
                        low=prices[2], close=prices[3], volume=volume, closed=True))
    # Do not silently reorder/deduplicate broker records: doing so can hide
    # stale or inconsistent prices and misrepresent a closed-bar checkpoint.
    if any(current.timestamp <= previous.timestamp for previous, current in zip(bars, bars[1:])):
        raise RuntimeError("BROKER_BARS_OUT_OF_ORDER")
    return tuple(bars)


def current_tick(mt5: Any, symbol: str) -> tuple[float, float, datetime]:
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        raise RuntimeError(f"symbol_info_tick failed: {mt5.last_error()}")
    bid = float(tick.bid)
    ask = float(tick.ask)
    if not math.isfinite(bid) or not math.isfinite(ask) or bid <= 0 or ask <= 0 or bid > ask:
        raise RuntimeError("invalid MT5 tick")
    tick_epoch = float(getattr(tick, "time", 0.0) or 0.0)
    if tick_epoch <= 0:
        raise RuntimeError("tick has no timestamp")
    return bid, ask, datetime.fromtimestamp(tick_epoch, timezone.utc)


def symbol_spread_points(mt5: Any, symbol: str, bid: float, ask: float) -> float:
    info = mt5.symbol_info(symbol)
    if info is None:
        raise RuntimeError(f"symbol_info failed: {mt5.last_error()}")
    point = float(info.point)
    if not math.isfinite(point) or point <= 0:
        raise RuntimeError("invalid symbol point")
    return (ask - bid) / point


def daily_pnl(mt5: Any, *, magic: int | None, now: datetime | None = None) -> float:
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    start = current.astimezone(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    deals = mt5.history_deals_get(start, current)
    if deals is None:
        raise RuntimeError(f"history_deals_get failed: {mt5.last_error()}")
    total = 0.0
    for deal in deals:
        if magic is not None and int(getattr(deal, "magic", 0) or 0) != magic:
            continue
        try:
            values = tuple(float(getattr(deal, name, 0.0))
                           for name in ("profit", "commission", "swap", "fee"))
        except (TypeError, ValueError, OverflowError) as exc:
            raise RuntimeError("BROKER_DAILY_PNL_INVALID") from exc
        if not all(math.isfinite(value) for value in values):
            raise RuntimeError("BROKER_DAILY_PNL_INVALID")
        total += sum(values)
    if not math.isfinite(total):
        raise RuntimeError("BROKER_DAILY_PNL_INVALID")
    return total


def collect_market_state(
    mt5: Any,
    *,
    symbol: str,
    timeframe: int,
    count: int,
    magic: int,
) -> RuntimeMarketState:
    bars = closed_bars(mt5, symbol, timeframe, count)
    bid, ask, tick_time = current_tick(mt5, symbol)
    spread = symbol_spread_points(mt5, symbol, bid, ask)
    pnl = daily_pnl(mt5, magic=magic)
    return RuntimeMarketState(bars, bid, ask, spread, pnl, tick_time)


def runtime_snapshot(
    *,
    market: RuntimeMarketState,
    now: datetime,
    reconciled: bool,
    max_tick_age_seconds: float,
    risk_allowed: bool = False,
    manual_pause: bool = False,
) -> SafetySnapshot:
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    if (isinstance(max_tick_age_seconds, bool)
            or not isinstance(max_tick_age_seconds, (int, float))
            or not math.isfinite(max_tick_age_seconds) or max_tick_age_seconds <= 0):
        raise ValueError("INVALID_TICK_AGE_LIMIT")
    age = (now - market.tick_time).total_seconds()
    fresh = 0 <= age <= max_tick_age_seconds
    return SafetySnapshot(
        connected=True,
        data_fresh=fresh,
        state_known=True,
        reconciled=reconciled,
        risk_allowed=risk_allowed,
        manual_pause=manual_pause,
    )


def runtime_risk_context(
    *,
    own_open_positions: int,
    market: RuntimeMarketState,
    current_symbol_volume: float = 0.0,
) -> RiskContext:
    return RiskContext(
        open_positions=own_open_positions,
        spread_points=market.spread_points,
        daily_loss=market.daily_pnl,
        current_symbol_volume=current_symbol_volume,
    )


def verified_demo_risk_context(
    mt5: Any,
    *,
    expected_login: str,
    expected_server: str,
    symbol: str,
    market: RuntimeMarketState,
    now: datetime | None = None,
) -> RiskContext:
    """Rebuild account-wide risk data directly from an authenticated MT5 DEMO.

    The caller must source expected_login/server from the authorized Founder
    binding, symbol/timeframe from the frozen strategy and market from fresh
    broker quotes. This function never authorizes a trade or changes a gate.
    """
    if not expected_login.isascii() or not expected_login.isdecimal() or not expected_server:
        raise RuntimeError("BROKER_IDENTITY_REQUIRED")

    def confirmed_account() -> Any:
        account = mt5.account_info()
        if (
            account is None
            or getattr(account, "trade_mode", None) != 0
            or str(getattr(account, "login", "")) != expected_login
            or getattr(account, "server", None) != expected_server
            or getattr(account, "currency", None) != "USD"
        ):
            raise RuntimeError("BROKER_DEMO_IDENTITY_MISMATCH")
        return account

    before = confirmed_account()
    try:
        equity = float(before.equity)
        balance = float(before.balance)
    except (AttributeError, TypeError, ValueError) as exc:
        raise RuntimeError("BROKER_BALANCE_EQUITY_REQUIRED") from exc
    if not all(math.isfinite(v) and v > 0 for v in (equity, balance)):
        raise RuntimeError("BROKER_BALANCE_EQUITY_INVALID")

    info = mt5.symbol_info(symbol)
    if info is None:
        raise RuntimeError("BROKER_SYMBOL_METADATA_REQUIRED")
    try:
        tick_size = float(info.trade_tick_size)
        # Loss-side tick value is safer than profit-side value, which can differ.
        tick_value = float(info.trade_tick_value_loss)
    except (AttributeError, TypeError, ValueError) as exc:
        raise RuntimeError("BROKER_LOSS_TICK_VALUE_REQUIRED") from exc
    if not all(math.isfinite(v) and v > 0 for v in (tick_size, tick_value)):
        raise RuntimeError("BROKER_LOSS_TICK_VALUE_INVALID")

    positions = mt5.positions_get()
    if positions is None:
        raise RuntimeError("BROKER_POSITIONS_UNAVAILABLE")
    symbol_volume = 0.0
    for position in positions:
        try:
            volume = float(position.volume)
            position_symbol = position.symbol
        except (AttributeError, TypeError, ValueError) as exc:
            raise RuntimeError("BROKER_POSITION_INCOMPLETE") from exc
        if not math.isfinite(volume) or volume <= 0 or not isinstance(position_symbol, str):
            raise RuntimeError("BROKER_POSITION_INVALID")
        if position_symbol == symbol:
            symbol_volume += volume

    # Include other positions and all account deals, not just this strategy's
    # magic number. Negative floating P/L is never offset by floating gains.
    closed_account_pnl = daily_pnl(mt5, magic=None, now=now)
    if not math.isfinite(closed_account_pnl):
        raise RuntimeError("BROKER_DAILY_PNL_INVALID")
    daily_account_loss = closed_account_pnl + min(equity - balance, 0.0)
    if not math.isfinite(daily_account_loss):
        raise RuntimeError("BROKER_DAILY_PNL_INVALID")

    # Fence account switching during metadata, positions or history reads.
    confirmed_account()
    return RiskContext(
        open_positions=len(positions),
        spread_points=market.spread_points,
        daily_loss=daily_account_loss,
        current_symbol_volume=symbol_volume,
        account_equity=equity,
        tick_size=tick_size,
        tick_value_per_lot=tick_value,
        account_currency="USD",
    )
