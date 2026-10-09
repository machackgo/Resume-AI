"""Explicit conservative semantic contracts. Similarity never grants a license.

Catalog names come exclusively from canonical source metadata/section spans.
Unknown identity/type is retained as unknown, never inferred from shared tools.
"""
import hashlib
import json
import re

CAPABILITIES = {
    'COMPUTER_VISION': r'computer vision|object detection|image segmentation',
    'IMAGE_PROCESSING': r'image[ -]processing|process(?:ed|ing)? images|images?|pixels?|photographs?|opencv|webcam',
    'STATE_MANAGEMENT': r'numeric|button history|state/features|state management|game state',
    'UI_INTERACTION': r'button|click|user interaction',
    'DATABASE': r'postgresql|postgres|sqlite|database|cloud sql|pgvector',
    'VECTOR_RETRIEVAL': r'vector (?:search|retrieval|storage)|pgvector|nearest neighbor|retrieval.augmented|\bRAG\b',
    'NLP': r'question.answering|natural language|\bNLP\b|\bBERT\b',
    'LLM_INFERENCE': r'\bLLM|\bQwen|language model|model inference',
    'MODEL_TRAINING': r'\btrain(?:ed|ing)?\b|fine.tun',
    'MODEL_ARCHITECTURE': r'classifier|classification|neural network|\bCNN\b|model architecture',
    'DATA_PROCESSING': r'data processing|feature pipeline|filtering|vectorization',
    'BACKEND_API': r'\bAPI\b|\bAPIs\b|backend|fastapi|flask',
    'FRONTEND': r'frontend|next\.js|react|typescript',
    'DEPLOYMENT': r'deploy|docker|container|kubernetes|\bAWS\b|\bGCP\b',
    'OBSERVABILITY': r'observability|monitoring|prometheus|grafana',
}
PARENTS = {'COMPUTER_VISION': ['IMAGE_PROCESSING'], 'VECTOR_RETRIEVAL': ['DATA_PROCESSING']}
TECHNOLOGIES = r'PostgreSQL|Postgres|pgvector|SQLite|OpenCV|Python|PyTorch|FastAPI|Flask|Qwen[\w.-]*|RAG|LLMs?|Docker(?:ized)?|AWS|GCP|Kubernetes|Next\.js|TypeScript|React|scikit-learn|TensorFlow|Supabase|BERT|PPO'
ACTION = r'build|built|implement(?:ed)?|deploy(?:ed)?|train(?:ed)?|process(?:ed)?|develop(?:ed)?|design(?:ed)?|architect(?:ed)?|evaluat(?:e|ed)|us(?:e|ed)|combin(?:e|ed)|reduc(?:e|ed)|improv(?:e|ed)|serv(?:e|ed)|connect(?:ed)?|maintain(?:ed)?'

def norm(s):
    return ' '.join(re.findall(r'[a-z0-9]+', s.casefold()))

def capability_types(text):
    # Negative mentions do not establish a positive capability. The original
    # expression is retained separately for exclusion/constraint auditing.
    positive=re.sub(r'\b(?:not|never|without|no)\b[^.;\n]*','',text,flags=re.I)
    found = {k for k, pattern in CAPABILITIES.items() if re.search(pattern, positive, re.I)}
    for k in list(found):
        found.update(PARENTS.get(k, []))
    return sorted(found)

def compatible(expected, actual):
    # Mandatory modality must not be inferred from generic processing or CNNs.
    if 'IMAGE_PROCESSING' in expected and 'IMAGE_PROCESSING' not in actual:
        return False
    if 'VECTOR_RETRIEVAL' in expected and 'VECTOR_RETRIEVAL' not in actual:
        return False
    if 'MODEL_TRAINING' in expected and 'MODEL_TRAINING' not in actual:
        return False
    return not expected or bool(set(expected) & set(actual))

