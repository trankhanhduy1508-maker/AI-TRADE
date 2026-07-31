"""RULE_004_PULLBACK — Xác định Pullback Hợp lệ

Tham chiếu: rule_engine/RULE_004_PULLBACK.md

Xác định sau breakout, giá có hồi lại gần swing level một cách hợp lệ
(không phá ngược lại sâu bên trong vùng cũ).
"""

from src.rule_engine.types import Bar, RuleResult


def evaluate(
    bars: list[Bar],
    breakout_level: float,
    direction: str,
    lookback_bars: int = 20
) -> RuleResult:
    """
    Đánh giá pullback hợp lệ sau breakout.

    Tham chiếu: rule_engine/RULE_004_PULLBACK.md, mục 5 (Điều kiện)

    Giả định:
    - Ghi nhận breakout_level là vùng vừa phá qua.
    - Kiểm tra 20 nến sau breakout có pullback hay không.
    - Pullback VALID: giá hồi gần breakout level (50-100% distance) mà không phá ngược hẳn.
    - Pullback WAITING: giá tiếp tục theo breakout (chưa hồi rõ ràng).
    - FALSE_BREAK: hồi quá sâu, phá ngược lại.

    Args:
        bars: Danh sách các nến OHLCV.
        breakout_level: Mức swing vừa phá qua (breakout point).
        direction: "UP" (breakout qua swing high) hoặc "DOWN" (breakout qua swing low).
        lookback_bars: Số nến để kiểm tra pullback (mặc định 20).

    Returns:
        RuleResult với:
        - status: "VALID", "WAITING", hoặc "FALSE_BREAK"
        - score: 15 (valid), 12-8 (waiting), 0 (false_break)
        - reject: True nếu FALSE_BREAK, False nếu VALID/WAITING
        - detail: Thông tin về pullback
    """
    if not bars or len(bars) < 2:
        return RuleResult(
            rule_id="RULE_004",
            status="WAITING",
            score=8,
            max_score=15,
            reject=False,
            detail={"reason": "Insufficient bars"}
        )

    current_bar = bars[-1]

    # Xác định ngưỡng hồi và ngưỡng phá ngược
    if direction.upper() == "UP":
        # Breakout UP: breakout_level là swing high
        # False break: close quay lại dưới một mức nào đó (ví dụ: breakout_level - distance)
        # Pullback valid: giá hồi trong 50-100% distance từ breakout_level

        # Tìm low của breakout (giả định breakout từ swing low)
        swing_low = min(bar.low for bar in bars)

        pullback_distance = breakout_level - swing_low
        pullback_min = breakout_level - pullback_distance * 1.0  # 100% distance
        pullback_max = breakout_level - pullback_distance * 0.5  # 50% distance

        # Kiểm tra nếu close hiện tại nằm trong vùng pullback
        if swing_low < current_bar.close <= breakout_level:
            # Nằm trong vùng pullback
            if pullback_min <= current_bar.close <= breakout_level:
                # PULLBACK_VALID
                return RuleResult(
                    rule_id="RULE_004",
                    status="VALID",
                    score=15,
                    max_score=15,
                    reject=False,
                    detail={
                        "type": "valid",
                        "breakout_level": breakout_level,
                        "swing_low": swing_low,
                        "current_close": current_bar.close,
                        "pullback_range": (pullback_min, pullback_max),
                        "direction": "UP"
                    }
                )
            else:
                # Hồi nhẹ, vẫn ổn nhưng không đến full distance
                return RuleResult(
                    rule_id="RULE_004",
                    status="VALID",
                    score=15,
                    max_score=15,
                    reject=False,
                    detail={
                        "type": "light_pullback",
                        "breakout_level": breakout_level,
                        "swing_low": swing_low,
                        "current_close": current_bar.close,
                        "direction": "UP"
                    }
                )
        elif current_bar.close > breakout_level:
            # Tiếp tục lên, chưa có pullback rõ ràng
            return RuleResult(
                rule_id="RULE_004",
                status="WAITING",
                score=10,
                max_score=15,
                reject=False,
                detail={
                    "type": "continuing",
                    "breakout_level": breakout_level,
                    "current_close": current_bar.close,
                    "direction": "UP",
                    "reason": "No pullback yet, price continuing"
                }
            )
        else:
            # Phá ngược (close < swing_low)
            return RuleResult(
                rule_id="RULE_004",
                status="FALSE_BREAK",
                score=0,
                max_score=15,
                reject=True,
                detail={
                    "type": "false_break",
                    "breakout_level": breakout_level,
                    "swing_low": swing_low,
                    "current_close": current_bar.close,
                    "direction": "UP",
                    "reason": "Close below swing low, false break"
                }
            )

    elif direction.upper() == "DOWN":
        # Breakout DOWN: breakout_level là swing low
        # False break: close quay lại trên một mức nào đó
        # Pullback valid: giá hồi trong 50-100% distance từ breakout_level

        # Tìm high của breakout (giả định breakout từ swing high)
        swing_high = max(bar.high for bar in bars)

        pullback_distance = swing_high - breakout_level
        pullback_min = breakout_level + pullback_distance * 1.0  # 100% distance
        pullback_max = breakout_level + pullback_distance * 0.5  # 50% distance

        # Kiểm tra nếu close hiện tại nằm trong vùng pullback
        if breakout_level <= current_bar.close < swing_high:
            # Nằm trong vùng pullback
            if breakout_level <= current_bar.close <= pullback_min:
                # PULLBACK_VALID
                return RuleResult(
                    rule_id="RULE_004",
                    status="VALID",
                    score=15,
                    max_score=15,
                    reject=False,
                    detail={
                        "type": "valid",
                        "breakout_level": breakout_level,
                        "swing_high": swing_high,
                        "current_close": current_bar.close,
                        "pullback_range": (pullback_max, pullback_min),
                        "direction": "DOWN"
                    }
                )
            else:
                # Hồi nhẹ, vẫn ổn
                return RuleResult(
                    rule_id="RULE_004",
                    status="VALID",
                    score=15,
                    max_score=15,
                    reject=False,
                    detail={
                        "type": "light_pullback",
                        "breakout_level": breakout_level,
                        "swing_high": swing_high,
                        "current_close": current_bar.close,
                        "direction": "DOWN"
                    }
                )
        elif current_bar.close < breakout_level:
            # Tiếp tục xuống, chưa có pullback rõ ràng
            return RuleResult(
                rule_id="RULE_004",
                status="WAITING",
                score=10,
                max_score=15,
                reject=False,
                detail={
                    "type": "continuing",
                    "breakout_level": breakout_level,
                    "current_close": current_bar.close,
                    "direction": "DOWN",
                    "reason": "No pullback yet, price continuing"
                }
            )
        else:
            # Phá ngược (close > swing_high)
            return RuleResult(
                rule_id="RULE_004",
                status="FALSE_BREAK",
                score=0,
                max_score=15,
                reject=True,
                detail={
                    "type": "false_break",
                    "breakout_level": breakout_level,
                    "swing_high": swing_high,
                    "current_close": current_bar.close,
                    "direction": "DOWN",
                    "reason": "Close above swing high, false break"
                }
            )

    else:
        return RuleResult(
            rule_id="RULE_004",
            status="WAITING",
            score=0,
            max_score=15,
            reject=False,
            detail={"reason": "Invalid direction"}
        )
