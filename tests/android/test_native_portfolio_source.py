"""Source QA: DEMO broker aggregate is native and never uses synthetic positions."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "android/app/src/main/java/vn/cws/aitrade"


def test_native_broker_summary_is_wired_only_after_validation():
    activity = (APP / "DemoLoginActivity.java").read_text(encoding="utf-8")
    body = activity.split("private void refresh() {", 1)[1].split(
        "private void verifyDemo() {", 1
    )[0]
    assert "NativePortfolioSummary.of(nativePositions)" in body
    assert "summary.display(currency)" in body
    assert body.index("double lot = p.getDouble") < body.index(
        "nativePositions.add(new NativePortfolioSummary.Position"
    )
    assert body.index("summary.display(currency)") < body.index(
        'append("\\nVị thế chi tiết:")'
    )
    assert r'\\nBalance: ' not in body
    assert r'\\nEquity: ' not in body
    assert r'\\nPositions: ' not in body
    assert "readbackSource" in body and "MT5_INVESTOR_BROKER" in body


def test_portfolio_has_no_total_lot_dashboard_metric():
    aggregator = (APP / "NativePortfolioSummary.java").read_text(encoding="utf-8")
    assert "Tổng lãi: " in aggregator
    assert "Tổng lỗ: " in aggregator
    assert "Lãi/lỗ ròng: " in aggregator
    assert "Số cặp có vị thế: " in aggregator
    assert "Tổng Lot" not in aggregator
    assert "INVALID_BROKER_POSITION_COUNT" in aggregator
