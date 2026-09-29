"""Isolated, frozen R0 research simulator. NO broker/network/order-send imports.

Only completed OHLC bars enter this module. Monetary returns are deliberately NOT
calculated because contract multipliers, account-currency conversions and verified
broker execution profiles are not available in generic public market data.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Sequence

PREREG_SHA = "9041d3de3122abfb41ef8ab2f0fca12f114307cf"
SMA_PERIOD = 200
ATR_PERIOD = 20
CHANNEL = 55
TRAIL = 20
ATR_MULTIPLIER = 2.5
BOOTSTRAP_SEED = 20260929


@dataclass(frozen=True)
class Bar:
    ts: int  # bar OPEN timestamp, UTC seconds; the bar must have fully closed
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


@dataclass(frozen=True)
class Costs:
    spread_price: float = 0.0
    commission_price: float = 0.0
    slippage_price: float = 0.0  # one-side adverse price slippage
    swap_price_per_bar: float = 0.0
    provenance: str = "GROSS_ONLY"

    def __post_init__(self) -> None:
        if not all(
            math.isfinite(v) and v >= 0
            for v in (self.spread_price, self.commission_price,
                      self.slippage_price, self.swap_price_per_bar)
        ):
            raise ValueError("cost values must be finite and nonnegative")

    def round_trip(self, holding_bars: int, multiplier: float = 1.0) -> float:
        if holding_bars < 0 or multiplier < 0:
            raise ValueError("invalid holding bars or multiplier")
        return multiplier * (
            self.spread_price + self.commission_price
            + 2 * self.slippage_price
            + self.swap_price_per_bar * holding_bars
        )


def validate_bars(bars: Sequence[Bar]) -> None:
    previous = -1
    for b in bars:
        if not isinstance(b.ts, int) or b.ts <= previous:
            raise ValueError("timestamps must be unique and strictly increasing")
        previous = b.ts
        vals = (b.open, b.high, b.low, b.close, b.volume)
        if not all(math.isfinite(v) for v in vals):
            raise ValueError("OHLCV cannot contain NaN/infinite")
        if min(b.open, b.high, b.low, b.close) <= 0 or b.volume < 0:
            raise ValueError("OHLC must be positive and volume nonnegative")
        if b.high < max(b.open, b.close, b.low) or b.low > min(b.open, b.close, b.high):
            raise ValueError("inconsistent OHLC candle")


def _atr(bars: Sequence[Bar], i: int) -> float | None:
    if i < ATR_PERIOD:
        return None
    values = []
    for j in range(1, i + 1):
        b, p = bars[j], bars[j-1]
        values.append(max(b.high - b.low, abs(b.high - p.close), abs(b.low - p.close)))
    atr = sum(values[:ATR_PERIOD]) / ATR_PERIOD
    for value in values[ATR_PERIOD:]:
        atr = (atr * (ATR_PERIOD - 1) + value) / ATR_PERIOD
    return atr


def atr_series(bars: Sequence[Bar]) -> list[float | None]:
    """Wilder ATR(20) in O(N), complete bars only."""
    out: list[float | None] = [None] * len(bars)
    if len(bars) <= ATR_PERIOD:
        return out
    warm = []
    atr = 0.0
    for j in range(1, len(bars)):
        b, p = bars[j], bars[j-1]
        tr = max(b.high-b.low, abs(b.high-p.close), abs(b.low-p.close))
        if j <= ATR_PERIOD:
            warm.append(tr)
            if j == ATR_PERIOD:
                atr = sum(warm)/ATR_PERIOD
                out[j] = atr
        else:
            atr = (atr*(ATR_PERIOD-1)+tr)/ATR_PERIOD
            out[j] = atr
    return out


def _signal(bars: Sequence[Bar], i: int, channel: int,
            atr_multiple: float, atr: float | None,
            *, allow_short: bool) -> tuple[int, float] | None:
    if i < max(SMA_PERIOD-1, channel, ATR_PERIOD):
        return None
    b = bars[i]
    sma = sum(x.close for x in bars[i-SMA_PERIOD+1:i+1]) / SMA_PERIOD
    prev = bars[i-channel:i]
    if atr is None or atr <= 0:
        return None
    if b.close > max(x.high for x in prev) and b.close > sma:
        return 1, b.close - atr_multiple * atr
    if allow_short and b.close < min(x.low for x in prev) and b.close < sma:
        return -1, b.close + atr_multiple * atr
    return None


def _summarize(trades: list[dict], marked: list[float],
               open_position: dict | None, costs: Costs,
               cost_multiplier: float) -> dict:
    pnls = [t["pnl_price"] for t in trades]
    rs = [t["pnl_r"] for t in trades]
    winners = [t for t in trades if t["pnl_price"] > 0]
    losers = [t for t in trades if t["pnl_price"] < 0]
    gross_w = sum(max(0, x) for x in pnls)
    gross_l = abs(sum(min(0, x) for x in pnls))
    win_r = [t["pnl_r"] for t in winners]
    lose_r = [t["pnl_r"] for t in losers]
    peak = 0.0
    dd = 0.0
    for e in marked:
        peak = max(peak, e)
        dd = max(dd, peak-e)
    return {
        "trade_count": len(trades),
        "winner_count": len(winners),
        "loser_count": len(losers),
        "flat_count": len(trades)-len(winners)-len(losers),
        "win_rate": len(winners)/len(trades) if trades else None,
        "loss_rate": len(losers)/len(trades) if trades else None,
        "average_win_price": sum(t["pnl_price"] for t in winners)/len(winners) if winners else None,
        "average_loss_price": sum(t["pnl_price"] for t in losers)/len(losers) if losers else None,
        "realized_rr": (sum(win_r)/len(win_r))/abs(sum(lose_r)/len(lose_r))
                       if win_r and lose_r else None,
        "expectancy_r": sum(rs)/len(rs) if rs else None,
        "net_pnl_price": sum(pnls),
        "gross_pnl_price": sum(t["gross_pnl_price"] for t in trades),
        "cost_price": sum(t["cost_price"] for t in trades),
        "profit_factor": gross_w/gross_l if gross_l > 0 else None,
        "realized_net_r": sum(rs),
        "max_drawdown_r_marked": dd,
        "ending_marked_equity_r": marked[-1] if marked else 0.0,
        "open_position_marked": open_position,
        "cost_provenance": costs.provenance,
        "cost_multiplier": cost_multiplier,
        "account_currency_pnl": None,  # deliberately blocked
    }


def simulate(
    bars: Sequence[Bar], *, begin: int, end: int,
    costs: Costs | None = None, cost_multiplier: float = 1.0,
    channel: int = CHANNEL, trail: int = TRAIL,
    atr_multiplier: float = ATR_MULTIPLIER, allow_short: bool = True,
) -> dict:
    """One symbol/TF/window: signals at closed t; entry at t+1 OPEN.

    At each bar, existing position's protective stop is updated only from
    strictly PRIOR bars; adverse opening gaps execute at the worse OPEN.
    Marked equity uses initial-risk (R) units, not account-money units.
    """
    validate_bars(bars)
    if not (0 <= begin < end <= len(bars)):
        raise ValueError("invalid chronological signal/execution window")
    if channel < 2 or trail < 2 or atr_multiplier <= 0:
        raise ValueError("invalid frozen research parameters")
    costs = costs or Costs()
    if cost_multiplier < 0 or not math.isfinite(cost_multiplier):
        raise ValueError("invalid cost multiplier")
    position = None
    pending = None
    trades: list[dict] = []
    marked: list[float] = []
    realized_r = 0.0
    atrs = atr_series(bars)
    skipped_gap_entries = 0
    for i in range(begin, end):
        bar = bars[i]
        exited_this_bar = False
        if position is not None:
            p = position
            # prior bars only; no price from current high/low enters stop update
            if i >= trail:
                prior = bars[i-trail:i]
                if p["dir"] == 1:
                    p["stop"] = max(p["stop"], min(x.low for x in prior))
                else:
                    p["stop"] = min(p["stop"], max(x.high for x in prior))
            gap = (p["dir"] == 1 and bar.open <= p["stop"]) or (
                p["dir"] == -1 and bar.open >= p["stop"])
            touch = (p["dir"] == 1 and bar.low <= p["stop"]) or (
                p["dir"] == -1 and bar.high >= p["stop"])
            if gap or touch:
                exit_price = bar.open if gap else p["stop"]
                holding = i-p["entry_index"]
                charge = costs.round_trip(holding, cost_multiplier)
                gross = p["dir"]*(exit_price-p["entry_price"])
                pnl = gross-charge
                r = pnl/p["initial_risk"]
                trades.append({
                    "entry_ts": p["entry_ts"], "exit_ts": bar.ts,
                    "entry_price": p["entry_price"], "exit_price": exit_price,
                    "direction": p["dir"], "initial_stop": p["initial_stop"],
                    "final_stop": p["stop"], "holding_bars": holding,
                    "exit_reason": "GAP_STOP" if gap else "STOP",
                    "gross_pnl_price": gross, "cost_price": charge,
                    "pnl_price": pnl, "pnl_r": r,
                })
                realized_r += r
                position = None
                exited_this_bar = True
        if position is None and pending is not None and not exited_this_bar:
            direction, stop, signal_ts = pending
            pending = None
            invalid = (direction == 1 and bar.open <= stop) or (
                direction == -1 and bar.open >= stop)
            if invalid:
                skipped_gap_entries += 1
            else:
                position = {
                    "dir": direction, "entry_index": i,
                    "entry_ts": bar.ts, "signal_ts": signal_ts,
                    "entry_price": bar.open, "initial_stop": stop,
                    "stop": stop, "initial_risk": abs(bar.open-stop)
                }
                # Stop can hit on the entry bar; no positive intrabar ordering
                if ((direction == 1 and bar.low <= stop)
                    or (direction == -1 and bar.high >= stop)):
                    charge = costs.round_trip(0, cost_multiplier)
                    gross = direction*(stop-bar.open)
                    pnl = gross-charge
                    r = pnl/position["initial_risk"]
                    trades.append({
                        "entry_ts": bar.ts, "exit_ts": bar.ts,
                        "entry_price": bar.open, "exit_price": stop,
                        "direction": direction, "initial_stop": stop,
                        "final_stop": stop, "holding_bars": 0,
                        "exit_reason": "ENTRY_BAR_STOP",
                        "gross_pnl_price": gross, "cost_price": charge,
                        "pnl_price": pnl, "pnl_r": r,
                    })
                    realized_r += r
                    position = None
                    exited_this_bar = True
        pending = None  # orders cannot cross the end of this window
        if position is None and not exited_this_bar and i+1 < end:
            pending = _signal(bars, i, channel, atr_multiplier, atrs[i],
                              allow_short=allow_short)
            if pending is not None:
                pending = (*pending, bar.ts)
        mark = realized_r
        if position is not None:
            p = position
            est_cost = costs.round_trip(i-p["entry_index"], cost_multiplier)
            mark += (p["dir"]*(bar.close-p["entry_price"])-est_cost)/p["initial_risk"]
        marked.append(mark)
    open_state = None
    if position is not None:
        p = position
        open_state = {
            "entry_ts": p["entry_ts"], "entry_price": p["entry_price"],
            "direction": p["dir"], "stop": p["stop"],
            "unrealized_pnl_r": marked[-1]-realized_r,
            "marked_at_ts": bars[end-1].ts
        }
    out = _summarize(trades, marked, open_state, costs, cost_multiplier)
    out["window_start_ts"] = bars[begin].ts
    out["window_last_ts"] = bars[end-1].ts
    out["skipped_gap_entries"] = skipped_gap_entries
    out["trades"] = trades
    return out


def block_bootstrap(trades: Sequence[dict], *, n: int = 10000,
                    block: int = 5, seed: int = BOOTSTRAP_SEED) -> dict:
    values = [float(t["pnl_r"]) for t in trades]
    if not values:
        return {"status": "INSUFFICIENT_TRADES", "samples": 0}
    rng = random.Random(seed)
    totals = []
    for _ in range(n):
        sequence = []
        while len(sequence) < len(values):
            start = rng.randrange(len(values))
            sequence.extend(values[(start+j) % len(values)] for j in range(block))
        totals.append(sum(sequence[:len(values)]))
    totals.sort()
    return {
        "status": "TRAIN_VALIDATION_ONLY", "samples": len(values),
        "iterations": n, "block": block, "seed": seed,
        "total_r_p05": totals[int((n-1)*.05)],
        "total_r_median": totals[int((n-1)*.50)],
        "total_r_p95": totals[int((n-1)*.95)],
    }
