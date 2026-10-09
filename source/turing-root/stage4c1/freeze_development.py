"""Seal selected endpoints after validation decisions; cannot launch training."""
import json,subprocess,sys,os,datetime
from pathlib import Path
from stage4c1.evaluate import sha,write
R=Path.cwd()
def main(decision_path):
    lock=R/'results/stage4c1/development_frozen.json';assert not lock.exists()
    decision=json.loads(Path(decision_path).read_text())
    assert decision['development_frozen'] is True and decision['further_training_forbidden'] is True
    assert decision['selection_basis']=='VALIDATION_ONLY'
    assert decision['status'] in ('VALIDATION_ELIGIBLE','FAILED_VALIDATION_DESCRIPTIVE_ENDPOINT')
    assert decision['protocol_sha256']==sha(R/'docs/stage4c1_experiment_protocol.md')
    assert decision['reviewed_artifacts']
    for p,h in decision['reviewed_artifacts'].items():assert sha(R/p)==h
    for chosen in (decision,decision['evidence_only_comparator']):
        checkpoint=R/chosen['checkpoint'];assert sha(checkpoint/'checksums.json')==chosen['checkpoint_checksums_sha256']
        assert all(sha(checkpoint/p)==h for p,h in json.loads((checkpoint/'checksums.json').read_text()).items())
    active=subprocess.check_output(['/cm/shared/apps/slurm/current/bin/squeue','-h','-u',os.environ['USER'],'-o','%i %j %T'],text=True)
    assert not any('resume-stage4c1-train' in line for line in active.splitlines()),'cannot freeze while own training jobs remain queued/active'
    # Verify every actual training job recorded in this experiment has left Slurm.
    jobids={json.loads(p.read_text())['job'] for p in (R/'results/stage4c1').glob('*/environment_*.json') if p.parent.name in ('evidence_only','interleaved')}
    active_ids={line.split()[0] for line in active.splitlines() if line.strip()}
    assert not jobids&active_ids
    decision['frozen_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    decision['decision_source_sha256']=sha(Path(decision_path));decision['active_jobs_at_freeze']=active
    write(lock,decision);print(json.dumps({'development_frozen':True,'lock_sha256':sha(lock),'further_training_forbidden':True}))
if __name__=='__main__':main(sys.argv[1])
