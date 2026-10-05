"""Replay R2 đã đóng băng với lifecycle liên tục; KHÔNG là full R3.

Selections giữ nguyên từ R2 past-only, không tối ưu lại sau khi thấy P/L.
R2 lịch sử giữ nguyên, module mới chỉ đối chiếu lỗi reset tại fold.
"""
from .r2_walkforward import _validate, run_walkforward, CANDIDATES, MIN_BARS, STEP
from .continuous_replay import replay

def run_continuous(bars, *, study, as_of_utc: int) -> dict:
    usable=_validate(bars,study,as_of_utc)
    frozen=run_walkforward(bars,study=study,as_of_utc=as_of_utc)
    choices={c[0]:c for c in CANDIDATES}
    decisions={e['decision_bar_index']:choices.get(e['selected']) for e in frozen['episodes']}
    end=MIN_BARS+STEP*len(decisions)
    scenarios=(0., study.assumed_round_trip_cost_price, study.assumed_round_trip_cost_price*2,study.assumed_round_trip_cost_price*3)
    output={}
    for name,selections in [('R2_FROZEN_SELECTION',decisions),('R0_FIXED',{MIN_BARS:CANDIDATES[0]}),('FLAT',{MIN_BARS:None})]:
        lane={}
        for cost in sorted(set(scenarios)):
            result=replay(usable,begin=MIN_BARS,end=end,selections=selections,cost=cost,short=study.allow_short)
            # Only metrics and simulated checkpoint indexes; no raw price retention.
            for key in ('marks','trades','position'):
                result.pop(key)
            result['cost_price']=cost
            result['cost_status']='MODELED_ONLY' if cost else 'GROSS_ONLY'
            lane[str(cost)]=result
        output[name]=lane
    return dict(symbol=study.symbol,timeframe=study.timeframe,source_kind=study.source_kind,
                source_sha256=study.source_sha256,source_history=study.exposure,
                completed_evaluation_bars=end-MIN_BARS,
                ignored_partial_tail=len(usable)-end,
                selections=[dict(bar_index=i,candidate=c[0] if c else 'FLAT') for i,c in decisions.items()],
                lanes=output,r3_nested_selection_implemented=False,
                orders_sent=0,llm_calls=0,promotion='NOT_APPROVED',edge_status='UNPROVEN',
                source_rights_independently_verified=False,calendar_audited=False,
                account_currency_pnl=None)