def relationship(text, rid):
    """Fields annotate an immutable expression; unknown parsing keeps full text."""
    actions = [m.group() for m in re.finditer(r'\b(?:' + ACTION + r')\b', text, re.I)]
    tech = [m.group() for m in re.finditer(r'\b(?:' + TECHNOLOGIES + r')\b', text, re.I)]
    m = re.search(r'\b(?:' + ACTION + r')\b\s+(.+?)(?=\s+(?:using|with|via|on|for|without)\b|[.;]|$)', text, re.I)
    return dict(relationship_id='rel_' + hashlib.sha256((rid+'\0'+text).encode()).hexdigest()[:24],
                requirement_id=rid, text=text, action=actions, object=m.group(1) if m else None,
                technology=tech, purpose=re.findall(r'\b(?:for|to)\s+([^.;]+)', text, re.I),
                constraint=re.findall(r'\b(?:without|not|never|only|at least|no)\b[^.;]*', text, re.I),
                qualifier=re.findall(r'\b(?:optional|preferred|required|must|professional|academic|years?)\b', text, re.I),
                capability_types=capability_types(text), parsing='conservative_annotation_original_retained')

def project_label(text):
    text = re.sub(r'^#+\s*', '', text).strip()
    return re.split(r'\s+[|—–]\s+|\s+-\s+', text)[0].strip()

def identity(ref, unit, evidence=None):
    meta = json.loads(getattr(evidence, 'metadata_json', '{}')) if evidence else {}
    heading = unit.get('source_context') or {}
    # Resume sections are independent entities even in the same canonical file.
    resume_section = bool(' | ' in heading.get('text', '') or (' — ' in heading.get('text', '') and not heading.get('text','').startswith('#')))
    label = project_label(heading['text']) if resume_section else meta.get('project')
    if not label or norm(label) in {'academic work','candidate profile','candidate resume','resume','personal profile'}:
        label = project_label(heading.get('text','')) or None
    key = [ref['scope'], ref['source_id'], ref['source_version'], heading.get('start',0)]
    return dict(candidate_id=ref['scope']['candidate_id'], source_id=ref['source_id'],
                canonical_evidence_id=ref['evidence_id'], project_label=label,
                entity_id='entity_'+hashlib.sha256(json.dumps(key,sort_keys=True).encode()).hexdigest()[:24],
                evidence_type=meta.get('evidence_type',ref.get('source_type','unknown')),
                provenance=dict(source_version=ref['source_version'], start=unit['start'], end=unit['end']),
                capability_types=capability_types(unit['text']), resolution='source_bound')

def entity_catalog(ledger):
    cached = getattr(ledger, '_semantic_entity_catalog', None)
    if cached is not None:
        return cached
    names = set()
    for e in getattr(ledger,'review_evidence',[]):
        meta=json.loads(e.metadata_json)
        if meta.get('project') and norm(meta['project']) not in {'academic work','candidate profile','candidate resume','resume','personal profile'}:
            names.add(project_label(meta['project']))
        text=ledger.content(e.normalized_ref).decode()
        for line in text.splitlines():
            if meta.get('evidence_type')!='implementation_artifact' and ' | ' in line and re.match(r'^[A-Z][\w ,&/—–.-]+\s+\|',line) and not line.rstrip().endswith('.'):
                names.add(project_label(line))
    ledger._semantic_entity_catalog=sorted(n for n in names if len(norm(n))>=3)
    return ledger._semantic_entity_catalog

def mentions(text, names):
    value=' '+norm(text)+' '; found=set()
    for name in names:
        key=norm(name)
        if ' '+key+' ' in value:
            found.add(key)
        # A distinctive CamelCase name may omit its descriptive suffix.
        first=re.split(r'[\s_-]',name)[0]
        descendants={norm(n) for n in names if norm(n).startswith(norm(first)+' ')}
        if len(descendants)<=1 and re.search(r'[a-z][A-Z]',first) and ' '+norm(first)+' ' in value:
            found.add(key)
    return found

def identity_compatible(requirement, evidence_identity, catalog):
    requested=mentions(requirement,catalog)
    # An explicitly named entity absent from the corpus is still a constraint,
    # not permission to borrow from the nearest known project.
    explicit=re.findall(r'\b(?:[Pp]roject|[Ee]vent)\s+([A-Z][A-Za-z0-9_-]*(?:\s+[A-Z][A-Za-z0-9_-]*)?)',requirement)
    requested.update(norm(x) for x in explicit)
    label=evidence_identity.get('project_label')
    actual=mentions(label or '',catalog)|({norm(label)} if label else set())
    strip_role=lambda x:re.sub(r'^(?:project|event)\s+','',x)
    requested={strip_role(x) for x in requested};actual={strip_role(x) for x in actual}
    return dict(compatible=not requested or requested<=actual, requested_entities=sorted(requested),
                evidence_entities=sorted(actual), entity_id=evidence_identity['entity_id'])

