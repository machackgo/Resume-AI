"""Actual model smoke checks; use the same Slurm CPU resource boundary."""
import json
import os
from pathlib import Path
from .local import LocalTransformerProvider
from .similarity import cosine

ROOT=Path(__file__).resolve().parents[2]

def main():
    if not os.environ.get('SLURM_JOB_ID'): raise RuntimeError('Slurm allocation required')
    reports=[]
    for spec in json.loads((ROOT/'results/stage3c/models.lock.json').read_text()):
        p=LocalTransformerProvider(spec,str(ROOT/'models/stage3c'))
        text='Implemented a Python service.'
        doc=p.embed_documents([text])[0]; query=p.embed_queries([text])[0]
        assert len(doc)==p.config.dimension==384
        assert abs(sum(v*v for v in doc)-1)<1e-5
        assert doc==p._embed([text],spec['document_prefix'])[0]
        assert query==p._embed([text],spec['query_prefix'])[0]
        assert (doc==query)==(spec['document_prefix']==spec['query_prefix'])
        assert p.embed_documents([])==()
        rejected=0
        for value in ('','word '*1000):
            try: p.embed_documents([value])
            except ValueError: rejected+=1
        assert rejected==2
        batched=p.embed_documents([text,'Unrelated sentence.'])[0]
        delta=max(abs(a-b) for a,b in zip(doc,batched))
        assert delta<1e-5
        reports.append({'model':spec['model'],'passed':True,'checks':8,
                        'query_document_cosine':cosine(doc,query),'batch_max_abs_delta':delta})
    (ROOT/'results/stage3c/local_integration.json').write_text(json.dumps(reports,indent=2)+'\n')

if __name__=='__main__': main()
