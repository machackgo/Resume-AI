"""Inspect an empty meta-device architecture; no weights, adapters or optimizer."""
import json,inspect
from collections import Counter
from transformers import AutoConfig,AutoModelForCausalLM
from accelerate import init_empty_weights
from .inspect import ROOT,OUT,dump,sha

def main():
 config=AutoConfig.from_pretrained(ROOT/'models/Qwen3.8-27B',local_files_only=True)
 with init_empty_weights():model=AutoModelForCausalLM.from_config(config)
 assert all(p.device.type=='meta' for p in model.parameters())
 modules={name:dict(type=type(m).__name__,shape=list(m.weight.shape)) for name,m in model.named_modules() if type(m).__name__=='Linear' and any(x in name for x in ['self_attn.','linear_attn.','mlp.'])}
 base=sum(p.numel() for p in model.parameters());header=json.loads((OUT/'architecture.json').read_text());assert base==header['text_parameters'],(base,header['text_parameters'])
 assert len(modules)==len(header['projection_shapes'])
 choices=[]
 for family in ['full_attention_only','hybrid_attention','hybrid_attention_and_mlp']:
  targets={k:v for k,v in modules.items() if family=='hybrid_attention_and_mlp' or '.mlp.' not in k and (family=='hybrid_attention' or '.self_attn.' in k)}
  for r in [8,16,32]:
   n=sum(r*sum(v['shape']) for v in targets.values());choices.append(dict(family=family,rank=r,parameters=n,percent_base=100*n/base,module_count=len(targets),target_modules=sorted(targets)))
 dump(OUT/'runtime-architecture.json',dict(class_name=type(model).__name__,construction='accelerate.init_empty_weights; meta device only; no checkpoint tensors read',base_parameters=base,all_parameters_on_meta=True,modules=modules,candidates=choices,source_file=inspect.getfile(type(model)),source_sha256=sha(__import__('pathlib').Path(inspect.getfile(type(model))))))
 print('META ARCHITECTURE VERIFIED',base,len(modules),flush=True)
if __name__=='__main__':main()
