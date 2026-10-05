import json
import re
import urllib.parse
import urllib.request

ROOT="https://web.metatrader.app/terminal"
UA="AI-TRADE-build6230-onboarding-inspector/1.1"

CALL_PATTERNS=[
    r"\.\w+\(\s*27\s*,",
    r"\.\w+\(\s*30\s*,",
    r"\.\w+\(\s*40\s*,",
    r"\(\s*27\s*,",
    r"\(\s*30\s*,",
    r"\(\s*40\s*,",
]
SEMANTIC=[
    "openDemo","btnOpenDemo","accountOpening","verificationCodes",
    "emailConfirm","phoneConfirm","firstName","secondName",
    "#web_group_74","Forex Hedged USD"
]

def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"*/*"})
    with urllib.request.urlopen(req,timeout=25) as r:
        return r.geturl(),r.read()

def refs(base,text):
    out=set()
    for m in re.finditer(r'["\']([^"\']+\.js(?:\?[^"\']*)?)["\']',text):
        v=m.group(1)
        if "/" in v or v.startswith(".") or v.endswith(".js"):
            out.add(urllib.parse.urljoin(base,v))
    return out

def compact(s):
    return re.sub(r"\s+"," ",s)

def scan_text(source,text,kind="js"):
    t=compact(text)
    hits=[]
    for pat in CALL_PATTERNS:
        for m in list(re.finditer(pat,t))[:80]:
            hits.append({
                "source":source,"kind":kind,"type":"numeric_call","pattern":pat,
                "snippet":t[max(0,m.start()-1400):min(len(t),m.end()+2200)]
            })
    for marker in SEMANTIC:
        start=0
        count=0
        while count<12:
            i=t.find(marker,start)
            if i<0: break
            hits.append({
                "source":source,"kind":kind,"type":"semantic","marker":marker,
                "snippet":t[max(0,i-900):min(len(t),i+2200)]
            })
            start=i+len(marker); count+=1
    return hits

def main():
    final,raw=fetch(ROOT)
    html=raw.decode("utf-8","replace")
    queue=sorted(refs(final,html))
    seen=set()
    all_hits=scan_text(final,html,"html")
    maps_checked=0
    source_map_hits=[]

    idx=0
    while idx<len(queue) and len(seen)<180:
        url=queue[idx]; idx+=1
        if url in seen: continue
        seen.add(url)
        try:
            final_js,raw_js=fetch(url)
            text=raw_js.decode("utf-8","replace")
            all_hits.extend(scan_text(final_js,text,"js"))
            for x in refs(final_js,text):
                if x not in seen and len(queue)<500: queue.append(x)

            map_urls=[]
            for m in re.finditer(r"sourceMappingURL=([^\s*]+)",text):
                map_urls.append(urllib.parse.urljoin(final_js,m.group(1).strip()))
            map_urls.append(final_js.split("?")[0]+".map")
            for map_url in dict.fromkeys(map_urls):
                if maps_checked>=120: break
                maps_checked+=1
                try:
                    _,map_raw=fetch(map_url)
                    data=json.loads(map_raw.decode("utf-8","replace"))
                    sources=data.get("sources") or []
                    contents=data.get("sourcesContent") or []
                    for i,src_content in enumerate(contents):
                        if not isinstance(src_content,str): continue
                        src_name=sources[i] if i<len(sources) else f"source-{i}"
                        found=scan_text(f"{map_url}::{src_name}",src_content,"sourcemap")
                        if found: source_map_hits.extend(found)
                except Exception:
                    pass
        except Exception:
            pass

    # Prioritize numeric calls and sourcemap hits, then semantic JS hits.
    combined=source_map_hits+[x for x in all_hits if x["type"]=="numeric_call"]+[x for x in all_hits if x["type"]=="semantic"]
    unique=[]; keys=set()
    for x in combined:
        k=(x["source"],x.get("pattern"),x.get("marker"),x["snippet"])
        if k not in keys:
            keys.add(k);unique.append(x)

    result={
        "status":"ONBOARDING_CALL_INSPECTION_COMPLETE",
        "bundles_scanned":len(seen),
        "maps_checked":maps_checked,
        "sourcemap_hit_count":len(source_map_hits),
        "numeric_hit_count":sum(1 for x in unique if x["type"]=="numeric_call"),
        "total_hit_count":len(unique),
        "hits":unique[:500],
        "broker_orders":False,"demo_created":False
    }
    with open("mt5_onboarding_calls.json","w",encoding="utf-8") as f:
        json.dump(result,f,ensure_ascii=False,indent=2)

    print(json.dumps({k:v for k,v in result.items() if k!="hits"},separators=(",",":")))
    for x in unique[:100]:
        if x["type"]=="numeric_call" or x["kind"]=="sourcemap":
            print("ONBOARDING",json.dumps(x,ensure_ascii=False,separators=(",",":")))

if __name__=="__main__":
    main()
