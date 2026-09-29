"""CWS METHOD LAB V1: causal, research-only signal and closed-trade feedback.

This module cannot send orders. Caller-supplied audit flags are NOT external proof.
No execution-cost study, net PnL, backtest edge claim or automatic tuning.
"""
from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass
import math
import statistics
import time

CHANNEL = 55
SMA_PERIOD = 200
SMA_SLOPE_LAG = 20
ATR_PERIOD = 20
TRAIL = 20
INITIAL_ATR_MULTIPLE = 2.5
BREAKOUT_ATR_BUFFER = 0.25
BODY_ATR_MIN = 0.50
CLOSE_LOCATION_LONG_MIN = 0.75
VOL_SHOCK_MULTIPLE = 2.0
VOL_REFERENCE_COUNT = 100
STOP_COOLDOWN_BARS = 5
LOSS_FEEDBACK_WINDOW = 5
LOSS_FEEDBACK_TRIGGER = 3
FEEDBACK_PAUSE_BARS = 20
SPEC_COMMIT = "750bb1a68c5b8fa90e116ae08feff5eb10f0d2d4"
RESEARCH_MODES = frozenset(("SYNTHETIC_FIXTURE", "HISTORICAL_REUSED"))
PERIODS = {"H4": 14400, "D1": 86400}


@dataclass(frozen=True)
class ClosedBar:
    ts: int  # normalized UTC open seconds; only after externally checked clock
    open: float
    high: float
    low: float
    close: float
    close_at_utc: int
    captured_at_utc: int
    source_confirmed_closed: bool
    calendar_gap_verified: bool = False


@dataclass(frozen=True)
class Signal:
    direction: int
    stop: float | None
    reason: str
    atr: float | None = None
    failed_checks: tuple[str, ...] = ()


@dataclass
class Position:
    direction: int
    entry_ts: int
    entry: float
    stop: float
    initial_stop: float
    initial_risk: float
    signal_ts: int


def _number(v: object) -> bool:
    return type(v) in (int, float) and math.isfinite(v)


def signal_from_closed_history(bars: list[ClosedBar], atr_history: list[float],
                               *, short_allowed: bool = False) -> Signal:
    """Pure method hypothesis: only current and earlier completed candles."""
    if short_allowed is not True and short_allowed is not False:
        raise ValueError("SHORT_FLAG_MUST_BE_BOOLEAN")
    if len(bars) < SMA_PERIOD + SMA_SLOPE_LAG or len(atr_history) < VOL_REFERENCE_COUNT + 1:
        return Signal(0, None, "INDICATORS_NOT_READY")
    b = bars[-1]
    atr = atr_history[-1]
    past_atr = atr_history[-VOL_REFERENCE_COUNT-1:-1]
    if not _number(atr) or atr <= 0 or not all(_number(v) and v > 0 for v in past_atr):
        return Signal(0, None, "ATR_NOT_VALID")
    if atr > VOL_SHOCK_MULTIPLE * statistics.median(past_atr):
        return Signal(0, None, "VOLATILITY_SHOCK", atr)
    if b.high <= b.low:
        return Signal(0, None, "NO_CANDLE_RANGE", atr)
    sma = sum(x.close for x in bars[-SMA_PERIOD:]) / SMA_PERIOD
    sma_previous = sum(x.close for x in bars[-SMA_PERIOD-SMA_SLOPE_LAG:-SMA_SLOPE_LAG]) / SMA_PERIOD
    prior = bars[-CHANNEL-1:-1]
    location = (b.close - b.low) / (b.high - b.low)
    long_checks = {
        "CHANNEL_BUFFER": b.close > max(x.high for x in prior) + BREAKOUT_ATR_BUFFER * atr,
        "ABOVE_SMA": b.close > sma,
        "RISING_SMA": sma > sma_previous,
        "STRONG_BODY": b.close - b.open >= BODY_ATR_MIN * atr,
        "CLOSE_NEAR_EXTREME": location >= CLOSE_LOCATION_LONG_MIN,
    }
    if all(long_checks.values()):
        return Signal(1, b.close - INITIAL_ATR_MULTIPLE * atr,
                      "CONFIRMED_LONG", atr)
    short_checks = {
        "CHANNEL_BUFFER": b.close < min(x.low for x in prior) - BREAKOUT_ATR_BUFFER * atr,
        "BELOW_SMA": b.close < sma,
        "FALLING_SMA": sma < sma_previous,
        "STRONG_BODY": b.open - b.close >= BODY_ATR_MIN * atr,
        "CLOSE_NEAR_EXTREME": location <= 1 - CLOSE_LOCATION_LONG_MIN,
    }
    if short_allowed is True and all(short_checks.values()):
        return Signal(-1, b.close + INITIAL_ATR_MULTIPLE * atr,
                      "CONFIRMED_SHORT", atr)
    failed = tuple("LONG_" + k for k, ok in long_checks.items() if not ok)
    if short_allowed is True:
        failed += tuple("SHORT_" + k for k, ok in short_checks.items() if not ok)
    return Signal(0, None, "BREAKOUT_NOT_CONFIRMED", atr, failed)


