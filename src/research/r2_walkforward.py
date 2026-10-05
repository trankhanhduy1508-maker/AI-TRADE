"""R2 exploratory, synthetic-testable chronological walk-forward, offline only.

Never relabel historically exposed observations as independent new forward.
No account PnL, broker imports, network calls, order APIs or future bars.
R0 stays frozen in its own module. R2 candidates are preregistered separately.
"""
from __future__ import annotations

import hashlib
import json
import math
import time
from dataclasses import dataclass
from typing import Sequence

CANDIDATES = (("R0_REFERENCE", 55, 20, 2.5),
              ("R2_FAST", 40, 15, 2.0),
              ("R2_SLOW", 80, 30, 3.0))
MIN_BARS = 500
STEP = 250
TRAIN_SPAN = 1000
MIN_TRAIN_TRADES = 5
ATR_N = 20
SMA_N = 200
VALID_KIND = frozenset(("NATIVE_D1", "NATIVE_H4", "DERIVED_H4_BID_ONLY"))


@dataclass(frozen=True)
class Bar:
    ts: int  # UTC bar-open timestamp, fully closed as of the study cutoff
    open: float
    high: float
    low: float
    close: float


@dataclass(frozen=True)
class Study:
    symbol: str
    timeframe: str
    source_kind: str
    source_sha256: str
    exposure: str  # SYNTHETIC_FIXTURE or HISTORICAL_REUSED
    session: str   # 24_7 or UNVERIFIED_MARKET_CALENDAR
    allow_short: bool = False
    assumed_round_trip_cost_price: float = 0.0


def _validate(bars: Sequence[Bar], study: Study, as_of_utc: int) -> list[Bar]:
    if not isinstance(study, Study) or not study.symbol or study.source_kind not in VALID_KIND:
        raise ValueError("UNREGISTERED_SOURCE_KIND")
    if study.timeframe not in ("D1", "H4") or (study.source_kind in ("NATIVE_H4", "DERIVED_H4_BID_ONLY")) != (study.timeframe == "H4"):
        raise ValueError("SOURCE_TIMEFRAME_MISMATCH")
    if study.exposure not in ("SYNTHETIC_FIXTURE", "HISTORICAL_REUSED"):
        raise ValueError("FORWARD_CLAIM_FORBIDDEN")
    if study.session not in ("24_7", "UNVERIFIED_MARKET_CALENDAR"):
        raise ValueError("UNKNOWN_SESSION")
    if type(study.allow_short) is not bool:
        raise ValueError("SHORT_VEHICLE_NOT_VERIFIED")
    if not isinstance(study.source_sha256, str) or len(study.source_sha256) != 64 or any(c not in "0123456789abcdef" for c in study.source_sha256) or study.source_sha256 == "0"*64:
        raise ValueError("MISSING_SOURCE_HASH")
    cost = study.assumed_round_trip_cost_price
    if isinstance(cost, bool) or not isinstance(cost, (float, int)) or not math.isfinite(cost) or cost < 0:
        raise ValueError("INVALID_COST_SCENARIO")
    if type(as_of_utc) is not int or as_of_utc > int(time.time()) or as_of_utc <= 0:
        raise ValueError("INVALID_AS_OF_CLOCK")
    seconds = 14400 if study.timeframe == "H4" else 86400
    prefix = []
    prev = -1
    for b in bars:
        if not isinstance(b, Bar) or type(b.ts) is not int or b.ts <= prev:
            raise ValueError("DUPLICATE_UNSORTED_OR_BAD_BAR")
        prev = b.ts
        if b.ts + seconds > as_of_utc:
            continue  # unfinished/future suffix cannot affect any decision
        if study.session == "24_7" and prefix and b.ts != prefix[-1].ts + seconds:
            raise ValueError("UNVERIFIED_GAP_IN_24_7_SOURCE")
        prices = (b.open, b.high, b.low, b.close)
        if (not all(type(v) in (float, int) and math.isfinite(v) and v > 0 for v in prices)
                or b.high < max(b.open, b.low, b.close)
                or b.low > min(b.open, b.high, b.close)):
            raise ValueError("INVALID_OHLC")
        prefix.append(b)
    if len(prefix) < MIN_BARS + STEP:
        raise ValueError("INSUFFICIENT_COMPLETED_HISTORY")
    return prefix


def _atr(bars: Sequence[Bar]) -> list[float]:
    out = [0.0] * len(bars)
    tr = []
    value = 0.0
    for i in range(1, len(bars)):
        b, p = bars[i], bars[i-1]
        change = max(b.high-b.low, abs(b.high-p.close), abs(b.low-p.close))
        if i <= ATR_N:
            tr.append(change)
            if i == ATR_N:
                value = sum(tr) / ATR_N
                out[i] = value
        else:
            value = (value*(ATR_N-1)+change)/ATR_N
            out[i] = value
    return out


