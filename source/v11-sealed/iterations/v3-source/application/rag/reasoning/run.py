"""One Qwen load per process; original Stage 2, matched full-context and RAG arms."""
import json,os,sys,time,hashlib,subprocess,importlib.metadata
from pathlib import Path
from .prepare import ROOT,OUT,dump
from .contract import messages
from ..retrieval import InformationNeed,NeedType
from .evaluate import score_run

def build_messages(row,arm):
    case=row['case'];ctx=row['contexts']['full' if arm=='stage2' else arm]
    if arm!='stage2':return messages(InformationNeed(NeedType.JOB_REQUIREMENT,case['requirement'],case['id']),case['components'],ctx)
    sys.path.insert(0,str(ROOT/'eval/runners'))
    from prompt_contract import build_messages as original
    evidence=[{'id':e['evidence_id'],'text':json.dumps({k:v for k,v in e.items() if k!='evidence_id'})} for g in ctx['groups'] for e in g['evidence']]
    old={'job':'Required: '+case['requirement'],'evidence':evidence,'request':'Assess the proposed claims. Do not generate resume bullets.',
         'gold':{'claims':[{'id':'whole','text':case['requirement']}]+[{'id':a['id'],'text':a['claim']} for a in case['components']]}}
    return original(old,json.loads((ROOT/'eval/schemas/analysis_v1.json').read_text()),['requirement'],ROOT/'eval/prompts/grounded_v3')

def frozen_files():
    paths=list((ROOT/'rag/reasoning').glob('*.py'))+list((ROOT/'rag/reasoning').glob('*.json'))+list((ROOT/'rag/reasoning').glob('*.txt'))+[ROOT/'fixtures/rag/reasoning_eval/stage3g_v1.json',OUT/'prepared.json',OUT/'query-vectors.json',ROOT/'eval/prompts/grounded_v3/system.txt',ROOT/'eval/prompts/grounded_v3/task.txt',ROOT/'eval/schemas/analysis_v1.json']+list((ROOT/'tests/rag').glob('test_reasoning*.py'))
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

