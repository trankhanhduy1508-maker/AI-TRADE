"""CWS METHOD LAB V2: causal regime, quality score and closed-trade learning.

Research only. No broker/order/network actions. No fee study or net-PnL claim.
All adaptive behavior is gating or stop-tightening; score never scales risk.
"""
from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass
import math
import statistics
import time

CHANNEL = 55
ATR_PERIOD = 20
SMA_FAST = 50
SMA_SLOW = 200
SMA_SLOPE_LAG = 20
ATR_REFERENCE = 100
BREAKOUT_BUFFER_ATR = 0.25
BODY_ATR_MIN = 0.50
CLOSE_LOCATION_MIN = 0.75
STRONG_SEPARATION_ATR = 1.0
COMPRESSION_ATR_RATIO = 0.70
SHOCK_ATR_RATIO = 2.0
SCORE_TRADE = 80
SCORE_WATCH = 60
INITIAL_STOP_ATR = 2.5
STOP_COOLDOWN = 5
FEEDBACK_WINDOW = 8
QUALITY_FAILURE_TRIGGER = 4
REVERSAL_TRIGGER = 3
FEEDBACK_PAUSE = 20
SPEC_COMMIT = "2509ad559a69fd54aba04a27da4a6b3d7baa53b6"
PERIODS = {"H4": 14400, "D1": 86400}
EXPOSURES = frozenset(("SYNTHETIC_FIXTURE", "HISTORICAL_REUSED"))


@dataclass(frozen=True)
class ClosedBar:
    ts: int
    open: float
    high: float
    low: float
    close: float
    close_at_utc: int
    captured_at_utc: int
    source_confirmed_closed: bool
    calendar_gap_verified: bool = False


@dataclass(frozen=True)
class Regime:
    name: str
    atr: float | None
    atr_ratio: float | None
    sma50: float | None
    sma200: float | None
    sma200_slope: float | None
    separation_atr: float | None


@dataclass(frozen=True)
class Decision:
    action: str
    direction: int
    score: int
    reason: str
    regime: str
    stop: float | None
    checks: tuple[tuple[str, bool], ...]


@dataclass
class Position:
    direction: int
    entry_ts: int
    entry: float
    stop: float
    initial_stop: float
    initial_risk: float
    signal_ts: int
    signal_score: int
    entry_regime: str


def _number(value: object) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def _sma(bars: list[ClosedBar], n: int, end: int | None = None) -> float:
    segment = bars[-n:] if end is None else bars[end-n:end]
    if len(segment) != n:
        raise ValueError("SMA_HISTORY_INSUFFICIENT")
    return sum(x.close for x in segment) / n


def atr_series(bars: list[ClosedBar]) -> list[float]:
    if len(bars) < 2:
        return []
    values: list[float] = []
    atr: float | None = None
    warm: list[float] = []
    for i in range(1, len(bars)):
        bar, prev = bars[i], bars[i-1]
        tr = max(bar.high-bar.low, abs(bar.high-prev.close), abs(bar.low-prev.close))
        if atr is None:
            warm.append(tr)
            if len(warm) == ATR_PERIOD:
                atr = sum(warm) / ATR_PERIOD
                values.append(atr)
        else:
            atr = (atr*(ATR_PERIOD-1)+tr)/ATR_PERIOD
            values.append(atr)
    return values


