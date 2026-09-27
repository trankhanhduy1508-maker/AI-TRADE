# TEMPORARY BUILD-6230 SERIALIZER INSPECTION MODE.
# No account creation commands are sent.
import json
import re
import urllib.request

URL="https://web.metatrader.app/terminal/CKnWTLdC.js"
req=urllib.request.Request(URL,headers={"User-Agent":"AI-TRADE-build6230-serializer-inspector/1.0"})
with urllib.request.urlopen(req,timeout=25) as r:
    text=r.read().decode("utf-8","replace")

patterns=[
    r"function\s+xi\s*\(",
    r"\bxi\s*=\s*(?:function|\(?\w+\)?\s*=>)",
    r"function\s+Fi\s*\(",
    r"\bFi\s*=\s*(?:function|\(?\w+\)?\s*=>)",
    r"\bLs\s*=",
    r"mt_firstName",
]

out=[]
for pat in patterns:
    for m in list(re.finditer(pat,text))[:12]:
        lo=max(0,m.start()-2200)
        hi=min(len(text),m.end()+5200)
        out.append({"pattern":pat,"snippet":text[lo:hi]})

print(json.dumps({
    "status":"SERIALIZER_INSPECTION",
    "source":URL,
    "bytes":len(text),
    "hits":len(out),
    "broker_orders":False,
    "demo_created":False
},separators=(",",":")))
for item in out:
    print("SERIALIZER",json.dumps(item,separators=(",",":"),ensure_ascii=False))
