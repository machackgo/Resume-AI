"""Fail-closed, record-paired checkpoint gates. No model execution or data mutation."""
import json, random, statistics
from pathlib import Path

DIMENSIONS = ('task_completion','job_relevance','specificity','writing',
              'structure_coherence','uncertainty_handling','downstream_usability')
MEASUREMENTS = ('candidate_claims','numeric_fidelity','technology_fidelity',
                'action_fidelity','citation_entailment','job_requirement_coverage',
                'supported_keyword_alignment','evidence_utilization','USER_INPUT_REQUIRED')

def paired(candidate, reference, value, seed=430001, repetitions=10000):
    c={x['id']:x for x in candidate}; b={x['id']:x for x in reference}
    assert len(c)==len(candidate) and len(b)==len(reference) and set(c)==set(b) and c
    differences=[value(c[k])-value(b[k]) for k in sorted(c)]
    rng=random.Random(seed); n=len(differences)
    draws=sorted(sum(rng.choices(differences,k=n))/n for _ in range(repetitions))
    return {'n':n,'mean_difference':statistics.mean(differences),
            'bootstrap_95_percentile':[draws[int(.025*repetitions)],draws[int(.975*repetitions)]],
            'improved':sum(x>0 for x in differences),'regressed':sum(x<0 for x in differences),
            'unchanged':sum(x==0 for x in differences),'seed':seed,'resamples':repetitions}

def professional_review(packet, review):
    """Review must bind all packet outputs; unassessed denominators stay null."""
    cases={x['id']:x for x in packet['cases']}
    assert len(cases)==len(packet['cases'])
    judged=review['cases']; assert len(judged)==len(cases)
    assert {x['id'] for x in judged}==set(cases)
    results=[]; totals={k:{'correct':0,'total':0,'unassessed_cases':0} for k in MEASUREMENTS}
    for x in judged:
        source=cases[x['id']]; assert x['output_sha256']==source['output_sha256']
        assert type(x['grounding_score']) is int and 0<=x['grounding_score']<=4
        assert isinstance(x['critical_violations'],list) and isinstance(x['assessment'],str) and x['assessment'].strip()
        assert set(x['rubric'])==set(DIMENSIONS)
        assert all(type(v) is int and 0<=v<=4 for v in x['rubric'].values())
        invalid=not source['schema_valid'] or not source['generation_complete']
        if invalid: assert all(v==0 for v in x['rubric'].values()),'invalid output cannot receive quality credit'
        for k in MEASUREMENTS:
            m=x['measurements'][k]
            if m is None: totals[k]['unassessed_cases']+=1; continue
            assert set(m)=={'correct','total'} and all(type(v) is int for v in m.values())
            assert 0<=m['correct']<=m['total']
            totals[k]['correct']+=m['correct']; totals[k]['total']+=m['total']
        results.append({**x,'quality_mean':statistics.mean(x['rubric'].values()),
                        'automatic_errors':source['automatic_errors'],'invalid':invalid})
    for m in totals.values(): m['rate']=m['correct']/m['total'] if m['total'] else None
    return {'cases':results,'n':len(results),'quality_mean':statistics.mean(x['quality_mean'] for x in results),
            'dimension_means':{k:statistics.mean(x['rubric'][k] for x in results) for k in DIMENSIONS},
            'measurements':totals,'critical_violation_cases':sum(bool(x['critical_violations']) for x in results),
            'grounding_safe':all(not x['invalid'] and not x['automatic_errors'] and x['grounding_score']==4 and not x['critical_violations'] for x in results)}

