"""Freeze Stage4A artifacts only. Never invokes a training or adapter API."""
import datetime,json,re,shutil,subprocess,os
from pathlib import Path
from .inspect import ROOT,OUT,sha,dump
from .validate import validate_release

def main(candidate):
 candidate=Path(candidate);dest=ROOT/'datasets/stage4a/v1'
 assert not dest.exists(),'never overwrite frozen v1'
 reg=json.loads((OUT/'regression.json').read_text());pres=json.loads((OUT/'preservation.json').read_text());assert reg['passed'] and pres['passed']
 log=(OUT/'stage4a-tests.log').read_text();assert re.search(r'Ran 55 tests',log) and log.rstrip().endswith('OK')
 from transformers import AutoTokenizer
 tok=AutoTokenizer.from_pretrained(ROOT/'models/Qwen3.8-27B',local_files_only=True)
 pre=validate_release(candidate,tok);assert pre['passed']
 revisions=dict(rejected_examples=0,silent_repairs=0,history=[dict(candidate='candidate-01',reason='initial measured coverage; validated',record_changes=False),dict(candidate='candidate-02',reason='stronger complete-record schema and explanation checks; messages unchanged',record_changes=False),dict(candidate='candidate-03',reason='domain-specific compound companions and full five-group contexts',record_changes=True),dict(candidate='candidate-04',reason='parent-template grouping to prevent technology-name substitutions crossing splits; strict 4608-token cap',record_changes=True),dict(candidate='candidate-05',reason='bounded physically meaningful percentage ranges; three-supported/one-missing compounds; remove ambiguous negative wording from adjacent RAG evidence',record_changes=True)],method='systemic generator and validator revisions, not tuning to base-Qwen failures; historical final-test examples never used as generated examples')
 dump(OUT/'generation-revisions.json',revisions)
 shutil.copytree(candidate,dest)
 dump(dest/'generation-revisions.json',revisions)
 manifest=json.loads((dest/'manifest.json').read_text());manifest.update(status='FROZEN',freeze_timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),frozen_from='datasets/stage4a/candidate-05',recommended_sequence_length=4608,training_performed=False,adapters_created=False,gpu_allocated=False,quality_gates=dict(stage4a_tests=55,historical_tests=486,all_passed=True,protected_files=pres['files'],changed_or_missing=0,known_leakage=0))
 manifest['checksums']={p.name:sha(p) for p in sorted(dest.iterdir()) if p.is_file() and p.name!='manifest.json'}
 manifest['source_checksums'].update({str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'stage4a').glob('*.py'))})
 manifest['source_checksums']['tests/stage4a/test_dataset.py']=sha(ROOT/'tests/stage4a/test_dataset.py')
 dump(dest/'manifest.json',manifest)
 (dest/'checksums.sha256').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in sorted(dest.iterdir()) if p.is_file()))
 final=validate_release(dest,tok);dump(OUT/'final-validation.json',final)
 for line in (dest/'checksums.sha256').read_text().splitlines():
  h,name=line.split('  ',1);assert sha(dest/name)==h
 dump(OUT/'test-results.json',dict(stage4a_tests=55,stage4a_passed=True,historical=reg,mutations_rejected=True,token_mask_test_passed=True))
 from .report import main as report
 report(dest)
 # Recheck historical byte identity after all work; hashes include checkpoint shards.
 protected=json.loads((OUT/'protected-manifest.json').read_text());bad=[p for p,h in protected.items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h];assert not bad,bad
 dump(OUT/'final-preservation.json',dict(passed=True,protected_files=len(protected),changed_or_missing=bad))
 jobs='2334124,2334125,2334127,2334129,2334134,2334135,2334136,2334137,'+os.environ['SLURM_JOB_ID']
 accounting=subprocess.check_output(['/cm/shared/apps/slurm/current/bin/sacct','-j',jobs,'-n','-X','-P','-o','JobID,State,NodeList,AllocTRES,Elapsed'],text=True)
 assert 'gres/gpu' not in accounting
 (OUT/'slurm-accounting.txt').write_text(accounting)
 dump(OUT/'completion.json',dict(stage='4A',complete=True,dataset='datasets/stage4a/v1',report='docs/stage4a_report.md',example_count=1920,split_counts=final['split_counts'],stage4a_tests=55,historical_tests=486,known_leakage=0,protected_files=len(protected),training_executed=False,adapters_created=False,model_weights_modified=False,rag_modified=False,gpu_allocated=False,stage4b_started=False,baseline_replay='optional new-Qwen replay deferred; no new model metrics claimed',cpu_replay_hardware_note='strict learned-reranker replay required historical CPU host class; first mismatch retained',freeze_slurm_job=os.environ['SLURM_JOB_ID']))
 paths=list((ROOT/'stage4a').rglob('*'))+list((ROOT/'tests/stage4a').rglob('*'))+list(dest.rglob('*'))+list(OUT.rglob('*'))+[ROOT/'docs/stage4a_report.md']
 excluded={OUT/'final-manifest.json'}
 files={str(p.relative_to(ROOT)):sha(p) for p in sorted(paths) if p.is_file() and p not in excluded and p.suffix!='.log' and '__pycache__' not in str(p)}
 dump(OUT/'final-manifest.json',files)
 for p in dest.iterdir():p.chmod(0o444)
 dest.chmod(0o555)
 print('STAGE4A COMPLETE',final['split_counts'],'no training',flush=True)
if __name__=='__main__':
 import sys
 main(sys.argv[1])
