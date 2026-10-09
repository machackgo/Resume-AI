"""One model load: infrastructure smoke, freeze, controlled scale experiment."""
import os,json,time,hashlib,subprocess,importlib.metadata,gc
from .prepare import ROOT,OUT,dump,sha,load_rows
from .dataset import SCALES
from .metrics import feasibility,report
from ..reasoning.run import build_messages

def freeze_files():
    paths=list((ROOT/'rag').rglob('*.py'))+list((ROOT/'rag/reasoning').glob('*.txt'))+[ROOT/'rag/reasoning/schema.json',ROOT/'tests/rag/test_scale.py',ROOT/'docs/stage3h_architecture.md']
    paths+=list(OUT.glob('*-prepared.json'))+list(OUT.glob('*-full.json'))+list(OUT.glob('*-corpus.json'))+[OUT/'dataset.json',OUT/'query-vectors.json']
    return {str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)}

def main():
    assert os.getenv('SLURM_JOB_ID'),'Slurm required'
    import torch
    from transformers import AutoTokenizer,AutoModelForCausalLM,BitsAndBytesConfig,set_seed
    assert torch.cuda.is_available() and torch.cuda.device_count()==1
    run=OUT/('benchmark-'+os.environ['SLURM_JOB_ID']);run.mkdir(exist_ok=False)
    set_seed(42);start_total=time.perf_counter()
    bnb=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',bnb_4bit_use_double_quant=True,bnb_4bit_compute_dtype=torch.bfloat16)
    gen={'max_new_tokens':1536,'do_sample':False,'use_cache':True};modelpath=ROOT/'models/Qwen3.8-27B'
    config={'slurm_job_id':os.environ['SLURM_JOB_ID'],'model_path':str(modelpath.resolve()),'generation_overrides':gen,'seed':42,'thinking':False,'quantization':bnb.to_dict(),
       'dependencies':{p:importlib.metadata.version(p) for p in ('torch','transformers','accelerate','bitsandbytes','tokenizers')},
       'gpu':subprocess.check_output(['nvidia-smi','--query-gpu=name,uuid,memory.total,driver_version','--format=csv,noheader'],text=True),'status':'loading'}
    previous=json.loads((ROOT/'results/stage3g/benchmark-2330445/config.json').read_text())
    for k in ('model_path','generation_overrides','seed','thinking','quantization','dependencies'):assert config[k]==previous[k],k
    dump(run/'config.json',config)
    tok=AutoTokenizer.from_pretrained(modelpath,local_files_only=True)
    t=time.perf_counter();model=AutoModelForCausalLM.from_pretrained(modelpath,quantization_config=bnb,device_map='auto',dtype=torch.bfloat16,low_cpu_mem_usage=True,local_files_only=True);model.eval()
    assert {str(p.device) for p in model.parameters()}=={'cuda:0'},'offload not permitted in controlled comparison'
    conf=getattr(model.config,'text_config',model.config);limit=conf.max_position_embeddings
    assert conf.layer_types.count('full_attention')*2*conf.num_key_value_heads*conf.head_dim*2==65536
    config.update(load_seconds=time.perf_counter()-t,model_config=model.config.to_dict(),architecture=type(model).__name__,generation_defaults=model.generation_config.to_dict(),
                  gpu_free_after_load_bytes=torch.cuda.mem_get_info()[0],model_gpu_allocated_bytes=torch.cuda.memory_allocated(),model_position_limit=limit,status='smoke')
    dump(run/'config.json',config)
    def render(row,arm):
        msg=build_messages(row,arm);s=tok.apply_chat_template(msg,tokenize=False,add_generation_prompt=True,enable_thinking=False)
        ids=tok(s,add_special_tokens=False)['input_ids']
        evidence=tok(json.dumps(row['contexts'][arm]['groups'],ensure_ascii=True),add_special_tokens=False)['input_ids']
        return msg,s,ids,len(evidence)
    def generate(row,arm,full_tokens,full_evidence):
        msg,s,ids,evtokens=render(row,arm);check=feasibility(len(ids),limit,config['gpu_free_after_load_bytes'])
        base={'scale':row['scale'],'id':row['case']['id'],'arm':arm,'input_tokens':len(ids),'evidence_tokens':evtokens,
              'full_input_tokens':full_tokens,'full_evidence_tokens':full_evidence,'evidence_chunks':sum(len(g['evidence']) for g in row['contexts'][arm]['groups']),
              'evidence_groups':len(row['contexts'][arm]['groups']),'prompt_reduction_vs_full':1-len(ids)/full_tokens,'evidence_reduction_vs_full':1-evtokens/full_evidence}
        if check['status']!='ATTEMPT':return None,dict(base,**check)
        inputs=tok(s,return_tensors='pt',add_special_tokens=False).to(model.device)
        torch.cuda.empty_cache();torch.cuda.reset_peak_memory_stats();torch.cuda.synchronize();t=time.perf_counter()
        try:
            with torch.inference_mode():out=model.generate(**inputs,**gen)
            torch.cuda.synchronize();elapsed=time.perf_counter()-t;output=out[0,len(ids):].tolist()
            record=dict(base,messages=msg,rendered_prompt=s,text=tok.decode(output,skip_special_tokens=True),raw_text=tok.decode(output,skip_special_tokens=False),token_ids=output,
                        output_tokens=len(output),total_tokens=len(ids)+len(output),seconds=elapsed,tokens_per_second=len(output)/elapsed,hit_token_limit=len(output)>=1536,
                        peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),peak_gpu_reserved_bytes=torch.cuda.max_memory_reserved())
            del out,inputs
            return record,dict(base,status='FEASIBLE',reason='actual_generation',seconds=elapsed)
        except torch.cuda.OutOfMemoryError as e:
            fail=dict(base,status='FULL_CONTEXT_NOT_FEASIBLE' if arm=='full' else 'RAG_CONTEXT_NOT_FEASIBLE',reason='observed_CUDA_OOM',error=str(e),seconds=time.perf_counter()-t,
                      peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),peak_gpu_reserved_bytes=torch.cuda.max_memory_reserved())
            del inputs;gc.collect();torch.cuda.empty_cache();return None,fail
    # Smoke validates execution, raw persistence and token decoding, not answer labels.
    small=load_rows('SMALL');smoke=[]
    for index in (0,10):
        r=small[index];_,_,fi,fe=render(r,'full');out,status=generate(r,'rag5',len(fi),fe)
        assert out is not None,status
        assert tok.decode(out['token_ids'],skip_special_tokens=True)==out['text'];smoke.append(out)
    dump(run/'smoke.json',smoke)
    frozen=freeze_files();dump(OUT/'freeze.json',{'version':'stage3h-freeze-v1','job_id':os.environ['SLURM_JOB_ID'],'after_smoke':True,'files':frozen})
    assert freeze_files()==frozen
    config.update(status='running',frozen_files=frozen);dump(run/'config.json',config)
    statuses=[];deadline=start_total+3*3600+45*60
    with (run/'raw.jsonl').open('x') as stream:
        for scale in SCALES:
            rows=load_rows(scale);scale_oom=False
            for index,row in enumerate(rows):
                _,_,fi,fe=render(row,'full')
                arms=['full','rag3','rag5'];arms=arms[index%3:]+arms[:index%3]
                for arm in arms:
                    if time.perf_counter()>deadline:
                        statuses.append({'scale':scale,'id':row['case']['id'],'arm':arm,'status':'NOT_RUN_TIME_BUDGET'});continue
                    if arm=='full' and scale_oom:
                        statuses.append({'scale':scale,'id':row['case']['id'],'arm':arm,'status':'NOT_ATTEMPTED_AFTER_SAME_SCALE_OOM','input_tokens':len(fi),'evidence_tokens':fe});continue
                    out,status=generate(row,arm,len(fi),fe);statuses.append(status);dump(run/'feasibility.json',statuses)
                    if out:
                        stream.write(json.dumps(out)+'\n');stream.flush();print(scale,out['id'],arm,out['input_tokens'],out['output_tokens'],round(out['seconds'],1),flush=True)
                    else:
                        print(scale,row['case']['id'],arm,status['status'],status.get('reason'),flush=True)
                        if arm=='full' and status.get('reason')=='observed_CUDA_OOM':scale_oom=True
                        if arm!='full':raise RuntimeError('RAG infeasible; preserve failure and diagnose')
    dump(run/'feasibility.json',statuses)
    report(run);config.update(status='complete',total_seconds=time.perf_counter()-start_total);dump(run/'config.json',config)
    assert freeze_files()==frozen
    print('COMPLETE',config['total_seconds'],flush=True)
if __name__=='__main__':main()
