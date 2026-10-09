"""Measure saved candidate outputs; never load model weights or accept examples."""
import json,sys
from pathlib import Path
from transformers import AutoTokenizer
from .io import read_json,read_jsonl,sha_file,write_json
from .pipeline import messages
from .analysis import token_report

run=Path(sys.argv[1]);out=Path(sys.argv[2]);model=Path('models/Qwen3.8-27B')
tok=AutoTokenizer.from_pretrained(model,local_files_only=True);rows=[]
for r in read_jsonl(run/'registry.jsonl'):
    p=run/'teacher'/(r['example_id']+'.json')
    if p.exists():
        s=r['scenario'];target=read_json(p)['output']
        rows.append({'messages':messages(s,target),'metadata':{'example_id':r['example_id'],'task':s['input']['task'],'split':s['split']}})
report=token_report(rows,tok)
report['tokenizer_files']={str(p):sha_file(p) for p in model.iterdir() if p.is_file() and ('token' in p.name or p.name in ['vocab.json','merges.txt','chat_template.jinja'])}
report['tokenizer_class']=type(tok).__name__;report['model_weights_loaded']=False
write_json(out,report)
print(json.dumps({'n':len(rows),'total_tokens':report['overall']['total_tokens'],'over4233':len(report['over_demonstrated_complete_4233']),'over4608':len(report['over_4608'])}),flush=True)