def main(phase):
    if not os.getenv('SLURM_JOB_ID'):raise RuntimeError('Qwen requires Slurm GPU allocation')
    run=OUT/(phase+'-'+os.environ['SLURM_JOB_ID']);run.mkdir(exist_ok=False)
    if phase=='benchmark':
        frozen=json.loads((OUT/'freeze_v2.json').read_text())
        for p,h in frozen.items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
    (run/'prepared.json').write_bytes((OUT/'prepared.json').read_bytes())
    rows=json.loads((run/'prepared.json').read_text())
    if phase=='smoke':rows=[r for r in rows if r['case']['id'] in ('direct_api','compound_four_of_six','injection_role','verified_exact','empty')]
    import torch
    from transformers import AutoTokenizer,AutoModelForCausalLM,BitsAndBytesConfig,set_seed
    if not torch.cuda.is_available() or torch.cuda.device_count()!=1:raise RuntimeError('Expected exactly one allocated GPU')
    set_seed(42)
    # Embedding preparation is a separate process; retain Stage 2 Torch generation settings.
    bnb=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',bnb_4bit_use_double_quant=True,bnb_4bit_compute_dtype=torch.bfloat16)
    gen={'max_new_tokens':1536,'do_sample':False,'use_cache':True}
    modelpath=ROOT/'models/Qwen3.8-27B'
    cfg={'slurm_job_id':os.environ['SLURM_JOB_ID'],'model_path':str(modelpath.resolve()),'quantization':bnb.to_dict(),'dtype':'bfloat16','device_map_requested':'auto','generation_overrides':gen,'thinking':False,'seed':42,'prompt_version':'stage3g-v2','context_version':'stage3g-v2','phase':phase,
        'dependencies':{p:importlib.metadata.version(p) for p in ('torch','transformers','accelerate','bitsandbytes','tokenizers')},
        'gpu':subprocess.check_output(['nvidia-smi','--query-gpu=name,uuid,memory.total,driver_version','--format=csv,noheader'],text=True),'files':frozen_files(),'status':'loading'}
    control=json.loads((ROOT/'results/prompt_engineered/stage2_control.json').read_text())
    for k in ('model_path','quantization','generation_overrides','seed','thinking'):assert cfg[k]==control['fixed_config'][k],k
    for k,v in control['fixed_config']['dependencies'].items():assert cfg['dependencies'][k]==v,k
    dump(run/'config.json',cfg);start_total=time.perf_counter()
    tok=AutoTokenizer.from_pretrained(modelpath,local_files_only=True)
    start=time.perf_counter();model=AutoModelForCausalLM.from_pretrained(modelpath,quantization_config=bnb,device_map='auto',dtype=torch.bfloat16,low_cpu_mem_usage=True,local_files_only=True);model.eval()
    cfg.update(load_seconds=time.perf_counter()-start,architecture=type(model).__name__,parameter_devices=sorted({str(p.device) for p in model.parameters()}),model_config=model.config.to_dict(),device_map={k:str(v) for k,v in getattr(model,'hf_device_map',{}).items()},generation_defaults=model.generation_config.to_dict(),status='running');dump(run/'config.json',cfg)
    jobs=[]
    for index,row in enumerate(rows):
        arms=['stage2','full','rag5'];arms=arms[index%3:]+arms[:index%3]
        if phase=='benchmark' and row['case']['category'] in ('compound','distractors','rank5','injection','corroboration'):arms+=['rag1','rag3']
        if phase=='smoke':arms=['rag5']
        jobs.extend((row,a) for a in arms)
    prompt_cache={}
    with (run/'raw.jsonl').open('x') as raw:
        for row,arm in jobs:
            msg=build_messages(row,arm);rendered=tok.apply_chat_template(msg,tokenize=False,add_generation_prompt=True,enable_thinking=False)
            if rendered in prompt_cache:
                cached=prompt_cache[rendered]
                record=dict(cached,arm=arm,reused_from_arm=cached['arm'],seconds=0.,tokens_per_second=None)
                raw.write(json.dumps(record)+'\n');raw.flush();print(record['id'],arm,'exact-prompt reuse from',cached['arm'],flush=True);continue
            inputs=tok(rendered,return_tensors='pt',add_special_tokens=False).to(model.device)
            if inputs.input_ids.shape[1]+gen['max_new_tokens']>getattr(model.config,'text_config',model.config).max_position_embeddings:raise RuntimeError('context overflow; no truncation')
            torch.cuda.reset_peak_memory_stats();torch.cuda.synchronize();start=time.perf_counter()
            with torch.inference_mode():result=model.generate(**inputs,**gen)
            torch.cuda.synchronize();elapsed=time.perf_counter()-start
            ids=result[0,inputs.input_ids.shape[1]:]
            record={'id':row['case']['id'],'arm':arm,'messages':msg,'rendered_prompt':rendered,'text':tok.decode(ids,skip_special_tokens=True),'raw_text':tok.decode(ids,skip_special_tokens=False),'token_ids':ids.tolist(),'input_tokens':inputs.input_ids.shape[1],'output_tokens':len(ids),'seconds':elapsed,'tokens_per_second':len(ids)/elapsed,'hit_token_limit':len(ids)>=gen['max_new_tokens'],'peak_gpu_allocated_bytes':torch.cuda.max_memory_allocated(),'peak_gpu_reserved_bytes':torch.cuda.max_memory_reserved()}
            prompt_cache[rendered]=record
            raw.write(json.dumps(record)+'\n');raw.flush();print(record['id'],arm,len(ids),round(elapsed,2),flush=True)
    cfg.update(status='complete',total_seconds=time.perf_counter()-start_total,cases=len(jobs));dump(run/'config.json',cfg)
    print(json.dumps(score_run(run),indent=2),flush=True)
if __name__=='__main__':main(sys.argv[1])