def classify_regime(bars: list[ClosedBar], atr_history: list[float]) -> Regime:
    if len(bars) < SMA_SLOW + SMA_SLOPE_LAG or len(atr_history) < ATR_REFERENCE + 1:
        return Regime("UNKNOWN", None, None, None, None, None, None)
    atr = atr_history[-1]
    reference = atr_history[-ATR_REFERENCE-1:-1]
    if not _number(atr) or atr <= 0 or not all(_number(x) and x > 0 for x in reference):
        return Regime("UNKNOWN", None, None, None, None, None, None)
    sma50 = _sma(bars, SMA_FAST)
    sma200 = _sma(bars, SMA_SLOW)
    sma200_previous = _sma(bars, SMA_SLOW, -SMA_SLOPE_LAG)
    slope = sma200 - sma200_previous
    ratio = atr / statistics.median(reference)
    separation = abs(sma50-sma200) / atr
    if ratio > SHOCK_ATR_RATIO:
        name = "VOLATILITY_SHOCK"
    elif sma50 > sma200 and slope > 0 and separation >= STRONG_SEPARATION_ATR:
        name = "TREND_STRONG_UP"
    elif sma50 < sma200 and slope < 0 and separation >= STRONG_SEPARATION_ATR:
        name = "TREND_STRONG_DOWN"
    elif sma50 > sma200 and slope > 0:
        name = "TREND_WEAK_UP"
    elif sma50 < sma200 and slope < 0:
        name = "TREND_WEAK_DOWN"
    elif ratio < COMPRESSION_ATR_RATIO:
        name = "COMPRESSION"
    else:
        name = "RANGE_OR_TRANSITION"
    return Regime(name, atr, ratio, sma50, sma200, slope, separation)


def _score_direction(bars: list[ClosedBar], regime: Regime, direction: int) -> tuple[int, tuple[tuple[str, bool], ...]]:
    if regime.name == "UNKNOWN" or regime.atr is None:
        return 0, ()
    bar = bars[-1]
    prior = bars[-CHANNEL-1:-1]
    if len(prior) != CHANNEL or bar.high <= bar.low:
        return 0, ()
    atr = regime.atr
    location = (bar.close-bar.low)/(bar.high-bar.low)
    if direction == 1:
        checks = (
            ("CHANNEL_BUFFER", bar.close > max(x.high for x in prior) + BREAKOUT_BUFFER_ATR*atr),
            ("SMA_SIDE", bar.close > regime.sma200),
            ("SMA_SLOPE", regime.sma200_slope > 0),
            ("FAST_SLOW", regime.sma50 > regime.sma200),
            ("STRONG_BODY", bar.close-bar.open >= BODY_ATR_MIN*atr),
            ("CLOSE_LOCATION", location >= CLOSE_LOCATION_MIN),
            ("REGIME_STRONG", regime.name == "TREND_STRONG_UP"),
            ("REGIME_WEAK", regime.name == "TREND_WEAK_UP"),
            ("ATR_NORMAL", COMPRESSION_ATR_RATIO <= regime.atr_ratio <= 1.50),
        )
    else:
        checks = (
            ("CHANNEL_BUFFER", bar.close < min(x.low for x in prior) - BREAKOUT_BUFFER_ATR*atr),
            ("SMA_SIDE", bar.close < regime.sma200),
            ("SMA_SLOPE", regime.sma200_slope < 0),
            ("FAST_SLOW", regime.sma50 < regime.sma200),
            ("STRONG_BODY", bar.open-bar.close >= BODY_ATR_MIN*atr),
            ("CLOSE_LOCATION", location <= 1-CLOSE_LOCATION_MIN),
            ("REGIME_STRONG", regime.name == "TREND_STRONG_DOWN"),
            ("REGIME_WEAK", regime.name == "TREND_WEAK_DOWN"),
            ("ATR_NORMAL", COMPRESSION_ATR_RATIO <= regime.atr_ratio <= 1.50),
        )
    flags = dict(checks)
    score = 0
    score += 25 if flags["CHANNEL_BUFFER"] else 0
    score += 15 if flags["SMA_SIDE"] else 0
    score += 15 if flags["SMA_SLOPE"] else 0
    score += 10 if flags["FAST_SLOW"] else 0
    score += 10 if flags["STRONG_BODY"] else 0
    score += 10 if flags["CLOSE_LOCATION"] else 0
    score += 10 if flags["REGIME_STRONG"] else (5 if flags["REGIME_WEAK"] else 0)
    score += 5 if flags["ATR_NORMAL"] else 0
    return max(0, min(100, score)), checks


