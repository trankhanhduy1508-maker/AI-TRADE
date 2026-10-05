"""Create a portable, license-conscious CWS AI Trade static PWA.

Supabase Edge on the shared supabase.co domain rewrites HTML to text/plain.
This builder emits browser-renderable static HTML/JS/CSS for a *separate*
static frontend host. The Supabase backend remains API-only. Never use this
to publish private Masterbook EPUBs, market snapshots or model artifacts.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import struct
import zlib

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "google-sites" / "cws-ai-trade"
ALLOWLIST = ("index.html", "styles.css", "portfolio.js", "tradingview.js",
             "app.js", "pwa.js", "sw.js", "manifest.webmanifest",
             "mt5-login.html", "founder-mt5.js", "session-client.js")
APP_OLD_ROOT = "/functions/v1/cws-ai-trade-site/app/"


def _require_replace(value: str, old: str, new: str, label: str) -> str:
    if old not in value:
        raise ValueError("missing static-build anchor: " + label)
    return value.replace(old, new)


def _icon(size: int) -> bytes:
    """Exact stdlib port of the first-party Supabase PWA icon raster."""
    if size not in (192, 512):
        raise ValueError("invalid icon size")
    scan = bytearray(size * (1 + size * 4))
    points = ((.19, .68), (.37, .52), (.49, .58), (.73, .32), (.80, .37))
    for y in range(size):
        line = y * (1 + size * 4)
        for x in range(size):
            u, v, at = (x + .5) / size, (y + .5) / size, line + 1 + x * 4
            red, green, blue = 8, 19, 32
            dx = max(abs(u - .5) - .33, 0)
            dy = max(abs(v - .5) - .33, 0)
            dist = math.hypot(dx, dy)
            within = dist <= .14
            if within:
                red, green, blue = 16, 45, 66
            if dist >= .122 and within:
                red, green, blue = 38, 105, 148
            diamond = abs(u - .34) + abs(v - .28)
            if diamond < .135:
                red, green, blue = 45, 155, 242
            if u > .34 and diamond < .135:
                red, green, blue = 24, 111, 215
            for (ax, ay), (bx, by) in zip(points, points[1:]):
                sx, sy = bx - ax, by - ay
                k = max(0, min(1, ((u - ax)*sx + (v - ay)*sy)/(sx*sx + sy*sy)))
                if math.hypot(u - ax - k*sx, v - ay - k*sy) < .019:
                    red, green, blue = 41, 217, 163
                    break
            scan[at:at+4] = bytes((red, green, blue, 255))
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I",len(data)) + kind + data + struct.pack(
            ">I",zlib.crc32(kind+data)&0xffffffff)
    ihdr = struct.pack(">IIBBBBB",size,size,8,6,0,0,0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR",ihdr) + chunk(
        b"IDAT",zlib.compress(scan,9)) + chunk(b"IEND",b"")


def _cache_revision(source: dict[str, str]) -> str:
    """Content-addressed SW cache: every first-party source change upgrades PWA."""
    parts = [
        f"{name}\\0{sha256(source[name].encode('utf-8')).hexdigest()}"
        for name in sorted(source)
    ]
    parts.append("builder\\0" + sha256(Path(__file__).read_bytes()).hexdigest())
    return sha256("\\n".join(parts).encode("utf-8")).hexdigest()[:12]


def build(output: Path, base: str = "/", *, android: bool = False) -> dict[str, str]:
    """Whitelist public source assets and emit direct URLs (no API HTML)."""
    if not re.fullmatch(r"/(?:[A-Za-z0-9_-]+/)*", base):
        raise ValueError("base must be a safe root-relative directory")
    if android and base != "/assets/":
        raise ValueError("Android asset base must be /assets/")
    if not SOURCE.is_dir():
        raise ValueError("verified first-party source directory is missing")
    if output.resolve() == SOURCE.resolve():
        raise ValueError("refuse to overwrite canonical Web App source")
    source = {name:(SOURCE/name).read_text(encoding="utf-8") for name in ALLOWLIST}
    if "preview-candles" in source["app.js"]:
        raise ValueError("public Yahoo quote proxy must remain disabled")
    if "embed-widget-advanced-chart.js" not in source["tradingview.js"]:
        raise ValueError("official hosted chart module missing")
    index = source["index.html"]
    index = _require_replace(index,APP_OLD_ROOT+"?asset=",base,"head manifest and icons")
    index = _require_replace(index,'"?asset=', '"./',"static CSS and scripts")
    if "?asset=" in index or APP_OLD_ROOT in index:
        raise ValueError("nonstatic asset URL remains in HTML")
    if android:
        index = _require_replace(index,'<script src="./pwa.js" defer></script>',
                                 "<!-- Native Android includes the offline shell; no PWA registration. -->",
                                 "Android shell install")
        index = _require_replace(index, "<title>CWS AI Trade · Founder</title>",
                                 "<title>CWS AutoTrade · DEMO LOCKED</title>",
                                 "Android-only app title")
        index = _require_replace(index,
                                 "<strong>CWS <em>AI TRADE</em></strong>",
                                 "<strong>CWS <em>AUTOTRADE</em></strong>",
                                 "Android-only app brand")
        index = _require_replace(index, "<h1>CWS AI Trade</h1>",
                                 "<h1>CWS AutoTrade</h1>",
                                 "Android-only dashboard title")
    source["index.html"] = index

    pwa = source["pwa.js"]
    pwa = _require_replace(pwa,'const BASE="'+APP_OLD_ROOT+'";',
                           'const BASE='+json.dumps(base)+';',"PWA root")
    pwa = _require_replace(pwa,'location.pathname===BASE&&',
                           '(location.pathname===BASE||location.pathname===BASE+"index.html")&&',
                           "PWA top-level path")
    pwa = _require_replace(pwa,'navigator.serviceWorker.register(BASE+"?asset=sw.js"',
                           'navigator.serviceWorker.register(BASE+"sw.js"',
                           "PWA worker path")
    source["pwa.js"] = pwa

    sw = source["sw.js"]
    sw = _require_replace(sw,'const ROOT="'+APP_OLD_ROOT+'";',
                          'const ROOT='+json.dumps(base)+';',"offline root")
    sw = _require_replace(sw,'cws-ai-trade-static-v5',
                          'cws-ai-trade-static-'+_cache_revision(source),
                          "content-addressed PWA cache version")
    sw = _require_replace(sw,'ROOT+"?asset=','ROOT+"',"direct offline assets")
    sw = _require_replace(sw,'const asset=u.searchParams.get("asset");',
                          'const asset=u.pathname.slice(ROOT.length);',"static asset guard")
    if '?asset=' in sw:
        raise ValueError("query-format assets remain in service worker")
    source["sw.js"] = sw

    manifest = json.loads(source["manifest.webmanifest"])
    manifest["id"] = base
    manifest["start_url"] = base
    manifest["scope"] = base
    if android:
        manifest["name"] = "CWS AutoTrade"
        manifest["short_name"] = "CWS AutoTrade"
        manifest["description"] = "CWS AutoTrade: quản lý danh mục, kết nối MT5 DEMO; Auto Trade chưa được phê duyệt."
    for icon in manifest.get("icons",[]):
        icon["src"] = base + "icon-" + icon["sizes"].split("x")[0] + ".png"
    for shortcut in manifest.get("shortcuts",[]):
        view = shortcut["url"].split("view=",1)[-1]
        if view not in ("portfolio","book"):
            raise ValueError("unverified PWA shortcut")
        shortcut["url"] = base + "?view=" + view
        for icon in shortcut.get("icons",[]):
            icon["src"] = base + "icon-192.png"
    source["manifest.webmanifest"] = json.dumps(
        manifest,ensure_ascii=False,indent=2)+"\n"
    if APP_OLD_ROOT in "".join(source[n] for n in (
        "index.html","pwa.js","sw.js","manifest.webmanifest")):
        raise ValueError("shared-domain PWA URLs remain")
    # Explicit whitelist prevents accidental inclusion of private input,
    # book chapters, research models, credentials and data snapshots.
    output.mkdir(parents=True,exist_ok=True)
    digest = {}
    for name, content in source.items():
        data = content.encode("utf-8")
        (output/name).write_bytes(data)
        digest[name] = sha256(data).hexdigest()
    for size in (192,512):
        data = _icon(size)
        name = f"icon-{size}.png"
        (output/name).write_bytes(data)
        digest[name] = sha256(data).hexdigest()
    # Render's no-op build or GitHub Pages directly serves this directory.
    (output/".nojekyll").write_text("",encoding="utf-8")
    return digest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base",default="/")
    parser.add_argument("--output",default="site-dist")
    parser.add_argument("--android",action="store_true",help="Native assets without SW registration")
    args = parser.parse_args()
    result = build(Path(args.output),args.base,android=args.android)
    print(json.dumps({"base":args.base,"files":result},sort_keys=True))
