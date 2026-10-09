"""Fresh-process CPU load and memory probe; no embedding model is loaded."""
import json
import os
from pathlib import Path
import resource
import sys
import time
from .prepare import ROOT, OUT
from .cross_encoder import LocalCrossEncoder
from .input_builder import build_input
from ..retrieval import InformationNeed, NeedType

def main(index):
    if not os.environ.get('SLURM_JOB_ID'): raise RuntimeError('Slurm allocation required')
    spec=json.loads((OUT/'models.lock.json').read_text())[index]
    start=time.perf_counter()
    provider=LocalCrossEncoder(spec,ROOT/'models/stage3f')
    seconds=time.perf_counter()-start
    pairs=[build_input(InformationNeed(NeedType.JOB_REQUIREMENT,'Built production REST APIs','resource-probe'),
            'Implemented FastAPI endpoints for a production inference service.')]*20
    scores=provider.score(pairs)
    assert len(scores)==20
    result={'model':spec['model'],'revision':spec['revision'],'constructor_seconds_including_framework_imports':seconds,
            'weight_tokenizer_load_seconds':provider.load_seconds,
            'peak_rss_kib_after_20_pairs':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'parameters':provider.parameter_count,'config':provider.config.identity,
            'slurm_job_id':os.environ['SLURM_JOB_ID'],
            'note':'Fresh Python process; shared filesystem page caches may already be warm. No embedding/Qwen model loaded. CPU float32; no GPU requested.'}
    (OUT/('resources-'+str(index)+'.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__': main(int(sys.argv[1]))
