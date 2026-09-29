"""Static regression gate; device lifecycle race still needs Android E2E."""
from pathlib import Path

ACTIVITY = (
    Path(__file__).resolve().parents[2]
    / "android/app/src/main/java/vn/cws/aitrade/DemoLoginActivity.java"
)


def _methods():
    src = ACTIVITY.read_text(encoding="utf-8")
    refresh = src.split("    private void refresh() {", 1)[1].split(
        "    private void verifyDemo() {", 1
    )[0]
    verify = src.split("    private void verifyDemo() {", 1)[1].split(
        "    /** Response size bounded", 1
    )[0]
    return src, refresh, verify


def test_stale_refresh_cannot_overwrite_a_newer_demo_verification():
    source, refresh, verify = _methods()
    assert "private volatile long brokerGeneration = 0L;" in source
    assert "final long operation = ++brokerGeneration;" in refresh
    assert "final long operation = ++brokerGeneration;" in verify
    assert "if (generation != sessionGeneration || operation != brokerGeneration)" in refresh
    assert "if (generation == sessionGeneration && operation == brokerGeneration)" in refresh
    assert refresh.count("operation != brokerGeneration") >= 5
    assert verify.count("operation != brokerGeneration") >= 3
    assert verify.index("++brokerGeneration") < verify.index('password.setText("");')
    assert verify.index("refreshButton.setEnabled(false);") < verify.index(
        'network.execute(() -> {'
    )


def test_failed_relogin_restores_only_its_own_buttons():
    _, _, verify = _methods()
    invalid = verify.split('status.setText("UNSUPPORTED_SERVER', 1)[1]
    assert invalid.index("refreshButton.setEnabled(!accessToken.isEmpty());") < invalid.index("return;")
    failure = verify.split("} catch (Exception error) {", 1)[1].split(
        "} finally {", 1
    )[0]
    assert "generation == sessionGeneration && operation == brokerGeneration" in failure
    completion = verify.split("} finally {", 1)[1]
    assert "if (operation == brokerGeneration)" in completion
    assert "verifyButton.setEnabled(!accessToken.isEmpty());" in completion
    assert "refreshButton.setEnabled(!accessToken.isEmpty());" in completion
