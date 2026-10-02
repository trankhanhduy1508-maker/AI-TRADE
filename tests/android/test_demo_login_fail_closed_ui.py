"""Source regression checks only: no Android device or broker is used."""
from pathlib import Path


SOURCE = (
    Path(__file__).resolve().parents[2]
    / "android/app/src/main/java/vn/cws/aitrade/DemoLoginActivity.java"
)


def test_failed_demo_relogin_clears_previous_broker_values():
    code = SOURCE.read_text(encoding="utf-8")
    assert "private void verifyDemo() {" in code
    method = code.split("private void verifyDemo() {", 1)[1].split(
        "/** Response size bounded", 1
    )[0]
    placeholder = 'account.setText("Balance: — | Equity: — | Positions: —"'
    # Clear immediately and again after any asynchronous failure.
    assert method.count(placeholder) == 2
    assert method.index(placeholder) < method.index("if (!id.matches(")
    catch = method.split("} catch (Exception error) {", 1)[1]
    assert catch.index(placeholder) < catch.index(
        'status.setText("Không xác minh được MT5 DEMO.'
    )
    assert method.count(r'\nKhông có dữ liệu broker mới.') == 2
    assert r'\\nKhông có dữ liệu broker mới.' not in method
    assert "Auto Trade: LOCKED | LIVE: LOCKED" in method