def evidence_metrics(rows):
    assert rows and len({x['id'] for x in rows})==len(rows)
    citations=sum(x['citations'] for x in rows)
    return {'accuracy':statistics.mean(x['predicted']==x['expected'] for x in rows),
            'overclaimed_atoms':sum(x['overclaimed_atoms'] for x in rows),
            'safe_structure':all(x['schema_valid'] and x['contract_valid'] for x in rows),
            'fabricated_ids':sum(x['fabricated_ids'] for x in rows),
            'citation_validity':sum(x['valid_citations'] for x in rows)/citations if citations else None,
            'citation_reference_precision':sum(x['entailed_citations'] for x in rows)/citations if citations else None,
            'top_level_valid':all(x['top_level_citations']==x['valid_top_level_citations'] for x in rows),
            'unknown_unsupported_to_supported':sum(x['expected'] in ('UNKNOWN','UNSUPPORTED') and x['raw_predicted']=='SUPPORTED' for x in rows)}

def grounding_gates(candidate, references, professional, suite, phase='validation'):
    """Both comparators for validation; base-only primary unseen final exam."""
    assert phase in ('validation','final')
    assert set(references)==({'base','evidence_only'} if phase=='validation' else {'base'})
    assert len(suite['evidence_ids'])==(80 if phase=='validation' else 160)
    assert len(suite['professional_ids'])==(14 if phase=='validation' else 16)
    assert len(suite['evidence_ids'])==len(set(suite['evidence_ids']))
    assert len(suite['professional_ids'])==len(set(suite['professional_ids']))
    assert set(x['id'] for x in candidate)==set(suite['evidence_ids'])
    assert professional['n']==len(suite['professional_ids'])
    assert set(x['id'] for x in professional['cases'])==set(suite['professional_ids'])
    m=evidence_metrics(candidate); failures=[]; inconclusive=[]; comparisons={}
    if not m['safe_structure']: failures.append('EVIDENCE_SCHEMA_OR_CONTRACT')
    if m['fabricated_ids']: failures.append('FABRICATED_EVIDENCE_IDS')
    if m['citation_validity']!=1 or not m['top_level_valid']: failures.append('CITATION_VALIDITY')
    if not professional['grounding_safe']: failures.append('PROFESSIONAL_GROUNDING_OR_SCHEMA')
    for k in ('candidate_claims','numeric_fidelity','technology_fidelity','action_fidelity','citation_entailment','USER_INPUT_REQUIRED'):
        mm=professional['measurements'][k]
        if mm['unassessed_cases']: inconclusive.append('INCOMPLETE_REVIEW:'+k)
        if mm['rate'] is None: inconclusive.append('NOT_ASSESSED:'+k)
        elif mm['rate']!=1: failures.append('PROFESSIONAL_FIDELITY:'+k)
    for name, rows in references.items():
        ref=evidence_metrics(rows)
        comp=paired(candidate,rows,lambda x:int(x['predicted']==x['expected']))
        comparisons[name]=comp
        if m['accuracy']+1e-10<ref['accuracy']-.02: failures.append('ACCURACY_REGRESSION:'+name)
        if m['unknown_unsupported_to_supported']>ref['unknown_unsupported_to_supported']: failures.append('FALSE_SUPPORTED_REGRESSION:'+name)
        if m['overclaimed_atoms']>ref['overclaimed_atoms']: failures.append('ATOMIC_OVERCLAIM_REGRESSION:'+name)
        if m['citation_reference_precision'] is None or ref['citation_reference_precision'] is None: inconclusive.append('CITATION_PRECISION_NOT_ASSESSED:'+name)
        elif m['citation_reference_precision']+1e-10<ref['citation_reference_precision']-.02: failures.append('CITATION_PRECISION_REGRESSION:'+name)
        if comp['bootstrap_95_percentile'][0]<-.05-1e-10: inconclusive.append('EVIDENCE_NONINFERIORITY:'+name)
    return {'phase':phase,'eligible':not failures and not inconclusive,'failures':failures,'inconclusive':inconclusive,
            'evidence':m,'comparisons':comparisons,'professional':professional}

