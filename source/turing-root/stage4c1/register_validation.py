"""Resource amendment before optimization: outcome-blind stratified VAL subset."""
import json,hashlib,collections
from pathlib import Path
from stage4c1.evaluate import write,sha
R=Path.cwd();out=R/'results/stage4c1/plan/validation_subset.json'
assert not out.exists()
assert not list((R/'adapters/stage4c1').glob('**/adapter_model.safetensors')),'register before any optimization'
p=R/'datasets/stage4a/v1/validation.jsonl';rows=[json.loads(l) for l in p.read_text().splitlines()];groups=collections.defaultdict(list)
for r in rows:
 m=r['metadata'];assert m['split']=='validation';groups[(m['scenario_family'],m['expected_label'],m['compound'])].append(m)
chosen=[]
for key,xs in sorted(groups.items()):
 assert len(xs)%2==0
 ordered=sorted(xs,key=lambda m:hashlib.sha256(('430001:validation:'+m['example_id']).encode()).hexdigest());chosen.extend(ordered[:len(xs)//2])
assert len(chosen)==80 and set(collections.Counter(m['expected_label'] for m in chosen).values())=={20}
write(out,{'seed':430001,'selection':'half of each scenario_family x expected_label x compound stratum; SHA256(seed:validation:example_id) ascending; no student outputs inspected','reason':'Measured generation runtime around one minute/case; bounded first experiment keeps all professional validation and all evidence final TEST','stage4a_ids':sorted(m['example_id'] for m in chosen),'source_sha256':sha(p),'label_counts':dict(collections.Counter(m['expected_label'] for m in chosen)),'metadata':chosen,'stage4c0_policy':'all14 validation examples','baseline_policy':'preserve all160 baseline outputs; paired checkpoint scoring uses these80 IDs','registered_before_optimizer':True})
print(json.dumps({'evidence_validation_subset':80,'label_counts':dict(collections.Counter(m['expected_label'] for m in chosen))}))
