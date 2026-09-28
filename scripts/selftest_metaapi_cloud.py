"""Run the current, offline MetaApi DEMO adapter and readback tests.

The deprecated transport-era self-test imported classes no longer present in
MetaApiCloudAdapter. This command never authorizes real broker orders.
"""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TESTS = (
    "tests/execution/test_metaapi_cloud.py",
    "tests/execution/test_metaapi_demo_guard.py",
    "tests/execution/test_metaapi_readback.py",
)


def main() -> int:
    if any(not (ROOT / path).is_file() for path in TESTS):
        print("BLOCKED: missing current offline MetaApi tests")
        return 2
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *TESTS],
        cwd=ROOT,
        check=False,
    )
    if completed.returncode:
        print("METAAPI_CLOUD_SELFTEST_FAIL")
        return completed.returncode
    print("METAAPI_CLOUD_SELFTEST_PASS (offline fakes only, not broker E2E)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
