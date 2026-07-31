"""RULE_007_EMA — Đánh giá EMA Bias.

Ref: rule_engine/RULE_007_EMA.md
EMA là bộ lọc bias. Setup UP nên có giá trên EMA; setup DOWN nên có giá dưới EMA.

Scoring:
- ALIGNED (5): Giá > EMA (setup UP) hoặc Giá < EMA (setup DOWN)
- NEUTRAL (3): Giá gần EMA (±2%)
- AGAINST (0): Giá ngược bias của EMA
"""

from src.rule_engine.types import Bar, RuleResult


def _calculate_ema(bars: list[Bar], period: int = 50) -> float:
    """Tính EMA từ bars.

    Args:
        bars: danh sách Bar (phải có ít nhất period nến đã đóng)
        period: EMA period (default 50)

    Returns:
        EMA value, hoặc -1 nếu không đủ dữ liệu
    """
    if len(bars) < period:
        return -1.0

    # Chỉ dùng những bar đã đóng
    closed_bars = [b for b in bars if b.closed]
    if len(closed_bars) < period:
        return -1.0

    # Tính SMA của period nến đầu tiên
    sum_price = sum(b.close for b in closed_bars[:period])
    ema = sum_price / period

    # Tính EMA với multiplier = 2 / (period + 1)
    multiplier = 2.0 / (period + 1)
    for i in range(period, len(closed_bars)):
        ema = closed_bars[i].close * multiplier + ema * (1 - multiplier)

    return ema


def evaluate(bars: list[Bar], direction: str, period: int = 50) -> RuleResult:
    """Đánh giá EMA bias.

    Args:
        bars: danh sách Bar (phải có ít nhất period nến đã đóng)
        direction: "UP" hoặc "DOWN"
        period: EMA period (default 50)

    Returns:
        RuleResult với status ALIGNED/NEUTRAL/AGAINST, score 5/3/0

    Scoring logic (từ RULE_007_EMA.md):
    - Nếu setup UP + Giá > EMA (>0.5% để tránh noise) → ALIGNED (5)
    - Nếu setup UP + Giá gần EMA (±2%) → NEUTRAL (3)
    - Nếu setup UP + Giá < EMA (>2%) → AGAINST (0)
    - Tương tự cho setup DOWN (ngược lại)
    """
    if len(bars) == 0:
        return RuleResult(
            rule_id="RULE_007",
            status="NO_DATA",
            score=0,
            max_score=5,
            reject=False,
            detail={"period": period}
        )

    ema = _calculate_ema(bars, period)

    if ema < 0:
        # Không đủ dữ liệu
        return RuleResult(
            rule_id="RULE_007",
            status="INSUFFICIENT_DATA",
            score=0,
            max_score=5,
            reject=False,
            detail={"ema": ema, "period": period, "bars_count": len(bars)}
        )

    # Lấy giá close hiện tại (nến gần nhất đã đóng hoặc sắp đóng)
    current_price = bars[-1].close

    # Tính khoảng cách % giữa giá và EMA
    if ema == 0:
        return RuleResult(
            rule_id="RULE_007",
            status="INVALID_EMA",
            score=0,
            max_score=5,
            reject=False,
            detail={"ema": ema, "price": current_price}
        )

    distance_pct = abs(current_price - ema) / ema * 100

    if direction == "UP":
        if current_price > ema and distance_pct > 0.5:
            # Giá trên EMA, cách xa đủ → ALIGNED
            status = "ALIGNED"
            score = 5.0
        elif distance_pct <= 2:
            # Giá gần EMA → NEUTRAL
            status = "NEUTRAL"
            score = 3.0
        else:
            # Giá dưới EMA, cách xa → AGAINST
            status = "AGAINST"
            score = 0.0
    elif direction == "DOWN":
        if current_price < ema and distance_pct > 0.5:
            # Giá dưới EMA, cách xa đủ → ALIGNED
            status = "ALIGNED"
            score = 5.0
        elif distance_pct <= 2:
            # Giá gần EMA → NEUTRAL
            status = "NEUTRAL"
            score = 3.0
        else:
            # Giá trên EMA, cách xa → AGAINST
            status = "AGAINST"
            score = 0.0
    else:
        status = "INVALID_DIRECTION"
        score = 0.0

    return RuleResult(
        rule_id="RULE_007",
        status=status,
        score=score,
        max_score=5,
        reject=False,
        detail={
            "ema": ema,
            "price": current_price,
            "distance_pct": distance_pct,
            "period": period,
            "direction": direction
        }
    )
