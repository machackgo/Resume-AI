"""Explicit release gate; failing data is never labeled frozen or train-ready."""
import argparse,collections,json
from pathlib import Path
from .io import read_json,read_jsonl,strict_json,sha_file,write_json
from .contracts import TASKS
from .exclusion import near_duplicate_artifacts

def check(root,records,validation,factory,protection,tests):
    rows=read_jsonl(records);v=read_json(validation);f=read_json(factory);p=read_json(protection);t=read_json(tests);errors=[]
    if not v.get('passed') or v.get('records_file_sha256')!=sha_file(records):errors.append('BOUND_COMPLETE_VALIDATION_REQUIRED')
    if not v.get('historical_exclusion',{}).get('passed') or not v.get('provenance_validation_executed'):errors.append('HISTORICAL_AND_PROVENANCE_CHECKS_REQUIRED')
    if not v.get('tokenizer_fingerprint',{}).get('files'):errors.append('REAL_TOKENIZER_FINGERPRINT_REQUIRED')
    if not f.get('factory_frozen'):errors.append('FACTORY_NOT_FROZEN')
    for path,h in f.get('sha256',{}).items():
        if not (root/path).is_file() or sha_file(root/path)!=h:errors.append('FROZEN_FACTORY_CHANGED:'+path)
    if not p.get('passed') or p.get('phase')!='after':errors.append('AFTER_PROTECTION_REQUIRED')
    if t.get('returncode')!=0:errors.append('CURRENT_TESTS_REQUIRED')
    bysplit=collections.defaultdict(list)
    for r in rows:
        m=r['metadata'];bysplit[m['split']].append(r)
        if not m.get('qwen_token_counts') or not m.get('tokenizer_fingerprint_sha256'):errors.append('PER_RECORD_TOKEN_PROVENANCE_REQUIRED:'+m['example_id'])
    if set(bysplit)!={'train','validation','test','challenge'}:errors.append('ALL_RELEASE_SPLITS_REQUIRED')
    for split in ['train','validation','test']:
        if {r['metadata']['task'] for r in bysplit[split]}!=set(TASKS):errors.append('TASK_COVERAGE_INCOMPLETE:'+split)
    sections=set();complete_resumes=0
    for r in rows:
        out=strict_json(r['messages'][-1]['content'])
        if out['status']!='COMPLETE':continue
        if out['task']=='GENERATE_RESUME':
            complete_resumes+=1;sections.update(s['section'] for s in out['artifact']['sections'])
        elif out['task']=='GENERATE_RESUME_SECTION':sections.add(out['artifact']['section']['section'])
    if sections!={'SUMMARY','SKILLS','EXPERIENCE','PROJECTS','EDUCATION','CERTIFICATIONS'}:errors.append('SECTION_COVERAGE_INCOMPLETE')
    if not complete_resumes:errors.append('COMPLETE_RESUME_REQUIRED')
    near=near_duplicate_artifacts(rows)
    if near['cross_split_review_required']:errors.append('CROSS_SPLIT_NEAR_DUPLICATES_REQUIRE_DISPOSITION')
    return {'version':'stage4c0-release-gate-v1','passed':not errors,'decision':'A. PROFESSIONAL CURRICULUM READY FOR QLORA TRAINING' if not errors else 'B. PROFESSIONAL CURRICULUM NOT READY','errors':errors,'records':len(rows),'splits':{k:len(x) for k,x in bysplit.items()},'complete_resumes':complete_resumes,'sections':sorted(sections),'near_duplicates':near,'audit_files_sha256':{str(x):sha_file(x) for x in [records,validation,factory,protection,tests]},'training_executed':False,'note':'This gate supports only a controlled separately authorized experiment. Finite synthetic coverage and same-model-family judges do not establish production quality.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path.cwd())
    for k in ['records','validation','factory','protection','tests','out']:p.add_argument('--'+k,required=True,type=Path)
    a=p.parse_args();r=check(a.root,a.records,a.validation,a.factory,a.protection,a.tests);write_json(a.out,r);print(json.dumps(r,indent=2));raise SystemExit(0 if r['passed'] else 1)
