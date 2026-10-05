"""Chạy lại nghiên cứu CSV bằng quy tắc đã nạp, không dùng API AI."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.research.r2_walkforward import Bar,Study
from src.research.knowledge_pipeline import research

def run(csv_path,metadata_path,as_of_utc):
    data=Path(csv_path).read_bytes()
    metadata=json.loads(Path(metadata_path).read_text(encoding='utf-8'))
    if metadata.get('source_sha256')!=hashlib.sha256(data).hexdigest():
        raise ValueError('CSV_SOURCE_HASH_MISMATCH')
    with Path(csv_path).open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    bars=[Bar(ts=int(r['timestamp']),open=float(r['open']),high=float(r['high']),
              low=float(r['low']),close=float(r['close'])) for r in rows]
    return research(bars,root=ROOT,study=Study(**metadata),as_of_utc=as_of_utc)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv',required=True)
    parser.add_argument('--metadata',required=True)
    parser.add_argument('--as-of-utc',required=True,type=int)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    result=run(args.csv,args.metadata,args.as_of_utc)
    Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
