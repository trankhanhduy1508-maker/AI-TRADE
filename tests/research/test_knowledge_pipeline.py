import unittest
import tempfile
import shutil
import json
from pathlib import Path
from copy import deepcopy
from src.research.knowledge_pipeline import load_package, research
from tests.research.test_r2_walkforward import fixture,source,START,DAY
ROOT=Path(__file__).resolve().parents[2]

class KnowledgePipeline(unittest.TestCase):
 def test_all_principles_have_traceable_sources_but_no_promotion(self):
  p=load_package(ROOT)
  self.assertEqual(len(p['principles']),12)
  self.assertTrue(all(x['status']=='HYPOTHESIS' for x in p['principles']))
  self.assertFalse(p['broker_send_enabled'])
 def test_offline_research_is_reproducible_without_ai(self):
  args=dict(root=ROOT,study=source(assumed_round_trip_cost_price=.15),as_of_utc=START+1000*DAY)
  a=research(fixture(1000),**args)
  self.assertEqual(a,research(fixture(1000),**args))
  self.assertEqual(a['promotion'],'NOT_APPROVED')
  self.assertEqual(a['orders_sent'],0)
  self.assertEqual(a['llm_calls'],0)
  self.assertEqual(a['evidence']['fee_status'],'MODELED_ONLY')
 def test_source_tampering_cannot_silently_change_learned_rules(self):
  with tempfile.TemporaryDirectory() as tmp:
   shutil.copytree(ROOT/'knowledge',Path(tmp)/'knowledge')
   target=Path(tmp)/'knowledge/CWS_TRADING_MASTERBOOK_V3_DISTILLED_2026-09-28.md'
   target.write_text(target.read_text()+'\nUnreviewed rule change\n')
   with self.assertRaisesRegex(ValueError,'KNOWLEDGE_SOURCE_CHANGED'):load_package(tmp)
 def test_manifest_cannot_self_promote_or_enable_orders(self):
  for key,value in [('broker_send_enabled',True),('claim','DEMO_VERIFIED')]:
   with tempfile.TemporaryDirectory() as tmp:
    shutil.copytree(ROOT/'knowledge',Path(tmp)/'knowledge')
    target=Path(tmp)/'knowledge/runtime/autonomous_rules_v1.json'
    p=json.loads(target.read_text())
    if key=='claim':p['principles'][0]['status']=value
    else:p[key]=value
    target.write_text(json.dumps(p))
    with self.assertRaises(ValueError):load_package(tmp)

if __name__=='__main__':unittest.main()
