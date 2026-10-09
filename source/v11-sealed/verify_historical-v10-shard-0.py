import pathlib,hashlib,json
D=pathlib.Path('/scratch/mohammedmubashir/resume-ai/work/semantic-contracts-20261008/historical-v10-shard-0')
P=pathlib.Path('/scratch/mohammedmubashir/resume-ai/work/final-semantic-remediation-20261007/full-v7')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files=['benchmark.json','stress-inputs.json','candidate_sources.json','embedding-records.json']+[str(p.relative_to(D)) for p in (D/'candidate-vector-store').rglob('*.sqlite3')]
result={'inputs':{f:{'sha256':sha(D/f),'matches_full_v7':sha(D/f)==sha(P/f)} for f in files},'application':{str(p.relative_to(D/'application')):sha(p) for p in (D/'application').rglob('*') if p.is_file() and '__pycache__' not in p.parts}}
assert all(v['matches_full_v7'] for v in result['inputs'].values())
print(json.dumps(result,indent=2))
