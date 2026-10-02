"""Frozen TF014 cross-market H4-proxy backtest; research only, no broker calls."""
import argparse, hashlib, json, math, os, sys, time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.execution.demo_candidate import DemoTrendCandidate
from src.rule_engine.types import Bar

GROUPS = {
 "fx_majors":{"EURUSD":"EURUSD=X","GBPUSD":"GBPUSD=X","USDJPY":"USDJPY=X",
              "AUDUSD":"AUDUSD=X","USDCAD":"CAD=X","USDCHF":"CHF=X",
              "NZDUSD":"NZDUSD=X"},
 "fx_crosses":{"EURJPY":"EURJPY=X","GBPJPY":"GBPJPY=X","EURGBP":"EURGBP=X",
               "AUDJPY":"AUDJPY=X","EURCHF":"EURCHF=X","NZDJPY":"NZDJPY=X"},
 "crypto_commodities":{"BTCUSD":"BTC-USD","ETHUSD":"ETH-USD",
                       "XAUUSD_FUTURES_PROXY":"GC=F","USOIL_FUTURES_PROXY":"CL=F"},
 "us_indices_stocks":{"US500_INDEX":"^GSPC","NAS100_INDEX":"^NDX",
                      "US30_INDEX":"^DJI","AAPL":"AAPL","MSFT":"MSFT",
                      "NVDA":"NVDA","AMZN":"AMZN","GOOGL":"GOOGL","META":"META"},
}
# Spread, commission, one-side slippage and daily swap in instrument price units.
# RESEARCH_PROXY is NOT verified broker execution cost. Others are GROSS_ONLY.
COSTS = {
 "EURUSD":(.00020,.000020,.000050,.000010),
 "GBPUSD":(.00020,.000020,.000050,.000010),
 "USDJPY":(.020,.002,.005,.001),
 "AUDUSD":(.00025,.000025,.00006,.000012),
 "BTCUSD":(50.,20.,25.,0.),
 "XAUUSD_FUTURES_PROXY":(.5,.1,.25,.05),
 "USOIL_FUTURES_PROXY":(.05,.02,.03,.02),
}
CANDIDATE=DemoTrendCandidate()
AS_OF=datetime.now(timezone.utc)

def yahoo_hourly(ticker):
    problems=[]
    for host,days in (("query2.finance.yahoo.com",700),
                      ("query1.finance.yahoo.com",600)):
        params=urlencode({"period1":int((AS_OF-timedelta(days=days)).timestamp()),
                          "period2":int(AS_OF.timestamp()),"interval":"1h",
                          "events":"history"})
        url="https://"+host+"/v8/finance/chart/"+quote(ticker,safe="")+"?"+params
        try:
            req=Request(url,headers={"User-Agent":"Mozilla/5.0 CWS-research/1.0",
                                     "Accept":"application/json"})
            with urlopen(req,timeout=35) as resp:
                raw=json.load(resp)["chart"]
            if raw.get("error") or not raw.get("result"):
                raise RuntimeError("EMPTY_OR_ERROR_CHART")
            result=raw["result"][0]
            zone=result.get("meta",{}).get("exchangeTimezoneName") or "UTC"
            try: ZoneInfo(zone)
            except (KeyError,ValueError): zone="UTC"
            quotes=result.get("indicators",{}).get("quote",[{}])[0]
            rows=[]; seen=set()
            cutoff=int((AS_OF-timedelta(hours=1)).timestamp())
            for i,ts in enumerate(result.get("timestamp") or []):
                if ts in seen: raise RuntimeError("DUPLICATE_TIMESTAMP")
                seen.add(ts)
                if ts >= cutoff: continue
                try:
                    o,h,l,c=(float(quotes[k][i]) for k in
                             ("open","high","low","close"))
                except (IndexError,TypeError,ValueError,KeyError): continue
                if (not all(math.isfinite(x) and x>0 for x in (o,h,l,c))
                    or h<max(o,c) or l>min(o,c)): continue
                rows.append((int(ts),o,h,l,c))
            return sorted(rows),zone
        except (HTTPError,URLError,OSError,ValueError,KeyError,RuntimeError) as e:
            problems.append(type(e).__name__+
                            (":"+str(e.code) if isinstance(e,HTTPError) else ""))
            time.sleep(.6)
    raise RuntimeError("DATA_UNAVAILABLE:"+",".join(problems))

