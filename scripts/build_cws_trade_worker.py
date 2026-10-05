"""Embed the existing allowlisted shell in a dependency-free Sites Worker."""
from pathlib import Path
import base64, json, mimetypes, shutil
from build_cws_trade_static import build, ROOT

def main():
    output=ROOT / "dist"
    if output.exists(): shutil.rmtree(output)
    build(output)
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
