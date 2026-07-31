"""RULE_001_TREND — Xác định Xu hướng Hợp lệ (trend_detection.py)

Tham chiếu: rule_engine/RULE_001_TREND.md

Xác định xu hướng (UP/DOWN/NEUTRAL) bằng cấu trúc Higher High/Higher Low (tăng)
hoặc Lower High/Lower Low (giảm). Bắt buộc tối thiểu 2 cặp liên tiếp rõ ràng.
"""

from src.rule_engine.types import Bar, RuleResult


def _identify_trend_from_swings(bars: list[Bar], n: int = 2) -> tuple[str, int, int]:
    """
    Xác định xu hướng dựa trên cấu trúc HH/HL hoặc LH/LL.

    Phương pháp: Tìm swing highs và lows, sau đó kiểm tra xem chúng có tạo thành
    chuỗi HH/HL (uptrend) hay LH/LL (downtrend).

    Returns:
        (status, hh_hl_pairs, lh_ll_pairs): Trạng thái xu hướng và số cặp
    """
    if len(bars) < 2 * n + 1:
        return "TREND_NEUTRAL", 0, 0

    # Tìm tất cả local highs và local lows
    local_highs = []  # (index, value)
    local_lows = []   # (index, value)

    for i in range(n, len(bars) - n):
        # Check if local high
        is_high = all(bars[i].high > bars[j].high for j in range(i - n, i)) and \
                  all(bars[i].high > bars[j].high for j in range(i + 1, i + n + 1))
        if is_high:
            local_highs.append((i, bars[i].high))

        # Check if local low
        is_low = all(bars[i].low < bars[j].low for j in range(i - n, i)) and \
                 all(bars[i].low < bars[j].low for j in range(i + 1, i + n + 1))
        if is_low:
            local_lows.append((i, bars[i].low))

    if len(local_highs) < 2 and len(local_lows) < 2:
        return "TREND_NEUTRAL", 0, 0

    # Đơn giản hoá: Nếu có 2+ swing highs với Higher Highs → TREND_UP
    hh_count = 0
    for i in range(len(local_highs) - 1):
        if local_highs[i][1] < local_highs[i + 1][1]:
            hh_count += 1

    # Nếu có 2+ swing lows với Higher Lows → TREND_UP
    hl_count = 0
    for i in range(len(local_lows) - 1):
        if local_lows[i][1] < local_lows[i + 1][1]:
            hl_count += 1

    # Nếu có 2+ swing highs với Lower Highs → TREND_DOWN
    lh_count = 0
    for i in range(len(local_highs) - 1):
        if local_highs[i][1] > local_highs[i + 1][1]:
            lh_count += 1

    # Nếu có 2+ swing lows với Lower Lows → TREND_DOWN
    ll_count = 0
    for i in range(len(local_lows) - 1):
        if local_lows[i][1] > local_lows[i + 1][1]:
            ll_count += 1

    # Xác định trend: cần có cả HH và HL (hoặc LH và LL)
    # Giả định: nếu HH >= 2 hay HL >= 2 → TREND_UP
    hh_hl_pairs = min(hh_count, hl_count) if hh_count > 0 and hl_count > 0 else max(hh_count, hl_count)

    # Tương tự cho downtrend
    lh_ll_pairs = min(lh_count, ll_count) if lh_count > 0 and ll_count > 0 else max(lh_count, ll_count)

    if hh_hl_pairs >= 2:
        return "TREND_UP", hh_hl_pairs, lh_ll_pairs
    elif lh_ll_pairs >= 2:
        return "TREND_DOWN", hh_hl_pairs, lh_ll_pairs
    else:
        return "TREND_NEUTRAL", hh_hl_pairs, lh_ll_pairs


def evaluate(bars: list[Bar], n: int = 2) -> RuleResult:
    """
    Đánh giá xu hướng hiện tại dựa trên cấu trúc swing high/low.

    Tham chiếu: rule_engine/RULE_001_TREND.md, mục 5 (Điều kiện) và 3.2 (Cách tính điểm)

    Args:
        bars: Danh sách các nến OHLCV (tối thiểu 20-50 nến).
        n: Số nến trái/phải để định nghĩa swing (mặc định 2).

    Returns:
        RuleResult với:
        - status: "TREND_UP", "TREND_DOWN", hoặc "TREND_NEUTRAL"
        - score: Điểm theo bảng (25, 20-22, 15-18, 0)
        - reject: True nếu TREND_NEUTRAL, False nếu UP/DOWN
        - detail: Chứa số cặp HH/HL hoặc LH/LL tìm được
    """
    if not bars or len(bars) < 2 * n + 1:
        return RuleResult(
            rule_id="RULE_001",
            status="TREND_NEUTRAL",
            score=0,
            max_score=25,
            reject=True,
            detail={"reason": "Insufficient bars for swing detection"}
        )

    status, hh_hl_pairs, lh_ll_pairs = _identify_trend_from_swings(bars, n)

    # Xác định xu hướng
    if status == "TREND_UP":
        if hh_hl_pairs >= 3:
            score = 25  # 3+ pairs rõ ràng
        else:
            score = 21  # 2 cặp rõ ràng (mặc định)

        return RuleResult(
            rule_id="RULE_001",
            status="TREND_UP",
            score=score,
            max_score=25,
            reject=False,
            detail={
                "hh_hl_pairs": hh_hl_pairs,
                "lh_ll_pairs": lh_ll_pairs
            }
        )
    elif status == "TREND_DOWN":
        if lh_ll_pairs >= 3:
            score = 25  # 3+ pairs rõ ràng
        else:
            score = 21  # 2 cặp rõ ràng (mặc định)

        return RuleResult(
            rule_id="RULE_001",
            status="TREND_DOWN",
            score=score,
            max_score=25,
            reject=False,
            detail={
                "hh_hl_pairs": hh_hl_pairs,
                "lh_ll_pairs": lh_ll_pairs
            }
        )
    else:
        # TREND_NEUTRAL — không đủ 2 cặp
        return RuleResult(
            rule_id="RULE_001",
            status="TREND_NEUTRAL",
            score=0,
            max_score=25,
            reject=True,
            detail={
                "hh_hl_pairs": hh_hl_pairs,
                "lh_ll_pairs": lh_ll_pairs,
                "reason": "Insufficient trend pairs"
            }
        )
