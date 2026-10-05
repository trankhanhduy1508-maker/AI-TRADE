"""Offline lifecycle replay: giữ vị thế/pending qua lần chọn lại candidate.

Không phải R3 nested selection, không đổi TF-013A, không tính tiền tài khoản.
Caller khóa selections từ quá khứ. Chỉ candidate R2 đã đóng băng được dùng.
Cost là giả định round-trip đơn vị giá, không phải phí broker được xác minh.
"""
from __future__ import annotations
import math
from .r2_walkforward import Bar, CANDIDATES, SMA_N, ATR_N, _atr

def replay(bars, *, begin: int, end: int, selections: dict,
           cost: float, short: bool) -> dict:
    if type(begin) is not int or type(end) is not int or not SMA_N <= begin < end <= len(bars):
        raise ValueError('INVALID_REPLAY_RANGE')
    if type(short) is not bool or isinstance(cost,bool) or not isinstance(cost,(int,float)) or not math.isfinite(cost) or cost < 0:
        raise ValueError('INVALID_REPLAY_COST_OR_SHORT')
    if not isinstance(selections,dict) or begin not in selections:
        raise ValueError('MISSING_INITIAL_SELECTION')
    for index,candidate in selections.items():
        if type(index) is not int or not begin <= index < end:
            raise ValueError('INVALID_SELECTION_BOUNDARY')
        if candidate is not None and candidate not in CANDIDATES:
            raise ValueError('UNKNOWN_CANDIDATE')
    history=bars[:end]
    previous_ts=-1
    for b in history:
        if (not isinstance(b,Bar) or type(b.ts) is not int or b.ts<=previous_ts
                or not all(type(v) in (int,float) and math.isfinite(v) and v>0 for v in (b.open,b.high,b.low,b.close))
                or b.high<max(b.open,b.low,b.close) or b.low>min(b.open,b.high,b.close)):
            raise ValueError('INVALID_REPLAY_BAR')
        previous_ts=b.ts
    atrs=_atr(history)
    selected=None
    pos=None
    pending=None
    trades=[]
    marks=[]
    realized=0.
    gap_count=0
    for i in range(begin,end):
        b=history[i]
        if i in selections:
            selected=selections[i]
        exited=False
        if pos is not None:
            # Candidate at entry remains owner of this position's exit rules.
            direction=pos['direction'];trail=pos['config'][2]
            prior=history[i-trail:i]
            stop=(max(pos['stop'],min(x.low for x in prior)) if direction==1
                  else min(pos['stop'],max(x.high for x in prior)))
            pos['stop']=stop
            gap=b.open<=stop if direction==1 else b.open>=stop
            touch=b.low<=stop if direction==1 else b.high>=stop
            if gap or touch:
                price=b.open if gap else stop
                r=(direction*(price-pos['entry_price'])-cost)/pos['risk_price']
                trades.append(dict(entry_index=pos['entry_index'],exit_index=i,
                                   candidate=pos['candidate'],direction=direction,
                                   entry_price=pos['entry_price'],exit_price=price,
                                   net_r=r,gap=gap))
                realized+=r;gap_count+=int(gap);pos=None;exited=True
        if pos is None and pending is not None and not exited:
            direction,stop,owner=pending
            invalid=b.open<=stop if direction==1 else b.open>=stop
            if not invalid:
                risk=abs(b.open-stop)
                pos=dict(direction=direction,entry_price=b.open,stop=stop,
                         risk_price=risk,entry_index=i,candidate=owner[0],config=owner)
                touch=b.low<=stop if direction==1 else b.high>=stop
                if touch:
                    r=(direction*(stop-b.open)-cost)/risk
                    trades.append(dict(entry_index=i,exit_index=i,candidate=owner[0],
                                       direction=direction,entry_price=b.open,
                                       exit_price=stop,net_r=r,gap=False))
                    realized+=r;pos=None;exited=True
        pending=None
        if pos is None and not exited and selected is not None and i>=max(SMA_N-1,selected[1],ATR_N):
            _,channel,_,multiple=selected
            prior=history[i-channel:i]
            sma=sum(x.close for x in history[i-SMA_N+1:i+1])/SMA_N
            if atrs[i]>0:
                if b.close>max(x.high for x in prior) and b.close>sma:
                    pending=(1,b.close-multiple*atrs[i],selected)
                elif short and b.close<min(x.low for x in prior) and b.close<sma:
                    pending=(-1,b.close+multiple*atrs[i],selected)
        unrealized=((pos['direction']*(b.close-pos['entry_price'])-cost)/pos['risk_price'] if pos else 0.)
        marks.append(dict(bar_index=i,realized_r=realized,unrealized_r=unrealized,marked_r=realized+unrealized))
    peak=0.;dd=0.
    for mark in marks:
        peak=max(peak,mark['marked_r']);dd=max(dd,peak-mark['marked_r'])
    public_pos={k:v for k,v in pos.items() if k!='config'} if pos else None
    return dict(closed_trades=len(trades),realized_r=realized,
                expectancy_r=realized/len(trades) if trades else None,
                unrealized_r=marks[-1]['unrealized_r'],max_dd_r_marked=dd,
                gap_stops=gap_count,open_position_at_boundary=pos is not None,
                position=public_pos,pending_at_boundary=pending is not None,
                trades=trades,marks=marks,orders_sent=0,account_currency_pnl=None)
