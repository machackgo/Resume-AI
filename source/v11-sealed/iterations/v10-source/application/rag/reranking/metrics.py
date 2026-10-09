"""Evaluation-only graded relevance: never support or credential labels.

Each ranking entry is a unique exact-text group. Grade 3 is a direct match;
2 is strongly related/incomplete; 1 is adjacent useful context; 0 is irrelevant
or misleading. Recall/MRR use grade 3. nDCG gain is 2**grade - 1.
"""
import math
import statistics

def dcg(grades, k):
    return sum((2 ** g - 1) / math.log2(i + 2) for i, g in enumerate(grades[:k]))

def evaluate(ranking, grades, hard_negatives=(), dangerous_pairs=()):
    if len(ranking) != len(set(ranking)):
        raise ValueError('rank unique evidence groups, not duplicate evidence')
    if any(type(x) is not int or not 0 <= x <= 3 for x in grades.values()):
        raise ValueError('grades must be integers 0..3')
    if any(x not in grades for x in ranking):
        raise ValueError('unjudged candidate')
    relevant = {key for key, grade in grades.items() if grade == 3}
    if not relevant:
        raise ValueError('benchmark need requires a direct relevant group')
    if any(a not in grades or b not in grades or grades[a] <= grades[b] for a,b in dangerous_pairs):
        raise ValueError('danger pair requires explicitly stronger/weaker judgments')
    positions = {key: i for i, key in enumerate(ranking)}
    values = [grades[x] for x in ranking]
    ideal = sorted(grades.values(), reverse=True)
    out = {'mrr': next((1 / (i + 1) for i, x in enumerate(ranking) if x in relevant), 0.),
           'top1_hard_negative_error': float(bool(ranking) and ranking[0] in hard_negatives),
           'candidate_recall': len(set(ranking) & relevant) / len(relevant)}
    for k in (1, 2, 3, 5):
        out['recall_at_' + str(k)] = len(set(ranking[:k]) & relevant) / len(relevant)
        out['hit_at_' + str(k)] = float(bool(set(ranking[:k]) & relevant))
        denom = dcg(ideal, k)
        out['ndcg_at_' + str(k)] = dcg(values, k) / denom if denom else 0.
    conditional_ideal = sorted(values, reverse=True)
    for k in (3, 5):
        denom = dcg(conditional_ideal, k)
        out['conditional_ndcg_at_' + str(k)] = dcg(values, k) / denom if denom else 0.
    pairs = [(a,b) for a,b in dangerous_pairs if a in positions and b in positions]
    failures = [(a,b) for a,b in pairs if positions[b] < positions[a]]
    out.update({'danger_pairs_total': len(dangerous_pairs), 'danger_pairs_evaluable': len(pairs),
                'danger_pairs_failed': len(failures),
                'dangerous_neighbor_rate': len(failures) / len(pairs) if pairs else None,
                'dangerous_query': float(bool(failures)),
                'positive_over_hard_negative_win_rate': (len(pairs)-len(failures))/len(pairs) if pairs else None,
                'dangerous_pairs_missing_stronger': sum(a not in positions and b in positions for a,b in dangerous_pairs)})
    graded_pairs = [(a,b) for a in ranking for b in ranking if grades[a] > grades[b]]
    out['pairwise_accuracy'] = sum(positions[a] < positions[b] for a,b in graded_pairs)/len(graded_pairs) if graded_pairs else None
    hits = 0; total = 0.
    for i, key in enumerate(ranking, 1):
        if key in relevant:
            hits += 1; total += hits/i
    out['map'] = total/len(relevant)
    return out

def aggregate(rows):
    if not rows: return {}
    out = {k: statistics.mean([row[k] for row in rows if row[k] is not None])
           if any(row[k] is not None for row in rows) else None for k in rows[0]}
    for k in ('danger_pairs_total', 'danger_pairs_evaluable', 'danger_pairs_failed', 'dangerous_pairs_missing_stronger'):
        out[k] = sum(row[k] for row in rows)
    n = out['danger_pairs_evaluable']
    out['dangerous_neighbor_rate'] = out['danger_pairs_failed']/n if n else None
    out['positive_over_hard_negative_win_rate'] = 1-out['dangerous_neighbor_rate'] if n else None
    return out
