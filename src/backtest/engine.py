"""Closed-bar deterministic backtest engine.

The engine deliberately separates signal evaluation from position/risk
simulation. A signal evaluator may propose a direction and stop, but this
module does not size capital or modify project risk policy.
"""

from collections.abc import Callable, Sequence

from src.backtest.costs import CostModel
from src.backtest.spec import StrategySpec
from src.backtest.types import BacktestResult, OpenPosition, Signal, Trade
from src.rule_engine.incremental import CachedRuleFeatures, PointInTimeRuleCache
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
        "gross_pnl_price": sum(trade.gross_pnl_price for trade in trades),
        "total_cost_price": sum(trade.cost_price for trade in trades),
    }


def _validate_signal(
    signal: Signal, entry: float, spec: StrategySpec
) -> tuple[str, float, float | None] | None:
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
    if spec.exit_model == "CHANNEL_TRAILING":
        target = None
    elif target is None:
        target = entry + risk * spec.reward_risk if direction == "UP" else entry - risk * spec.reward_risk
    if target is not None and direction == "UP" and target <= entry:
        return None
    if target is not None and direction == "DOWN" and target >= entry:
        return None
    return direction, stop, float(target) if target is not None else None


def run_backtest(
    bars: Sequence[Bar],
    spec: StrategySpec,
    evaluator: SignalEvaluator,
    cost_model: CostModel | None = None,
    signal_start_index: int = 0,
    signal_end_index: int | None = None,
) -> BacktestResult:
    """Run a deterministic closed-bar simulation.

    At index ``i`` the evaluator receives only ``bars[:i + 1]``. A position
    opened at a bar close can only exit on a later bar, preventing same-bar
    lookahead and duplicate signal execution.
    """

    if any(not bar.closed for bar in bars):
        raise ValueError("backtest requires all input bars to be closed")
    if not 0 <= signal_start_index <= len(bars):
        raise ValueError("signal_start_index is outside the bar range")
    if signal_end_index is None:
        signal_end_index = len(bars)
    if not signal_start_index <= signal_end_index <= len(bars):
        raise ValueError("signal_end_index is outside the bar range")

    costs = cost_model or CostModel(
        "spec-slippage-only", 0.0, 0.0, spec.slippage_price, 0.0
    )

    trades: list[Trade] = []
    position: dict[str, object] | None = None

    for index, bar in enumerate(bars):
        exited_this_bar = False
        if position is not None and index > int(position["entry_index"]):
            direction = str(position["direction"])
            stop = float(position["stop"])
            target = position["target"]
            if spec.exit_model == "CHANNEL_TRAILING" and index >= spec.exit_lookback_bars:
                prior = bars[index - spec.exit_lookback_bars : index]
                if direction == "UP":
                    candidate = min(bar.low for bar in prior)
                    stop = max(stop, candidate)
                else:
                    candidate = max(bar.high for bar in prior)
                    stop = min(stop, candidate)
                position["stop"] = stop
            stop_hit = bar.low <= stop if direction == "UP" else bar.high >= stop
            target_hit = (
                target is not None
                and (bar.high >= float(target) if direction == "UP" else bar.low <= float(target))
            )

            exit_reason = None
            exit_level = None
            if stop_hit:
                exit_reason = (
                    "TRAILING_STOP"
                    if spec.exit_model == "CHANNEL_TRAILING"
                    else "STOP"
                )
                exit_level = stop
            elif target_hit:
                exit_reason, exit_level = "TARGET", target

            if exit_reason is not None:
                slippage_price = costs.slippage_price
                exit_price = _execution_price(
                    exit_level,
                    direction,
                    entry=False,
                    slippage=slippage_price,
                )
                entry_price = float(position["entry_price"])
                theoretical_entry = float(position["reference_entry_price"])
                gross_pnl = (
                    exit_level - theoretical_entry
                    if direction == "UP"
                    else theoretical_entry - exit_level
                )
                executed_pnl = (
                    exit_price - entry_price
                    if direction == "UP"
                    else entry_price - exit_price
                )
                holding_bars = index - int(position["entry_index"])
                explicit_cost = costs.total_explicit(holding_bars)
                total_cost = gross_pnl - executed_pnl + explicit_cost
                pnl = executed_pnl - explicit_cost
                trades.append(
                    Trade(
                        direction=direction,
                        entry_timestamp=str(position["entry_timestamp"]),
                        exit_timestamp=bar.timestamp,
                        entry_price=entry_price,
                        exit_price=exit_price,
                        stop_price=stop,
                        target_price=float(target) if target is not None else None,
                        pnl_price=pnl,
                        exit_reason=exit_reason,
                        gross_pnl_price=gross_pnl,
                        cost_price=total_cost,
                        holding_bars=holding_bars,
                    )
                )
                position = None
                exited_this_bar = True

        if position is None and not exited_this_bar:
            history = tuple(bars[: index + 1])
            signal = evaluator(history, spec)
            if signal is not None and signal_start_index <= index < signal_end_index:
                candidate = _validate_signal(signal, bar.close, spec)
                if candidate is not None:
                    direction, stop, target = candidate
                    entry_price = _execution_price(
                        bar.close,
                        direction,
                        entry=True,
                        slippage=costs.slippage_price,
                    )
                    position = {
                        "direction": direction,
                        "entry_index": index,
                        "entry_timestamp": bar.timestamp,
                        "entry_price": entry_price,
                        "reference_entry_price": bar.close,
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
            target_price=(
                float(position["target"])
                if position["target"] is not None
                else None
            ),
        )

    return BacktestResult(
        trades=tuple(trades),
        metrics=_metrics(trades),
        open_position=open_position,
    )


def _rule_engine_signal(
    history: Sequence[Bar],
    spec: StrategySpec,
    features: CachedRuleFeatures | None = None,
) -> Signal | None:
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
            trend_result=features.trend_result if features is not None else None,
            swing_levels=features.swing_levels if features is not None else None,
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


class RuleEngineSignalEvaluator:
    """Stateful point-in-time adapter for repeated backtest prefixes."""

    def __init__(self, n: int = 2):
        self._cache = PointInTimeRuleCache(n=n)

    def __call__(self, history: Sequence[Bar], spec: StrategySpec) -> Signal | None:
        features = self._cache.update(history)
        return _rule_engine_signal(history, spec, features)


def rule_engine_signal(history: Sequence[Bar], spec: StrategySpec) -> Signal | None:
    """Stateless compatibility adapter using the original full-scan rules."""

    return _rule_engine_signal(history, spec)
