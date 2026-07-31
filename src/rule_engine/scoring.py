"""Scoring System & Decision Flow Orchestrator.

Ref: RULE_ENGINE.md sections 2, 3, 4
Orchest Decision Flow 10 bước tuần tự từ RULE_001 → RULE_009.
Nếu bất kỳ rule nào reject, dừng ngay.
Tính tổng score và quyết định: TRADE (>=80), WAIT (60-79), REJECT (<60).

Max score: Trend 25 + Structure 20 + Breakout 15 + Pullback 15 + Volume 10 +
           RSI 5 + EMA 5 + Risk 5 + Liquidity 5 = 100

Decision thresholds:
- Score >= 80 → TRADE
- 60-79 → WAIT
- < 60 → REJECT
"""

from dataclasses import dataclass, field
from src.rule_engine.types import Bar, RuleResult
from src.rule_engine import rsi_filter, ema_filter, risk_validation, liquidity_check


# Orchestrator sẽ import từ RULE_001-005, nhưng chúng có thể chưa tồn tại
# Dùng try-except để tránh ImportError
try:
    from src.rule_engine.trend_detection import evaluate as eval_rule_001
except ImportError:
    eval_rule_001 = None

try:
    from src.rule_engine.market_structure import evaluate as eval_rule_002
except ImportError:
    eval_rule_002 = None

try:
    from src.rule_engine.breakout_detection import evaluate as eval_rule_003
except ImportError:
    eval_rule_003 = None

try:
    from src.rule_engine.pullback_validation import evaluate as eval_rule_004
except ImportError:
    eval_rule_004 = None

try:
    from src.rule_engine.volume_confirmation import evaluate as eval_rule_005
except ImportError:
    eval_rule_005 = None


@dataclass
class SetupScore:
    """Output của scoring orchestrator.

    Attributes:
        total: Tổng điểm (0-100)
        decision: "TRADE", "WAIT", hoặc "REJECT"
        results: Danh sách RuleResult đã execute (kể cả những bị reject sớm)
    """
    total: float
    decision: str
    results: list[RuleResult] = field(default_factory=list)


def evaluate_setup(
    bars: list[Bar],
    entry: float,
    stop: float,
    target: float | None,
    direction: str,
    spread_pips: float = 2.0,
    depth_ok: bool = True,
) -> SetupScore:
    """Evaluate setup tuần tự từ RULE_001 → RULE_009.

    Thứ tự thực tế (RULE_ENGINE.md mục 2):
    RULE_001 → RULE_002 → RULE_003 → RULE_004 → RULE_005 → RULE_006 → RULE_007 → RULE_008 → RULE_009

    `direction` là hướng giao dịch ĐỀ XUẤT ("UP"/"DOWN"). RULE_001 tự phát hiện
    xu hướng thật từ `bars`; nếu xu hướng phát hiện được không khớp `direction`
    đề xuất (hoặc là NEUTRAL), setup bị reject ngay ở RULE_002 — đúng nguyên tắc
    "không giao dịch ngược xu hướng chính" (DECISIONS.md).

    `spread_pips`/`depth_ok` là input thanh khoản cho RULE_009 — CHƯA có nguồn
    dữ liệu order-book thật (chờ Data Loader), mặc định đặt thanh khoản "tạm ổn"
    cho tới khi có nguồn thật; caller (backtest/execution engine) nên truyền
    giá trị thật khi có.

    Args:
        bars: Danh sách Bar từ lịch sử tới hiện tại (không chứa nến chưa đóng).
        entry: Entry price
        stop: Stop loss level
        target: Target level (có thể None)
        direction: "UP" hoặc "DOWN" — hướng giao dịch đề xuất

    Returns:
        SetupScore(total, decision, results)
        - Nếu reject ở bước nào, results chứa các rule đã run, decision="REJECT"
        - Nếu xong tất cả: total = tổng score, decision = "TRADE"/"WAIT"/"REJECT"
    """
    results: list[RuleResult] = []
    total_score = 0.0
    expected_trend = "TREND_UP" if direction.upper() == "UP" else "TREND_DOWN"

    # === RULE_001: Trend (tự phát hiện từ bars, không nhận direction) ===
    if eval_rule_001 is None:
        return SetupScore(total=0.0, decision="REJECT", results=results)
    result = eval_rule_001(bars)
    results.append(result)
    if result.reject:
        return SetupScore(total=total_score, decision="REJECT", results=results)
    total_score += result.score

    # Xu hướng phát hiện được phải khớp hướng đề xuất — không giao dịch ngược xu hướng
    if result.status != expected_trend:
        return SetupScore(total=total_score, decision="REJECT", results=results)

    # === RULE_002: Market Structure (dùng trend_status thật từ RULE_001) ===
    if eval_rule_002 is None:
        return SetupScore(total=total_score, decision="REJECT", results=results)
    result = eval_rule_002(bars, result.status)
    results.append(result)
    if result.reject:
        return SetupScore(total=total_score, decision="REJECT", results=results)
    total_score += result.score

    structure_level = result.detail.get(
        "swing_high" if direction.upper() == "UP" else "swing_low"
    )

    # === RULE_003: Breakout (dùng structure_level thật từ RULE_002) ===
    if eval_rule_003 is None or structure_level is None:
        return SetupScore(total=total_score, decision="REJECT", results=results)
    result = eval_rule_003(bars, structure_level, direction)
    results.append(result)
    if result.reject:
        return SetupScore(total=total_score, decision="REJECT", results=results)
    total_score += result.score

    # === RULE_004: Pullback (breakout_level = structure_level vừa phá) ===
    if eval_rule_004 is not None:
        result = eval_rule_004(bars, structure_level, direction)
        results.append(result)
        if result.reject:
            return SetupScore(total=total_score, decision="REJECT", results=results)
        total_score += result.score

    # === RULE_005: Volume ===
    if eval_rule_005 is not None:
        result = eval_rule_005(bars)
        results.append(result)
        if result.reject:
            return SetupScore(total=total_score, decision="REJECT", results=results)
        total_score += result.score

    # === RULE_006: RSI ===
    result = rsi_filter.evaluate(bars, direction, period=14)
    results.append(result)
    if result.reject:
        return SetupScore(total=total_score, decision="REJECT", results=results)
    total_score += result.score

    # === RULE_007: EMA ===
    result = ema_filter.evaluate(bars, direction, period=50)
    results.append(result)
    if result.reject:
        return SetupScore(total=total_score, decision="REJECT", results=results)
    total_score += result.score

    # === RULE_008: Risk ===
    result = risk_validation.evaluate(entry, stop, target, direction, rr_min=1.5)
    results.append(result)
    if result.reject:
        return SetupScore(total=total_score, decision="REJECT", results=results)
    total_score += result.score

    # === RULE_009: Liquidity ===
    result = liquidity_check.evaluate(spread_pips=spread_pips, depth_ok=depth_ok)
    results.append(result)
    if result.reject:
        return SetupScore(total=total_score, decision="REJECT", results=results)
    total_score += result.score

    # === Tính Final Decision ===
    # Score thresholds (từ RULE_ENGINE.md mục 3.3)
    if total_score >= 80:
        decision = "TRADE"
    elif 60 <= total_score < 80:
        decision = "WAIT"
    else:  # < 60
        decision = "REJECT"

    return SetupScore(total=total_score, decision=decision, results=results)