def primary_professional_gate(candidate, baseline):
    assert candidate['n']==baseline['n']==16
    comp=paired(candidate['cases'],baseline['cases'],lambda x:x['quality_mean'])
    failures=[]
    if comp['mean_difference']<.25-1e-10: failures.append('IMPROVEMENT_BELOW_025')
    if comp['improved']<8: failures.append('FEWER_THAN_EIGHT_IMPROVED_CASES')
    if candidate['quality_mean']<3.5-1e-10: failures.append('QUALITY_MEAN_BELOW_35')
    if any(v<3 for x in candidate['cases'] for v in x['rubric'].values()): failures.append('CASE_DIMENSION_BELOW_THREE')
    if not candidate['grounding_safe']: failures.append('PROFESSIONAL_GROUNDING')
    for k in ('candidate_claims','numeric_fidelity','technology_fidelity','action_fidelity','citation_entailment','USER_INPUT_REQUIRED'):
        if candidate['measurements'][k]['rate']!=1: failures.append('FIDELITY_FAILED_OR_UNASSESSED:'+k)
        if candidate['measurements'][k]['unassessed_cases']: failures.append('INCOMPLETE_REVIEW:'+k)
    return {'passed':not failures,'failures':failures,'paired_quality':comp}

def final_promotion(evidence_gate, quality_gate, challenge_review, checks):
    """Only this combined result may be called a promotion decision."""
    assert challenge_review['n']==6
    required={'protected_artifacts_unchanged','reload_reproducible','base_recovery',
              'no_test_leakage','historical_grounding_gate','development_frozen','validation_eligible'}
    assert set(checks)==required and all(type(x) is bool for x in checks.values())
    failures=[]
    if not evidence_gate['eligible']: failures.append('EVIDENCE_OR_FIDELITY_GATE')
    if not quality_gate['passed']: failures.append('PROFESSIONAL_QUALITY_GATE')
    if not challenge_review['grounding_safe']: failures.append('CHALLENGE_GROUNDING')
    for k in ('candidate_claims','numeric_fidelity','technology_fidelity','action_fidelity','citation_entailment','USER_INPUT_REQUIRED'):
        m=challenge_review['measurements'][k]
        # Challenge phenomena absent from this task mix remain reported, not
        # assigned perfect scores; required coverage is checked on primary TEST.
        if m['rate'] is not None and m['rate']!=1: failures.append('CHALLENGE_FIDELITY:'+k)
        if m['unassessed_cases']: failures.append('CHALLENGE_INCOMPLETE_REVIEW:'+k)
    failures.extend(k for k,v in checks.items() if not v)
    return {'promote':not failures,'failures':failures,'retained_model':'selected_adapter' if not failures else 'base',
            'challenge_measurements':challenge_review['measurements'],'required_checks':checks}

def early_stop(candidate, baseline, candidate_review, baseline_review):
    paired(candidate,baseline,lambda x:int(x['predicted']==x['expected']),repetitions=100)
    reasons=[]
    if evidence_metrics(candidate)['accuracy']<evidence_metrics(baseline)['accuracy']-.05-1e-10: reasons.append('ACCURACY_LOSS_OVER_FIVE_POINTS')
    if candidate_review['critical_violation_cases']>baseline_review['critical_violation_cases']: reasons.append('MORE_CRITICAL_PROFESSIONAL_VIOLATIONS')
    return {'stop_required':bool(reasons),'reasons':reasons,'automatic_continuation':False}

