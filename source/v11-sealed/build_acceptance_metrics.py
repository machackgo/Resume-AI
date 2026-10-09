"""Count a complete verified cohort; never generate independent audit labels."""
import collections
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
manifest = json.loads((D / 'full-v1/cohort-manifest.json').read_text())
decisions = json.loads((D / 'full-v1-independent-decisions.json').read_text())
audit = json.loads((D / 'full-v1-independent-audit.json').read_text())
expected = {x['case'] for x in manifest['cases']}
assert expected == set(decisions)
assert len(expected) == manifest['input_count'] == 30
runtime = collections.Counter()
coverage = collections.Counter()
dimensions = {k: collections.Counter() for k in
              ['factual_class', 'content_class', 'identity_class', 'capability_class', 'relationship_class']}
claim_ids = set()
case_rows = []
for entry in sorted(manifest['cases'], key=lambda x: x['case']):
    p = D / 'full-v1' / Path(entry['source']).name
    raw = p.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == entry['sha256'] == decisions[entry['case']]['raw_sha256']
    r = json.loads(raw)
    decision = decisions[r['id']]
    claims = [c for s in (r.get('resume') or {}).get('sections', []) for c in s['claims']]
    assert {c['claim_id'] for c in claims} == {c['claim_id'] for c in decision['claims']}
    runtime[r['status']] += 1
    for row in r.get('requirement_coverage', []):
        coverage[row['status']] += 1
        if row.get('omitted'):
            coverage['OMITTED'] += 1
    for c in decision['claims']:
        claim_ids.add(c['claim_id'])
        for key in dimensions:
            dimensions[key][c.get(key, 'NOT_RECORDED_IN_HISTORICAL_AUDIT')] += 1
    case_rows.append(dict(case=r['id'],runtime_status=r['status'],claims=len(claims),
                          independent_passed=decision['case_passed'],outcome_kind=r.get('outcome_kind'),
                          raw_sha256=entry['sha256']))
mechanical = []
controls = []
for shard in manifest['shards']:
    name = shard['run']
    suffix = '-final' if name.startswith('full-') else ''
    check = json.loads((D / (name + '-mechanical-audit' + suffix + '.json')).read_text())
    mechanical.extend(check['cases'])
    cr = json.loads((D / name / 'controlled-review-results.json').read_text())
    assert len(cr) == 8 and all(c['passed'] for c in cr)
    controls.extend(cr)
assert len(mechanical) == len(expected) and {r['case'] for r in mechanical} == expected
result = dict(suite='unchanged full-v7: 20 original + 10 stress', cases=case_rows,
              runtime_status=dict(runtime), claims_audited=sum(x['claims'] for x in case_rows),
              unique_claim_ids=len(claim_ids), dimensions={k:dict(v) for k,v in dimensions.items()},
              pipeline_requirement_coverage=dict(coverage),
              coverage_note='Pipeline coverage is conservative final-claim coverage, not a finding that the corpus lacks every omitted capability. Repeated raw requirement occurrences are counted.',
              controls_passed=len(controls), controls_failed=0,
              mechanical_failures=sum(bool(r['issues']) for r in mechanical),
              model_calls=sum(r['model_calls'] for r in mechanical),
              maximum_input_tokens=max(r['maximum_input_tokens'] for r in mechanical),
              canonical_context_checks=sum(r['canonical_context_checks'] for r in mechanical),
              independently_passed_cases=sum(x['independent_passed'] for x in case_rows),
              independently_failed_cases=sum(not x['independent_passed'] for x in case_rows),
              independent_audit_complete=audit['independent_audit_complete'],
              reused_valid_fresh_historical_cases=8, newly_generated_remaining_cases=22,
              all_cases_passed=audit['all_cases_passed'])
with (D / 'full-v1-acceptance-metrics.json').open('x') as f:
    json.dump(result, f, indent=2)
print(json.dumps({k:v for k,v in result.items() if k!='cases'}, indent=2))
