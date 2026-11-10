"""Conservative, extractive structural decomposition; no evidence/model access.
Unsupported syntax remains intact and explicitly unresolved, never expanded.
"""
from dataclasses import dataclass
import hashlib
import re
from ..retrieval import InformationNeed
VERSION='structural-relationship-v2'
ACTIONS=r'(?:built|implemented|deployed|trained|fine-tuned|evaluated|used|reduced|improved|containerized|packaged|designed|tested|maintained)'
@dataclass(frozen=True)
class AtomicInformationNeed:
    component_id:str
    text:str
    order:int
    source_tokens:tuple[str,...]
    relation:str='conjunct_of_original'
    semantic_relationship:dict|None=None
@dataclass(frozen=True)
class Decomposition:
    requirement_id:str
    original_text:str
    strategy_version:str
    components:tuple[AtomicInformationNeed,...]
    status:str
    relationships:tuple[tuple[str,str,str],...]

def words(s):return re.findall(r"[\w]+(?:[-.][\w]+)*|%|\+\+|#",s)
class RequirementDecomposer:
    version=VERSION
    def decompose(self,need:InformationNeed)->Decomposition:
        if not isinstance(need,InformationNeed):raise ValueError('typed requirement required')
        text=need.text;body=text.rstrip('.');parts=[text];status='atomic_or_preserved'
        # Scope-bearing negation, disjunction and conditional modifiers must not
        # be distributed by a syntactic rule lacking semantic scope resolution.
        guarded=bool(re.search(r'\b(?:not|never|without|unless|either|or|if|no)\b',body,re.I))
        if guarded:
            status='unresolved_scope_preserved'
        else:
            # Separate action clauses. Pronouns and shared original requirement
            # remain in the decomposition relationship, avoiding invented nouns.
            clauses=re.split(r'\s+and\s+(?='+ACTIONS+r'\b)',body,flags=re.I)
            if len(clauses)>1 and all(re.match(ACTIONS+r'\b',c,re.I) for c in clauses):
                if re.fullmatch(ACTIONS,clauses[0],re.I):
                    # Shared object: Built and deployed X. Preserve deployment
                    # platform only on deployment; nested Dockerized modifier is
                    # an independently stated proposition, not a new technology.
                    # A shared leading verb binds the NEXT action's object,
                    # never a later independent clause's object/technology.
                    last=clauses[1];m=re.match('('+ACTIONS+r')\s+(.+)',last,re.I)
                    if m:
                        obj=m.group(2);base=re.split(r'\s+on\s+',obj,maxsplit=1)[0]
                        nested=re.match(r'(Dockerized|containerized)\s+(.+)',base,re.I)
                        plain=nested.group(2) if nested else base
                        parts=[clauses[0]+' '+plain+'.',last+'.']
                        if nested:
                            parts[-1]=re.sub(re.escape(nested.group(1))+' ', '',parts[-1],count=1)
                            parts.insert(1,nested.group(1)+' '+plain+'.')
                        parts.extend(c[0].upper()+c[1:]+'.' for c in clauses[2:])
                        status='structural_split'
                else:parts=[c[0].upper()+c[1:]+'.' for c in clauses];status='structural_split'
            else:
                # Explicit shared predicate, e.g. Implemented both RAG and
                # fine-tuning for Juniper; do not infer base-weight changes.
                m=re.fullmatch('('+ACTIONS+r')\s+both\s+(.+?)\s+and\s+(.+?)(\s+for\s+.+)?',body,re.I)
                if m:
                    tail=m.group(4) or ''
                    parts=[m.group(1)+' '+m.group(i)+tail+'.' for i in (2,3)];status='structural_split'
                elif re.search(r'\band\b',body,re.I):status='unresolved_conjunction_preserved'
        original={w.casefold() for w in words(text)}
        assert all({w.casefold() for w in words(p)}<=original for p in parts),'invented token'
        components=tuple(AtomicInformationNeed('C'+hashlib.sha256((VERSION+'\0'+need.requirement_id+'\0'+text+'\0'+str(i)+'\0'+p).encode()).hexdigest()[:16],p,i,tuple(words(p))) for i,p in enumerate(parts,1))
        from dataclasses import replace
        from ...grounding.semantic_contracts import relationship
        components=tuple(replace(c,semantic_relationship=dict(relationship(c.text,c.component_id),parent_requirement_id=need.requirement_id,original_text=text)) for c in components)
        return Decomposition(need.requirement_id,text,VERSION,components,status,tuple((c.component_id,'conjunct_of',need.requirement_id) for c in components))