def decision_from_history(bars: list[ClosedBar], atr_history: list[float],
                          *, short_allowed: bool = False) -> Decision:
    if type(short_allowed) is not bool:
        raise ValueError("SHORT_FLAG_MUST_BE_BOOLEAN")
    regime = classify_regime(bars, atr_history)
    if regime.name == "UNKNOWN":
        return Decision("ABSTAIN", 0, 0, "REGIME_UNKNOWN", regime.name, None, ())
    if regime.name == "VOLATILITY_SHOCK":
        return Decision("ABSTAIN", 0, 0, "VOLATILITY_SHOCK", regime.name, None, ())
    long_score, long_checks = _score_direction(bars, regime, 1)
    candidates = [(long_score, 1, long_checks)]
    if short_allowed:
        short_score, short_checks = _score_direction(bars, regime, -1)
        candidates.append((short_score, -1, short_checks))
    candidates.sort(key=lambda x: (-x[0], -x[1]))
    score, direction, checks = candidates[0]
    action = "TRADE" if score >= SCORE_TRADE else "WATCH" if score >= SCORE_WATCH else "ABSTAIN"
    reason = "QUALITY_" + action
    stop = None
    if action == "TRADE":
        stop = bars[-1].close - direction*INITIAL_STOP_ATR*regime.atr
    return Decision(action, direction if score else 0, score, reason,
                    regime.name, stop, checks)


def trail_window(regime_name: str, direction: int) -> int | None:
    if regime_name == "UNKNOWN":
        return None
    if regime_name == "VOLATILITY_SHOCK":
        return 5
    if (direction == 1 and regime_name == "TREND_STRONG_UP") or (
            direction == -1 and regime_name == "TREND_STRONG_DOWN"):
        return 30
    if (direction == 1 and regime_name == "TREND_WEAK_UP") or (
            direction == -1 and regime_name == "TREND_WEAK_DOWN"):
        return 20
    return 10


