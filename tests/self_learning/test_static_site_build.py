"""Offline static PWA build regression, using real committed UI assets."""
import json
from pathlib import Path
import struct
import zlib

import pytest

from scripts.build_cws_trade_static import ALLOWLIST, build


@pytest.mark.parametrize("base", ["/","/AI-TRADE/"])
def test_static_page_renderable_and_pwa_scoped(base,tmp_path):
    output=tmp_path/"public"
    manifest=build(output,base)
    assert len(manifest)==len(ALLOWLIST)+2
    assert set(p.name for p in output.iterdir())==set(ALLOWLIST)|{
        "icon-192.png","icon-512.png",".nojekyll"}
    html=(output/"index.html").read_text()
    assert "href=\"./styles.css\"" in html
    assert "src=\"./tradingview.js\"" in html
    assert "src=\"./app.js\"" in html
    assert html.index("tradingview.js")<html.index("app.js")
    assert f'href="{base}manifest.webmanifest"' in html
    assert "hostedChart" in html
    assert "Google Sites chưa xuất bản" in html
    app=(output/"app.js").read_text()
    assert "preview-candles" not in app
    assert "embed-widget-advanced-chart.js" in (
        output/"tradingview.js").read_text()
    worker=(output/"sw.js").read_text()
    assert f'const ROOT="{base}";' in worker
    assert "cws-ai-trade-static-v6" in worker
    assert 'ROOT+"styles.css"' in worker
    assert 'ROOT+"tradingview.js"' in worker
    assert "u.pathname.slice(ROOT.length)" in worker
    assert "?asset=" not in worker
    pwa=(output/"pwa.js").read_text()
    assert f'const BASE="{base}";' in pwa
    assert 'BASE+"sw.js"' in pwa
    data=json.loads((output/"manifest.webmanifest").read_text())
    assert data["id"]==data["scope"]==data["start_url"]==base
    assert all(i["src"].startswith(base+"icon-") for i in data["icons"])
    assert all(i["src"].startswith(base+"icon-") for s in data["shortcuts"]
               for i in s["icons"])
    assert all(s["url"].startswith(base+"?view=") for s in data["shortcuts"])


@pytest.mark.parametrize("size", [192,512])
def test_png_assets_are_real_image_data(size,tmp_path):
    build(tmp_path)
    data=(tmp_path/f"icon-{size}.png").read_bytes()
    assert data[:8]==b"\x89PNG\r\n\x1a\n"
    assert struct.unpack(">II",data[16:24])==(size,size)
    assert data[24:26]==bytes((8,6))  # RGBA 8-bit
    pos=8
    compressed=b""
    while pos<len(data):
        n=struct.unpack(">I",data[pos:pos+4])[0]
        kind=data[pos+4:pos+8]
        payload=data[pos+8:pos+8+n]
        crc=struct.unpack(">I",data[pos+8+n:pos+12+n])[0]
        assert zlib.crc32(kind+payload)&0xffffffff==crc
        if kind==b"IDAT":compressed+=payload
        pos+=12+n
    assert len(zlib.decompress(compressed))==size*(1+size*4)


@pytest.mark.parametrize("base", ["AI-TRADE","//evil/","/../../","/AI TRADE/"])
def test_unsafe_path_rejected_without_output(base,tmp_path):
    output=tmp_path/"public"
    with pytest.raises(ValueError,match="base"):
        build(output,base)
    assert not output.exists()
