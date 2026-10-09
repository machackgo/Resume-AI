"""Offline judgments measure discovery quality, never runtime support labels."""
import math

def metrics(ids,relevant,negative,texts=None,sources=None,k=5,scores=None):
    relevant=set(relevant); negative=set(negative)
    positions=[ids.index(x)+1 for x in relevant if x in ids]
    first=min(positions,default=float('inf'))
    neg=min((i+1 for i,x in enumerate(ids) if x in negative),default=float('inf'))
    dcg=sum(1/math.log2(i+2) for i,x in enumerate(ids[:k]) if x in relevant and ids.index(x)==i)
    ideal=sum(1/math.log2(i+2) for i in range(min(k,len(relevant))))
    out={f'recall_at_{j}':sum(x<=j for x in positions)/len(relevant) for j in (1,3,5)}
    out.update(mrr=0. if not positions else 1/first,ndcg_at_5=dcg/ideal if ideal else 0.,
               hard_negative_win_rate=float(first<neg),dangerous_neighbor_at_1=float(bool(ids) and ids[0] in negative),
               dangerous_neighbor_at_3=sum(x in negative for x in ids[:3])/max(1,len(ids[:3])),
               dangerous_query_at_3=float(any(x in negative for x in ids[:3])))
    if scores is not None:
        positive=max((scores.get(x,float('-inf')) for x in relevant),default=float('-inf'))
        negative_score=max((scores.get(x,float('-inf')) for x in negative),default=float('-inf'))
        out['hard_negative_win_rate']=float(positive>negative_score+1e-8)
    if texts is not None: out['duplicate_result_rate_at_5']=1-len(set(texts[:5]))/max(1,len(texts[:5])) if texts else 0.
    if sources is not None: out['unique_sources_at_5']=len(set(sources[:5]))
    return out

def aggregate(rows):
    return {k:sum(row[k] for row in rows)/len(rows) for k in rows[0]}
