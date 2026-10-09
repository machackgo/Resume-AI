"""Read-only independent input-factory audit; never regenerates teacher targets."""
import json, hashlib
from collections import Counter, defaultdict
from pathlib import Path
from stage4c0.contracts import validate_input
from stage4c0.grounding import validate_scenario
ROOT=Path(__file__).resolve().parent

def run():
 parts={n:[json.loads(l) for l in (ROOT/(n+'.jsonl')).read_text().splitlines()] for n in ['pilot','pool','challenge']}
 allrows=sum(parts.values(),[]);errors=[]
 for r in allrows:
  errors += [(r['scenario_id'],e) for e in validate_input(r['input'])+validate_scenario(r)]
  for req in r['input']['job']['requirements']:
   if req['source_quote'] not in r['input']['job']['text']:errors.append((r['scenario_id'],'source quote not found'))
  if r['input']['task']=='ANALYZE_JOB' and r['input']['job']['requirements']:errors.append((r['scenario_id'],'pre-extracted analysis answer'))
 ids=[r['scenario_id'] for r in allrows]
 assert len(set(ids))==len(ids)
 key=[(r['input']['profile']['candidate_id'],r['input']['job']['job_id'],r['input']['task']) for r in allrows]
 assert len(set(key))==len(key)
 groups={}
 for field in ['scenario_family','candidate_archetype','job_archetype','template_family','split_group']:
  seen=defaultdict(set)
  for r in allrows:seen[r['metadata'][field]].add(r['split'])
  bad={k:sorted(v) for k,v in seen.items() if len(v)>1}
  if bad:errors.append((field,bad))
  groups[field]={'unique_groups':len(seen),'cross_split_groups':bad}
 def counts(rows,key):return dict(sorted(Counter(r['metadata'][key] for r in rows).items()))
 report={'status':'PASS' if not errors else 'FAIL','errors':errors,'target_generation_performed':False,'partitions':{},'group_isolation':groups,'maximum_rag_characters':max(len(e['content']) for r in allrows for e in r['input']['rag']),'maximum_distinct_rag_groups':max(len({e['content'] for e in r['input']['rag']}) for r in allrows),'historical_leakage_status':'Requires main historical fingerprint audit; not measured here.'}
 for name,rows in parts.items():
  representatives={r['input']['profile']['candidate_id']:r for r in rows if r['input']['task']!='ANALYZE_JOB'}
  report['partitions'][name]={'records':len(rows),'candidate_variants':len(representatives),'families':len({r['metadata']['scenario_family'] for r in rows}),'tasks':dict(sorted(Counter(r['input']['task'] for r in rows).items())),'splits':dict(Counter(r['split'] for r in rows)),'roles':counts(rows,'role_family'),'seniority':counts(rows,'seniority'),'fit':counts(rows,'fit_level'),'difficulty':counts(rows,'difficulty'),'technology_by_candidate':dict(sorted(Counter(t for r in representatives.values() for t in r['metadata']['technology_tags']).items())),'actions_by_candidate':dict(sorted(Counter(t for r in representatives.values() for t in r['metadata']['action_tags']).items())),'trust_by_candidate':dict(sorted(Counter(t for r in representatives.values() for t in r['metadata']['trust_tags']).items()))}
 return report
if __name__=='__main__':
 result=run();print(json.dumps(result,indent=2));raise SystemExit(bool(result['errors']))
