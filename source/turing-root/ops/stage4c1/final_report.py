"""Create blind final-exam packets from completed cached outputs; no inference."""
import datetime
import hashlib
import json
import sys
from pathlib import Path
from stage4c1.judge_packet import main as packet

root = Path.cwd()
out = root / 'results/stage4c1'
label, anonymous = sys.argv[1:]
assert label in ('base', 'selected', 'evidence_only')
assert anonymous in ('exam_f', 'exam_g', 'exam_h')
freeze = json.loads((out / 'development_frozen.json').read_text())
assert freeze['development_frozen'] and freeze['further_training_forbidden']
source = out / 'final_exam' / label
assert json.loads((source / 'curriculum_exam_complete.json').read_text())['passed']
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
reports = []
for split, count in (('test', 16), ('challenge', 6)):
    destination = out / 'blind_reviews' / (anonymous + '_' + split)
    packet(str(source / split), str(destination), split)
    path = destination / 'packet.json'
    obj = json.loads(path.read_text())
    assert len(obj['cases']) == count and obj['split'] == split
    for case in obj['cases']:
        generation = source / split / 'stage4c0' / (case['id'] + '.json')
        saved = json.loads(generation.read_text())
        assert sha(generation) == case['output_sha256']
        assert saved['raw'] == case['student_output'] and saved['split'] == split
    proof = {'passed': True, 'cases_verified': count, 'split': split,
             'packet_sha256': sha(path),
             'binding': 'SHA256 of complete saved generation JSON; visible student_output equals its raw field',
             'development_freeze_sha256': sha(out / 'development_frozen.json'),
             'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    (destination / 'source_binding_verified.json').write_text(json.dumps(proof, indent=2) + '\n')
    reports.append({'packet': destination.name, **proof})
receipt = out / 'final_exam' / label / 'blind_packets_verified.json'
assert not receipt.exists()
receipt.write_text(json.dumps(reports, indent=2) + '\n')
print(json.dumps(reports, indent=2))