def _play(bars: Sequence[Bar], begin: int, end: int, candidate: tuple, *,
          short: bool, cost: float) -> dict:
    """All signals at closed t, execute next open; reset flat per episode.

    Cost is a modeled ROUND-TRIP price-unit deduction upon closing, not a fee
    attestation. Open positions retain approximate cost liability in MTM.
    """
    _, channel, trail, atr_multiple = candidate
    atrs = _atr(bars[:end])
    pending = None
    pos = None
    closed = []
    marked = []
    realized = 0.0
    gap_count = 0
    for i in range(begin, end):
        b = bars[i]
        exited = False
        if pos is not None:
            dr, entry, stop, initial_r, entry_index = pos
            previous = bars[i-trail:i]
            if dr == 1:
                stop = max(stop, min(x.low for x in previous))
            else:
                stop = min(stop, max(x.high for x in previous))
            gap = b.open <= stop if dr == 1 else b.open >= stop
            touch = b.low <= stop if dr == 1 else b.high >= stop
            if gap or touch:
                exit_price = b.open if gap else stop
                result_r = (dr*(exit_price-entry)-cost)/initial_r
                closed.append(result_r)
                realized += result_r
                if gap:
                    gap_count += 1
                pos = None
                exited = True
            else:
                pos = (dr, entry, stop, initial_r, entry_index)
        if pos is None and pending is not None and not exited:
            dr, initial_stop = pending
            invalid = b.open <= initial_stop if dr == 1 else b.open >= initial_stop
            if not invalid:
                risk = abs(b.open-initial_stop)
                if risk > 0:
                    pos = (dr, b.open, initial_stop, risk, i)
                    touch = b.low <= initial_stop if dr == 1 else b.high >= initial_stop
                    if touch:  # conservatively stop on entry bar
                        result_r = (dr*(initial_stop-b.open)-cost)/risk
                        closed.append(result_r)
                        realized += result_r
                        pos = None
                        exited = True
        pending = None
        if pos is None and not exited and i+1 < end and i >= max(SMA_N-1, channel, ATR_N):
            sma = sum(x.close for x in bars[i-SMA_N+1:i+1])/SMA_N
            prev = bars[i-channel:i]
            if atrs[i] > 0:
                if b.close > max(x.high for x in prev) and b.close > sma:
                    pending = (1, b.close-atr_multiple*atrs[i])
                elif short and b.close < min(x.low for x in prev) and b.close < sma:
                    pending = (-1, b.close+atr_multiple*atrs[i])
        mark = realized
        if pos is not None:
            dr, entry, _, initial_r, _ = pos
            mark += (dr*(b.close-entry)-cost)/initial_r
        marked.append(mark)
    peak, dd = 0.0, 0.0
    for value in marked:
        peak = max(peak, value)
        dd = max(dd, peak-value)
    return {"closed_trades": len(closed),
            "expectancy_r": sum(closed)/len(closed) if closed else None,
            "realized_r": sum(closed), "max_dd_r_marked": dd,
            "unrealized_r": marked[-1]-realized if pos is not None else 0.0,
            "open_position_at_boundary": pos is not None,
            "gap_stops": gap_count}


def run_walkforward(bars: Sequence[Bar], *, study: Study,
                    as_of_utc: int, step: int = STEP) -> dict:
    if type(step) is not int or step != STEP:
        raise ValueError("R2_PREREG_STEP_IMMUTABLE")
    usable = _validate(bars, study, as_of_utc)
    cost = study.assumed_round_trip_cost_price
    episodes = []
    # No adaptation within a 250-bar episode. The final partial episode is
    # ignored rather than ex-post shortened to include known recent outcomes.
    for boundary in range(MIN_BARS, len(usable)-STEP+1, STEP):
        training_start = max(SMA_N, boundary - TRAIN_SPAN)
        history = usable[:boundary]  # physical prefix blocks future reads
        decisions = []
        for candidate in CANDIDATES:
            result = _play(history, training_start, boundary, candidate,
                           short=study.allow_short, cost=cost)
            if result["closed_trades"] >= MIN_TRAIN_TRADES:
                score = result["expectancy_r"] - .01*result["max_dd_r_marked"]
                decisions.append((score, candidate[0], candidate))
        selected = sorted(decisions, key=lambda x: (-x[0], x[1]))[0][2] if decisions else None
        if selected is None:
            result = {"closed_trades": 0, "expectancy_r": None,
                      "realized_r": 0.0, "max_dd_r_marked": 0.0,
                      "unrealized_r": 0.0, "open_position_at_boundary": False,
                      "gap_stops": 0}
        else:
            result = _play(usable[:boundary+STEP], boundary, boundary+STEP,
                           selected, short=study.allow_short, cost=cost)
        # Freeze the selected candidate from base training; stress changes
        # cost only, never changes selection or reuses future test scores.
        stress = {}
        if selected is not None and cost > 0:
            for multiplier in (2, 3):
                stressed = _play(usable[:boundary+STEP], boundary, boundary+STEP,
                                 selected, short=study.allow_short,
                                 cost=cost*multiplier)
                stress[f"{multiplier}x"] = {
                    "closed_trades": stressed["closed_trades"],
                    "realized_r": stressed["realized_r"],
                    "unrealized_r": stressed["unrealized_r"],
                    "cost_status": "MODELED_ONLY"}
        episodes.append({"decision_bar_index": boundary,
                         "modeled_cost_stress": stress,
                         "decision_open_ts": usable[boundary].ts,
                         "evaluation_end_open_ts": usable[boundary+STEP-1].ts,
                         "training_bar_count": boundary-training_start,
                         "candidate_training_trades_min": MIN_TRAIN_TRADES,
                         "selected": selected[0] if selected else "FLAT",
                         "status": "SYNTHETIC_TEST_ONLY" if study.exposure == "SYNTHETIC_FIXTURE" else "HISTORICAL_REUSED_DESCRIPTIVE",
                         **result})
    return {"symbol": study.symbol, "timeframe": study.timeframe,
            "source_kind": study.source_kind, "source_sha256": study.source_sha256,
            "source_rights_independently_verified": False,
            "calendar_audited": False, "fee_status": "MODELED_ONLY" if cost else "GROSS_ONLY",
            "source_history": study.exposure,
            "completed_input_bars": len(usable), "ignored_unclosed_or_future_bars": len(bars)-len(usable),
            "episode_count": len(episodes), "episodes": episodes,
            "orders_sent": 0, "independent_forward_trades": 0,
            "account_currency_pnl": None, "edge_status": "UNPROVEN"}