def aggregate_h4(hourly,zone):
    days=defaultdict(list);tz=ZoneInfo(zone)
    for r in hourly:
        d=datetime.fromtimestamp(r[0],timezone.utc).astimezone(tz).date()
        days[str(d)].append(r)
    out=[]
    for d in sorted(days):
        rows=days[d];j=0
        while j+4<=len(rows):
            four=rows[j:j+4]
            if any(four[k][0]-four[k-1][0]!=3600 for k in (1,2,3)):
                j+=1;continue
            stamp=datetime.fromtimestamp(four[-1][0]+3600,timezone.utc)
            out.append(Bar(stamp.isoformat(),four[0][1],
                           max(v[2] for v in four),min(v[3] for v in four),
                           four[-1][4],4.,True))
            j+=4
    if any(a.timestamp>=b.timestamp for a,b in zip(out,out[1:])):
        raise RuntimeError("H4_SEQUENCE_INVALID")
    return out

def stats(trades):
    vals=[t[0] for t in trades]
    wealth=peak=dd=gain=loss=0.
    for v in vals:
        wealth+=v;peak=max(peak,wealth);dd=max(dd,peak-wealth)
        if v>0: gain+=v
        if v<0: loss-=v
    return {"trades":len(trades),"net_r":round(sum(vals),4),
            "gross_r":round(sum(t[1] for t in trades),4),
            "expectancy_r":round(sum(vals)/len(vals),4) if vals else None,
            "profit_factor":round(gain/loss,4) if loss else None,
            "max_drawdown_r":round(dd,4),
            "win_rate":round(sum(v>0 for v in vals)/len(vals),4)
                         if vals else None,
            "gap_exits":sum(t[2] for t in trades)}

def simulate(bars,start,end,cost):
    spread,commission,slippage,swap_day=cost
    position=None;pending=None;trades=[]
    for i in range(max(61,start),end):
        b=bars[i];exited=False
        if pending and position is None:
            direction,stop=pending;pending=None
            side=1 if direction=="UP" else -1
            entry=b.open+side*slippage
            risk=side*(entry-stop)
            if math.isfinite(risk) and risk>spread+2*slippage:
                position={"side":side,"entry":entry,"raw":b.open,
                          "stop":stop,"risk":risk,"entry_i":i}
        if position:
            p=position;side=p["side"]
            if i>p["entry_i"]:
                prior=bars[i-20:i]
                if len(prior)==20:
                    trail=(min(x.low for x in prior) if side==1
                           else max(x.high for x in prior))
                    p["stop"]=(max(p["stop"],trail) if side==1
                               else min(p["stop"],trail))
            stop=p["stop"]
            if (b.low<=stop if side==1 else b.high>=stop):
                gap=(b.open<stop if side==1 else b.open>stop)
                raw_exit=b.open if gap else stop
                exit_price=raw_exit-side*slippage
                held=i-p["entry_i"]+1
                pnl=(side*(exit_price-p["entry"])-spread-commission-
                     swap_day*held/6)
                gross=side*(raw_exit-p["raw"])
                trades.append((pnl/p["risk"],gross/p["risk"],gap))
                position=None;exited=True
        if position is None and not exited and i<end-1:
            signal=CANDIDATE(bars[:i+1])
            if signal is not None:
                pending=(signal.direction,signal.stop_price)
    result=stats(trades);result["open_at_end"]=position is not None
    return result

