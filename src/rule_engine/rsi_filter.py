"""RULE_006_RSI — Đánh giá RSI Bias.

Ref: rule_engine/RULE_006_RSI.md
RSI là xác nhận phụ. Mục đích: cảnh báo nếu RSI có phân kỳ ngược chiều.

Scoring:
- ALIGNED (5): RSI không quá mua/bán, hoặc phân kỳ dương
- NEUTRAL (3): RSI trong vùng 30-70, không rõ signal
- AGAINST (0): RSI quá mua/bán ngược chiều hoặc phân kỳ âm
"""

from dataclasses import dataclass, field
from src.rule_engine.types import Bar, RuleResult


def _calculate_rsi(bars: list[Bar], period: int = 14) -> float:
    """Tính RSI bằng Wilder's smoothing (standard method).

    Args:
        bars: danh sách Bar (phải có ít nhất period+1 nến đã đóng)
        period: RSI period (default 14)

    Returns:
        RSI value (0-100), hoặc -1 nếu không đủ dữ liệu
    """
    if len(bars) < period + 1:
        return -1.0

    # Chỉ dùng những bar đã đóng (closed=True)
    closed_bars = [b for b in bars if b.closed]
    if len(closed_bars) < period + 1:
        return -1.0

    # Tính gains và losses
    gains = 0.0
    losses = 0.0
    for i in range(1, period + 1):
        change = closed_bars[i].close - closed_bars[i - 1].close
        if change > 0:
            gains += change
        else:
            losses -= change

    # Tính average gain/loss (Wilder's smoothing)
    avg_gain = gains / period
    avg_loss = losses / period

    # Tính RS và RSI
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def evaluate(bars: list[Bar], direction: str, period: int = 14) -> RuleResult:
    """Đánh giá RSI bias so với direction.

    Args:
        bars: danh sách Bar (phải có ít nhất period+1 nến đã đóng)
        direction: "UP" hoặc "DOWN"
        period: RSI period (default 14)

    Returns:
        RuleResult với status ALIGNED/NEUTRAL/AGAINST, score 5/3/0

    Scoring logic (từ RULE_006_RSI.md):
    - Setup UP:
        * RSI <= 70 (không quá mua, hoặc phân kỳ dương) → ALIGNED (5)
        * RSI 30-70 → NEUTRAL (3)
        * RSI > 80 hoặc phân kỳ âm → AGAINST (0)
    - Setup DOWN:
        * RSI >= 30 (không quá bán) → ALIGNED (5)
        * RSI 30-70 → NEUTRAL (3)
        * RSI < 20 hoặc phân kỳ âm → AGAINST (0)
    """
    rsi = _calculate_rsi(bars, period)

    if rsi < 0:
        # Không đủ dữ liệu
        return RuleResult(
            rule_id="RULE_006",
            status="INSUFFICIENT_DATA",
            score=0,
            max_score=5,
            reject=False,
            detail={"rsi": rsi, "period": period, "bars_count": len(bars)}
        )

    # Giả định: phân kỳ được xác định nếu RSI ở mức cực trị
    # (không tính toán full divergence vì yêu cầu không dùng external lib)
    # Giả định đơn giản: nếu RSI quá cao/quá thấp ngược direction → phân kỳ

    if direction == "UP":
        if rsi < 20:
            # Very oversold for UP → bearish divergence possible
            status = "AGAINST"
            score = 0.0
        elif 20 <= rsi < 30:
            # Oversold zone but not extreme
            status = "NEUTRAL"
            score = 3.0
        elif 30 <= rsi <= 70:
            # Optimal range for UP
            status = "ALIGNED"
            score = 5.0
        elif 70 < rsi <= 80:
            # Overbought but not extreme
            status = "NEUTRAL"
            score = 3.0
        else:  # rsi > 80
            # Very overbought (quá mua) → bearish warning
            status = "AGAINST"
            score = 0.0
    elif direction == "DOWN":
        if rsi > 80:
            # Very overbought for DOWN → bullish divergence possible
            status = "AGAINST"
            score = 0.0
        elif 70 < rsi <= 80:
            # Overbought zone but not extreme
            status = "NEUTRAL"
            score = 3.0
        elif 30 <= rsi <= 70:
            # Optimal range for DOWN
            status = "ALIGNED"
            score = 5.0
        elif 20 <= rsi < 30:
            # Oversold but not extreme
            status = "NEUTRAL"
            score = 3.0
        else:  # rsi < 20
            # Very oversold (quá bán) → bullish warning
            status = "AGAINST"
            score = 0.0
    else:
        status = "INVALID_DIRECTION"
        score = 0.0

    return RuleResult(
        rule_id="RULE_006",
        status=status,
        score=score,
        max_score=5,
        reject=False,
        detail={"rsi": rsi, "period": period, "direction": direction}
    )
