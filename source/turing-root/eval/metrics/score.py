"""Dependency-free deterministic scoring; free-text semantics require separate review."""
import json

def valid(x,s):
    t=s['type']
    if t=='object':
        return isinstance(x,dict) and set(x)==set(s['required']) and all(valid(x[k],v) for k,v in s['properties'].items())
    if t=='array':
        return isinstance(x,list) and len({json.dumps(v,sort_keys=True) for v in x})==len(x) and all(valid(v,s['items']) for v in x)
    return isinstance(x,str) and ('enum' not in s or x in s['enum'])

def prf(pred,gold):
    p,g=set(pred),set(gold); tp=len(p&g)
    precision=tp/len(p) if p else (1.0 if not g else 0.0)
    recall=tp/len(g) if g else 1.0
    return dict(tp=tp,fp=len(p-g),fn=len(g-p),precision=precision,recall=recall,f1=2*precision*recall/(precision+recall) if precision+recall else 0.)

def score(case,p,schema):
    ok=valid(p,schema)
    if not ok: p={}
    g=case['gold']; result={'schema_valid':ok}
    for key in ['requirements','skills']:
        result[key]=prf(p.get(key,[]),g[key])
    missing=[m['requirement'] for m in g['matches'] if m['label']!='SUPPORTED']
    result['missing_requirements']=prf(p.get('missing_requirements',[]),missing)
    for key,idkey in [('matches','requirement'),('claims','id')]:
        items=p.get(key,[]); lookup={m[idkey]:m for m in items}
        gold={m[idkey]:m for m in g[key]}
        denom=len(gold)+sum(k not in gold for k in lookup)
        # Duplicate IDs invalidate semantic structure, even if array objects differ.
        unique=len(lookup)==len(items)
        result[key+'_label_accuracy']=sum(unique and lookup.get(k,{}).get('label')==v['label'] for k,v in gold.items())/denom
        result[key+'_attribution_accuracy']=sum(unique and k in lookup and set(lookup[k]['evidence_ids'])==set(v['evidence_ids']) for k,v in gold.items())/denom
    claims={c['id']:c for c in g['claims']}; bullets=p.get('bullets',[])
    cited=[c for b in bullets for c in b['claim_ids']]
    bad=sum(c not in claims or claims[c]['label']!='SUPPORTED' for c in cited)
    grounded=0; covered=set()
    for b in bullets:
        ids=b['claim_ids']; ev=set(b['evidence_ids'])
        good=bool(ids) and all(c in claims and claims[c]['label']=='SUPPORTED' for c in ids)
        expected=set(e for c in ids if c in claims for e in claims[c]['evidence_ids'])
        good=good and ev==expected
        grounded+=int(good)
        if good:
            covered.update(m['requirement'] for m in g['matches'] if m['label']=='SUPPORTED' and set(m['evidence_ids'])<=ev)
    result.update(bullet_count=len(bullets),claim_assertion_count=len(cited),unsupported_claim_count=bad,unsupported_claim_rate=bad/len(cited) if cited else None,grounded_bullet_count=grounded,grounded_bullet_rate=grounded/len(bullets) if bullets else None,job_requirement_coverage_proxy=len(covered)/len(g['requirements']),bullet_claim_selection=prf(cited,g['bullets']),refusal=prf(p.get('refused_claim_ids',[]),[c['id'] for c in g['claims'] if c['label']!='SUPPORTED']))
    return result

def aggregate(rows):
    n=len(rows); means={k:sum(r[k] for r in rows)/n for k in ['matches_label_accuracy','claims_label_accuracy','matches_attribution_accuracy','claims_attribution_accuracy','job_requirement_coverage_proxy']}
    means['json_valid_rate']=sum(r.get('json_valid',r['schema_valid']) for r in rows)/n
    means['schema_valid_rate']=sum(r['schema_valid'] for r in rows)/n
    for k in ['requirements','skills','missing_requirements','bullet_claim_selection','refusal']:
        tp,fp,fn=[sum(r[k][v] for r in rows) for v in ['tp','fp','fn']]
        p=tp/(tp+fp) if tp+fp else 0; re=tp/(tp+fn) if tp+fn else 0
        means[k]={'tp':tp,'fp':fp,'fn':fn,'precision':p,'recall':re,'f1':2*p*re/(p+re) if p+re else 0}
    for k in ['bullet_count','grounded_bullet_count','claim_assertion_count','unsupported_claim_count']:means[k]=sum(r[k] for r in rows)
    means['grounded_bullet_rate']=means['grounded_bullet_count']/means['bullet_count'] if means['bullet_count'] else None
    means['unsupported_claim_rate']=means['unsupported_claim_count']/means['claim_assertion_count'] if means['claim_assertion_count'] else None
    return {'case_count':n,'deterministic':means,'subjective':{'free_text_hallucination_rate':None,'status':'Requires manual semantic audit; citation metrics do not verify text entailment.'},'per_case':rows}
