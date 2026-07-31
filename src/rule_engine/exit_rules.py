"""RULE_010_EXIT — Quy tắc Thoát Lệnh.

Ref: rule_engine/RULE_010_EXIT.md
Khác với các rule 001-009 (xác định vào lệnh), rule này xác định thoát lệnh.

Output: ExitSignal (action, new_stop, reason)
- EXIT_NOW: Thoát ngay (stop loss hit, false break, hoặc structure break)
- HOLD: Giữ lệnh, xu hướng vẫn mạnh
- TRAIL_SL: Dời stop loss theo cấu trúc mới
"""

from dataclasses import dataclass
from src.rule_engine.types import Bar


@dataclass
class ExitSignal:
    """Tín hiệu thoát lệnh.

    Attributes:
        action: "EXIT_NOW", "HOLD", "TRAIL_SL"
        new_stop: Stop loss mới (nếu TRAIL_SL), hoặc None
        reason: Mô tả lý do thoát/giữ
    """
    action: str
    new_stop: float | None = None
    reason: str = ""


def evaluate_exit(
    bars: list[Bar],
    entry: float,
    stop: float,
    target: float | None,
    direction: str
) -> ExitSignal:
    """Đánh giá điều kiện thoát lệnh.

    Args:
        bars: Danh sách Bar từ entry point tới hiện tại
        entry: Entry price (giá vào lệnh)
        stop: Stop loss level (định sẵn)
        target: Target/Profit target (có thể None)
        direction: "UP" hoặc "DOWN"

    Returns:
        ExitSignal với action, new_stop (nếu apply), reason

    Logic (từ RULE_010_EXIT.md):
    1. Nếu giá chạm/vượt SL → EXIT_NOW (ưu tiên cao nhất)
    2. Nếu giá chạm target (nếu có) → EXIT_NOW (TAKE_PROFIT)
    3. Nếu phát hiện false break (giá phá hỏng cấu trúc breakout) → EXIT_NOW
    4. Nếu phát hiện CHoCH (cấu trúc đảo chiều) → EXIT_NOW hoặc TRAIL_SL
    5. Nếu xu hướng tiếp tục + hình thành swing mới → TRAIL_SL
    6. Nếu không có signal thoát rõ ràng → HOLD

    Giả định (vì không có full structure detection):
    - False break: nếu giá đảo ngược hướng entry mạnh trong 2-3 nến gần nhất
    - Structure break: nếu có lower high (DOWN) hoặc higher low (UP) rõ ràng trong 3 nến gần nhất
    - Trailing: nếu giá lên (UP) hoặc xuống (DOWN) mạnh + hình thành swing mới
    """

    if len(bars) < 2:
        return ExitSignal(action="HOLD", reason="Not enough data to evaluate exit")

    # Lấy giá hiện tại (nến gần nhất)
    current_price = bars[-1].close
    current_high = bars[-1].high
    current_low = bars[-1].low

    # 1. Kiểm tra Stop Loss Hit
    if direction == "UP":
        if current_low <= stop:
            return ExitSignal(
                action="EXIT_NOW",
                reason=f"Stop loss hit: price {current_price} <= SL {stop}"
            )
    elif direction == "DOWN":
        if current_high >= stop:
            return ExitSignal(
                action="EXIT_NOW",
                reason=f"Stop loss hit: price {current_price} >= SL {stop}"
            )

    # 2. Kiểm tra Take Profit Hit
    if target is not None:
        if direction == "UP":
            if current_high >= target:
                return ExitSignal(
                    action="EXIT_NOW",
                    reason=f"Target hit: price {current_price} >= target {target}"
                )
        elif direction == "DOWN":
            if current_low <= target:
                return ExitSignal(
                    action="EXIT_NOW",
                    reason=f"Target hit: price {current_price} <= target {target}"
                )

    # 3. Phát hiện False Break (giá phá hỏng cấu trúc breakout)
    # Giả định đơn giản: nếu giá breakout rồi đảo ngược vào trong entry
    if len(bars) >= 3:
        # Tìm bar gần nhất đóng phía đúng (breakout direction)
        found_breakout = False
        for i in range(len(bars) - 2, -1, -1):
            if direction == "UP" and bars[i].close > entry:
                found_breakout = True
                break
            elif direction == "DOWN" and bars[i].close < entry:
                found_breakout = True
                break

        if found_breakout:
            # Đã có breakout, kiểm tra nếu current price lại đi vào entry
            if direction == "UP" and current_price < entry:
                return ExitSignal(
                    action="EXIT_NOW",
                    reason=f"False break detected: price below entry {entry}"
                )
            elif direction == "DOWN" and current_price > entry:
                return ExitSignal(
                    action="EXIT_NOW",
                    reason=f"False break detected: price above entry {entry}"
                )

    # 4. Phát hiện CHoCH / Structure Break
    # Giả định đơn giản: nếu có 2 nến liên tiếp phá cấu trúc
    if len(bars) >= 3:
        prev_bar = bars[-2]

        if direction == "UP":
            # Lower High: nến hiện tại high < nến trước high → cấu trúc đảo
            if current_high < prev_bar.high and current_price < entry:
                # Cấu trúc đảo + giá dưới entry → exit
                return ExitSignal(
                    action="EXIT_NOW",
                    reason=f"Structure break: lower high detected, price below entry"
                )
        elif direction == "DOWN":
            # Higher Low: nến hiện tại low > nến trước low → cấu trúc đảo
            if current_low > prev_bar.low and current_price > entry:
                # Cấu trúc đảo + giá trên entry → exit
                return ExitSignal(
                    action="EXIT_NOW",
                    reason=f"Structure break: higher low detected, price above entry"
                )

    # 5. Trailing Stop Loss
    # Nếu xu hướng tiếp tục và có swing mới, dời SL
    if len(bars) >= 4:
        if direction == "UP":
            # Tìm swing low mới trong 3-4 nến gần nhất
            recent_lows = [b.low for b in bars[-4:-1]]
            new_swing_low = min(recent_lows)
            if new_swing_low > stop and new_swing_low < entry and current_price > entry:
                # Có swing low mới, cao hơn SL cũ → dời SL
                return ExitSignal(
                    action="TRAIL_SL",
                    new_stop=new_swing_low,
                    reason=f"Trailing SL: new swing low at {new_swing_low}"
                )
        elif direction == "DOWN":
            # Tìm swing high mới trong 3-4 nến gần nhất
            recent_highs = [b.high for b in bars[-4:-1]]
            new_swing_high = max(recent_highs)
            if new_swing_high < stop and new_swing_high > entry and current_price < entry:
                # Có swing high mới, thấp hơn SL cũ → dời SL
                return ExitSignal(
                    action="TRAIL_SL",
                    new_stop=new_swing_high,
                    reason=f"Trailing SL: new swing high at {new_swing_high}"
                )

    # 6. HOLD: Không có signal thoát rõ ràng
    return ExitSignal(
        action="HOLD",
        reason="No exit signal detected, trend continues"
    )
