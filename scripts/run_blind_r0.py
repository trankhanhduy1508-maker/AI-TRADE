#!/usr/bin/env python3
"""CWS BLIND R0 only. Two-phase data ingest and evaluation; NO broker calls.

INGEST does not compute returns; exact data/code/cost hashes and chronological
split are committed before EVALUATE can open historical holdout. Public-provider
data may be incomplete or non-executable; such evidence is never promoted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.backtest.blind_r0 import (PREREG_SHA, Bar, Costs, atr_series,
                                    block_bootstrap, simulate, validate_bars)

REPO = Path(__file__).resolve().parents[1]
AS_OF = 1790640000  # 2026-09-29T00:00:00Z, frozen before run
DATA_ROOT = REPO / ".cws-r0-data"
MANIFEST = REPO / "research" / "manifests" / "CWS_BLIND_R0_2026-09-29.json"
RESULTS = REPO / "research" / "results" / "CWS_BLIND_R0_2026-09-29.json"
COST_FILE = REPO / "backtests" / "cost_profiles" / "research_multi_asset_assumption_v1.json"

FX = {
 "EURUSD":"EURUSD=X","GBPUSD":"GBPUSD=X","USDJPY":"JPY=X",
 "AUDUSD":"AUDUSD=X","USDCAD":"CAD=X","USDCHF":"CHF=X",
 "NZDUSD":"NZDUSD=X","EURJPY":"EURJPY=X","GBPJPY":"GBPJPY=X",
 "EURGBP":"EURGBP=X","AUDJPY":"AUDJPY=X","EURCHF":"EURCHF=X",
 "NZDJPY":"NZDJPY=X",
}
# A quote using =X without the exact source convention is NOT accepted
# as a verified MT5/broker execution price.
NON_FX = {
 "XAUUSD":("GC=F","YAHOO_FRONT_MONTH_FUTURES_PROXY"),
 "XAGUSD":("SI=F","YAHOO_FRONT_MONTH_FUTURES_PROXY"),
 "WTI":("CL=F","YAHOO_FRONT_MONTH_FUTURES_PROXY"),
 "Brent":("BZ=F","YAHOO_FRONT_MONTH_FUTURES_PROXY"),
 "S&P 500":("^GSPC","YAHOO_NONTRADEABLE_INDEX"),
 "Nasdaq 100":("^NDX","YAHOO_NONTRADEABLE_INDEX"),
 "Dow Jones":("^DJI","YAHOO_NONTRADEABLE_INDEX"),
 "AAPL":("AAPL","YAHOO_STOCK_UNADJUSTED_DIVIDEND"),
 "MSFT":("MSFT","YAHOO_STOCK_UNADJUSTED_DIVIDEND"),
 "NVDA":("NVDA","YAHOO_STOCK_UNADJUSTED_DIVIDEND"),
 "AMZN":("AMZN","YAHOO_STOCK_UNADJUSTED_DIVIDEND"),
 "GOOGL":("GOOGL","YAHOO_STOCK_UNADJUSTED_DIVIDEND"),
 "META":("META","YAHOO_STOCK_UNADJUSTED_DIVIDEND"),
}
CRYPTO = {"BTCUSD":"btcusd","ETHUSD":"ethusd"}
UNIVERSE = {**{k:(v,"YAHOO_INDICATIVE_FX") for k,v in FX.items()},
            **{k:(v,"BITSTAMP_USD_SPOT") for k,v in CRYPTO.items()},
            **NON_FX}


def canonical(x) -> bytes:
    return json.dumps(x, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha(x: bytes) -> str:
    return hashlib.sha256(x).hexdigest()


def request_json(url: str) -> tuple[dict, bytes]:
    req = Request(url, headers={"User-Agent":"Mozilla/5.0 CWS-Blind-R0-research/1.0",
                               "Accept":"application/json"})
    with urlopen(req, timeout=20) as resp:
        payload = resp.read(15_000_000)
    if not payload or len(payload) >= 15_000_000:
        raise ValueError("empty/oversized provider response")
    return json.loads(payload), payload


def yahoo_daily(symbol: str) -> tuple[list[Bar], dict]:
    p = urlencode({"period1":1262304000,"period2":AS_OF,
                   "interval":"1d","events":"div,splits"})
    errors = []
    for host in ("query2.finance.yahoo.com","query1.finance.yahoo.com"):
        url = "https://"+host+"/v8/finance/chart/"+quote(symbol, safe="")+"?"+p
        try:
            payload, raw = request_json(url)
            if payload.get("chart",{}).get("error"):
                raise ValueError(str(payload["chart"]["error"]))
            result = payload["chart"]["result"][0]
            quotes = result["indicators"]["quote"][0]
            timestamps = result.get("timestamp") or []
            invalid = 0
            bars = []
            for i, stamp in enumerate(timestamps):
                if int(stamp)+86400 > AS_OF:  # never include partially formed D1
                    continue
                try:
                    b = Bar(int(stamp), *(float(quotes[k][i])
                                for k in ("open","high","low","close")),
                            float(quotes.get("volume",[])[i] or 0) if
                            quotes.get("volume") else 0.0)
                    validate_bars([b])
                    bars.append(b)
                except (TypeError,ValueError,KeyError,IndexError):
                    invalid += 1
            bars.sort(key=lambda b:b.ts)
            validate_bars(bars)
            meta = {"provider":"Yahoo Finance chart unofficial",
                    "provider_url":url, "original_tf":"1d",
                    "source_symbol":symbol, "original_timezone":
                    result.get("meta",{}).get("exchangeTimezoneName"),
                    "price_adjustment":"VERIFY_SPLITS_DIVIDENDS_SEPARATELY",
                    "corporate_action_events":len(result.get("events",{}).get("dividends",{}))
                        +len(result.get("events",{}).get("splits",{})),
                    "invalid_ohlc_rows":invalid, "raw_sha256":sha(raw)}
            return bars, meta
        except (HTTPError,URLError,OSError,ValueError,KeyError,IndexError) as exc:
            errors.append(type(exc).__name__+":"+str(exc)[:180])
            time.sleep(.5)
    raise RuntimeError("YAHOO_FETCH_FAILED "+repr(errors))


def bitstamp_candles(symbol: str, step: int, max_rows: int) -> tuple[list[Bar], dict]:
    end = AS_OF
    pages = []
    seen: dict[int, Bar] = {}
    urls = []
    for _ in range(8):
        params = urlencode({"step":step,"limit":1000,
                            "end":end,"exclude_current_candle":"true"})
        url = "https://www.bitstamp.net/api/v2/ohlc/"+symbol+"/?"+params
        body, raw = request_json(url)
        urls.append(url)
        pages.append(raw)
        rows = body.get("data",{}).get("ohlc")
        if not isinstance(rows,list) or not rows:
            raise ValueError("BITSTAMP_EMPTY_OHLC")
        first = min(int(r["timestamp"]) for r in rows)
        for r in rows:
            ts = int(r["timestamp"])
            if ts+step > AS_OF:
                continue
            bar = Bar(ts, *(float(r[k]) for k in ("open","high","low","close")),
                      float(r.get("volume",0)))
            validate_bars([bar])
            if ts in seen and seen[ts] != bar:
                raise ValueError("CONFLICTING_DUPLICATE_TIMESTAMP")
            seen[ts] = bar
        if len(seen)>=max_rows or first>=end:
            break
        end = first-1
        time.sleep(.15)
    bars = sorted(seen.values(),key=lambda x:x.ts)[-max_rows:]
    validate_bars(bars)
    # 24/7 spot must have every source H4/D1 period; no fabricated gaps.
    missing = sum(max(0,(b.ts-a.ts)//step-1)
                  for a,b in zip(bars,bars[1:]))
    meta = {"provider":"Bitstamp public OHLC",
            "provider_url":urls,"original_tf":"H4" if step==14400 else "D1",
            "source_symbol":symbol, "original_timezone":"UTC",
            "price_adjustment":"SPOT_NO_FUTURES_ROLL",
            "missing_source_periods":missing,"page_count":len(pages),
            "raw_sha256":sha(b"\n--PAGE--\n".join(pages))}
    return bars,meta


def cost_snapshot(symbol: str, source_symbol: str, tf: str, info: dict) -> dict:
    value = info.get("profiles",{}).get(source_symbol)
    if value is None and source_symbol in CRYPTO.values():
        # Old Yahoo BTC-USD assumptions are not Bitstamp execution fees.
        return {"provenance":"GROSS_ONLY","reason":"NO_BITSTAMP_COST_SNAPSHOT"}
    if value is None:
        return {"provenance":"GROSS_ONLY","reason":"NO_SOURCE_MATCHED_COST"}
    if tf=="H4" and float(value.get("swap_price_per_bar",0))>0:
        return {"provenance":"GROSS_ONLY",
                "reason":"COST_SWAP_TIME_UNIT_NOT_H4_COMPATIBLE"}
    return {"provenance":"ASSUMED_RESEARCH_COST_NOT_BROKER_VERIFIED",
            "profile_id":info["profile_id"], **value}


def ingest() -> None:
    if not (len(FX)==13 and len(CRYPTO)==2 and len(NON_FX)==13
            and len(UNIVERSE)==28):
        raise AssertionError("28-instrument prereg universe has changed")
    DATA_ROOT.mkdir(exist_ok=True)
    MANIFEST.parent.mkdir(parents=True,exist_ok=True)
    profile = json.loads(COST_FILE.read_text(encoding="utf-8"))
    code = (REPO/"src/backtest/blind_r0.py").read_bytes()
    runner = Path(__file__).read_bytes()
    manifest = {
        "prereg_commit_sha":PREREG_SHA,
        "state":"INGESTED_NOT_EVALUATED",
        "as_of_utc":datetime.fromtimestamp(AS_OF,timezone.utc).isoformat(),
        "engine_sha256":sha(code),"runner_sha256":sha(runner),
        "cost_file_sha256":sha(COST_FILE.read_bytes()),
        "split":"first 60% train, next 20% validation, final 20% historical OOS",
        "independence":"HISTORICAL_REUSED_UNLESS_AUDITED; FORWARD_NOT_YET_AVAILABLE",
        "dataset":{},
    }
    for symbol,(source,kind) in UNIVERSE.items():
        for tf in ("H4","D1"):
            key = symbol+"_"+tf
            rec = {"symbol":symbol,"timeframe":tf,"instrument_type":kind,
                   "source_symbol":source,"status":"DATA_UNAVAILABLE"}
            try:
                if kind.startswith("BITSTAMP"):
                    bars,meta=bitstamp_candles(source,14400 if tf=="H4" else 86400,
                                               3000 if tf=="H4" else 2400)
                elif tf=="D1":
                    bars,meta=yahoo_daily(source)
                else:
                    rec["status"]="DATA_UNAVAILABLE_NATIVE_H4"
                    rec["reason"]="Yahoo does not supply original 4-hour bars; do not relabel hourly proxy as broker-native H4"
                    manifest["dataset"][key]=rec
                    print("INGEST",key,rec["status"],flush=True)
                    continue
                rec.update(meta)
                rec["cost_snapshot"]=cost_snapshot(symbol,source,tf,profile)
                rec["bars"]=len(bars)
                rec["first_open_ts"]=bars[0].ts if bars else None
                rec["last_open_ts"]=bars[-1].ts if bars else None
                rec["min_bars_required"]=1000 if tf=="H4" else 500
                n=len(bars)
                rec["split_indices"]={"train_end":int(n*.6),
                                      "validation_end":int(n*.8),
                                      "total":n}
                raw_rows=[[b.ts,b.open,b.high,b.low,b.close,b.volume] for b in bars]
                raw=canonical(raw_rows)
                rec["normalized_sha256"]=sha(raw)
                if n<rec["min_bars_required"]:
                    rec["status"]="INSUFFICIENT_DATA"
                elif meta.get("missing_source_periods",0):
                    rec["status"]="DATA_INCOMPLETE"
                    rec["reason"]="unobserved intraperiod stops; no synthetic fill"
                else:
                    rec["status"]="READY_EXPLORATORY"
                file=DATA_ROOT/(key.replace("/","_").replace(" ","_")+".json")
                file.write_bytes(raw)
                rec["local_data_filename"]=file.name
            except Exception as exc:
                rec["status"]="DATA_UNAVAILABLE"
                rec["reason"]=type(exc).__name__+": "+str(exc)[:500]
            manifest["dataset"][key]=rec
            print("INGEST",key,rec["status"],rec.get("bars",0),flush=True)
    MANIFEST.write_bytes(canonical(manifest)+b"\n")
    print("MANIFEST",MANIFEST,"sha256",sha(MANIFEST.read_bytes()),flush=True)


def _simple(result: dict) -> dict:
    return {k:v for k,v in result.items() if k!="trades"}


def _per_year(trades: list[dict]) -> dict:
    years=defaultdict(list)
    for t in trades:
        year=datetime.fromtimestamp(t["exit_ts"],timezone.utc).year
        years[str(year)].append(t["pnl_r"])
    return {y:{"closed_trades":len(v),"net_r":sum(v),
               "negative_trade_count":sum(x<0 for x in v)}
            for y,v in years.items()}


def _regime(trades: list[dict],bars: list[Bar]) -> dict:
    values=atr_series(bars)
    lookup={b.ts:i for i,b in enumerate(bars)}
    reg=defaultdict(list)
    for t in trades:
        i=lookup.get(t["exit_ts"])
        if i is None or i<110 or values[i] is None:
            reg["UNCLASSIFIED"].append(t["pnl_r"])
            continue
        history=[values[j]/bars[j].close for j in range(i-100,i)
                 if values[j] is not None]
        if len(history)<90:
            reg["UNCLASSIFIED"].append(t["pnl_r"])
            continue
        current=values[i]/bars[i].close
        rank=sum(v<current for v in history)/len(history)
        label="HIGH_VOL" if rank>=.7 else ("LOW_VOL" if rank<=.3 else "MID_VOL")
        reg[label].append(t["pnl_r"])
    return {k:{"closed_trades":len(v),"net_r":sum(v)} for k,v in reg.items()}


def evaluate() -> None:
    manifest=json.loads(MANIFEST.read_bytes())
    if manifest.get("prereg_commit_sha")!=PREREG_SHA:
        raise RuntimeError("PREREG_SHA_MISMATCH")
    if (manifest.get("engine_sha256")!=sha((REPO/"src/backtest/blind_r0.py").read_bytes())
        or manifest.get("runner_sha256")!=sha(Path(__file__).read_bytes())
        or manifest.get("cost_file_sha256")!=sha(COST_FILE.read_bytes())):
        raise RuntimeError("CODE_OR_COST_CHANGED_AFTER_INGEST")
    if os.environ.get("R0_MANIFEST_COMMITTED")!="verified":
        raise RuntimeError("MANIFEST_MUST_BE_COMMITTED_TO_GITHUB_FIRST")
    report={"prereg_commit_sha":PREREG_SHA,
            "manifest_sha256":sha(MANIFEST.read_bytes()),
            "research_state":"UNPROVEN_HISTORICAL_REUSED_NO_FORWARD",
            "live_order_send":False,"demo_order_send":False,
            "dataset":{}}
    for key,entry in manifest["dataset"].items():
        out={"symbol":entry["symbol"],"timeframe":entry["timeframe"],
             "source":entry.get("provider"),
             "instrument_type":entry["instrument_type"],
             "status":entry["status"],"cost_provenance":
             entry.get("cost_snapshot",{}).get("provenance","UNAVAILABLE"),
             "forward_paper":"NO_NEW_INDEPENDENT_BARS"}
        if entry["status"]!="READY_EXPLORATORY":
            out["reason"]=entry.get("reason")
            report["dataset"][key]=out
            continue
        try:
            data=(DATA_ROOT/entry["local_data_filename"]).read_bytes()
            if sha(data)!=entry["normalized_sha256"]:
                raise ValueError("NORMALIZED_DATA_HASH_MISMATCH")
            bars=[Bar(int(a),*map(float,row)) for a,*row in json.loads(data)]
            validate_bars(bars)
            n=len(bars)
            split=entry["split_indices"]
            a,b=split["train_end"],split["validation_end"]
            if not (n==split["total"] and a==int(n*.6)
                    and b==int(n*.8) and 0<a<b<n):
                raise ValueError("CHRONOLOGICAL_SPLIT_CHANGED")
            c=entry["cost_snapshot"]
            costs=Costs(*(float(c.get(z,0.0)) for z in (
                "spread_price","commission_price","slippage_price",
                "swap_price_per_bar")),provenance=c["provenance"])
            # Cash indices/spot cannot be shorted without a documented borrow
            # or executable shorting instrument: conservative LONG-only.
            allow_short=entry["instrument_type"] in (
                "YAHOO_INDICATIVE_FX","YAHOO_FRONT_MONTH_FUTURES_PROXY")
            if entry["instrument_type"]=="YAHOO_FRONT_MONTH_FUTURES_PROXY":
                # Continuous Yahoo futures have unverified roll adjustment:
                # study remains exploratory and non-executable.
                out["roll_warning"]="FRONT_MONTH_ROLL_NOT_VERIFIED"
            if entry["instrument_type"].startswith("YAHOO_STOCK"):
                out["dividend_warning"]="DIVIDENDS_NOT_INCLUDED_IN_PRICE_PNL"
            def run(start,end,**extra):
                return simulate(bars,begin=start,end=end,costs=costs,
                                allow_short=allow_short,**extra)
            train=run(0,a)
            val=run(a,b)
            historical=run(b,n)  # opened only AFTER committed manifest gate
            prefix=run(0,b)
            out["train"]=_simple(train)
            out["validation"]=_simple(val)
            out["historical_oos"]=_simple(historical)
            out["historical_oos_independence"]="HISTORICAL_REUSED_NOT_INDEPENDENT"
            out["baseline"]={
                "flat_price_return":0.0,
                "passive_price_return":bars[-1].close/bars[b].open-1,
                "passive_is_tradeable":False
            }
            step=max(1,int(b*.1))
            folds=[]
            for fold in range(4):
                start=int(b*.4)+fold*step
                end=min(start+step,b)
                if start>=end:break
                folds.append({"train_end":start,"test_end":end,
                              "metrics":_simple(run(start,end))})
            out["walk_forward_pre_holdout_only"]=folds
            out["stress_test"]={
                "cost_2x":_simple(run(b,n,cost_multiplier=2)),
                "cost_3x":_simple(run(b,n,cost_multiplier=3)),
            }
            varied={"channel50":dict(channel=50),"channel60":dict(channel=60),
                    "trail18":dict(trail=18),"trail22":dict(trail=22),
                    "atr2_25":dict(atr_multiplier=2.25),
                    "atr2_75":dict(atr_multiplier=2.75)}
            out["parameter_sensitivity_train_validation_only"]={
                label:_simple(run(0,b,**args)) for label,args in varied.items()
            }
            out["monte_carlo_train_validation_only"]=block_bootstrap(
                prefix["trades"])
            wins=[t["pnl_r"] for t in prefix["trades"] if t["pnl_r"]>0]
            out["largest_winner_dependence_train_validation_only"]={
                "total_net_r":prefix["realized_net_r"],
                "after_largest_winner_removed_r":
                    prefix["realized_net_r"]-max(wins) if wins else None
            }
            out["by_exit_year_historical_oos"]=_per_year(historical["trades"])
            out["by_volatility_regime_historical_oos"]=_regime(
                historical["trades"],bars)
            out["failure_cases_historical_oos"]=sorted(
                historical["trades"],key=lambda t:t["pnl_r"])[:5]
            # Predeclared 1-ATR adverse gap SHOCK on EACH stop fill.
            # Synthetic STRESS only; original market candles remain unaltered.
            atrs=atr_series(bars)
            indexes={bar.ts:i for i,bar in enumerate(bars)}
            adverse_r=0.0
            for trade in historical["trades"]:
                i=indexes[trade["exit_ts"]]
                atr=atrs[i]
                stop_risk=abs(trade["entry_price"]-trade["initial_stop"])
                if atr is not None and stop_risk>0:
                    adverse_r+=atr/stop_risk
            out["stress_test"]["synthetic_adverse_1atr_per_exit"]={
                "provenance":"SYNTHETIC_SHOCK_NOT_MARKET_DATA",
                "total_marked_r_after_shock":
                    historical["ending_marked_equity_r"]-adverse_r,
                "additional_loss_r":adverse_r,
                "assumption":"one adverse ATR20 exit shock per closed position"
            }
            out["historical_oos_closed_trade_count_sufficient"] = (
                historical["trade_count"] >=30
            )
            out["status"]="EXPLORATORY_HISTORICAL_REUSED_UNPROVEN"
            if costs.provenance!="VERIFIED_BROKER_EXECUTION":
                out["after_verified_costs"]="UNAVAILABLE"
        except Exception as exc:
            out["status"]="EVALUATION_FAILED"
            out["reason"]=type(exc).__name__+": "+str(exc)[:500]
        report["dataset"][key]=out
        print("EVALUATE",key,out["status"],flush=True)
    RESULTS.parent.mkdir(parents=True,exist_ok=True)
    RESULTS.write_bytes(canonical(report)+b"\n")
    print("RESULTS",RESULTS,"sha256",sha(RESULTS.read_bytes()),flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--stage",choices=("ingest","evaluate"),required=True)
    args=parser.parse_args()
    if args.stage=="ingest":ingest()
    else:evaluate()
