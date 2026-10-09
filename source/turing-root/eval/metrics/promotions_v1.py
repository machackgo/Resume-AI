"""Supplementary promotion metrics. Never replace or modify baseline scoring.
Rates apply to schema-valid cases, with explicit evaluability/denominator reporting.
Gold labels come from unchanged cases; skill proxy tests exact requirement IDs only.
"""
def promotion_metrics(cases,predictions,schema,validator):
    result={}
    valid_cases=[(c,predictions.get(c['id'])) for c in cases if validator(predictions.get(c['id']),schema)]
    result['schema_valid_cases']=len(valid_cases);result['total_cases']=len(cases)
    for label in ['UNKNOWN','PARTIALLY_SUPPORTED']:
        counts={'gold_label_items_total':0,'gold_label_items_evaluable':0,'labels_promoted_to_supported':0,'missing_or_duplicate_predictions':0,'gold_requirement_ids_not_supported_as_skills_total':0,'gold_requirement_ids_not_supported_as_skills_evaluable':0,'requirement_ids_asserted_as_skills':0}
        for c in cases:
            counts['gold_label_items_total']+=sum(x['label']==label for key in ['matches','claims'] for x in c['gold'][key])
            counts['gold_requirement_ids_not_supported_as_skills_total']+=sum(m['label']==label and m['requirement'] not in c['gold']['skills'] for m in c['gold']['matches'])
        for c,p in valid_cases:
            for key,idkey in [('matches','requirement'),('claims','id')]:
                for g in c['gold'][key]:
                    if g['label']!=label:continue
                    counts['gold_label_items_evaluable']+=1
                    found=[x for x in p[key] if x[idkey]==g[idkey]]
                    if len(found)!=1:counts['missing_or_duplicate_predictions']+=1
                    counts['labels_promoted_to_supported']+=int(any(x['label']=='SUPPORTED' for x in found))
            for g in c['gold']['matches']:
                if g['label']==label and g['requirement'] not in c['gold']['skills']:
                    counts['gold_requirement_ids_not_supported_as_skills_evaluable']+=1
                    counts['requirement_ids_asserted_as_skills']+=int(g['requirement'] in p['skills'])
        n=counts['gold_label_items_evaluable'];s=counts['gold_requirement_ids_not_supported_as_skills_evaluable']
        counts['label_promotion_rate']=counts['labels_promoted_to_supported']/n if n else None
        counts['skill_list_promotion_proxy_rate']=counts['requirement_ids_asserted_as_skills']/s if s else None
        result[label]=counts
    result['limitations']='Exact-ID skill proxy, not semantic alias matching; zero promotion with missing predictions is not success. Read availability, missing counts, recall and free-text audit together.'
    return result
