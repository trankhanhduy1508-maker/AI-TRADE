# TEMPORARY BUILD-6230 FORM VALUE INSPECTION MODE.\n# No account creation commands are sent.\nimport json
import re
import urllib.parse
import urllib.request

ROOT="https://web.metatrader.app/terminal"
UA="AI-TRADE-build6230-form-inspector/1.0"
MARKERS=[
    "mt_group","mt_agreements","mt_deposit","mt_leverage",
    "default_deposit","account_type","leverages",
    "demo.open","demo.controller","btnOpenDemo","#web_group_74"
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

def main():
    final,raw=fetch(ROOT)
    html=raw.decode("utf-8","replace")
    queue=list(refs(final,html))
    seen=set()
    hits=[]
    # Include HTML because group config lives there.
    sources=[(final,html)]
    idx=0
    while idx<len(queue) and len(seen)<180:
        url=queue[idx];idx+=1
        if url in seen: continue
        seen.add(url)
        try:
            fu,rr=fetch(url);tt=rr.decode("utf-8","replace")
            sources.append((fu,tt))
            for x in refs(fu,tt):
                if x not in seen and len(queue)<500: queue.append(x)
        except Exception:
            pass

    for source,text in sources:
        compact=re.sub(r"\s+"," ",text)
        for marker in MARKERS:
            start=0
            for _ in range(15):
                pos=compact.find(marker,start)
                if pos<0: break
                hits.append({
                    "source":source,
                    "marker":marker,
                    "snippet":compact[max(0,pos-1700):min(len(compact),pos+3500)]
                })
                start=pos+len(marker)

    # Score likely business-logic snippets above translations/config repeats.
    def score(x):
        s=x["snippet"]
        return (
            5*("mt_group" in s)
            +5*("mt_agreements" in s)
            +4*("mt_deposit" in s)
            +4*("mt_leverage" in s)
            +3*("demo.open" in s)
            +2*("default_deposit" in s)
            -2*("translation" in x["source"].lower())
        )
    hits.sort(key=score,reverse=True)

    unique=[];seen_key=set()
    for h in hits:
        k=(h["source"],h["snippet"])
        if k not in seen_key:
            seen_key.add(k);unique.append(h)

    print(json.dumps({
        "status":"FORM_VALUE_INSPECTION_COMPLETE",
        "sources_scanned":len(sources),
        "hit_count":len(unique),
        "broker_orders":False,
        "demo_created":False
    },separators=(",",":")))
    for h in unique[:70]:
        print("FORMVALUE",json.dumps(h,separators=(",",":"),ensure_ascii=False))

if __name__=="__main__":
    main()
