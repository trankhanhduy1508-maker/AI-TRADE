"""Fail closed before any Android package task.

This is a policy gate, NOT proof that a release is safe. The workflow intentionally
contains no APK build/publish steps until the Founder has accepted all gates and
the implementation has been independently verified on the Web App.
"""
from __future__ import annotations
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
APPROVAL = ROOT / "product" / "CWS_AI_TRADE_RELEASE_APPROVAL.json"
REQUIRED = (
    "web_app_html_mime_qa",
    "web_app_mobile_e2e",
    "founder_google_login_e2e",
    "mt5_authenticated_demo_readback",
    "model_approved_with_provenance_oos_wf_costs",
    "independent_risk_and_kill_switch_e2e",
    "the5ers_gate_if_applicable",
    "demo_auto_trade_forward_e2e",
    "stable_release_signing_and_update_e2e",
    "founder_release_approval",
    "live_money_locked",
)
def evaluate(payload: dict) -> tuple[bool, tuple[str,...]]:
    checks = payload.get("checks", {})
    if not isinstance(checks, dict):
        return False, ("INVALID_CHECKS",)
    missing = tuple(k for k in REQUIRED if not isinstance(checks.get(k),dict)
                    or checks[k].get("status") != "PASS"
                    or not isinstance(checks[k].get("evidence"),str)
                    or not checks[k]["evidence"].strip())
    return not missing, missing

def main() -> int:
    if not APPROVAL.is_file():
        print("BLOCKED: No approved Web App / demo auto-trade / Android update evidence. NO APK BUILD.")
        return 1
    try:
        value=json.loads(APPROVAL.read_text(encoding="utf-8"))
        if not isinstance(value,dict):
            raise ValueError("approval must be an object")
    except (ValueError,OSError) as e:
        print("BLOCKED: Invalid release approval; NO APK BUILD:",type(e).__name__)
        return 1
    allowed, missing=evaluate(value)
    if not allowed:
        print("BLOCKED: Release evidence missing for:",", ".join(missing),"; NO APK BUILD.")
        return 1
    print("Evidence manifest shape PASS. Independent runtime verification is still required.")
    print("NO APK BUILD: this workflow has no build or publish job until explicitly authorized.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
