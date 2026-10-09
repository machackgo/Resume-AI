"""Stage 3J controlled Qwen run; frozen retrieval, unchanged model/output cap."""
import os,json,time,subprocess,importlib.metadata
from .prepare import ROOT,OUT,H,dump,sha
from .retrieve import messages
from ..retrieval import InformationNeed,NeedType
from ..reasoning.contract import validate

def load_rows(scale):return json.loads((OUT/(scale+'-prepared.json')).read_text())
def build_messages(row):
    q=row['case'];return messages(InformationNeed(NeedType.JOB_REQUIREMENT,q['requirement'],q['id']),q['components'],row['contexts']['component'])
def check_freeze():
    frozen=json.loads((OUT/'retrieval-freeze.json').read_text())['files']
    for p,h in frozen.items():assert sha(ROOT/p)==h,p
    return frozen

def main():
    assert os.getenv('SLURM_JOB_ID'),'Slurm required'
    check_freeze()
    import torch
    from transformers import AutoTokenizer,AutoModelForCausalLM,BitsAndBytesConfig,set_seed
    assert torch.cuda.is_available() and torch.cuda.device_count()==1
    run=OUT/('benchmark-'+os.environ['SLURM_JOB_ID']);run.mkdir(exist_ok=False);set_seed(42);start_total=time.perf_counter()
    bnb=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',bnb_4bit_use_double_quant=True,bnb_4bit_compute_dtype=torch.bfloat16)
    gen={'max_new_tokens':1536,'do_sample':False,'use_cache':True};modelpath=ROOT/'models/Qwen3.8-27B'
    config={'slurm_job_id':os.environ['SLURM_JOB_ID'],'model_path':str(modelpath.resolve()),'generation_overrides':gen,'seed':42,'thinking':False,'quantization':bnb.to_dict(),'dtype':'bfloat16',
       'dependencies':{p:importlib.metadata.version(p) for p in ('torch','transformers','accelerate','bitsandbytes','tokenizers')},
       'gpu':subprocess.check_output(['nvidia-smi','--query-gpu=name,uuid,memory.total,driver_version','--format=csv,noheader'],text=True),'status':'loading',
       'retrieval_config':json.loads((OUT/'config.json').read_text()),'source_files':{str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'rag/deep').glob('*.py'))},'requested_resources':{'gpu':'A30:1','cpus':8,'ram':'64G','maximum':'02:00:00','account':'cs541','partition':'academic'}}
    previous=json.loads((H/'benchmark-2332803/config.json').read_text())
    for k in ('model_path','generation_overrides','seed','thinking','quantization','dependencies'):assert config[k]==previous[k],k
    priorconfig=json.loads((ROOT/'results/stage3i/benchmark-2333661/config.json').read_text())
    for k in ('model_path','generation_overrides','seed','thinking','quantization','dependencies'):assert config[k]==priorconfig[k],k
    dump(run/'config.json',config);tok=AutoTokenizer.from_pretrained(modelpath,local_files_only=True)
    t=time.perf_counter();model=AutoModelForCausalLM.from_pretrained(modelpath,quantization_config=bnb,device_map='auto',dtype=torch.bfloat16,low_cpu_mem_usage=True,local_files_only=True);model.eval()
    assert {str(p.device) for p in model.parameters()}=={'cuda:0'}
    config.update(load_seconds=time.perf_counter()-t,model_config=model.config.to_dict(),architecture=type(model).__name__,generation_defaults=model.generation_config.to_dict(),gpu_free_after_load_bytes=torch.cuda.mem_get_info()[0],status='smoke');dump(run/'config.json',config)
    historical_path=ROOT/'results/stage3i/benchmark-2333661/raw.jsonl'
    prior=[json.loads(l) for l in historical_path.read_text().splitlines()]
    oldraw=[json.loads(l) for l in (H/'benchmark-2332803/raw.jsonl').read_text().splitlines()];controls={(r['scale'],r['id'],r['arm']):r for r in oldraw}
    def generate(row,phase):
        msg=build_messages(row);s=tok.apply_chat_template(msg,tokenize=False,add_generation_prompt=True,enable_thinking=False)
        inputs=tok(s,return_tensors='pt',add_special_tokens=False).to(model.device);n=inputs.input_ids.shape[1]
        assert n+1536<getattr(model.config,'text_config',model.config).max_position_embeddings
        torch.cuda.empty_cache();torch.cuda.reset_peak_memory_stats();torch.cuda.synchronize();t=time.perf_counter()
        with torch.inference_mode():out=model.generate(**inputs,**gen)
        torch.cuda.synchronize();elapsed=time.perf_counter()-t;ids=out[0,n:].tolist();ctx=row['contexts']['component'];control=controls[(row['scale'],row['case']['id'],'rag3')]
        ev=len(tok(json.dumps(ctx['groups'],ensure_ascii=True),add_special_tokens=False)['input_ids'])
        record=dict(run_id='stage3j/'+phase+'/'+row['scale']+'/'+row['case']['id'],phase=phase,scale=row['scale'],id=row['case']['id'],arm='component',messages=msg,rendered_prompt=s,input_tokens=n,text=tok.decode(ids,skip_special_tokens=True),raw_text=tok.decode(ids,skip_special_tokens=False),token_ids=ids,output_tokens=len(ids),total_tokens=n+len(ids),seconds=elapsed,tokens_per_second=len(ids)/elapsed,hit_token_limit=len(ids)>=1536,peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),peak_gpu_reserved_bytes=torch.cuda.max_memory_reserved(),evidence_groups=len(ctx['groups']),evidence_chunks=sum(len(g['evidence']) for g in ctx['groups']),evidence_tokens=ev,full_input_tokens=control['full_input_tokens'],full_evidence_tokens=control['full_evidence_tokens'],prompt_reduction_vs_full=1-n/control['full_input_tokens'],evidence_reduction_vs_full=1-ev/control['full_evidence_tokens'],prompt_change_vs_rag3=n/control['input_tokens']-1,prompt_change_vs_rag5=n/controls[(row['scale'],row['case']['id'],'rag5')]['input_tokens']-1)
        del out,inputs
        return record
    # Reuse previously validated smoke outputs; only the whole-text canary
    # gate was wrong. Citation acceptance is checked structurally.
    review=json.loads((OUT/"smoke-gate-review.json").read_text());assert review["passed"]
    prior_smoke_path=OUT/"benchmark-2334070/smoke.json"
    assert sha(prior_smoke_path)==review["source_sha256"]
    smoke=json.loads(prior_smoke_path.read_text())
    for record in smoke:
        record["reused_smoke"]=True
        record["reuse_source"]=str(prior_smoke_path.relative_to(ROOT))
        record["reuse_source_sha256"]=review["source_sha256"]
    # Fresh reload check under this allocation before primary inference.
    row=next(r for r in load_rows("SMALL") if r["case"]["id"]=="h06")
    raw=generate(row,"smoke_reload");q=row["case"]
    pred,v=validate(raw["text"],InformationNeed(NeedType.JOB_REQUIREMENT,q["requirement"],q["id"]),q["components"],row["contexts"]["component"])
    raw["validation"]=v;raw["reused_smoke"]=False;smoke.append(raw);dump(run/"smoke.json",smoke)
    assert v["json_valid"] and v["schema_valid"] and "unknown_or_foreign_id" not in v["errors"]
    print("RELOAD SMOKE",v,flush=True)
    config['status']='primary';dump(run/'config.json',config);check_freeze()
    with (run/'raw.jsonl').open('x') as stream:
        # Primary LARGE/XL first; SMALL/MEDIUM complete the scale regression.
        for scale in ('LARGE','XL'):
            for row in load_rows(scale):
                matches=[r for r in prior if r['scale']==scale and r['id']==row['case']['id'] and r['messages']==build_messages(row)]
                if matches:
                    # Exact prompt and controlled model/generation configuration:
                    # reuse immutable observations with explicit lineage, never
                    # treat historical latency as newly consumed GPU runtime.
                    raw=dict(matches[0]);raw.update(run_id='stage3j/primary/'+scale+'/'+row['case']['id'],reused_historical=True,reuse_source=str(historical_path.relative_to(ROOT)),reuse_source_sha256=sha(historical_path),reuse_run_id=matches[0]['run_id'])
                else:
                    raw=generate(row,'primary');raw['reused_historical']=False
                stream.write(json.dumps(raw)+'\n');stream.flush();print(scale,raw['id'],raw['input_tokens'],raw['output_tokens'],round(raw['seconds'],2),flush=True)
    config.update(reuse_policy='exact messages, unchanged model and controlled generation; historical time is not new GPU consumption',status='complete',total_seconds=time.perf_counter()-start_total,cases=32);dump(run/'config.json',config);check_freeze();print('COMPLETE',config['total_seconds'],flush=True)
if __name__=='__main__':main()
