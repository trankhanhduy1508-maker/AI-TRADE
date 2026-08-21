"""Closed-bar deterministic backtest engine.

The engine deliberately separates signal evaluation from position/risk
simulation. A signal evaluator may propose a direction and stop, but this
module does not size capital or modify project risk policy.
"""

from collections.abc import Callable, Sequence

from src.backtest.spec import StrategySpec
from src.backtest.types import BacktestResult, OpenPosition, Signal, Trade
from src.rule_engine.types import Bar

SignalEvaluator = Callable[[Sequence[Bar], StrategySpec], Signal | None]


def _execution_price(level: float, direction: str, *, entry: bool, slippage: float) -> float:
    if slippage == 0:
        return level
    if entry:
        return level + slippage if direction == "UP" else level - slippage
    return level - slippage if direction == "UP" else level + slippage


def _metrics(trades: list[Trade]) -> dict[str, float | int | None]:
    pnls = [trade.pnl_price for trade in trades]
    winners = [pnl for pnl in pnls if pnl > 0]
    losers = [pnl for pnl in pnls if pnl < 0]
    equity = 0.0
    peak = 0.0
    max_drawdown = 0.0
    for pnl in pnls:
        equity += pnl
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, peak - equity)
    gross_profit = sum(winners)
    gross_loss = abs(sum(losers))
    return {
        "trade_count": len(trades),
        "winner_count": len(winners),
        "loser_count": len(losers),
        "win_rate": len(winners) / len(trades) if trades else 0.0,
        "gross_profit_price": gross_profit,
        "gross_loss_price": gross_loss,
        "net_pnl_price": sum(pnls),
        "expectancy_price": sum(pnls) / len(trades) if trades else 0.0,
        "profit_factor": gross_profit / gross_loss if gross_loss else None,
        "max_drawdown_price": max_drawdown,
    }


def _validate_signal(signal: Signal, entry: float, spec: StrategySpec) -> tuple[str, float, float] | None:
    direction = signal.direction.upper()
    if direction not in {"UP", "DOWN"}:
        return None
    if signal.score < spec.score_threshold:
        return None
    stop = float(signal.stop_price)
    if direction == "UP" and stop >= entry:
        return None
    if direction == "DOWN" and stop <= entry:
        return None
    risk = abs(entry - stop)
    target = signal.target_price
    if target is None:
        target = entry + risk * spec.reward_risk if direction == "UP" else entry - risk * spec.reward_risk
    if direction == "UP" and target <= entry:
        return None
    if direction == "DOWN" and target >= entry:
        return None
    return direction, stop, float(target)


def run_backtest(
    bars: Sequence[Bar],
    spec: StrategySpec,
    evaluator: SignalEvaluator,
) -> BacktestResult:
    """Run a deterministic closed-bar simulation.

    At index ``i`` the evaluator receives only ``bars[:i + 1]``. A position
    opened at a bar close can only exit on a later bar, preventing same-bar
    lookahead and duplicate signal execution.
    """

    if any(not bar.closed for bar in bars):
        raise ValueError("backtest requires all input bars to be closed")

    trades: list[Trade] = []
    position: dict[str, object] | None = None

    for index, bar in enumerate(bars):
        exited_this_bar = False
        if position is not None and index > int(position["entry_index"]):
            direction = str(position["direction"])
            stop = float(position["stop"])
            target = float(position["target"])
            stop_hit = bar.low <= stop if direction == "UP" else bar.high >= stop
            target_hit = bar.high >= target if direction == "UP" else bar.low <= target

            exit_reason = None
            exit_level = None
            if stop_hit:
                exit_reason, exit_level = "STOP", stop
            elif target_hit:
                exit_reason, exit_level = "TARGET", target

            if exit_reason is not None:
                exit_price = _execution_price(
                    exit_level,
                    direction,
                    entry=False,
                    slippage=spec.slippage_price,
                )
                entry_price = float(position["entry_price"])
                pnl = exit_price - entry_price if direction == "UP" else entry_price - exit_price
                trades.append(
                    Trade(
                        direction=direction,
                        entry_timestamp=str(position["entry_timestamp"]),
                        exit_timestamp=bar.timestamp,
                        entry_price=entry_price,
                        exit_price=exit_price,
                        stop_price=stop,
                        target_price=target,
                        pnl_price=pnl,
                        exit_reason=exit_reason,
                    )
                )
                position = None
                exited_this_bar = True

        if position is None and not exited_this_bar:
            history = tuple(bars[: index + 1])
            signal = evaluator(history, spec)
            if signal is not None:
                candidate = _validate_signal(signal, bar.close, spec)
                if candidate is not None:
                    direction, stop, target = candidate
                    entry_price = _execution_price(
                        bar.close,
                        direction,
                        entry=True,
                        slippage=spec.slippage_price,
                    )
                    position = {
                        "direction": direction,
                        "entry_index": index,
                        "entry_timestamp": bar.timestamp,
                        "entry_price": entry_price,
                        "stop": stop,
                        "target": target,
                    }

    open_position = None
    if position is not None:
        open_position = OpenPosition(
            direction=str(position["direction"]),
            entry_timestamp=str(position["entry_timestamp"]),
            entry_price=float(position["entry_price"]),
            stop_price=float(position["stop"]),
            target_price=float(position["target"]),
        )

    return BacktestResult(
        trades=tuple(trades),
        metrics=_metrics(trades),
        open_position=open_position,
    )


def rule_engine_signal(history: Sequence[Bar], spec: StrategySpec) -> Signal | None:
    """Adapt the existing rule engine to the deterministic backtest contract.

    Stop candidates use only bars before the current signal bar. The adapter
    is an implementation derivation of TF-001 and does not assign capital
    risk or position size.
    """

    if len(history) <= spec.stop_lookback_bars:
        return None

    from src.rule_engine.scoring import evaluate_setup

    prior = history[-spec.stop_lookback_bars - 1 : -1]
    entry = history[-1].close
    candidates: list[Signal] = []
    for direction in ("UP", "DOWN"):
        if direction == "UP":
            stop = min(bar.low for bar in prior) - spec.stop_buffer_price
            target = entry + (entry - stop) * spec.reward_risk
        else:
            stop = max(bar.high for bar in prior) + spec.stop_buffer_price
            target = entry - (stop - entry) * spec.reward_risk
        score = evaluate_setup(
            list(history),
            entry=entry,
            stop=stop,
            target=target,
            direction=direction,
            spread_pips=spec.spread_pips,
        )
        if score.decision == "TRADE" and score.total >= spec.score_threshold:
            candidates.append(
                Signal(
                    direction=direction,
                    stop_price=stop,
                    target_price=target,
                    score=score.total,
                )
            )
    return max(candidates, key=lambda signal: signal.score, default=None)
