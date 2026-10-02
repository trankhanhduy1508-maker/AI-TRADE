import json
import re
import urllib.parse
import urllib.request

PAGES = [
    "https://web.metatrader.app/",
    "https://web.metatrader.app/terminal",
]

PATTERNS = [
    r"sendCommand\s*\(\s*27\b",
    r"sendCommand\s*\(\s*30\b",
    r"sendCommand\s*\(\s*40\b",
    r"email[_A-Za-z]*confirm",
    r"phone[_A-Za-z]*confirm",
    r"agreements",
    r"open[_A-Za-z]*demo",
    r"demo[_A-Za-z]*account",
    r"verification",
    r"first[_A-Za-z]*name",
    r"second[_A-Za-z]*name",
]

UA = "AI-TRADE-build6230-public-bundle-inspector/1.0"


def fetch(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "*/*",
        },
    )
    with urllib.request.urlopen(req, timeout=25) as res:
        return res.geturl(), res.read()


def js_refs(base_url, text):
    refs = set()
    for attr in ("src", "href"):
        for m in re.finditer(
            rf'{attr}\s*=\s*["\']([^"\']+\.js(?:\?[^"\']*)?)["\']',
            text,
            re.I,
        ):
            refs.add(urllib.parse.urljoin(base_url, m.group(1)))
    # Vite/module chunks referenced inside JS.
    for m in re.finditer(r'["\']([^"\']+\.js(?:\?[^"\']*)?)["\']', text):
        value = m.group(1)
        if "/" in value or value.startswith("."):
            refs.add(urllib.parse.urljoin(base_url, value))
    return refs


def compact(s):
    return re.sub(r"\s+", " ", s)


def snippets(text, source):
    out = []
    normalized = compact(text)
    for pattern in PATTERNS:
        rx = re.compile(pattern, re.I)
        for m in list(rx.finditer(normalized))[:12]:
            lo = max(0, m.start() - 650)
            hi = min(len(normalized), m.end() + 1100)
            out.append(
                {
                    "source": source,
                    "pattern": pattern,
                    "snippet": normalized[lo:hi],
                }
            )
    return out


def main():
    queue = []
    seen = set()
    matches = []
    page_meta = []

    for page in PAGES:
        try:
            final, raw = fetch(page)
            text = raw.decode("utf-8", "replace")
            page_meta.append(
                {"requested": page, "final": final, "bytes": len(raw)}
            )
            matches.extend(snippets(text, final))
            queue.extend(sorted(js_refs(final, text)))
        except Exception as exc:
            page_meta.append(
                {
                    "requested": page,
                    "error": type(exc).__name__,
                    "detail": str(exc)[:200],
                }
            )

    # Crawl public JS chunks only, bounded to prevent runaway.
    idx = 0
    bundle_meta = []
    while idx < len(queue) and len(seen) < 160:
        url = queue[idx]
        idx += 1
        if url in seen:
            continue
        seen.add(url)
        try:
            final, raw = fetch(url)
            text = raw.decode("utf-8", "replace")
            bundle_meta.append({"url": final, "bytes": len(raw)})
            found = snippets(text, final)
            if found:
                matches.extend(found)
            # One level of imported chunks is useful for split frontend bundles.
            for ref in js_refs(final, text):
                if ref not in seen and len(queue) < 400:
                    queue.append(ref)
        except Exception as exc:
            bundle_meta.append(
                {
                    "url": url,
                    "error": type(exc).__name__,
                    "detail": str(exc)[:160],
                }
            )

    # Deduplicate snippets by source+pattern+content.
    unique = []
    keys = set()
    for item in matches:
        key = (item["source"], item["pattern"], item["snippet"])
        if key not in keys:
            keys.add(key)
            unique.append(item)

    result = {
        "status": "BUNDLE_INSPECTION_COMPLETE",
        "pages": page_meta,
        "bundles_scanned": len(seen),
        "bundle_meta": bundle_meta[:200],
        "match_count": len(unique),
        "matches": unique[:120],
        "broker_orders": False,
        "demo_created": False,
        "live_money_locked": True,
    }

    with open("mt5_bundle_inspection.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(
        json.dumps(
            {
                "status": result["status"],
                "pages": page_meta,
                "bundles_scanned": len(seen),
                "match_count": len(unique),
                "matched_sources": sorted({x["source"] for x in unique}),
                "broker_orders": False,
                "demo_created": False,
            },
            separators=(",", ":"),
            ensure_ascii=False,
        )
    )

    for item in unique[:40]:
        print("MATCH", json.dumps(item, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
