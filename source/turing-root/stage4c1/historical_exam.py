"""Final-only Stage3J frozen contexts; fresh paired decode, no retrieval changes."""
import hashlib,json,time
from pathlib import Path
from stage4c1.evaluate import write,sha

def historical_exam(model,tok,out,identity):
    import torch
    from rag.deep.run import check_freeze,load_rows,build_messages
    from rag.scale.metrics import score_record,aggregate_scored
    from rag.reasoning.contract import validate
    from rag.retrieval import InformationNeed,NeedType
    root=Path.cwd();lock=root/'results/stage4c1/development_frozen.json'
    assert lock.exists() and identity['development_freeze_sha256']==sha(lock)
    check_freeze();model.eval()
    identity={**identity,'historical_decode':{'max_new_tokens':1536,'do_sample':False,'use_cache':True,'enable_thinking':False},
              'frozen_rag_sha256':sha(root/'results/stage3j/frozen-rag-configuration.json'),
              'prepared_hashes':{s:sha(root/f'results/stage3j/{s}-prepared.json') for s in ('LARGE','XL')},
              'baseline_policy':'Fresh baseline: current SDPA/loading and explicit EOS settings are not assumed identical to the historical runtime.'}
    if (out/'identity.json').exists():assert json.loads((out/'identity.json').read_text())==identity
    else:write(out/'identity.json',identity)
    binding=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()
    scored=[];strict=[]
    for scale in ('LARGE','XL'):
        for row in load_rows(scale):
            case=row['case'];dst=out/'raw'/f'{scale}_{case["id"]}.json'
            prompt=tok.apply_chat_template(build_messages(row),tokenize=False,add_generation_prompt=True,enable_thinking=False)
            ph=hashlib.sha256(prompt.encode()).hexdigest()
            if dst.exists():
                raw=json.loads(dst.read_text());assert raw['identity_sha256']==binding and raw['prompt_sha256']==ph
            else:
                batch=tok(prompt,add_special_tokens=False,return_tensors='pt').to('cuda');start=time.monotonic()
                with torch.inference_mode():
                    output=model.generate(**batch,do_sample=False,max_new_tokens=1536,use_cache=True,pad_token_id=tok.pad_token_id,eos_token_id=[tok.eos_token_id,tok.convert_tokens_to_ids('<|im_end|>')])
                ids=output[0,batch['input_ids'].shape[1]:].tolist()
                raw={'id':case['id'],'scale':scale,'arm':'component','identity_sha256':binding,'prompt_sha256':ph,
                     'text':tok.decode(ids,skip_special_tokens=True),'token_ids':ids,'seconds':time.monotonic()-start,
                     'termination':'eos' if ids and ids[-1] in (tok.eos_token_id,tok.convert_tokens_to_ids('<|im_end|>')) else 'length'}
                write(dst,raw);del batch,output
            scored.append(score_record(row,raw))
            pred,v=validate(raw['text'],InformationNeed(NeedType.JOB_REQUIREMENT,case['requirement'],case['id']),case['components'],row['contexts']['component'])
            strict.append({'id':case['id'],'scale':scale,'contract':v,'generation_complete':raw['termination']=='eos'})
            write(out/'progress.json',{'done':len(scored),'total':32,'last_id':case['id'],'scale':scale,'time':time.time()})
    write(out/'scored.json',scored);write(out/'strict_contract.json',strict)
    write(out/'metrics.json',{'by_scale':{s:aggregate_scored([r for r in scored if r['scale']==s]) for s in ('LARGE','XL')},
                             'combined_descriptive':aggregate_scored(scored),
                             'strict_contract_pass':sum(not x['contract']['errors'] and x['generation_complete'] for x in strict),
                             'n_observations':32,'n_unique_cases':16,
                             'limitation':'Scales reuse16 case IDs:32 observations are not32 independent cases. Frozen historical metric definitions preserved; strict contract failures reported separately.'})
    check_freeze()
