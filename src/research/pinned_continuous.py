"""Nguồn D1 CSV đã khóa Git blob, nghiên cứu read-only, không giữ raw trong output."""
import csv
import hashlib
import io
from datetime import datetime, timezone
from statistics import median
from .r2_walkforward import Bar, Study
from .continuous_walkforward import run_continuous

def run_bundle(entries: list[dict], *, as_of_utc: int) -> dict:
    if not isinstance(entries,list) or not 1<=len(entries)<=56:
        raise ValueError('INVALID_SOURCE_COUNT')
    result={}
    for entry in entries:
        cell=entry['cell']
        if cell in result:
            raise ValueError('DUPLICATE_SOURCE_CELL')
        summary=dict(status=entry['status'],symbol=entry['symbol'],git_blob_sha=entry['git_blob_sha'],
                     source_repository=entry.get('repo'),source_commit=entry.get('commit'),
                     source_path=entry.get('path'),
                     instrument_equivalence='ETF_PROXY_NOT_MT5_UNDERLYING' if entry.get('format')=='ETF_WIDE' else 'PROVIDER_HISTORY_NOT_BROKER_VERIFIED')
        result[cell]=summary
        if entry['status']!='ELIGIBLE_HISTORICAL_REUSED':
            continue
        raw=entry['raw'].encode('utf-8')
        actual=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\x00'+raw).hexdigest()
        if actual!=entry['git_blob_sha']:
            summary['status']='SOURCE_HASH_MISMATCH'
            continue
        try:
            observations=[]
            timeframe=entry.get('timeframe','D1')
            if timeframe not in ('D1','H4'):
                raise ValueError('UNSUPPORTED_SOURCE_TIMEFRAME')
            date_format='%Y-%m-%d %H:%M:%S' if timeframe=='H4' else '%Y-%m-%d'
            if entry.get('format')=='ETF_WIDE':
                if timeframe!='D1':raise ValueError('ETF_TIMEFRAME_MISMATCH')
                rows=list(csv.reader(io.StringIO(entry['raw'])))
                indexes=[next(i for i,(symbol,field) in enumerate(zip(rows[0],rows[1]))
                              if symbol==entry['symbol'] and field==name)
                         for name in ('Open','High','Low','Close')]
                data=((row[0],*(row[i] for i in indexes)) for row in rows[3:])
            else:
                data=((row['Date'],*(row[k] for k in ('open','high','low','close')))
                      for row in csv.DictReader(io.StringIO(entry['raw'])))
            for row in data:
                stamp=int(datetime.strptime(row[0],date_format).replace(tzinfo=timezone.utc).timestamp())
                observations.append(Bar(stamp,*(float(value) for value in row[1:])))
            # Engineering cost sensitivity fixed from first 500 past closes,
            # not fitted to future profitability or labeled venue-realistic.
            cost=median(b.close for b in observations[:500])*.001
            study=Study(entry['symbol'],timeframe,'NATIVE_'+timeframe,hashlib.sha256(raw).hexdigest(),
                        'HISTORICAL_REUSED','UNVERIFIED_MARKET_CALENDAR',False,cost)
            summary.update(run_continuous(observations,study=study,as_of_utc=as_of_utc))
            summary['status']='HISTORICAL_REUSED_DESCRIPTIVE_ONLY'
            summary['cost_assumption']='CONSTANT_PRICE_10BPS_OF_FIRST_500_MEDIAN_CLOSE'
            summary['timestamp_provenance']='NAIVE_PROVIDER_DATE_ASSUMED_UTC_FOR_ORDERING_ONLY'
        except (ValueError,KeyError,TypeError,OverflowError,IndexError,StopIteration) as exc:
            summary['status']='DATA_REJECTED'
            summary['reason']=str(exc)
    return dict(status='OFFLINE_CONTINUOUS_REPLAY',cells=result,
                completed_cells=sum(v['status']=='HISTORICAL_REUSED_DESCRIPTIVE_ONLY' for v in result.values()),
                orders_sent=0,llm_calls=0,promotion='NOT_APPROVED',edge_status='UNPROVEN')
