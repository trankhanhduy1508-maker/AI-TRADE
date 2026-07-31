"""RULE_003_BREAKOUT — Xác định Breakout Hợp lệ

Tham chiếu: rule_engine/RULE_003_BREAKOUT.md

Xác định xem giá có thực sự phá vỡ swing high/low theo cách hợp lệ
(body ratio > 60%) hay chỉ chạm bằng bóng nến.

Giả định đơn giản hoá: Hiện tại (chưa có khái niệm thời gian chờ),
NO_BREAKOUT → status="WAIT" (chưa phá vỡ, chờ xác nhận), reject=False.
"""

from src.rule_engine.types import Bar, RuleResult


def evaluate(
    bars: list[Bar],
    structure_level: float,
    direction: str,
    body_ratio_min: float = 0.6
) -> RuleResult:
    """
    Đánh giá breakout hợp lệ của nến cuối cùng so với structure level.

    Tham chiếu: rule_engine/RULE_003_BREAKOUT.md, mục 5 (Điều kiện)

    Args:
        bars: Danh sách các nến OHLCV.
        structure_level: Swing high/low level cần phá qua.
        direction: "UP" (phá qua swing high) hoặc "DOWN" (phá qua swing low).
        body_ratio_min: Tỷ lệ thân nến tối thiểu để coi là true breakout (mặc định 0.6).

    Returns:
        RuleResult với:
        - status: "BREAKOUT", "WEAK", hoặc "WAIT" (nếu chưa phá)
        - score: 15 (true), 10 (weak), 5 (wait), 0 (none → wait)
        - reject: False (breakout không tự reject, chỉ giảm điểm)
        - detail: Chứa body ratio, close price, so sánh với level
    """
    if not bars:
        return RuleResult(
            rule_id="RULE_003",
            status="WAIT",
            score=0,
            max_score=15,
            reject=False,
            detail={"reason": "No bars provided"}
        )

    bar = bars[-1]  # Nến cuối cùng (hiện tại)
    bar_range = bar.high - bar.low

    if bar_range == 0:
        # Doji hoặc nến không có range
        return RuleResult(
            rule_id="RULE_003",
            status="WAIT",
            score=0,
            max_score=15,
            reject=False,
            detail={
                "reason": "Doji or no range bar",
                "bar_high": bar.high,
                "bar_low": bar.low,
                "bar_close": bar.close
            }
        )

    # Tính body ratio
    if direction.upper() == "UP":
        body = bar.close - bar.open
        body_ratio = body / bar_range if bar_range > 0 else 0
    elif direction.upper() == "DOWN":
        body = bar.open - bar.close
        body_ratio = body / bar_range if bar_range > 0 else 0
    else:
        return RuleResult(
            rule_id="RULE_003",
            status="WAIT",
            score=0,
            max_score=15,
            reject=False,
            detail={"reason": "Invalid direction"}
        )

    # Kiểm tra breakout
    if direction.upper() == "UP":
        # UP breakout: close > structure_level
        if bar.close > structure_level:
            # Có breakout
            if body_ratio >= body_ratio_min:
                # BREAKOUT_TRUE
                return RuleResult(
                    rule_id="RULE_003",
                    status="BREAKOUT",
                    score=15,
                    max_score=15,
                    reject=False,
                    detail={
                        "type": "true",
                        "structure_level": structure_level,
                        "close": bar.close,
                        "body_ratio": round(body_ratio, 3),
                        "direction": "UP"
                    }
                )
            else:
                # BREAKOUT_WEAK (body ratio 40-60%)
                if body_ratio >= 0.4:
                    return RuleResult(
                        rule_id="RULE_003",
                        status="WEAK",
                        score=10,
                        max_score=15,
                        reject=False,
                        detail={
                            "type": "weak",
                            "structure_level": structure_level,
                            "close": bar.close,
                            "body_ratio": round(body_ratio, 3),
                            "direction": "UP"
                        }
                    )
                else:
                    # Very weak
                    return RuleResult(
                        rule_id="RULE_003",
                        status="WEAK",
                        score=5,
                        max_score=15,
                        reject=False,
                        detail={
                            "type": "very_weak",
                            "structure_level": structure_level,
                            "close": bar.close,
                            "body_ratio": round(body_ratio, 3),
                            "direction": "UP"
                        }
                    )
        else:
            # Chưa breakout
            return RuleResult(
                rule_id="RULE_003",
                status="WAIT",
                score=0,
                max_score=15,
                reject=False,
                detail={
                    "type": "no_breakout",
                    "structure_level": structure_level,
                    "close": bar.close,
                    "direction": "UP",
                    "reason": "Close below structure level"
                }
            )

    else:  # direction == "DOWN"
        # DOWN breakout: close < structure_level
        if bar.close < structure_level:
            # Có breakout
            if body_ratio >= body_ratio_min:
                # BREAKOUT_TRUE
                return RuleResult(
                    rule_id="RULE_003",
                    status="BREAKOUT",
                    score=15,
                    max_score=15,
                    reject=False,
                    detail={
                        "type": "true",
                        "structure_level": structure_level,
                        "close": bar.close,
                        "body_ratio": round(body_ratio, 3),
                        "direction": "DOWN"
                    }
                )
            else:
                # BREAKOUT_WEAK
                if body_ratio >= 0.4:
                    return RuleResult(
                        rule_id="RULE_003",
                        status="WEAK",
                        score=10,
                        max_score=15,
                        reject=False,
                        detail={
                            "type": "weak",
                            "structure_level": structure_level,
                            "close": bar.close,
                            "body_ratio": round(body_ratio, 3),
                            "direction": "DOWN"
                        }
                    )
                else:
                    # Very weak
                    return RuleResult(
                        rule_id="RULE_003",
                        status="WEAK",
                        score=5,
                        max_score=15,
                        reject=False,
                        detail={
                            "type": "very_weak",
                            "structure_level": structure_level,
                            "close": bar.close,
                            "body_ratio": round(body_ratio, 3),
                            "direction": "DOWN"
                        }
                    )
        else:
            # Chưa breakout
            return RuleResult(
                rule_id="RULE_003",
                status="WAIT",
                score=0,
                max_score=15,
                reject=False,
                detail={
                    "type": "no_breakout",
                    "structure_level": structure_level,
                    "close": bar.close,
                    "direction": "DOWN",
                    "reason": "Close above structure level"
                }
            )