def analyze(symbol,ticker,hourly,zone):
    bars=aggregate_h4(hourly,zone)
    if len(bars)<150:
        raise RuntimeError("INSUFFICIENT_COMPLETE_H4:"+str(len(bars)))
    cost=COSTS.get(symbol,(0.,0.,0.,0.))
    split=int(.70*len(bars))
    oos=simulate(bars,split,len(bars),cost)
    gross=simulate(bars,split,len(bars),(0.,0.,0.,0.))
    double=simulate(bars,split,len(bars),tuple(v*2 for v in cost))
    start=max(61,int(.50*len(bars)))
    size=max(1,int(.10*len(bars)))
    wf=[simulate(bars,i,min(i+size,len(bars)),cost)
        for i in range(start,len(bars),size)]
    digest=hashlib.sha256(json.dumps(
        [(b.timestamp,b.open,b.high,b.low,b.close) for b in bars],
        separators=(",",":")).encode()).hexdigest()
    return {"symbol":symbol,"ticker":ticker,"timeframe":"SESSION_H4_PROXY",
            "source":"Yahoo public hourly (NOT MT5)", "timezone":zone,
            "cost_mode":"RESEARCH_PROXY" if symbol in COSTS else "GROSS_ONLY",
            "h4_bars":len(bars),"hourly_bars":len(hourly),
            "first":bars[0].timestamp,"last":bars[-1].timestamp,
            "oos_split":bars[split].timestamp,
            "h4_ohlc_sha256":digest,"oos":oos,"oos_gross":gross,
            "oos_cost_2x":double if symbol in COSTS else None,
            "wf_net_r":round(sum(x["net_r"] for x in wf),4),
            "wf_positive_folds":sum(x["trades"]>0 and x["net_r"]>0 for x in wf),
            "wf_folds":len(wf),"wf_trades":sum(x["trades"] for x in wf),
            "status":"INSUFFICIENT_OOS_TRADES" if oos["trades"]<5
                     else "RESEARCH_ONLY",
            "strategy":"TF014 20/10/20, min60, NEXT_OPEN, GAP_AWARE"}

def selftest():
    start=datetime(2024,1,1,tzinfo=timezone.utc)
    bars=[]
    for i in range(230):
        p=1.1+.0002*min(i,110)-.0003*max(i-110,0)
        bars.append(Bar((start+timedelta(hours=4*i)).isoformat(),
                        p,p+.0003,p-.0003,p+.00002,4.,True))
    a=simulate(bars,70,len(bars),(0.,0.,0.,0.))
    b=simulate(bars,70,len(bars),(.00004,.00001,.00001,0.))
    assert a["trades"]>0 and b["net_r"]<a["net_r"]
    rows=[(int(start.timestamp())+3600*i,1.,1.1,.9,1.05)
          for i in range(10)]
    assert len(aggregate_h4(rows,"UTC"))==2
    assert not aggregate_h4(rows[:3],"UTC")
    rows[3]=(rows[2][0]+7200,1.,1.1,.9,1.05)
    assert not aggregate_h4(rows[:4],"UTC")
    print("PASS: no future candles, complete H4 and adverse costs")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--group",choices=sorted(GROUPS))
    p.add_argument("--output",type=Path)
    p.add_argument("--self-test",action="store_true")
    a=p.parse_args()
    if a.self_test: selftest();return 0
    if not a.group or not a.output: p.error("--group and --output required")
    results=[];errors={}
    for symbol,ticker in GROUPS[a.group].items():
        try:
            hourly,zone=yahoo_hourly(ticker)
            result=analyze(symbol,ticker,hourly,zone)
            results.append(result)
            print("TF014_RESULT "+json.dumps(result,separators=(",",":")),
                  flush=True)
        except (RuntimeError,ValueError,TypeError,IndexError,OverflowError) as e:
            errors[symbol]=str(e)[:180]
            print("TF014_UNAVAILABLE "+json.dumps(
                {"symbol":symbol,"error":errors[symbol]}),flush=True)
        time.sleep(1.)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    payload={"group":a.group,"requested":list(GROUPS[a.group]),
             "completed":len(results),"results":results,"errors":errors,
             "broker_orders":False,"research_only":True}
    a.output.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    print("TF014_GROUP "+json.dumps(
        {"group":a.group,"completed":len(results),"errors":errors}),flush=True)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"],"a") as f:
            f.write("\n### "+a.group+" (TF014 public H4 proxy)\n\n")
            f.write("|Symbol|OOS trades|OOS net R|WF net R|Cost|\n|---|---:|---:|---:|---|\n")
            for v in results:
                f.write(f"|{v['symbol']}|{v['oos']['trades']}|{v['oos']['net_r']}|"
                        f"{v['wf_net_r']}|{v['cost_mode']}|\n")
            f.write("\nNot MT5 H4; no verified broker costs or approval.\n")
    return 0 if results else 2

if __name__=="__main__":raise SystemExit(main())