class MethodLabV2:
    """Causal sequential research state machine. Never sends an order."""

    def __init__(self, *, symbol: str, timeframe: str,
                 exposure: str = "SYNTHETIC_FIXTURE",
                 source_clock_verified: bool = False,
                 calendar_audited: bool = False,
                 short_vehicle_verified: bool = False):
        if not isinstance(symbol, str) or not symbol or timeframe not in PERIODS:
            raise ValueError("UNREGISTERED_SYMBOL_OR_TIMEFRAME")
        if exposure not in EXPOSURES:
            raise ValueError("INDEPENDENT_FORWARD_CLAIM_FORBIDDEN")
        for flag in (source_clock_verified, calendar_audited, short_vehicle_verified):
            if type(flag) is not bool:
                raise ValueError("AUDIT_FLAGS_MUST_BE_BOOLEAN")
        self.symbol = symbol
        self.timeframe = timeframe
        self.period = PERIODS[timeframe]
        self.exposure = exposure
        self.source_clock_verified = source_clock_verified
        self.calendar_audited = calendar_audited
        self.short_vehicle_verified = short_vehicle_verified
        self.bars: list[ClosedBar] = []
        self.atr_history: list[float] = []
        self.position: Position | None = None
        self.pending: tuple[int, float, int, int, str] | None = None
        self.closed: list[dict] = []
        self.feedback_tags: deque[tuple[str, ...]] = deque(maxlen=FEEDBACK_WINDOW)
        self.quality_quarantine_until = 0
        self.reversal_watch_until = 0
        self.cooldown_until = 0
        self.decision_counts: Counter[str] = Counter()
        self.failure_counts: Counter[str] = Counter()
        self.last_decision = Decision("ABSTAIN", 0, 0, "NOT_STARTED", "UNKNOWN", None, ())

    def _validate(self, bar: ClosedBar) -> None:
        if not isinstance(bar, ClosedBar):
            raise ValueError("BAR_SCHEMA_INVALID")
        if self.source_clock_verified is not True:
            raise ValueError("SOURCE_CLOCK_UNVERIFIED")
        if any(type(v) is not int for v in (bar.ts, bar.close_at_utc, bar.captured_at_utc)):
            raise ValueError("BAR_TIMESTAMP_TYPE_INVALID")
        if (bar.ts < 0 or bar.close_at_utc != bar.ts+self.period
                or bar.captured_at_utc < bar.close_at_utc
                or bar.captured_at_utc > int(time.time())):
            raise ValueError("BAR_FUTURE_OR_UNCLOSED")
        if bar.source_confirmed_closed is not True or type(bar.calendar_gap_verified) is not bool:
            raise ValueError("BAR_NOT_CONFIRMED_CLOSED_OR_FLAG_INVALID")
        values = (bar.open, bar.high, bar.low, bar.close)
        if (not all(_number(x) and x > 0 for x in values)
                or bar.high < max(bar.open, bar.low, bar.close)
                or bar.low > min(bar.open, bar.high, bar.close)):
            raise ValueError("OHLC_INVALID")
        if self.bars:
            delta = bar.ts-self.bars[-1].ts
            if delta <= 0:
                raise ValueError("BAR_DUPLICATE_OR_REORDERED")
            if delta != self.period and not (
                    delta > self.period and delta % self.period == 0
                    and self.calendar_audited is True
                    and bar.calendar_gap_verified is True):
                raise ValueError("CALENDAR_GAP_UNVERIFIED")

    def _update_atr(self, bar: ClosedBar, previous: ClosedBar | None) -> None:
        if previous is None:
            return
        tr = max(bar.high-bar.low, abs(bar.high-previous.close), abs(bar.low-previous.close))
        if not self.atr_history:
            if len(self.bars) < ATR_PERIOD+1:
                return
            trs = []
            for i in range(1, len(self.bars)):
                b, p = self.bars[i], self.bars[i-1]
                trs.append(max(b.high-b.low, abs(b.high-p.close), abs(b.low-p.close)))
            self.atr_history.append(sum(trs[-ATR_PERIOD:])/ATR_PERIOD)
            return
        self.atr_history.append((self.atr_history[-1]*(ATR_PERIOD-1)+tr)/ATR_PERIOD)

    def _failure_tags(self, position: Position, exit_bar: ClosedBar,
                      gross_r: float, bars_held: int) -> tuple[str, ...]:
        if gross_r > 0:
            return ("WIN",)
        if gross_r == 0:
            return ("FLAT",)
        tags: list[str] = []
        if bars_held <= 5:
            tags.append("FAST_STOP")
        if len(self.bars) >= CHANNEL+1:
            prior = self.bars[-CHANNEL-1:-1]
            if position.direction == 1 and exit_bar.close <= max(x.high for x in prior):
                tags.append("FAILED_BREAKOUT")
            if position.direction == -1 and exit_bar.close >= min(x.low for x in prior):
                tags.append("FAILED_BREAKOUT")
        regime = classify_regime(self.bars, self.atr_history)
        opposite = (position.direction == 1 and regime.name in ("TREND_WEAK_DOWN", "TREND_STRONG_DOWN")) or (
            position.direction == -1 and regime.name in ("TREND_WEAK_UP", "TREND_STRONG_UP"))
        if opposite:
            tags.append("REGIME_REVERSAL")
        if regime.name == "VOLATILITY_SHOCK":
            tags.append("VOL_SHOCK_EXIT")
        if not tags:
            tags.append("NORMAL_LOSS")
        return tuple(sorted(set(tags)))

    def _apply_feedback(self, tags: tuple[str, ...], index: int) -> None:
        self.feedback_tags.append(tags)
        flat = [tag for group in self.feedback_tags for tag in group]
        if sum(tag in ("FAST_STOP", "FAILED_BREAKOUT") for tag in flat) >= QUALITY_FAILURE_TRIGGER:
            self.quality_quarantine_until = max(self.quality_quarantine_until,
                                                index+FEEDBACK_PAUSE+1)
        if flat.count("REGIME_REVERSAL") >= REVERSAL_TRIGGER:
            self.reversal_watch_until = max(self.reversal_watch_until,
                                            index+FEEDBACK_PAUSE+1)
        self.failure_counts.update(tags)

    def _close(self, position: Position, bar: ClosedBar, exit_price: float,
               gap: bool, index: int, events: list[dict]) -> dict:
        gross_r = position.direction*(exit_price-position.entry)/position.initial_risk
        bars_held = max(0, (bar.ts-position.entry_ts)//self.period)
        record = {"entry_ts": position.entry_ts, "exit_ts": bar.ts,
                  "entry_regime": position.entry_regime,
                  "signal_score": position.signal_score,
                  "exit_reason": "GAP_STOP" if gap else "STOP_TOUCH",
                  "exit_price": exit_price, "gross_r": gross_r,
                  "bars_held": bars_held}
        self.closed.append(record)
        self.cooldown_until = max(self.cooldown_until, index+STOP_COOLDOWN+1)
        events.append({"kind": record["exit_reason"], "gross_r": gross_r})
        return record

    def on_bar(self, bar: ClosedBar) -> dict:
        self._validate(bar)
        index = len(self.bars)
        events: list[dict] = []
        previous = self.bars[-1] if self.bars else None
        prior_regime = classify_regime(self.bars, self.atr_history)
        exited_position: Position | None = None
        exit_record: dict | None = None
        if self.position is not None:
            p = self.position
            window = trail_window(prior_regime.name, p.direction)
            if window is not None and len(self.bars) >= window:
                prior = self.bars[-window:]
                candidate = min(x.low for x in prior) if p.direction == 1 else max(x.high for x in prior)
                p.stop = max(p.stop, candidate) if p.direction == 1 else min(p.stop, candidate)
            gap = bar.open <= p.stop if p.direction == 1 else bar.open >= p.stop
            touch = bar.low <= p.stop if p.direction == 1 else bar.high >= p.stop
            if gap or touch:
                exit_price = bar.open if gap else p.stop
                exited_position = p
                exit_record = self._close(p, bar, exit_price, gap, index, events)
                self.position = None
                self.pending = None
        blocked_entry = False
        if self.position is None and self.pending is not None and exited_position is None:
            direction, stop, signal_ts, score, signal_regime = self.pending
            self.pending = None
            invalid = bar.open <= stop if direction == 1 else bar.open >= stop
            if invalid:
                events.append({"kind": "PENDING_REJECT_GAP_INVALID_STOP"})
                blocked_entry = True
            else:
                risk = abs(bar.open-stop)
                if risk <= 0:
                    events.append({"kind": "PENDING_REJECT_ZERO_RISK"})
                    blocked_entry = True
                else:
                    self.position = Position(direction, bar.ts, bar.open, stop, stop,
                                             risk, signal_ts, score, signal_regime)
                    events.append({"kind": "HYPOTHETICAL_ENTRY_NEXT_OPEN",
                                   "score": score, "regime": signal_regime})
                    touch = bar.low <= stop if direction == 1 else bar.high >= stop
                    if touch:
                        p = self.position
                        exited_position = p
                        exit_record = self._close(p, bar, stop, False, index, events)
                        self.position = None
        self.bars.append(bar)
        self._update_atr(bar, previous)
        if exit_record is not None and exited_position is not None:
            tags = self._failure_tags(exited_position, bar, exit_record["gross_r"],
                                      exit_record["bars_held"])
            exit_record["failure_tags"] = tags
            self._apply_feedback(tags, index)
            events.append({"kind": "CLOSED_TRADE_CLASSIFIED", "tags": tags})
        if exited_position is not None:
            self.last_decision = Decision("ABSTAIN", 0, 0, "EXIT_BAR_NO_REENTRY",
                                          classify_regime(self.bars, self.atr_history).name,
                                          None, ())
        elif blocked_entry:
            self.last_decision = Decision("ABSTAIN", 0, 0, "PENDING_REJECT_BAR_NO_REENTRY",
                                          classify_regime(self.bars, self.atr_history).name,
                                          None, ())
        elif self.position is not None or self.pending is not None:
            self.last_decision = Decision("ABSTAIN", 0, 0, "POSITION_OR_PENDING_ACTIVE",
                                          classify_regime(self.bars, self.atr_history).name,
                                          None, ())
        else:
            d = decision_from_history(self.bars, self.atr_history,
                                      short_allowed=self.short_vehicle_verified)
            if index < self.quality_quarantine_until:
                d = Decision("ABSTAIN", 0, d.score, "QUALITY_QUARANTINE",
                             d.regime, None, d.checks)
            elif index < self.cooldown_until:
                d = Decision("ABSTAIN", 0, d.score, "POST_STOP_COOLDOWN",
                             d.regime, None, d.checks)
            elif index < self.reversal_watch_until and d.action == "TRADE":
                d = Decision("WATCH", d.direction, d.score, "REGIME_REVERSAL_WATCH_ONLY",
                             d.regime, None, d.checks)
            self.last_decision = d
            self.decision_counts[d.action] += 1
            if d.action == "TRADE" and d.stop is not None:
                self.pending = (d.direction, d.stop, bar.ts, d.score, d.regime)
                events.append({"kind": "RESEARCH_SIGNAL_NEXT_OPEN",
                               "direction": d.direction, "score": d.score,
                               "regime": d.regime})
        unrealized = None
        if self.position is not None:
            p = self.position
            unrealized = p.direction*(bar.close-p.entry)/p.initial_risk
        return {"symbol": self.symbol, "bar_index": index, "bar_ts": bar.ts,
                "events": events, "action": self.last_decision.action,
                "score": self.last_decision.score,
                "decision_reason": self.last_decision.reason,
                "regime": self.last_decision.regime,
                "position_open": self.position is not None,
                "pending_next_open": self.pending is not None,
                "gross_unrealized_r": unrealized,
                "closed_trade_count": len(self.closed),
                "quality_quarantine_until": self.quality_quarantine_until,
                "reversal_watch_until": self.reversal_watch_until,
                "cooldown_until": self.cooldown_until,
                "cost_status": "NOT_EVALUATED",
                "account_currency_pnl": None,
                "data_source_independently_verified": False,
                "orders_sent": 0, "independent_forward_trades": 0,
                "edge_status": "UNPROVEN"}

    def snapshot(self) -> dict:
        p = self.position
        return {"bars": len(self.bars),
                "last_ts": self.bars[-1].ts if self.bars else None,
                "last_regime": classify_regime(self.bars, self.atr_history).name,
                "last_decision": self.last_decision,
                "position": None if p is None else {
                    "direction": p.direction, "entry_ts": p.entry_ts,
                    "entry": p.entry, "stop": p.stop,
                    "initial_stop": p.initial_stop, "initial_risk": p.initial_risk,
                    "signal_score": p.signal_score, "entry_regime": p.entry_regime},
                "pending": self.pending, "closed": list(self.closed),
                "feedback_tags": list(self.feedback_tags),
                "failure_counts": dict(sorted(self.failure_counts.items())),
                "decision_counts": dict(sorted(self.decision_counts.items())),
                "quality_quarantine_until": self.quality_quarantine_until,
                "reversal_watch_until": self.reversal_watch_until,
                "cooldown_until": self.cooldown_until,
                "cost_status": "NOT_EVALUATED", "orders_sent": 0,
                "edge_status": "UNPROVEN"}
