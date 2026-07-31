"""RULE_008_RISK — Đánh giá Risk/Reward và Stop Loss.

Ref: rule_engine/RULE_008_RISK.md
Bắt buộc: Xác định stop loss hợp lệ và R/R >= ngưỡng tối thiểu.

Scoring:
- ACCEPTABLE (5): R/R >= 1.5, SL hợp lệ
- FAIR (3): R/R 1.0-1.5
- UNACCEPTABLE (0) + REJECT: R/R < 1.0 hoặc SL không xác định

Cấm tuyệt đối: R/R < 1.0 → REJECT (không exception)
"""

from src.rule_engine.types import RuleResult


def evaluate(
    entry: float,
    stop: float,
    target: float | None,
    direction: str,
    rr_min: float = 1.5
) -> RuleResult:
    """Đánh giá Risk/Reward và Stop Loss validity.

    Args:
        entry: Entry price
        stop: Stop loss level
        target: Target/Profit level (có thể None nếu chưa chốt target)
        direction: "UP" hoặc "DOWN"
        rr_min: R/R minimum threshold (default 1.5)

    Returns:
        RuleResult với status ACCEPTABLE/FAIR/UNACCEPTABLE/INVALID_STOP/NO_TARGET,
        score 5/3/0, reject flag nếu R/R < 1.0 hoặc SL không hợp lệ

    Logic (từ RULE_008_RISK.md):
    1. Kiểm tra SL validity:
       - stop == entry → INVALID_STOP (reject)
       - stop phía sai (UP nhưng stop > entry) → INVALID_STOP (reject)
    2. Nếu không có target → status NO_TARGET (không tính R/R, không reject)
    3. Tính R/R:
       - R/R >= rr_min (1.5) → ACCEPTABLE (5)
       - R/R 1.0-rr_min → FAIR (3)
       - R/R < 1.0 → UNACCEPTABLE (0) + REJECT
    """

    # Kiểm tra SL validity
    if entry == stop:
        return RuleResult(
            rule_id="RULE_008",
            status="INVALID_STOP",
            score=0.0,
            max_score=5,
            reject=True,
            detail={
                "entry": entry,
                "stop": stop,
                "reason": "Entry == Stop (no room to work)"
            }
        )

    # Kiểm tra stop phía đúng
    if direction == "UP":
        if stop > entry:
            return RuleResult(
                rule_id="RULE_008",
                status="INVALID_STOP",
                score=0.0,
                max_score=5,
                reject=True,
                detail={
                    "entry": entry,
                    "stop": stop,
                    "direction": direction,
                    "reason": "Stop above entry for UP direction"
                }
            )
    elif direction == "DOWN":
        if stop < entry:
            return RuleResult(
                rule_id="RULE_008",
                status="INVALID_STOP",
                score=0.0,
                max_score=5,
                reject=True,
                detail={
                    "entry": entry,
                    "stop": stop,
                    "direction": direction,
                    "reason": "Stop below entry for DOWN direction"
                }
            )

    # Nếu không có target
    if target is None:
        return RuleResult(
            rule_id="RULE_008",
            status="NO_TARGET",
            score=0.0,
            max_score=5,
            reject=False,
            detail={
                "entry": entry,
                "stop": stop,
                "target": target,
                "reason": "Cannot calculate R/R without target"
            }
        )

    # Tính R/R
    loss = abs(entry - stop)
    profit = abs(target - entry)

    if loss == 0:
        # Không thể tính R/R (stop quá gần entry)
        return RuleResult(
            rule_id="RULE_008",
            status="INVALID_STOP",
            score=0.0,
            max_score=5,
            reject=True,
            detail={
                "entry": entry,
                "stop": stop,
                "loss": loss,
                "reason": "Loss is zero (stop too close to entry)"
            }
        )

    rr = profit / loss

    # Áp dụng logic scoring
    if rr >= rr_min:
        status = "ACCEPTABLE"
        score = 5.0
    elif 1.0 <= rr < rr_min:
        status = "FAIR"
        score = 3.0
    else:  # rr < 1.0
        status = "UNACCEPTABLE"
        score = 0.0
        reject = True
        return RuleResult(
            rule_id="RULE_008",
            status=status,
            score=score,
            max_score=5,
            reject=True,
            detail={
                "entry": entry,
                "stop": stop,
                "target": target,
                "loss": loss,
                "profit": profit,
                "rr": rr,
                "rr_min": rr_min,
                "reason": f"R/R {rr:.2f} < {rr_min} (UNACCEPTABLE)"
            }
        )

    return RuleResult(
        rule_id="RULE_008",
        status=status,
        score=score,
        max_score=5,
        reject=False,
        detail={
            "entry": entry,
            "stop": stop,
            "target": target,
            "loss": loss,
            "profit": profit,
            "rr": rr,
            "rr_min": rr_min
        }
    )
