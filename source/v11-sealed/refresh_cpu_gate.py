"""Bind a passing CPU result to the exact current application snapshot."""
import json,hashlib
from pathlib import Path
D=Path(__file__).resolve().parent;r=json.loads((D/'test-results.json').read_text())
blocked=[e for e in r['errors'] if 'PermissionError: Protected evaluation content prohibited' in e['error']]
ordinary=[e for e in r['errors'] if e not in blocked]
files={str(p.relative_to(D/'application')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (D/'application').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
g=dict(passed=not r['failures'] and not ordinary,passed_assertions=r['tests_run']-len(r['skipped'])-len(r['errors'])-len(r['failures']),failed=len(r['failures'])+len(ordinary),skipped=len(r['skipped']),protected_blocked=len(blocked),application=files,test_results_sha256=hashlib.sha256((D/'test-results.json').read_bytes()).hexdigest())
(D/'cpu-gate.json').write_text(json.dumps(g,indent=2));print({k:v for k,v in g.items() if k!='application'});assert g['passed']
