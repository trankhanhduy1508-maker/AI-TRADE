"""One-shot source-pinned CSV replay. Raw input remains outside GitHub."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.research.pinned_continuous import run_bundle

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--bundle',type=Path,required=True)
    p.add_argument('--as-of-utc',type=int,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    report=run_bundle(json.loads(args.bundle.read_text()),as_of_utc=args.as_of_utc)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:report[k] for k in ('status','completed_cells','orders_sent','edge_status')}))
if __name__=='__main__':main()
