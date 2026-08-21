"""Fetch Yahoo chart OHLCV into a local research CSV.

This is a reproducibility helper for research only. The endpoint is not a
broker execution feed, and downloaded data should not be treated as canonical
or committed as performance evidence without a separate provenance review.
"""

import argparse
import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


def epoch(value: str) -> int:
    return int(datetime.fromisoformat(value).replace(tzinfo=timezone.utc).timestamp())


def fetch(symbol: str, interval: str, start: int, end: int) -> list[dict[str, object]]:
    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        f"{quote(symbol, safe='')}?period1={start}&period2={end}&interval={interval}"
    )
    request = Request(url, headers={"User-Agent": "AI-TRADE-research/0.1"})
    with urlopen(request, timeout=30) as response:
        payload = json.load(response)
    chart = payload.get("chart", {})
    if chart.get("error"):
        raise RuntimeError(f"Yahoo chart error for {symbol}/{interval}: {chart['error']}")
    result = (chart.get("result") or [None])[0]
    if not result:
        raise RuntimeError(f"Yahoo returned no result for {symbol}/{interval}")
    timestamps = result.get("timestamp") or []
    quote_data = (result.get("indicators", {}).get("quote") or [{}])[0]
    rows = []
    for index, timestamp in enumerate(timestamps):
        values = {name: (quote_data.get(name) or [None])[index] for name in ("open", "high", "low", "close", "volume")}
        if any(values[name] is None for name in ("open", "high", "low", "close")):
            continue
        rows.append(
            {
                "timestamp": datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat(),
                **values,
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--interval", required=True, choices=("1d", "1h"))
    parser.add_argument("--start", required=True, help="UTC date/time, ISO-8601")
    parser.add_argument("--end", required=True, help="UTC date/time, ISO-8601")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    rows = fetch(args.symbol, args.interval, epoch(args.start), epoch(args.end))
    if not rows:
        raise SystemExit("No complete OHLC rows returned")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("timestamp", "open", "high", "low", "close", "volume"))
        writer.writeheader()
        writer.writerows(rows)
    print(f"{args.symbol} {args.interval}: {len(rows)} rows -> {args.output}")


if __name__ == "__main__":
    main()
