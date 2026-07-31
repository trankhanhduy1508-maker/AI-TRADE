"""Integration test: evaluate_setup() chạy qua các module RULE_001-005 THẬT
(không mock) để xác nhận các module ghép nối đúng chữ ký/hợp đồng dữ liệu
(Bar, RuleResult, detail keys như swing_high/swing_low).

Không assert quyết định TRADE/WAIT/REJECT cụ thể (phụ thuộc dữ liệu giả định),
chỉ xác nhận pipeline chạy hết mà không lỗi và trả về cấu trúc hợp lệ.
"""

from src.rule_engine.types import Bar
from src.rule_engine.scoring import evaluate_setup, SetupScore


def _uptrend_bars() -> list[Bar]:
    # Fixture giống test_trend_detection.test_trend_up_clear_structure —
    # đã xác nhận cho TREND_UP thật với n=2.
    return [
        Bar("2024-01-01", 90, 95, 85, 93, 1000),
        Bar("2024-01-02", 93, 98, 90, 96, 1000),
        Bar("2024-01-03", 96, 105, 92, 100, 1000),
        Bar("2024-01-04", 100, 100, 90, 98, 1000),
        Bar("2024-01-05", 98, 102, 95, 99, 1000),
        Bar("2024-01-06", 99, 110, 96, 105, 1000),
        Bar("2024-01-07", 105, 108, 104, 107, 1000),
        Bar("2024-01-08", 107, 108, 104, 106, 1000),
        Bar("2024-01-09", 106, 115, 100, 112, 1000),
        Bar("2024-01-10", 112, 112, 108, 110, 1000),
        Bar("2024-01-11", 110, 114, 109, 111, 1000),
        Bar("2024-01-12", 111, 112, 110, 111, 1000),
    ]


def test_evaluate_setup_runs_real_pipeline_up_no_crash():
    bars = _uptrend_bars()
    score = evaluate_setup(bars=bars, entry=111.5, stop=108.0, target=118.0, direction="UP")

    assert isinstance(score, SetupScore)
    assert score.decision in ("TRADE", "WAIT", "REJECT")
    assert len(score.results) >= 1
    assert score.results[0].rule_id == "RULE_001"
    # rule_id phải theo đúng thứ tự Decision Flow, không lặp/nhảy cóc
    rule_ids = [r.rule_id for r in score.results]
    assert rule_ids == sorted(set(rule_ids), key=rule_ids.index)  # không trùng lặp


def test_evaluate_setup_wrong_direction_rejects_via_real_rule_001():
    # Dữ liệu là uptrend thật (TREND_UP) nhưng đề xuất direction=DOWN
    # -> phải reject sớm do lệch xu hướng (không phải do lỗi kiểu dữ liệu).
    bars = _uptrend_bars()
    score = evaluate_setup(bars=bars, entry=95.0, stop=100.0, target=85.0, direction="DOWN")

    assert score.decision == "REJECT"


def test_evaluate_setup_down_pipeline_no_crash():
    bars = [
        Bar("2024-01-01", 105, 115, 95, 110, 1000),
        Bar("2024-01-02", 110, 112, 88, 108, 1000),
        Bar("2024-01-03", 108, 110, 85, 105, 1000),
        Bar("2024-01-04", 105, 108, 87, 100, 1000),
        Bar("2024-01-05", 100, 105, 78, 102, 1000),
        Bar("2024-01-06", 102, 100, 75, 95, 1000),
    ]
    score = evaluate_setup(bars=bars, entry=94.0, stop=98.0, target=85.0, direction="DOWN")

    assert isinstance(score, SetupScore)
    assert score.decision in ("TRADE", "WAIT", "REJECT")