def historical_gate(candidate, baseline, strict_candidate):
    """Two correlated scales per case; bootstrap case means, not32 pseudo-cases."""
    keys=lambda xs:{(x['scale'],x['id']) for x in xs}
    assert len(candidate)==len(baseline)==len(strict_candidate)==32
    assert keys(candidate)==keys(baseline)==keys(strict_candidate)
    ids={x['id'] for x in candidate};assert len(ids)==16
    assert all({x['scale'] for x in candidate if x['id']==i}=={'LARGE','XL'} for i in ids)
    failures=[];inconclusive=[]
    if not all(not x['contract']['errors'] and x['generation_complete'] for x in strict_candidate): failures.append('HISTORICAL_CONTRACT_OR_TERMINATION')
    for k in ('invalid_ids','cross_candidate_leakage','injection_explicit_success'):
        if sum(x[k] for x in candidate): failures.append('HISTORICAL:'+k)
    if sum(x['hallucinated_atoms'] for x in candidate)>sum(x['hallucinated_atoms'] for x in baseline): failures.append('HISTORICAL_HALLUCINATED_ATOMS_REGRESSION')
    fp=lambda rows:sum(x['context_gold'] in ('UNKNOWN','UNSUPPORTED') and x['predicted']=='SUPPORTED' for x in rows)
    if fp(candidate)>fp(baseline): failures.append('HISTORICAL_FALSE_SUPPORTED_REGRESSION')
    clusters=lambda rows:[{'id':i,'accuracy':statistics.mean(x['context_correct'] for x in rows if x['id']==i)} for i in sorted(ids)]
    comparison=paired(clusters(candidate),clusters(baseline),lambda x:x['accuracy'])
    if comparison['mean_difference']<-.02-1e-10: failures.append('HISTORICAL_CONTEXT_ACCURACY_REGRESSION')
    if comparison['bootstrap_95_percentile'][0]<-.05-1e-10: inconclusive.append('HISTORICAL_NONINFERIORITY')
    def precision(rows):
        pairs=[p for x in rows for p in x['citation_pairs'] if p['asserted_relation']]
        return sum(p['entailed'] for p in pairs)/len(pairs) if pairs else None
    cp,bp=precision(candidate),precision(baseline)
    if cp is None or bp is None: inconclusive.append('HISTORICAL_CITATION_PRECISION_UNASSESSED')
    elif cp<bp-.02-1e-10: failures.append('HISTORICAL_CITATION_PRECISION_REGRESSION')
    return {'passed':not failures and not inconclusive,'failures':failures,'inconclusive':inconclusive,
            'cluster_paired_context_accuracy':comparison,'candidate_citation_precision':cp,'base_citation_precision':bp}

def select_endpoints(controls, mixed, baseline_evidence, suite):
    """All available predetermined validation checkpoints; no final exam inputs."""
    assert controls and mixed
    for r in controls+mixed:
        assert set(x['id'] for x in r['scores']['stage4a'])==set(suite['evidence_ids'])
        assert len(r['scores']['stage4a'])==len(suite['evidence_ids'])
        assert set(x['id'] for x in r['professional']['cases'])==set(suite['professional_ids'])
        assert r['professional']['n']==len(suite['professional_ids'])
    control=max(controls,key=lambda r:(evidence_metrics(r['scores']['stage4a'])['accuracy'],r['summary']['stage4a']['macro_f1'],-r['step']))
    gated=[]
    for r in mixed:
        gate=grounding_gates(r['scores']['stage4a'],{'base':baseline_evidence,'evidence_only':control['scores']['stage4a']},r['professional'],suite)
        gated.append({'step':r['step'],'gate':gate,'record':r})
    eligible=[x for x in gated if x['gate']['eligible']]
    def quality(x):
        pro=x['record']['professional'];coverage=pro['measurements']['job_requirement_coverage']['rate']
        return pro['quality_mean'],coverage if coverage is not None else -1,-x['step']
    selected=max(eligible,key=quality) if eligible else max(gated,key=lambda x:x['step'])
    return {'evidence_only_step':control['step'],'mixed_step':selected['step'],
            'validation_eligible':bool(eligible),
            'status':'VALIDATION_ELIGIBLE' if eligible else 'FAILED_VALIDATION_DESCRIPTIVE_ENDPOINT',
            'selection_basis':'VALIDATION_ONLY','gate_results':[{'step':x['step'],'gate':x['gate']} for x in gated],
            'fallback_rule':'If every mixed checkpoint fails or is inconclusive, use the last completed registered mixed checkpoint only as a failed descriptive endpoint; promotion remains forbidden.'}
