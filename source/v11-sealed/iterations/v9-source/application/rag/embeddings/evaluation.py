"""Offline exhaustive ranking experiments only; scores do not establish truth."""
from .similarity import cosine


def rank(query, documents):
    if len({key for key, _ in documents}) != len(documents):
        raise ValueError('duplicate document IDs')
    return sorted(((key, cosine(query, vector)) for key,vector in documents),
                  key=lambda item: (-item[1], item[0]))


def metrics(ranking, relevant):
    ids = [key for key,_ in ranking]
    relevant = set(relevant)
    if not relevant or not relevant.issubset(ids) or len(ids)!=len(set(ids)):
        raise ValueError('invalid relevance judgments/ranking')
    positions = [i+1 for i,key in enumerate(ids) if key in relevant]
    return {'recall_at_1':sum(p<=1 for p in positions)/len(relevant),
            'recall_at_3':sum(p<=3 for p in positions)/len(relevant),
            'mrr':1/min(positions)}


def evaluate(queries, query_vectors, document_vectors):
    if len(queries) != len(query_vectors) or not queries:
        raise ValueError('query cardinality mismatch/empty evaluation')
    rows = []
    for q,v in zip(queries,query_vectors):
        ranking = rank(v, document_vectors)
        scores = dict(ranking)
        if not q['hard_negatives'] or not set(q['hard_negatives']).issubset(scores):
            raise ValueError('missing hard negatives')
        m = metrics(ranking, q['relevant'])
        positive = max(scores[k] for k in q['relevant'])
        negative = max(scores[k] for k in q['hard_negatives'])
        margin = positive-negative
        m['hard_negative_win_rate'] = float(margin > 1e-8)
        rows.append({'id':q['id'], 'category':q['category'], 'query':q['query'], **m,
                     'positive_similarity':positive, 'hard_negative_similarity':negative,
                     'margin':margin, 'tie':abs(margin)<=1e-8,
                     'dangerous_top3':[key for key,_ in ranking[:3] if key in q['hard_negatives']],
                     'ranking':[{'id':key,'score':score,'relevant':key in q['relevant'],
                                 'hard_negative':key in q['hard_negatives']} for key,score in ranking]})
    names = ('recall_at_1','recall_at_3','mrr','hard_negative_win_rate')
    return {'metrics':{name:sum(r[name] for r in rows)/len(rows) for name in names},
            'queries':rows}
