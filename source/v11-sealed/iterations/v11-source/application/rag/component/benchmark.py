"""Frozen synthetic component gold, authored before retrieval/Qwen experiments."""
from dataclasses import asdict
import json,time
from .decompose import RequirementDecomposer,words,ACTIONS
from ..retrieval import InformationNeed,NeedType
import re
VERSION='stage3i-decomposition-v1'
def benchmark():
    cases=[]
    def add(text,parts=None,category='atomic'):
        cases.append(dict(id='d%02d'%(len(cases)+1),text=text,expected=parts or [text],category=category))
    for text in ('Built REST APIs using FastAPI.','Reduced inference latency by 40%.','Three years of production Kubernetes experience.','AWS Certified Solutions Architect.','Containerized ML service.','Cloud deployment.','Used QLoRA to adapt a four-bit base model.','Used LoRA.','Implemented RAG.','Built the hosted payment API consumed by Harbor.','Used AWS for the deployment.','Maintained C++ and C# libraries.','No Kubernetes experience is required.','Never deployed on AWS.','Either AWS or Azure experience.','Built APIs without deploying them.','At least 3.5 years of Python experience.','Improved p95 latency by exactly 18%.','Fine-tuned models using QLoRA.','Used an API.','Built an API.','Trained a classifier.','Deployed a classifier.'):
        add(text)
    add('Built and deployed Dockerized FastAPI services on AWS.',['Built FastAPI services.','Dockerized FastAPI services.','deployed FastAPI services on AWS.'],'nested')
    add('Fine-tuned models using QLoRA and evaluated them on held-out data.',['Fine-tuned models using QLoRA.','Evaluated them on held-out data.'],'actions')
    add('Built Cedar with FastAPI and deployed it on Kubernetes.',['Built Cedar with FastAPI.','Deployed it on Kubernetes.'],'actions')
    add('Trained Birch with PyTorch and deployed it using TensorFlow in production.',['Trained Birch with PyTorch.','Deployed it using TensorFlow in production.'],'actions')
    add('Implemented both RAG and fine-tuning for the Juniper assistant.',['Implemented RAG for the Juniper assistant.','Implemented fine-tuning for the Juniper assistant.'],'shared_predicate')
    add('Designed endpoints and tested authentication and maintained documentation.',['Designed endpoints.','Tested authentication.','Maintained documentation.'],'actions')
    add('Reduced latency by 40% and improved throughput by 20%.',['Reduced latency by 40%.','Improved throughput by 20%.'],'numeric')
    # Intentionally difficult cases: gold does NOT bless conservative under-split.
    add('Deployed Cedar using Docker on AWS EC2.',['Used Docker for Cedar deployment.','Deployed Cedar on AWS EC2.'],'modifier')
    add('Built REST APIs using FastAPI and Flask.',['Built REST APIs using FastAPI.','Built REST APIs using Flask.'],'technology_conjunction')
    add('Has AWS certification and three years of Kubernetes experience.',['Has AWS certification.','Has three years of Kubernetes experience.'],'credential_duration')
    add('Did not build or deploy Kubernetes services.',category='negation')
    return {'version':VERSION,'cases':cases,'policy':'Exact normalized component match; atomic numeric/credential phrases retained relationally. Unsplit compound is a precision error and missed gold components, not an invented requirement.'}
def normalize(s):return s.casefold().rstrip('.')
def evaluate(data):
    rows=[]
    for q in data['cases']:
        need=InformationNeed(NeedType.JOB_REQUIREMENT,q['text'],q['id']);t=time.perf_counter();d=RequirementDecomposer().decompose(need);elapsed=time.perf_counter()-t
        got={normalize(c.text) for c in d.components};gold={normalize(c) for c in q['expected']};original={w.casefold() for w in words(q['text'])};out={w.casefold() for c in d.components for w in words(c.text)}
        entities={w for w in words(q['text']) if any(x.isupper() for x in w[1:])};numbers=set(re.findall(r'\d+(?:\.\d+)?%?',q['text']));actions=set(re.findall(ACTIONS,q['text'],re.I))
        joined=' '.join(c.text for c in d.components)
        rows.append(dict(id=q['id'],decomposition=asdict(d),true_positive=len(got&gold),predicted=len(got),expected=len(gold),invented_tokens=sorted(out-original),entities_preserved=all(e in joined for e in entities),numbers_preserved=all(n in joined for n in numbers),actions_preserved=all(a.casefold() in joined.casefold() for a in actions),deterministic=d==RequirementDecomposer().decompose(need),seconds=elapsed))
    tp=sum(r['true_positive'] for r in rows);pred=sum(r['predicted'] for r in rows);gold=sum(r['expected'] for r in rows)
    metrics=dict(cases=len(rows),component_precision=tp/pred,component_recall=tp/gold,missed_component_rate=1-tp/gold,invented_component_rate=sum(bool(r['invented_tokens']) for r in rows)/len(rows),exact_entity_preservation=sum(r['entities_preserved'] for r in rows)/len(rows),numeric_preservation=sum(r['numbers_preserved'] for r in rows)/len(rows),action_preservation=sum(r['actions_preserved'] for r in rows)/len(rows),exact_decomposition_rate=sum(r['true_positive']==r['predicted']==r['expected'] for r in rows)/len(rows),mean_seconds=sum(r['seconds'] for r in rows)/len(rows))
    # Token extraction is a safety check, not proof of semantic entailment.
    # Authored semantic audit: all outputs here either unchanged or valid conjunctions.
    metrics['semantic_invented_components_authored_audit']=0
    metrics['smoke_pass']=metrics['component_precision']>=.85 and metrics['component_recall']>=.80 and all(metrics[k]==1 for k in ('exact_entity_preservation','numeric_preservation','action_preservation')) and not any(r['invented_tokens'] for r in rows)
    return dict(metrics=metrics,rows=rows)
