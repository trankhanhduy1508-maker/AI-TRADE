"""RULE_002_MARKET_STRUCTURE — Xác định Cấu trúc Thị trường

Tham chiếu: rule_engine/RULE_002_MARKET_STRUCTURE.md

Xác định cấu trúc thị trường hợp lệ và đảm bảo setup phá qua theo đúng hướng
của xu hướng chính (không giao dịch ngược xu hướng).
"""

from src.rule_engine.types import Bar, RuleResult


def _find_last_swing_levels(bars: list[Bar], n: int = 2) -> tuple[float, float]:
    """
    Tìm swing high và swing low gần nhất trong bars.

    Returns:
        (last_swing_high, last_swing_low): Giá trị của swing gần nhất
    """
    if len(bars) < 2 * n + 1:
        return None, None

    swing_high = None
    swing_low = None

    for i in range(n, len(bars) - n):
        # Swing High
        is_swing_high = True
        for j in range(i - n, i):
            if bars[j].high >= bars[i].high:
                is_swing_high = False
                break
        for j in range(i + 1, i + n + 1):
            if bars[j].high >= bars[i].high:
                is_swing_high = False
                break
        if is_swing_high:
            swing_high = bars[i].high

        # Swing Low
        is_swing_low = True
        for j in range(i - n, i):
            if bars[j].low <= bars[i].low:
                is_swing_low = False
                break
        for j in range(i + 1, i + n + 1):
            if bars[j].low <= bars[i].low:
                is_swing_low = False
                break
        if is_swing_low:
            swing_low = bars[i].low

    return swing_high, swing_low


def evaluate(bars: list[Bar], trend_status: str, n: int = 2) -> RuleResult:
    """
    Đánh giá cấu trúc thị trường hợp lệ dựa trên xu hướng từ RULE_001.

    Tham chiếu: rule_engine/RULE_002_MARKET_STRUCTURE.md, mục 5 (Điều kiện)

    Args:
        bars: Danh sách các nến OHLCV.
        trend_status: Kết quả từ RULE_001 ("TREND_UP", "TREND_DOWN", "TREND_NEUTRAL").
        n: Số nến trái/phải để định nghĩa swing (mặc định 2).

    Returns:
        RuleResult với:
        - status: "VALID" hoặc "INVALID"
        - score: 20 (valid), 15 (weak), 0 (invalid)
        - reject: True nếu INVALID, False nếu VALID
        - detail: Chứa swing levels và hướng phá qua
    """
    if trend_status == "TREND_NEUTRAL":
        return RuleResult(
            rule_id="RULE_002",
            status="INVALID",
            score=0,
            max_score=20,
            reject=True,
            detail={"reason": "Neutral trend, no valid structure"}
        )

    if not bars or len(bars) < 2 * n + 1:
        return RuleResult(
            rule_id="RULE_002",
            status="INVALID",
            score=0,
            max_score=20,
            reject=True,
            detail={"reason": "Insufficient bars"}
        )

    swing_high, swing_low = _find_last_swing_levels(bars, n)

    if swing_high is None or swing_low is None:
        return RuleResult(
            rule_id="RULE_002",
            status="INVALID",
            score=0,
            max_score=20,
            reject=True,
            detail={"reason": "Could not identify swing levels"}
        )

    current_close = bars[-1].close

    # Kiểm tra hướng phá qua và xu hướng
    if trend_status == "TREND_UP":
        # Phải phá qua swing high
        if current_close > swing_high:
            # VALID - phá qua theo đúng hướng
            return RuleResult(
                rule_id="RULE_002",
                status="VALID",
                score=20,
                max_score=20,
                reject=False,
                detail={
                    "trend": "UP",
                    "swing_high": swing_high,
                    "swing_low": swing_low,
                    "current_close": current_close,
                    "direction": "bullish"
                }
            )
        else:
            # INVALID - không phá qua hoặc phá qua swing_low (ngược chiều)
            return RuleResult(
                rule_id="RULE_002",
                status="INVALID",
                score=0,
                max_score=20,
                reject=True,
                detail={
                    "trend": "UP",
                    "swing_high": swing_high,
                    "swing_low": swing_low,
                    "current_close": current_close,
                    "reason": "Close not above swing high or opposing trend"
                }
            )

    elif trend_status == "TREND_DOWN":
        # Phải phá qua swing low
        if current_close < swing_low:
            # VALID - phá qua theo đúng hướng
            return RuleResult(
                rule_id="RULE_002",
                status="VALID",
                score=20,
                max_score=20,
                reject=False,
                detail={
                    "trend": "DOWN",
                    "swing_high": swing_high,
                    "swing_low": swing_low,
                    "current_close": current_close,
                    "direction": "bearish"
                }
            )
        else:
            # INVALID - không phá qua hoặc phá qua swing_high (ngược chiều)
            return RuleResult(
                rule_id="RULE_002",
                status="INVALID",
                score=0,
                max_score=20,
                reject=True,
                detail={
                    "trend": "DOWN",
                    "swing_high": swing_high,
                    "swing_low": swing_low,
                    "current_close": current_close,
                    "reason": "Close not below swing low or opposing trend"
                }
            )

    else:
        return RuleResult(
            rule_id="RULE_002",
            status="INVALID",
            score=0,
            max_score=20,
            reject=True,
            detail={"reason": "Unknown trend status"}
        )