def achievement(text):
    """Necessary substance gate, never a substitute for the factual audit."""
    action=bool(re.search(r'\b(?:'+ACTION+r'|engineered|contributed|achieved|supports|serves|enables|detects|classifies|routes|retrieves)\b',text,re.I))
    configuration=bool(re.search(r'\b(?:install(?:ed)?|initializ(?:ed|e)|loaded a model|created a (?:generic )?button|virtual environment|lives in|directory|folder|uses? (?:the |a )?(?:library|framework))\b',text,re.I))
    meaningful=bool(re.search(r'\b(?:pipeline|workflows?|classification|classifier|retrieval|search|question.answering|authentication|authorization|monitoring|observability|inference|prediction|connector|routing|recommendation|segmentation|detection|product flows|two.branch|multi.branch)\b',text,re.I))
    outcome=bool(re.search(r'\b(?:reduced|improved|achieved|latency|accuracy|throughput|serving|served|supports|enables|detects|classifies|routes|retrieves)\b',text,re.I))
    architecture=bool(re.search(r'\b(?:CNN|neural network|architecture|pipeline)\b.+\b(?:over|processing|for|with)\b',text,re.I))
    dimensions=dict(factual_support='INDEPENDENT_REVIEW_REQUIRED',job_relevance='INDEPENDENT_REVIEW_REQUIRED',demonstrated_action=action,
                    technical_substance=meaningful,outcome_or_capability=outcome or architecture or meaningful,
                    scope='SOURCE_BOUND',specificity=len(text.split())>=7,candidate_contribution='ATTRIBUTION_MUST_BE_PRESERVED')
    if configuration and not (meaningful and outcome):
        return dict(classification='D',standalone=False,reason='Setup/configuration without demonstrated system significance',dimensions=dimensions)
    if re.match(r'^(?:used|uses?|installed|loaded|initialized|configured)\b',text,re.I) and not (meaningful and outcome):
        return dict(classification='C',standalone=False,reason='Tool usage alone does not demonstrate a substantive system contribution',dimensions=dimensions)
    if not action and not architecture and not (meaningful and outcome):
        return dict(classification='C',standalone=False,reason='Technology/component label without demonstrated action or system capability',dimensions=dimensions)
    return dict(classification='REVIEW_REQUIRED',standalone=None,reason='Substantive candidate; all independent factual/content gates still required',dimensions=dimensions)

def license_contract(candidate_match, provenance_valid, factual_support, project_identity_compatible,
                     requirement_semantics_compatible, capability_compatible, claim_strength_supported,
                     contradicted, ambiguous, resume_worthy):
    checks=dict(candidate_match=candidate_match,provenance_valid=provenance_valid,factual_support=factual_support,
                project_identity_compatible=project_identity_compatible,requirement_semantics_compatible=requirement_semantics_compatible,
                capability_compatible=capability_compatible,claim_strength_supported=claim_strength_supported,
                not_contradicted=not contradicted,unambiguous=not ambiguous)
    licensed=all(checks.values())
    return dict(checks=checks,license=licensed,resume_promotion=licensed and resume_worthy,resume_worthy=resume_worthy)

def unresolved_negative(claim, claim_identity, sources, catalog):
    """An affirmative completion bundle cannot override same-entity noncompletion.

    This gate deliberately cannot resolve chronology from source ordering. It
    records a conservative veto for independent audit, not an invented repair.
    """
    if not re.search(r'\b(?:built|implemented|deployed|trained|completed)\b',claim,re.I):return []
    actual=claim_identity.get('project_label')
    if not actual:return []
    terms=set(norm(claim).split())-set('built implemented deployed trained completed project system model with and the for from using into a an on in to of api apis backend data'.split())
    conflicts=[]
    for source in sources:
        label=source.get('project_label')
        if not label:continue
        same=norm(label)==norm(actual) or bool(mentions(label,catalog)&mentions(actual,catalog))
        if not same:continue
        for line in re.split(r'[\n.!?]',source['content']):
            if re.search(r'\b(?:not|never)\s+(?:\w+\s+){0,3}(?:implemented|built|deployed|trained|completed)\b',line,re.I) and terms & set(norm(line).split()):
                conflicts.append(dict(evidence_id=source['evidence_id'],negative_span=line,reason='Same-project completion conflict without explicit supersession'))
    return conflicts
