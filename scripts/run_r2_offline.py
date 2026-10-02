"""One-shot offline R2 research batch. No fetching, scheduler or order APIs.

Input catalog lists up to 56 normalized OHLC sources. Output is metadata
only; private/local source rights remain the operator's responsibility.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import time

from src.research.r2_batch import run_batch

PREREG_COMMIT = '6934a383b145369bb2447da29b3232e7ef04ab4d'


def main(argv=None) -> int:
    p=argparse.ArgumentParser(description='R2 past-only exploratory backtest (offline)')
    p.add_argument('--catalog', required=True, type=Path)
    p.add_argument('--as-of-utc', required=True, type=int)
    p.add_argument('--output', required=True, type=Path)
    args=p.parse_args(argv)
    if args.as_of_utc > int(time.time()) or args.as_of_utc <= 0:
        raise ValueError('INVALID_AS_OF_CLOCK')
    manifest=json.loads(args.catalog.read_text(encoding='utf-8'))
    if manifest.get('prereg_commit') != PREREG_COMMIT:
        raise ValueError('PREREG_COMMIT_MISMATCH')
    report=run_batch(manifest['entries'], as_of_utc=args.as_of_utc)
    report['prereg_commit']=PREREG_COMMIT
    report['run_at_utc']=int(time.time())
    report['input_catalog_name']=args.catalog.name
    args.output.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.r2-report-',dir=args.output.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as out:
            os.fchmod(out.fileno(),0o600)
            json.dump(report,out,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)
            out.write('\n')
            out.flush()
            os.fsync(out.fileno())
        os.replace(tmp,args.output)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    print(json.dumps({'status':report['status'],'cells':report['cell_count'],
                      'historical_exploratory':report['cells_with_historical_exploratory_results'],
                      'edge_status':report['edge_status'],'orders_sent':0,
                      'output_path':str(args.output)},ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
