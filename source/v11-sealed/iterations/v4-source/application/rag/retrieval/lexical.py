"""Deterministic BM25; C++, C#, dotted technical names remain whole tokens."""
from collections import Counter
import math
import re
STOP=frozenset('a an the with of to in on and for by is'.split())
def tokens(text):
    return tuple(t for t in re.findall(r'[\w]+(?:\+\+|#)?(?:[.-][\w]+)*',text.casefold()) if t not in STOP)

def rank(query, documents):
    q=set(tokens(query)); counts={k:Counter(tokens(v)) for k,v in documents.items()}
    n=len(counts)
    if not n: return []
    avg=sum(sum(c.values()) for c in counts.values())/n or 1
    df={t:sum(t in c for c in counts.values()) for t in q}
    scores=[]
    for k,c in counts.items():
        length=sum(c.values()); score=0.
        for t in sorted(q):
            f=c[t]
            if f: score+=math.log(1+(n-df[t]+.5)/(df[t]+.5))*f*2.2/(f+1.2*(.25+.75*length/avg))
        if score>0: scores.append((k,score))
    return sorted(scores,key=lambda x:(-x[1],x[0]))
