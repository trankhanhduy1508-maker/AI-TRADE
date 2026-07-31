"""RULE_009_LIQUIDITY — Đánh giá Thanh khoản Thị trường.

Ref: rule_engine/RULE_009_LIQUIDITY.md
Thanh khoản kém → trượt giá lớn. Rule này cảnh báo khi vùng giá thiếu thanh khoản.

Scoring:
- GOOD (5): Spread < 2 pip, depth tốt
- FAIR (3): Spread 2-5 pip, depth trung bình
- POOR (0): Spread > 5 pip, depth sâu

Note: Liquidity không reject cứng (chỉ cảnh báo, có thể chờ hoặc vào với risk cao hơn)
"""

from src.rule_engine.types import RuleResult


def evaluate(spread_pips: float, depth_ok: bool = True) -> RuleResult:
    """Đánh giá thanh khoản dựa vào spread và depth.

    Args:
        spread_pips: Bid-Ask spread (pip)
        depth_ok: Có đủ order book depth hay không (default True)

    Returns:
        RuleResult với status GOOD/FAIR/POOR, score 5/3/0, reject=False (không reject cứng)

    Logic (từ RULE_009_LIQUIDITY.md):
    - Spread < 2 pip + depth_ok=True → GOOD (5)
    - Spread 2-5 pip + depth_ok=True → FAIR (3)
    - Spread > 5 pip hoặc depth_ok=False → POOR (0)
    """

    if spread_pips < 2 and depth_ok:
        status = "GOOD"
        score = 5.0
    elif 2 <= spread_pips <= 5 and depth_ok:
        status = "FAIR"
        score = 3.0
    else:
        # spread > 5 hoặc depth_ok=False
        status = "POOR"
        score = 0.0

    return RuleResult(
        rule_id="RULE_009",
        status=status,
        score=score,
        max_score=5,
        reject=False,  # Liquidity không reject cứng
        detail={
            "spread_pips": spread_pips,
            "depth_ok": depth_ok
        }
    )
