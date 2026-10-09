import argparse,datetime,hashlib,importlib.metadata,json,os,pathlib,random,shutil,subprocess,sys,time,traceback
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'eval/metrics'))
from score import score,aggregate

def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run-id',required=True);ap.add_argument('--model',default=str(ROOT/'models/Qwen3.8-27B'));a=ap.parse_args()
    if not os.getenv('SLURM_JOB_ID'):raise RuntimeError('GPU evaluation requires Slurm allocation')
    out=ROOT/'results/baseline'/a.run_id;out.mkdir(parents=True,exist_ok=False)
    import torch
    from transformers import AutoTokenizer,AutoModelForCausalLM,BitsAndBytesConfig,set_seed
    if not torch.cuda.is_available():raise RuntimeError('Slurm job has no CUDA device')
    set_seed(42);random.seed(42)
    data=json.loads((ROOT/'eval/datasets/resume_v1.json').read_text());schema=json.loads((ROOT/'eval/schemas/analysis_v1.json').read_text());prompt=(ROOT/'eval/prompts/base_v1.txt').read_text()
    vocabulary=sorted({s for c in data['cases'] for k in ['requirements','skills'] for s in c['gold'][k]})
    bnb=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',bnb_4bit_use_double_quant=True,bnb_4bit_compute_dtype=torch.bfloat16)
    gen={'max_new_tokens':1536,'do_sample':False,'use_cache':True}
    cfg={'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'model':'Qwen/Qwen3.8-27B (local README identity)','model_path':str(pathlib.Path(a.model).resolve()),'quantization':bnb.to_dict(),'generation_overrides':gen,'dtype':'bfloat16','device_map_requested':'auto','seed':42,'thinking':False,'reasoning_effort':None,'prompt_version':'base-v1','dataset_version':data['version'],'slurm_job_id':os.environ['SLURM_JOB_ID'],'python':sys.version,'dependencies':{p:importlib.metadata.version(p) for p in ['torch','transformers','accelerate','bitsandbytes','tokenizers']},'cuda':torch.version.cuda,'gpus':subprocess.check_output(['nvidia-smi','--query-gpu=name,uuid,memory.total,driver_version','--format=csv,noheader'],text=True),'git_commit':None,'files':{str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'eval').rglob('*') if p.is_file() and '__pycache__' not in str(p)},'model_metadata_hashes':{p.name:sha(p) for p in pathlib.Path(a.model).glob('*') if p.is_file() and p.suffix in ['.json','.jinja','.md']},'weight_manifest':[{'name':p.name,'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns} for p in pathlib.Path(a.model).glob('*.safetensors')],'status':'loading'}
    if shutil.which('git'):
        rev=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True)
        if rev.returncode==0:cfg['git_commit']=rev.stdout.strip()
    cfg['slurm_step_id']=os.getenv('SLURM_STEP_ID')
    cfg['download_revision']=(pathlib.Path(a.model)/'.cache/huggingface/download/config.json.metadata').read_text().splitlines()[0]
    shutil.copytree(ROOT/'eval',out/'eval_snapshot',ignore=shutil.ignore_patterns('__pycache__'))
    dump(out/'config.json',cfg)
    try:
        tok=AutoTokenizer.from_pretrained(a.model,local_files_only=True)
        start=time.perf_counter();model=AutoModelForCausalLM.from_pretrained(a.model,quantization_config=bnb,device_map='auto',dtype=torch.bfloat16,low_cpu_mem_usage=True,local_files_only=True);model.eval()
        cfg.update(load_seconds=time.perf_counter()-start,model_class=type(model).__name__,device_map={k:str(v) for k,v in getattr(model,'hf_device_map',{}).items()},parameter_devices=sorted({str(p.device) for p in model.parameters()}),generation_defaults=model.generation_config.to_dict(),tokenizer_class=type(tok).__name__,status='running');dump(out/'config.json',cfg)
        rows=[]
        with (out/'raw_outputs.jsonl').open('w') as raw,(out/'predictions.jsonl').open('w') as predictions:
            for c in data['cases']:
                payload={k:c[k] for k in ['id','job','evidence','request']};payload['proposed_claims']=[{'id':x['id'],'text':x['text']} for x in c['gold']['claims']];payload['vocabulary']=vocabulary;payload['schema']=schema
                messages=[{'role':'system','content':prompt},{'role':'user','content':json.dumps(payload)}]
                rendered=tok.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=False)
                inputs=tok(rendered,return_tensors='pt',add_special_tokens=False).to(model.device)
                for i in range(torch.cuda.device_count()):torch.cuda.reset_peak_memory_stats(i)
                torch.cuda.synchronize();start=time.perf_counter()
                with torch.inference_mode():output=model.generate(**inputs,**gen)
                torch.cuda.synchronize();elapsed=time.perf_counter()-start
                ids=output[0,inputs.input_ids.shape[1]:];decoded=tok.decode(ids,skip_special_tokens=True)
                record={'id':c['id'],'messages':messages,'rendered_prompt':rendered,'raw_text':tok.decode(ids,skip_special_tokens=False),'text':decoded,'token_ids':ids.tolist(),'input_tokens':inputs.input_ids.shape[1],'output_tokens':len(ids),'seconds':elapsed,'tokens_per_second':len(ids)/elapsed,'hit_token_limit':len(ids)>=gen['max_new_tokens'],'peak_gpu_bytes':[torch.cuda.max_memory_allocated(i) for i in range(torch.cuda.device_count())]}
                raw.write(json.dumps(record)+'\n');raw.flush()
                try:p=json.loads(decoded);error=None
                except json.JSONDecodeError as e:p=None;error=str(e)
                predictions.write(json.dumps({'id':c['id'],'prediction':p,'parse_error':error})+'\n');predictions.flush()
                row=score(c,p,schema);row['json_valid']=error is None;row['id']=c['id'];rows.append(row);dump(out/'metrics.json',aggregate(rows));print(c['id'],len(ids),round(elapsed,2),'schema',row['schema_valid'],flush=True)
        metrics=aggregate(rows);cfg['status']='complete';dump(out/'config.json',cfg)
        (out/'summary.md').write_text('# Untouched NF4 base-model baseline\n\n'+json.dumps(metrics['deterministic'],indent=2)+'\n\nFree-text semantic audit is separate. No RAG, adapters, fine-tuning, or few-shot examples. Thinking disabled explicitly for this baseline; this differs from legacy reasoning probes.\n')
    except Exception:
        cfg['status']='failed';cfg['error']=traceback.format_exc();dump(out/'config.json',cfg);raise
if __name__=='__main__':main()
