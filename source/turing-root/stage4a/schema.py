def schema():
 string={'type':'string','minLength':1};strings={'type':'array','items':string}
 meta={k:string for k in ['example_id','scenario_id','scenario_family','template_family','expected_label','difficulty','generator_version','candidate']}
 meta['expected_label']={'enum':['SUPPORTED','PARTIALLY_SUPPORTED','UNKNOWN','UNSUPPORTED']}
 meta['difficulty']={'enum':['EASY','MEDIUM','HARD','ADVERSARIAL']}
 meta.update(split={'enum':['train','validation','test']},variant={'type':'integer','minimum':0,'maximum':7},**{k:strings for k in ['domain_tags','action_tags','trust_tags']},**{k:{'type':'boolean'} for k in ['compound','numeric','hard_negative','security','duplicate_lineage','independent_corroboration']})
 return {'$schema':'https://json-schema.org/draft/2020-12/schema','title':'Stage4A v1 supervised record','type':'object','additionalProperties':False,'required':['metadata','messages','oracle'],'properties':{'metadata':{'type':'object','additionalProperties':False,'required':list(meta),'properties':meta},'messages':{'type':'array','minItems':3,'maxItems':3,'items':{'type':'object','additionalProperties':False,'required':['role','content'],'properties':{'role':{'enum':['system','user','assistant']},'content':string}}},'oracle':{'type':'object','additionalProperties':False,'required':['spec','facts'],'properties':{'spec':{'type':'object'},'facts':{'type':'array','items':{'type':'object'}}}}},'description':'oracle and metadata NEVER enter model messages; semantic validation further restricts every field to the authored catalog. Assistant JSON is validated against target-schema.json.'}

def conforms(x,s):
 if 'enum' in s and x not in s['enum']:return False
 t=s.get('type')
 if t=='object':
  if not isinstance(x,dict):return False
  if not set(s.get('required',[]))<=set(x):return False
  if s.get('additionalProperties') is False and not set(x)<=set(s.get('properties',{})):return False
  return all(conforms(x[k],v) for k,v in s.get('properties',{}).items() if k in x)
 if t=='array':return isinstance(x,list) and s.get('minItems',0)<=len(x)<=s.get('maxItems',10**9) and all(conforms(v,s['items']) for v in x)
 if t=='string':return isinstance(x,str) and len(x)>=s.get('minLength',0)
 if t=='integer':return type(x)==int and s.get('minimum',-10**9)<=x<=s.get('maximum',10**9)
 if t=='boolean':return type(x)==bool
 return t is None
