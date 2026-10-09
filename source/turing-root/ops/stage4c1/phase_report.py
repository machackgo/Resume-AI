"""CPU-only reporting after a registered validation phase; never trains."""
import json,sys,hashlib,collections,datetime
from pathlib import Path
from stage4c1.diagnose import main as diagnose
from stage4c1.judge_packet import main as packet
r=Path.cwd();arm,step,blind=sys.argv[1:];step=int(step)
assert arm in ('evidence_only','interleaved')
out=r/'results/stage4c1'/arm
marker=out/f'needs_teacher_review_{step:06d}.json';assert marker.exists()
ck=r/f'adapters/stage4c1/run_430001/{arm}/checkpoint_{step:06d}'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=json.loads((ck/'checksums.json').read_text());assert all(sha(ck/n)==h for n,h in checks.items())
tr=json.loads((ck/'trajectory.json').read_text());plan=json.loads((ck/'mixture.json').read_text())
assert [x['step'] for x in tr]==list(range(1,step+1))
ids=[i for x in tr for i in x['ids']];entries=plan['entries'][:len(ids)];assert ids==[x['id'] for x in entries]
assert all(x['base_frozen'] for x in tr)
report={'arm':arm,'step':step,'unique_examples':len(set(ids)),'effective_exposures':len(ids),'supervised_tokens':sum(x['supervised_tokens'] for x in tr),'training_seconds':sum(x['seconds'] for x in tr),'peak_reserved_gib':max(x['peak_reserved'] for x in tr)/2**30,'gradient_norm_range':[min(x['gradient_norm'] for x in tr),max(x['gradient_norm'] for x in tr)],'loss_range':[min(x['loss'] for x in tr),max(x['loss'] for x in tr)],'base_frozen_all_updates':True,'checkpoint_checksums_verified':True,'resume_verified':any(out.glob('resume_verified_000010_*.json')),'checkpoint_checksums_sha256':sha(ck/'checksums.json'),'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
assert sum(x['target_tokens'] for x in entries)==report['supervised_tokens']
for dimension in ('dataset','task'):
 counts=collections.Counter()
 for entry in entries:counts[entry[dimension]]+=entry['target_tokens']
 report['supervised_tokens_by_'+dimension]=dict(counts)
report['maximum_example_exposure']=max(collections.Counter(ids).values())
report['entry_fields']=list(entries[0]);report['exposures_by_dataset']=dict(collections.Counter(x.get('dataset','unspecified') for x in entries));report['exposures_by_task']=dict(collections.Counter(x.get('task','unspecified') for x in entries))
p=out/f'phase_report_{step:06d}.json';assert not p.exists();p.write_text(json.dumps(report,indent=2)+'\n')
v=out/f'validation_{step:06d}';diagnose(v);packet(v,r/'results/stage4c1/blind_reviews'/blind)
print(json.dumps(report))
