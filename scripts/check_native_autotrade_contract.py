"""Run standalone Android Java contract tests without building or releasing an APK.

This is source-only QA. It cannot prove Android SDK compatibility, broker
connectivity, Google OAuth, physical-device behavior, or release signing.
"""
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "android/app/src/main/java/vn/cws/aitrade"
CHECKS = (
    ("NativeDemoAuth", "NativeDemoAuthCheck", "PKCE"),
    ("NativeReleaseVerifier", "NativeReleaseVerifierCheck", "signed-update"),
    ("NativeSessionCodec", "NativeSessionCodecCheck", "encrypted-session"),
)


def run() -> int:
    javac, java = shutil.which("javac"), shutil.which("java")
    if javac is None or java is None:
        print("BLOCKED: JDK javac and java are required; source-only QA not run.")
        return 2
    with tempfile.TemporaryDirectory(prefix="cws-native-qa-") as temp:
        for name, check, label in CHECKS:
            source = SOURCE / (name + ".java")
            test = ROOT / "android/qa" / (check + ".java")
            if not source.is_file() or not test.is_file():
                print(f"BLOCKED: missing {label} sources or tests.")
                return 2
            compile_result = subprocess.run(
                [javac, "-encoding", "UTF-8", "-d", temp, str(source), str(test)],
                text=True, capture_output=True, timeout=30, check=False,
            )
            if compile_result.returncode:
                print(f"FAIL: {label} Java compile: {compile_result.stderr[-2400:]}")
                return 1
            tested = subprocess.run(
                [java, "-cp", temp, check],
                text=True, capture_output=True, timeout=30, check=False,
            )
            if tested.returncode or not tested.stdout.startswith("PASS:"):
                print(f"FAIL: {label} contract: {(tested.stdout + tested.stderr)[-2400:]}")
                return 1
            print(tested.stdout.strip())
    print("PASS: source-only Java QA. Android SDK/device/broker/release NOT TESTED.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
