"""Embed the existing allowlisted shell in a dependency-free Sites Worker."""
from pathlib import Path
import base64, json, mimetypes, shutil, re
from hashlib import sha256
from build_cws_trade_static import build, ROOT

def main():
    output=ROOT / "dist"
    if output.exists(): shutil.rmtree(output)
    build(output)
    # Worker web app is core-only; legacy shell remains available to Android.
    core=(ROOT / "google-sites/cws-ai-trade/core.html").read_text()
    (output / "index.html").write_text(core)
    manifest=output / "manifest.webmanifest"
    data=json.loads(manifest.read_text());data.pop("shortcuts",None)
    manifest.write_text(json.dumps(data,ensure_ascii=False))
    sw=output / "sw.js"
    revision=sha256((core+sw.read_text()).encode()).hexdigest()[:12]
    sw.write_text(re.sub(r"cws-ai-trade-static-[a-f0-9]{12}","cws-ai-trade-static-"+revision,sw.read_text()))
    assets={}
    for p in output.iterdir():
        if p.is_file() and not p.name.startswith("."):
            mime=mimetypes.guess_type(p.name)[0] or "application/octet-stream"
            if p.suffix==".js": mime="application/javascript"
            if p.suffix in (".html",".js",".css"): mime+="; charset=utf-8"
            assets["/"+p.name]={"type":mime,"body":base64.b64encode(p.read_bytes()).decode()}
    server=output / "server"
    server.mkdir()
    runtime=(ROOT / "scripts/site-runtime/paper-worker.mjs").read_text()
    (server / "index.js").write_text(runtime+"\nconst assets="+json.dumps(assets)+";\nexport default {fetch(request,env){return serve(request,env,assets)}};\n")
    print(json.dumps({"worker":"dist/server/index.js","assets":len(assets)}))

if __name__=="__main__": main()