class ResearchMethod:
    """Sequential causal state; no broker/order API. External attestations untrusted."""

    def __init__(self, *, symbol: str, timeframe: str,
                 exposure: str = "SYNTHETIC_FIXTURE",
                 source_clock_verified: bool = False,
                 calendar_audited: bool = False,
                 short_vehicle_verified: bool = False):
        if not isinstance(symbol, str) or not symbol or timeframe not in PERIODS:
            raise ValueError("UNREGISTERED_SYMBOL_OR_TIMEFRAME")
        if exposure not in RESEARCH_MODES:
            raise ValueError("INDEPENDENT_FORWARD_CLAIM_FORBIDDEN")
        for f in (source_clock_verified, calendar_audited, short_vehicle_verified):
            if type(f) is not bool:
                raise ValueError("AUDIT_FLAGS_MUST_BE_BOOLEAN")
        self.symbol = symbol
        self.timeframe = timeframe
        self.period = PERIODS[timeframe]
        self.exposure = exposure
        self.source_clock_verified = source_clock_verified
        self.calendar_audited = calendar_audited
        self.short_vehicle_verified = short_vehicle_verified
        self.bars: list[ClosedBar] = []
        self._atr: float | None = None
        self._warm_true_ranges: list[float] = []
        self._atr_history: deque[float] = deque(maxlen=VOL_REFERENCE_COUNT + 1)
        self.position: Position | None = None
        self.pending: tuple[int, float, int] | None = None
        self.recent_closed_loss: deque[bool] = deque(maxlen=LOSS_FEEDBACK_WINDOW)
        self.closed_events: list[dict] = []
        self.cooldown_eligible_at = 0
        self.quarantine_eligible_at = 0
        self.last_signal = Signal(0, None, "NOT_STARTED")
        self.diagnostic_counts: Counter[str] = Counter()
        self.confirmed_signal_count = 0

    def _validate(self, b: ClosedBar) -> None:
        if not isinstance(b, ClosedBar):
            raise ValueError("BAR_SCHEMA_INVALID")
        if self.source_clock_verified is not True:
            raise ValueError("SOURCE_CLOCK_UNVERIFIED")
        if any(type(v) is not int for v in (b.ts, b.close_at_utc, b.captured_at_utc)):
            raise ValueError("BAR_TIMESTAMP_TYPE_INVALID")
        if (b.ts < 0 or b.close_at_utc != b.ts + self.period
                or b.captured_at_utc < b.close_at_utc
                or b.captured_at_utc > int(time.time())):
            raise ValueError("BAR_FUTURE_OR_UNCLOSED")
        if b.source_confirmed_closed is not True or type(b.calendar_gap_verified) is not bool:
            raise ValueError("BAR_NOT_CONFIRMED_CLOSED_OR_FLAG_INVALID")
        prices = (b.open, b.high, b.low, b.close)
        if (not all(_number(v) and v > 0 for v in prices)
                or b.high < max(b.open, b.close, b.low)
                or b.low > min(b.open, b.close, b.high)):
            raise ValueError("OHLC_INVALID")
        if self.bars:
            delta = b.ts - self.bars[-1].ts
            if delta <= 0:
                raise ValueError("BAR_DUPLICATE_OR_REORDERED")
            if delta != self.period and not (
                    delta > self.period and delta % self.period == 0
                    and self.calendar_audited is True
                    and b.calendar_gap_verified is True):
                raise ValueError("CALENDAR_GAP_UNVERIFIED")

    def _record_exit(self, p: Position, *, bar: ClosedBar,
                     price: float, gap: bool, events: list[dict], i: int) -> None:
        gross_r = p.direction * (price - p.entry) / p.initial_risk
        record = {"entry_ts": p.entry_ts, "exit_ts": bar.ts,
                  "initial_stop": p.initial_stop, "exit_price": price,
                  "exit_reason": "GAP_STOP" if gap else "STOP_TOUCH",
                  "gross_r": gross_r}
        self.closed_events.append(record)
        self.recent_closed_loss.append(gross_r < 0)
        self.cooldown_eligible_at = max(self.cooldown_eligible_at, i + STOP_COOLDOWN_BARS + 1)
        if (len(self.recent_closed_loss) == LOSS_FEEDBACK_WINDOW
                and sum(self.recent_closed_loss) >= LOSS_FEEDBACK_TRIGGER):
            self.quarantine_eligible_at = max(self.quarantine_eligible_at,
                                               i + FEEDBACK_PAUSE_BARS + 1)
            events.append({"kind": "QUARANTINE_FROM_CLOSED_LOSSES",
                           "eligible_bar_index": self.quarantine_eligible_at})
        events.append({"kind": record["exit_reason"], "gross_r": gross_r,
                       "price": price})

    def on_bar(self, bar: ClosedBar) -> dict:
        """Atomically reject bad input; then process open, stop and close in order."""
        self._validate(bar)
        i = len(self.bars)
        events: list[dict] = []
        exited = False
        blocked_entry_bar = False
        if self.position is not None:
            p = self.position
            prior = self.bars[-TRAIL:]
            if len(prior) == TRAIL:
                new_stop = min(x.low for x in prior) if p.direction == 1 else max(x.high for x in prior)
                p.stop = max(p.stop, new_stop) if p.direction == 1 else min(p.stop, new_stop)
            gap = bar.open <= p.stop if p.direction == 1 else bar.open >= p.stop
            touch = bar.low <= p.stop if p.direction == 1 else bar.high >= p.stop
            if gap or touch:
                exit_price = bar.open if gap else p.stop
                self._record_exit(p, bar=bar, price=exit_price, gap=gap, events=events, i=i)
                self.position = None
                exited = True
        if self.position is None and self.pending is not None and not exited:
            direction, stop, signal_ts = self.pending
            self.pending = None
            invalid = bar.open <= stop if direction == 1 else bar.open >= stop
            if invalid:
                events.append({"kind": "PENDING_REJECT_GAP_INVALID_STOP"})
                blocked_entry_bar = True
            else:
                risk = abs(bar.open - stop)
                if risk <= 0:
                    events.append({"kind": "PENDING_REJECT_ZERO_RISK"})
                    blocked_entry_bar = True
                else:
                    p = Position(direction, bar.ts, bar.open, stop, stop, risk, signal_ts)
                    self.position = p
                    events.append({"kind": "HYPOTHETICAL_ENTRY_NEXT_OPEN", "price": bar.open})
                    touch = bar.low <= stop if direction == 1 else bar.high >= stop
                    if touch:
                        self._record_exit(p, bar=bar, price=stop, gap=False, events=events, i=i)
                        self.position = None
                        exited = True
        if exited:
            self.pending = None
        prev = self.bars[-1] if self.bars else None
        tr = (max(bar.high-bar.low, abs(bar.high-prev.close), abs(bar.low-prev.close))
              if prev is not None else None)
        self.bars.append(bar)
        if tr is not None:
            if self._atr is None:
                self._warm_true_ranges.append(tr)
                if len(self._warm_true_ranges) == ATR_PERIOD:
                    self._atr = sum(self._warm_true_ranges) / ATR_PERIOD
                    self._atr_history.append(self._atr)
            else:
                self._atr = (self._atr * (ATR_PERIOD-1) + tr) / ATR_PERIOD
                self._atr_history.append(self._atr)
        if not exited and not blocked_entry_bar and self.position is None and self.pending is None:
            if i < self.quarantine_eligible_at:
                self.last_signal = Signal(0, None, "CLOSED_LOSS_QUARANTINE")
            elif i < self.cooldown_eligible_at:
                self.last_signal = Signal(0, None, "POST_STOP_COOLDOWN")
            else:
                self.last_signal = signal_from_closed_history(
                    self.bars, list(self._atr_history),
                    short_allowed=self.short_vehicle_verified)
                self.diagnostic_counts.update(self.last_signal.failed_checks)
                if self.last_signal.direction and self.last_signal.stop is not None:
                    self.confirmed_signal_count += 1
                    self.pending = (self.last_signal.direction,
                                    self.last_signal.stop, bar.ts)
                    events.append({"kind": "RESEARCH_SIGNAL_NEXT_OPEN",
                                   "direction": self.last_signal.direction,
                                   "signal_ts": bar.ts})
        elif exited:
            self.last_signal = Signal(0, None, "EXIT_BAR_NO_REENTRY")
        elif blocked_entry_bar:
            self.last_signal = Signal(0, None, "PENDING_REJECT_BAR_NO_REENTRY")
        else:
            self.last_signal = Signal(0, None, "POSITION_OR_PENDING_ACTIVE")
        unrealized = None
        if self.position is not None:
            p = self.position
            unrealized = p.direction * (bar.close-p.entry) / p.initial_risk
        return {"symbol": self.symbol, "bar_index": i,
                "bar_ts": bar.ts, "events": events,
                "signal_reason": self.last_signal.reason,
                "failed_signal_checks": self.last_signal.failed_checks,
                "hypothetical_position": self.position is not None,
                "pending_next_open": self.pending is not None,
                "gross_unrealized_r": unrealized,
                "closed_trade_count": len(self.closed_events),
                "quarantine_eligible_at": self.quarantine_eligible_at,
                "cooldown_eligible_at": self.cooldown_eligible_at,
                "data_source_independently_verified": False,
                "exposure": self.exposure, "cost_status": "NOT_EVALUATED",
                "account_currency_pnl": None, "orders_sent": 0,
                "independent_forward_trades": 0, "edge_status": "UNPROVEN"}

    def snapshot(self) -> dict:
        p = self.position
        return {"bars": len(self.bars), "last_ts": self.bars[-1].ts if self.bars else None,
                "pending": self.pending, "position": None if p is None else {
                    "direction": p.direction, "entry": p.entry, "entry_ts": p.entry_ts,
                    "stop": p.stop, "initial_stop": p.initial_stop,
                    "initial_risk": p.initial_risk, "signal_ts": p.signal_ts},
                "closed": list(self.closed_events),
                "recent_closed_loss": list(self.recent_closed_loss),
                "cooldown_eligible_at": self.cooldown_eligible_at,
                "quarantine_eligible_at": self.quarantine_eligible_at,
                "last_signal_reason": self.last_signal.reason,
                "failed_signal_checks": self.last_signal.failed_checks,
                "diagnostic_counts": dict(sorted(self.diagnostic_counts.items())),
                "confirmed_signal_count": self.confirmed_signal_count,
                "orders_sent": 0, "edge_status": "UNPROVEN"}
