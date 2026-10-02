"""Source and reproducible first-party Android WebView asset build contract.

Run on a checked-out repository with: pytest -q tests/android/test_android_asset_packaging.py
This does NOT establish an APK build or device E2E.
"""
from __future__ import annotations
from pathlib import Path
import re
from scripts.build_cws_trade_static import build

ROOT = Path(__file__).resolve().parents[2]
WEBVIEW = ROOT / "android/app/src/main/java/vn/cws/aitrade/MainActivity.java"
BUNDLE = {
    "index.html", "styles.css", "portfolio.js", "tradingview.js",
    "app.js", "pwa.js", "sw.js", "manifest.webmanifest",
    "icon-192.png", "icon-512.png",
}
PRIVATE_FORBIDDEN = (".epub", ".sqlite", ".key", ".jks", ".keystore")


def test_native_asset_build_whitelist_and_brand(tmp_path: Path):
    output = tmp_path / "www"
    manifest = build(output, "/assets/", android=True)
    assert BUNDLE.issubset(manifest)
    assert set(manifest) == BUNDLE | {"mt5-login.html", "founder-mt5.js"}
    assert {f.name for f in output.iterdir()} == set(manifest) | {".nojekyll"}
    assert not any(name.lower().endswith(PRIVATE_FORBIDDEN) for name in manifest)
    index = (output / "index.html").read_text(encoding="utf-8")
    assert "<title>CWS AutoTrade · DEMO LOCKED</title>" in index
    assert '<script src="./pwa.js" defer></script>' not in index
    assert "/functions/v1/cws-ai-trade-site/app/" not in index
    assert "https://appassets.androidplatform.net/" not in index
    for name in BUNDLE:
        assert (output / name).is_file(), name


def test_webview_asset_allowlist_matches_built_distribution(tmp_path: Path):
    output = tmp_path / "www"
    build(output, "/assets/", android=True)
    source = WEBVIEW.read_text(encoding="utf-8")
    values = source.split("private static final Set<String> ALLOWED", 1)[1]
    values = values.split("Arrays.asList(", 1)[1].split("));", 1)[0]
    allowed = set(re.findall(r'"([^"]+)"', values))
    assert allowed == BUNDLE
    # HTML auth bridge deliberately does not live in native WebView.
    assert "founder-mt5.js" not in allowed
    assert "mt5-login.html" not in allowed
