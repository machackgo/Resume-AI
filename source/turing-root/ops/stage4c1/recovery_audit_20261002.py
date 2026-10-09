"""Read-only CPU audit of completed Stage4C1; exclusively creates new receipts."""
import datetime
import hashlib
import json
import math
import os
from pathlib import Path

R = Path.cwd()
O = R / 'results/stage4c1'
cache = {}

def sha(p):
    p = Path(p)
    if p not in cache:
        h = hashlib.sha256()
        with p.open('rb') as f:
            for b in iter(lambda: f.read(8 * 1024 * 1024), b''):
                h.update(b)
        cache[p] = h.hexdigest()
    return cache[p]

def read(p):
    return json.loads(Path(p).read_text())

def save(name, obj):
    with (O / name).open('x') as f:
        json.dump(obj, f, indent=2)
        f.write('\n')

def verify(items, root):
    bad = []
    for name, value in items.items():
        expected = value['sha256'] if isinstance(value, dict) else value
        p = root / name
        if not p.is_file() or sha(p) != expected:
            bad.append(name)
    return bad

def rows(dataset, split):
    p = R / f'datasets/{dataset}/v1/{split}.jsonl'
    return {x['metadata']['example_id']: x for x in map(json.loads, p.read_text().splitlines())}

def main():
    assert os.environ.get('SLURM_JOB_ID'), 'CPU allocation required'
    freeze = read(O / 'development_frozen.json')
    freeze_sha = sha(O / 'development_frozen.json')
    assert freeze['development_frozen'] and freeze['further_training_forbidden']
    assert freeze['promotion_forbidden'] and not freeze['validation_eligible']
    assert not verify(freeze['reviewed_artifacts'], R)
    assert read(O / 'jobs/final_exam.json')['development_freeze_sha256'] == freeze_sha
    protected = []
    manifests = [
        ('results/stage4a/final-manifest.json', R, None),
        ('results/stage4c0/protected-manifest.json', R, None),
        ('results/stage4b/smoke/release-checksums.json', R, None),
        ('datasets/stage4c0/v1/checksums.json', R / 'datasets/stage4c0/v1', None),
        ('datasets/stage4c0/v1/audits/factory-freeze-v2.json', R, 'sha256'),
    ]
    for name, root, key in manifests:
        obj = read(R / name)
        items = obj[key] if key else obj
        bad = verify(items, root)
        protected.append({'manifest': name, 'files': len(items), 'changed_or_missing': bad})
        assert not bad, (name, bad)
    a = R / 'datasets/stage4a/v1'
    items = {p: h for h, p in (line.split('  ', 1) for line in (a / 'checksums.sha256').read_text().splitlines())}
    assert not verify(items, a)
    protected.append({'manifest': 'datasets/stage4a/v1/checksums.sha256', 'files': len(items), 'changed_or_missing': []})
    archives = {
        'release/resume-ai-stage4c0-v1.tar.gz': '3e3f452ec32471ec2d22c6552e1743e86c179e0cec18f70128a2a2348fc4147d',
        'results/stage4a-release-v1.tar.gz': '3c84bbd04035357161267095b9b2feccae5178f8541378eb832ae9466945ea18',
    }
    assert not verify(archives, R)
    protected.append({'manifest': 'frozen archives', 'files': 2, 'changed_or_missing': []})
    source = read(O / 'source_manifest_pretrain_v2.json')['files']
    core = {p: h for p, h in source.items() if p in (
        'stage4c1/train.py', 'stage4c1/prepare.py', 'stage4c1/training_config.json',
        'stage4c1/evaluate.py', 'stage4c1/selection.py', 'docs/stage4c1_experiment_protocol.md')}
    assert len(core) == 6 and not verify(core, R)
    datasets = {d: {s: rows(d, s) for s in ('train', 'validation', 'test')} for d in ('stage4a', 'stage4c0')}
    datasets['stage4c0']['challenge'] = rows('stage4c0', 'challenge')
    for d, splits in datasets.items():
        keys = list(splits)
        for i, s in enumerate(keys):
            for t in keys[i + 1:]:
                assert not set(splits[s]) & set(splits[t]), (d, s, t)
    assert read(O / 'preflight/stage4a-validation.json')['passed']
    assert read(O / 'preflight/stage4c0-validation.json')['passed']
    checkpoint_reports = []
    for manifest in sorted((R / 'adapters/stage4c1/run_430001').glob('*/checkpoint_*/checksums.json')):
        items = read(manifest)
        bad = verify(items, manifest.parent)
        assert not bad, (str(manifest), bad)
        checkpoint_reports.append({'path': str(manifest.parent.relative_to(R)), 'files': len(items), 'manifest_sha256': sha(manifest)})
    assert checkpoint_reports
    arms = []
    for arm, last in [('interleaved', 124), ('evidence_only', 131)]:
        plan = read(O / f'plan/{arm}.json')
        chosen = freeze if arm == 'interleaved' else freeze['evidence_only_comparator']
        cp = R / chosen['checkpoint']
        assert sha(cp / 'checksums.json') == chosen['checkpoint_checksums_sha256']
        assert read(cp / 'mixture.json') == plan
        trajectory = read(cp / 'trajectory.json')
        logged = [json.loads(line) for line in (O / arm / 'training_metrics.jsonl').read_text().splitlines()]
        assert trajectory == logged
        assert [x['step'] for x in trajectory] == list(range(1, last + 1))
        ids = [i for x in trajectory for i in x['ids']]
        assert ids == [x['id'] for x in plan['entries']]
        assert len(ids) == len(set(ids))
        for e in plan['entries']:
            assert e['id'] in datasets[e['dataset']]['train']
        for i, x in enumerate(trajectory):
            assert x['base_frozen'] and x['before_sha256'] != x['after_sha256']
            assert math.isfinite(x['loss']) and math.isfinite(x['gradient_norm']) and x['gradient_norm'] > 0
            if i:
                assert x['before_sha256'] == trajectory[i - 1]['after_sha256']
        arms.append({'arm': arm, 'steps': last, 'unique_train_examples': len(ids), 'repeated_updates': 0,
                     'plan_sha256': sha(O / f'plan/{arm}.json'), 'trajectory_sha256': sha(cp / 'trajectory.json'),
                     'heldout_training_ids': [], 'base_frozen_all_updates': True})
    finals = {}
    for label in ('base', 'selected', 'evidence_only'):
        out = O / 'final_exam' / label
        completed = read(out / 'curriculum_exam_complete.json')
        assert completed['passed'] and completed['identity']['development_freeze_sha256'] == freeze_sha
        counts = {}
        for split in ('test', 'challenge'):
            directory = out / split
            identity = read(directory / 'evaluation_identity.json')
            assert identity == completed['identity']
            ident_sha = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
            scores = read(directory / 'scores.json')
            for d in ('stage4a', 'stage4c0'):
                expected = datasets[d][split] if d == 'stage4c0' or (split == 'test' and label != 'evidence_only') else {}
                files = {p.stem: p for p in (directory / d).glob('*.json')}
                assert set(files) == set(expected) == {x['id'] for x in scores[d]}
                for eid, p in files.items():
                    record = read(p)
                    assert record['id'] == eid and record['split'] == split and record['dataset'] == d
                    assert record['identity_sha256'] == ident_sha
                    assert record['input_file_sha256'] == sha(R / f'datasets/{d}/v1/{split}.jsonl')
                    assert math.isfinite(record['teacher_forced_loss'])
                    sha(p)
                counts[f'{split}/{d}'] = len(files)
        if label != 'evidence_only':
            historical = read(out / 'historical/scored.json')
            strict = read(out / 'historical/strict_contract.json')
            assert len(historical) == len(strict) == 32
            assert len({x['id'] for x in historical}) == 16
            assert {(x['id'], x['scale']) for x in historical} == {(x['id'], x['scale']) for x in strict}
            counts['historical_observations'] = 32
        if label != 'base':
            reload = read(out / 'adapter_reload_verified.json')
            assert reload['passed'] and all(reload['checks'].values())
        finals[label] = counts
    assert read(O / 'historical/regression.json')['passed']
    assert all(v == 0 for v in read(O / 'historical/additional-checks.json').values())
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    result = {'passed': True, 'completed_utc': stamp, 'slurm_cpu_job': os.environ['SLURM_JOB_ID'],
              'development_freeze_sha256': freeze_sha, 'protected': protected, 'checkpoints': checkpoint_reports,
              'arms': arms, 'final_output_counts': finals, 'historical_cpu_regression_passed': True,
              'new_optimizer_steps': 0, 'new_gpu_generations': 0}
    save('recovery_audit_20261002.json', result)
    save('final_isolation_audit.json', {'passed': True, 'completed_utc': stamp, 'arms': arms,
         'split_id_sets_disjoint': True, 'training_core_unchanged': True,
         'preflight_group_and_historical_leakage_checks_passed': True,
         'development_freeze_sha256': freeze_sha, 'final_outputs_bind_frozen_identity': True,
         'source_sha256': {str(p.relative_to(R)): h for p, h in cache.items()},
         'limitations': ['Recorded provenance and frozen split audits support isolation; lexical audits do not prove absence of all semantic overlap.']})
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
