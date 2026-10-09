def rrf(rankings, constant=60):
    if type(constant) is not int or constant<1: raise ValueError('RRF constant')
    scores={}
    for ranking in rankings:
        if len(ranking)!=len(set(ranking)): raise ValueError('duplicate ranking IDs')
        for i,key in enumerate(ranking,1): scores[key]=scores.get(key,0.)+1/(constant+i)
    return sorted(scores.items(),key=lambda x:(-x[1],x[0]))
