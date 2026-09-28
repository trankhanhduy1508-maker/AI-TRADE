"""QA entrypoint tests; do not misrepresent mocked runner as broker PASS."""
from types import SimpleNamespace

from scripts import selftest_metaapi_cloud as runner


def test_fails_closed_when_required_tests_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    assert runner.main() == 2


def test_test_failure_never_reports_pass(monkeypatch, tmp_path):
    for file in runner.TESTS:
        target = tmp_path / file
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("def test_placeholder(): pass\n")
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    calls = []

    def fail(args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(returncode=1)

    monkeypatch.setattr(runner.subprocess, "run", fail)
    assert runner.main() == 1
    assert calls[0][0][:4] == [runner.sys.executable, "-m", "pytest", "-q"]


def test_success_only_after_offline_suite_succeeds(monkeypatch, tmp_path):
    for file in runner.TESTS:
        target = tmp_path / file
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("def test_placeholder(): pass\n")
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=0))
    assert runner.main() == 0
