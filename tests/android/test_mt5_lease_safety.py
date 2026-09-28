"""Static security invariant for OIDC preflight lease. Source-only QA."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "supabase/functions/ai-trade-mt5-demo-lease/index.ts"


def test_preflight_lease_cannot_grant_demo_order_permission():
    source = SOURCE.read_text(encoding="utf-8")
    assert 'ALLOWED_PURPOSES=new Set(["preflight"])' in source
    assert 'brokerOrdersAllowed:false' in source
    assert 'brokerOrdersAllowed:purpose!=="preflight"' not in source
    assert "credentialScope:\"INVESTOR_READ_ONLY\"" in source


def test_preflight_lease_uses_investor_secret_only():
    source = SOURCE.read_text(encoding="utf-8")
    assert "investor.decrypted_secret as investor_password" in source
    assert "investor.id=a.investor_password_secret_id" in source
    assert "password:String(row.investor_password)" in source
    assert "NO_READ_ONLY_DEMO_CREDENTIAL" in source
    assert re.search(r"\ba\.password_secret_id\b", source) is None
    assert re.search(r"\brow\.password\b", source) is None
