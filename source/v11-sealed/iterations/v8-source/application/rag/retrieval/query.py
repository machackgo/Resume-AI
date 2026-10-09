from ..domain import stable_id
from .models import QueryPlan, InformationNeed

def construct(need: InformationNeed, expansion=False):
    if not isinstance(need,InformationNeed): raise ValueError('typed need required')
    text=' '.join(need.text.split())
    # Exact aliases/concept discovery only. No adjacent-cloud/framework substitutions.
    additions=[]
    if expansion:
        for phrase,terms in (('aws',('Amazon Web Services',)),
                             ('containerized',('containerization','Docker','model serving')),
                             ('postgres',('PostgreSQL',))):
            if phrase in text.lower().split(): additions.extend(terms)
    policy='focused-v1-conservative-expansion' if expansion else 'focused-v1'
    expanded=text+(' '+ ' '.join(additions) if additions else '')
    return QueryPlan(stable_id('query',policy,need.kind.value,need.requirement_id,text,additions),need,expanded,tuple(additions),policy)
