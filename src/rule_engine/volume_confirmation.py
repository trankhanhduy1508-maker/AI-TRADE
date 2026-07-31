"""RULE_005_VOLUME — Đánh giá Xác nhận Volume

Tham chiếu: rule_engine/RULE_005_VOLUME.md

Đánh giá khối lượng giao dịch xác nhận breakout/phản ứng.
Volume là chỉ báo xác nhận độ tin cậy của breakout.
"""

from src.rule_engine.types import Bar, RuleResult


def evaluate(bars: list[Bar], sma_period: int = 20) -> RuleResult:
    """
    Đánh giá volume xác nhận so với SMA volume.

    Tham chiếu: rule_engine/RULE_005_VOLUME.md, mục 5 (Điều kiện) và 3.2 (Cách tính điểm)

    Giả định:
    - Tính SMA volume từ `sma_period` nến TRƯỚC đó (không tính nến hiện tại).
    - So sánh volume nến cuối cùng với SMA.
    - Scoring dựa trên tỷ lệ % (>150%→10đ, 100-150%→7đ, 80-100%→5đ, <80%→0đ).

    Args:
        bars: Danh sách các nến OHLCV.
        sma_period: Số nến để tính SMA volume (mặc định 20).

    Returns:
        RuleResult với:
        - status: "STRONG", "NORMAL", "WEAK"
        - score: 10 (>150%), 7 (100-150%), 5 (80-100%), 0 (<80%)
        - reject: False (volume không tự reject, chỉ giảm điểm)
        - detail: Chứa SMA volume, current volume, ratio %
    """
    if not bars or len(bars) < sma_period + 1:
        return RuleResult(
            rule_id="RULE_005",
            status="WEAK",
            score=0,
            max_score=10,
            reject=False,
            detail={
                "reason": "Insufficient bars for SMA calculation",
                "bars_available": len(bars) if bars else 0,
                "bars_required": sma_period + 1
            }
        )

    # Tính SMA volume từ sma_period nến trước đó (không tính nến hiện tại)
    # Ví dụ: nếu có 25 bars và sma_period=20, lấy bars[0:20]
    sma_bars = bars[-sma_period - 1:-1]  # Lấy sma_period nến trước nến cuối cùng

    if len(sma_bars) < sma_period:
        # Không đủ bars để tính SMA
        return RuleResult(
            rule_id="RULE_005",
            status="WEAK",
            score=0,
            max_score=10,
            reject=False,
            detail={
                "reason": "Insufficient historical bars for SMA",
                "available": len(sma_bars)
            }
        )

    sma_volume = sum(bar.volume for bar in sma_bars) / len(sma_bars)
    current_volume = bars[-1].volume

    if sma_volume == 0:
        return RuleResult(
            rule_id="RULE_005",
            status="WEAK",
            score=0,
            max_score=10,
            reject=False,
            detail={"reason": "SMA volume is zero"}
        )

    # Tính tỷ lệ %
    volume_ratio = current_volume / sma_volume
    volume_pct = volume_ratio * 100

    # Xác định status và score dựa trên bảng (mục 3.2)
    if volume_ratio > 1.5:  # > 150%
        status = "STRONG"
        score = 10
    elif volume_ratio >= 1.0:  # 100-150%
        status = "NORMAL"
        score = 7
    elif volume_ratio >= 0.8:  # 80-100%
        status = "WEAK"
        score = 5
    else:  # < 80%
        status = "WEAK"
        score = 0

    return RuleResult(
        rule_id="RULE_005",
        status=status,
        score=score,
        max_score=10,
        reject=False,
        detail={
            "current_volume": current_volume,
            "sma_volume": round(sma_volume, 2),
            "volume_ratio": round(volume_ratio, 3),
            "volume_pct": round(volume_pct, 1),
            "sma_period": sma_period
        }
    )
