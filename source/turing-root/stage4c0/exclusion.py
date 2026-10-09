"""Read-only historical fingerprint audit. Never sends benchmark text to teachers."""
from pathlib import Path
from .io import norm,digest,read_jsonl,sha_file

def shingles(text,n=5):
    ws=norm(text).split();return {tuple(ws[i:i+n]) for i in range(max(0,len(ws)-n+1))}
def factual_input_strings(inp):
    yield inp['job']['text']
    yield from (e['content'] for e in inp['rag'])
    yield from (f['value'] for f in inp['profile']['facts'] if len(f['value'].split())>=5)
def historical_audit(rows,root):
    from stage4a.validate import historical_index
    h=historical_index();history=set(h['normalized_texts']);stage4a=set()
    test=root/'datasets/stage4a/v1/test.jsonl'
    # Extract meaningful context strings, not schema boilerplate or one-word labels.
    import json
    def walk(x):
        if isinstance(x,dict):
            for k,v in x.items():
                if k in ('requirement','claim','content','text') and isinstance(v,str) and len(v.split())>=5:stage4a.add(norm(v))
                else:walk(v)
        elif isinstance(x,list):
            for v in x:walk(v)
    for r in read_jsonl(test):walk(json.loads(r['messages'][1]['content']))
    if not history or not stage4a or not h['files']:raise ValueError('HISTORICAL_FINGERPRINT_INVENTORY_EMPTY')
    pools={'historical_stage3':history,'stage4a_test':stage4a};result={}
    for name,strings in pools.items():
        signatures=[shingles(s) for s in strings if len(s.split())>=8];matches=[];maximum=0
        for r in rows:
            for s in factual_input_strings(r['scenario']['input']):
                ns=norm(s);a=shingles(s)
                if ns in strings:matches.append({'example_id':r['metadata']['example_id'],'type':'EXACT_NORMALIZED','text_sha256':digest(ns)})
                if len(ns.split())<8:continue
                for b in signatures:
                    score=len(a&b)/len(a|b) if a|b else 0;maximum=max(maximum,score)
                    if score>=.85:matches.append({'example_id':r['metadata']['example_id'],'type':'HIGH_SHINGLE_OVERLAP','jaccard':score,'text_sha256':digest(ns)})
        result[name]={'fingerprints':len(strings),'matches':matches,'maximum_fivegram_jaccard':maximum,'passed':not matches}
    return {'passed':all(x['passed'] for x in result.values()),'audits':result,'sources':{**h['files'],str(test.relative_to(root)):sha_file(test)},'policy':'Read-only fingerprints; no historical output targets or cases supplied to teacher. Exact input-context and 0.85 fivegram Jaccard hard gate. Generic schema/short labels excluded.','limitation':'Lexical screening cannot prove semantic independence; templates and lineage are separately audited.'}

def near_duplicate_artifacts(rows):
    from .grounding import claims
    items=[];pairs=[]
    for r in rows:
        import json
        out=json.loads(r['messages'][-1]['content'])
        text=' '.join(c['text'] for _,c in claims(out['artifact']) if len(c['text'].split())>=6)
        a=shingles(text)
        for old,b in items:
            if not a or not b:continue
            score=len(a&b)/len(a|b)
            if score>=.80:pairs.append({'a':old['metadata']['example_id'],'b':r['metadata']['example_id'],'jaccard':score,'cross_split':old['metadata']['split']!=r['metadata']['split'],'same_family':old['metadata']['scenario_family']==r['metadata']['scenario_family']})
        items.append((r,a))
    return {'threshold':.8,'pairs':pairs,'cross_split_review_required':sum(x['cross_split'] for x in pairs),'policy':'Counterfactual pairs may legitimately be close but must remain same split; other repeated artifact patterns require expert disposition.'}
