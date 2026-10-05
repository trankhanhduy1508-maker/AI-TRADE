"""Nạp kiến thức có nguồn và chạy nghiên cứu quy tắc offline, không cần LLM.

Không huấn luyện model ML, không tự promote chiến lược, không gửi broker order.
R2 là phòng nghiên cứu; TF-013A đang chạy không bị thay thế bởi module này.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from .r2_walkforward import run_walkforward

PACKAGE='knowledge/runtime/autonomous_rules_v1.json'

def digest(text):
    return hashlib.sha256((text.rstrip()+'\n').encode('utf-8')).hexdigest()

def load_package(root):
    root=Path(root).resolve()
    p=json.loads((root/PACKAGE).read_text(encoding='utf-8'))
    if p.get('schema_version')!=1 or p.get('broker_send_enabled') is not False:
        raise ValueError('KNOWLEDGE_PACKAGE_NOT_RESEARCH_ONLY')
    sources={}
    for s in p.get('sources',[]):
        target=(root/s['path']).resolve()
        if not target.is_relative_to(root):raise ValueError('SOURCE_OUTSIDE_REPOSITORY')
        text=target.read_text(encoding='utf-8')
        if digest(text)!=s['sha256_normalized']:raise ValueError('KNOWLEDGE_SOURCE_CHANGED')
        if s['id'] in sources:raise ValueError('DUPLICATE_SOURCE_ID')
        sources[s['id']]=text
    ids=set()
    for rule in p.get('principles',[]):
        if rule['id'] in ids:raise ValueError('DUPLICATE_CLAIM_ID')
        ids.add(rule['id'])
        if rule.get('status')!='HYPOTHESIS':raise ValueError('UNVERIFIED_PROMOTION')
        if rule.get('source_id') not in sources or rule.get('source_heading') not in sources[rule['source_id']]:
            raise ValueError('CLAIM_SOURCE_NOT_FOUND')
    if len(ids)!=12:raise ValueError('INCOMPLETE_KNOWLEDGE_PACKAGE')
    return p

def research(bars,*,root,study,as_of_utc):
    p=load_package(root)
    result=run_walkforward(bars,study=study,as_of_utc=as_of_utc)
    package_hash=digest(json.dumps(p,ensure_ascii=False,sort_keys=True))
    return {'knowledge_version':p['version'],'knowledge_sha256':package_hash,
            'claims_loaded':[r['id'] for r in p['principles']],
            'research_engine':'EXISTING_R2_WALKFORWARD',
            'active_runtime_strategy_changed':False,
            'llm_calls':0,'orders_sent':0,'promotion':'NOT_APPROVED',
            'edge_status':'UNPROVEN','evidence':result,
            'unimplemented_principles':[r['id'] for r in p['principles']
                if r['research_mapping']=='REQUIRES_SEPARATE_VALIDATION']}
