"""CPU-only token and diversity accounting; no truncation or training."""
import math,statistics
from collections import Counter,defaultdict
from .io import norm,digest

def distribution(xs):
    xs=sorted(xs)
    if not xs:return {'n':0,'mean':None,'median':None,'p50':None,'p90':None,'p95':None,'p99':None,'max':None,'sum':0}
    def p(q):return xs[max(0,math.ceil(len(xs)*q)-1)]
    return {'n':len(xs),'mean':statistics.mean(xs),'median':statistics.median(xs),'p50':p(.50),'p90':p(.90),'p95':p(.95),'p99':p(.99),'max':max(xs),'sum':sum(xs)}

def token_report(rows,tokenizer):
    # Frozen Stage4A template and loss-boundary helper: exact same inference prefix.
    from stage4a.data import tokenized
    groups=defaultdict(list);examples=[]
    for row in rows:
        encoded=tokenized(row,tokenizer)
        n=encoded['input_tokens']
        total=encoded['total_tokens'];target=encoded['target_tokens']
        if any(type(x) is not int for x in (n,total,target)) or not 0<n<total or target<=0 or n+target!=total or total!=len(encoded['input_ids']) or total!=len(encoded['labels']):raise ValueError('TOKEN_COUNT_INCONSISTENCY')
        if encoded['labels'][:n]!=[-100]*n:raise ValueError('prompt loss not masked')
        if encoded['labels'][n:]!=encoded['input_ids'][n:]:raise ValueError('assistant target not supervised exactly')
        item={k:encoded[k] for k in ['input_tokens','target_tokens','total_tokens']}
        item.update(example_id=row['metadata']['example_id'],task=row['metadata']['task'],split=row['metadata']['split'],messages_sha256=digest(row['messages']),assistant_text_sha256=digest(row['messages'][-1]['content']))
        groups[item['task']].append(item);examples.append(item)
    def stats(items):return {k:distribution([r[k] for r in items]) for k in ['input_tokens','target_tokens','total_tokens']}
    return {'method':'real local Qwen tokenizer and unchanged chat template, enable_thinking=False; assistant JSON plus one im_end; no truncation','by_task':{k:stats(v) for k,v in sorted(groups.items())},'overall':stats(examples),'examples':examples,'over_4608':[x for x in examples if x['total_tokens']>4608],'over_demonstrated_complete_4233':[x for x in examples if x['total_tokens']>4233]}

def diversity(rows):
    scalar=['task','split','scenario_family','template_family','candidate_archetype','job_archetype','role_family','seniority','fit_level','difficulty']
    tags=['technology_tags','action_tags','trust_tags'];out={}
    for key in scalar:out[key]=dict(sorted(Counter(str(r['metadata'].get(key,'MISSING')) for r in rows).items()))
    for key in tags:out[key]=dict(sorted(Counter(x for r in rows for x in r['metadata'].get(key,[])).items()))
    words=[norm(r['messages'][-1]['content']).split() for r in rows]
    out['lexical']={'unique_normalized_targets':len({digest(' '.join(w)) for w in words}),'unique_target_tokens':len({t for w in words for t in w}),'target_word_count':sum(map(len,words)),'limitation':'Whole JSON lexical counts contain schema vocabulary and do not establish stylistic diversity. Artifact-only near duplicates require separate review.'}
    return out

def grouped_leakage(rows):
    errors=[];tables=defaultdict(dict)
    grouping=['scenario_family','template_family','candidate_archetype','job_archetype','counterfactual_group','split_group']
    for r in rows:
        m=r['metadata'];split=m['split']
        if 'scenario' in r:
            inp=r['scenario']['input']
            for key,value in [('actual_candidate_id',inp['profile']['candidate_id']),('actual_job_id',inp['job']['job_id'])]:
                old=tables[key].get(value)
                if old is not None and old!=split:errors.append({'type':'ACTUAL_IDENTITY_SPLIT_LEAKAGE','key':key,'value':value,'splits':[old,split]})
                tables[key][value]=split
        for key in grouping:
            if key!='counterfactual_group' and (key not in m or not isinstance(m[key],str) or not m[key]):errors.append({'type':'MISSING_GROUP_METADATA','key':key})
        for key in grouping:
            v=m.get(key)
            if v is None:continue
            old=tables[key].get(v)
            if old is not None and old!=split:errors.append({'type':'GROUP_SPLIT_LEAKAGE','key':key,'value':v,'splits':[old,split]})
            tables[key][v]=split
        for key,value in [('input',r['messages'][1]['content']),('output',r['messages'][2]['content'])]:
            for mode,v in [('exact',value),('normalized',norm(value))]:
                h=digest(v);table=tables[key+'_'+mode];old=table.get(h)
                if old is not None and old!=split:errors.append({'type':'CROSS_SPLIT_DUPLICATE','key':key+'_'+mode,'splits':[old,split]})
                table[h]=split
    return {'passed':not errors,'known_prohibited_leakage':len(errors),'errors':errors,'group_dimensions':grouping,'limitation':'Group and lexical audits do not prove semantic independence; scenario-family quality requires expert review.'}
