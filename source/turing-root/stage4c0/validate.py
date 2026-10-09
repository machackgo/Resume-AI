"""Standalone Stage 4C-0 validator. Saved teacher outputs only; no regeneration.

Run python -B -m stage4c0.validate RECORDS.jsonl [--tokenizer LOCAL_MODEL_DIR]
Exit nonzero on any hard error. Tokenization is CPU-only, local_files_only.
"""
import argparse,json,re
from pathlib import Path
from . import contracts as c
from .grounding import validate_claims,claims
from .io import read_json,read_jsonl,canonical,leaves,digest,sha_file,strict_json
from .analysis import grouped_leakage,token_report

VERSION='stage4c0-validator-v2'

def validate_target(s,target,critic=None):
    errors=c.validate_input(s['input'])+c.validate_output(target,s['input']['task']);soft=[]
    if errors:return {'hard_errors':['SCHEMA:'+e for e in errors],'soft_findings':[],'claims':[]}
    report=validate_claims(s,target);errors+=report['hard_errors'];soft+=report['soft_findings'];inp=s['input'];task=inp['task'];artifact=target['artifact']
    ev={e['evidence_id'] for e in inp['rag']};facts={f['fact_id'] for f in inp['profile']['facts']};events={f['event_id'] for f in inp['profile']['facts']};req={r['requirement_id'] for r in inp['job']['requirements']}
    oracle_reqs={r['requirement_id']:r for r in s['oracle'].get('requirements',[])}
    allowed_req={r['requirement_id'] for r in artifact.get('requirements',[])} if task=='ANALYZE_JOB' else req
    for pointer,value in leaves(target):
        parts=pointer.split('/');parent=parts[-2] if len(parts)>1 else ''
        if parent in ['evidence_ids','selected_evidence_ids','excluded_evidence_ids'] and value not in ev:errors.append('UNKNOWN_EVIDENCE_ID:'+pointer)
        if parent=='fact_ids' and value not in facts:errors.append('UNKNOWN_FACT_ID:'+pointer)
        if parent in ['requirement_ids','selected_requirement_ids'] and value not in allowed_req:errors.append('UNKNOWN_REQUIREMENT_ID:'+pointer)
        if parts[-1]=='event_id' and value not in events:errors.append('UNKNOWN_EVENT_ID:'+pointer)
        if parent=='reference_ids' and value not in ev|facts|events|allowed_req:errors.append('UNKNOWN_TRACE_REFERENCE:'+pointer)
        if isinstance(value,str) and re.search(r'<\|(?:im_start|im_end|endoftext)\|>|PRIVATE[_-]DATA|EV-SECRET|BEGIN PRIVATE',value,re.I):errors.append('PRIVATE_OR_CONTROL_MARKER:'+pointer)
    trace=target['trace']
    if set(trace['selected_evidence_ids'])&set(trace['excluded_evidence_ids']):errors.append('TRACE_SELECTION_CONFLICT')
    used_ev={eid for _,claim in claims(target) for eid in claim['evidence_ids']}
    if not used_ev<=set(trace['selected_evidence_ids']):errors.append('TRACE_OMITS_USED_EVIDENCE')
    # Generative tasks can discover missing mandatory identity fields; a blanket
    # COMPLETE oracle is not a proof that every artifact can be completed.
    # The independent critic checks justified blocking. Exact field-routing cases
    # retain the pre-authored deterministic expected status.
    if task in ('ANSWER_APPLICATION_QUESTION','IDENTIFY_MISSING_INFORMATION') and s['oracle'].get('expected_status') and target['status']!=s['oracle']['expected_status']:errors.append('WRONG_USER_INPUT_REQUIRED_STATUS')
    if target['status']=='COMPLETE':
        if task=='ANALYZE_JOB':
            seen=[]
            for r in artifact['requirements']:
                seen.append(r['requirement_id'])
                span=r['source_span'];text=inp['job']['text']
                if not 0<=span['start']<span['end']<=len(text) or text[span['start']:span['end']]!=span['quote']:errors.append('INVALID_JOB_SPAN')
                for n in r['numeric_constraints']:
                    ns=n['source_span']
                    if text[ns['start']:ns['end']]!=ns['quote'] or n['value'] not in ns['quote']:errors.append('JOB_NUMERIC_MISMATCH')
            if len(seen)!=len(set(seen)):errors.append('DUPLICATE_JOB_REQUIREMENT')
        if task=='MAP_JOB_TO_CANDIDATE':
            mappings=artifact['mappings'];seen=[x['requirement_id'] for x in mappings]
            if set(seen)!=set(oracle_reqs) or len(seen)!=len(set(seen)):errors.append('REQUIREMENT_MAPPING_COVERAGE')
            for m in mappings:
                expected=oracle_reqs.get(m['requirement_id'])
                if m['label'] in ('SUPPORTED','PARTIALLY_SUPPORTED') and (not m['supported_claims'] or not (m['evidence_ids'] or m['fact_ids'])):errors.append('SUPPORTED_MAPPING_WITHOUT_SUPPORT:'+m['requirement_id'])
                if expected and m['label']!=expected['label']:errors.append('WRONG_EVIDENCE_LABEL:'+m['requirement_id'])
                if expected and not set(m['evidence_ids'])<=set(expected['evidence_ids']):errors.append('NONENTAILING_MAPPING_CITATION:'+m['requirement_id'])
                if expected and not set(m['fact_ids'])<=set(expected['fact_ids']):errors.append('NONENTAILING_MAPPING_FACT:'+m['requirement_id'])
                if m['label']=='UNKNOWN' and (m['evidence_ids'] or m['fact_ids'] or m['supported_claims']):errors.append('UNKNOWN_WITH_SUPPORT_CITATION')
        if task=='GENERATE_RESUME':
            sections={x['section'] for x in artifact['sections']}
            if not set(inp['constraints']['required_sections'])<=sections:errors.append('MISSING_REQUIRED_SECTION')
        if task=='GENERATE_RESUME_SECTION' and artifact['section']['section']!=inp['request']['section']:errors.append('WRONG_REQUESTED_SECTION')
        if task=='DRAFT_OUTREACH':
            if artifact['channel']!=inp['request']['channel'] or artifact['purpose']!=inp['request']['purpose']:errors.append('WRONG_OUTREACH_INTENT')
        if task=='ANSWER_APPLICATION_QUESTION' and artifact['question_type']!=inp['request']['question_type']:errors.append('WRONG_QUESTION_TYPE')
        if task=='SELECT_RESUME_CONTENT':
            for sel in artifact['selections']:
                for eid in sel['evidence_ids']:
                    ef=[f for f in s['oracle']['facts'] if eid in f['evidence_ids']]
                    if not ef or not any(f['polarity']=='positive' and f['event_id']==sel['event_id'] and not f['event_id'].startswith('context_') and f['fact_id'] not in inp['constraints']['excluded_fact_ids'] for f in ef):errors.append('SELECTION_UNSUPPORTED_EVIDENCE')
                for fid in sel['fact_ids']:
                    fact=next((f for f in inp['profile']['facts'] if f['fact_id']==fid),None)
                    if fact is None or fact['event_id']!=sel['event_id']:errors.append('SELECTION_EVENT_MISMATCH')
                    if fid in inp['constraints']['excluded_fact_ids']:errors.append('SELECTION_EXCLUDED_FACT')
                    truth=next((f for f in s['oracle']['facts'] if f['fact_id']==fid),None)
                    if truth is None or truth['polarity']!='positive':errors.append('SELECTION_UNSUPPORTED_FACT')
                    if fact and fact['event_id'].startswith('context_'):errors.append('SELECTION_CONTEXT_AS_BIOGRAPHY')
    # Measure rendered content, not audit IDs/trace/schema syntax.
    text='\n'.join(claim['text'] for _,claim in claims(artifact))
    request=inp['request']
    if task=='ANSWER_APPLICATION_QUESTION' and target['status']=='COMPLETE':text=artifact['answer']['text']
    if request['max_words'] is not None and len(text.split())>request['max_words']:errors.append('WORD_LIMIT_EXCEEDED')
    if request['max_characters'] is not None and len(text)>request['max_characters']:errors.append('CHARACTER_LIMIT_EXCEEDED')
    if critic is None:errors.append('INDEPENDENT_CRITIC_REQUIRED')
    else:errors+=['CRITIC:'+x for x in c.validate_critic(critic,inp,target)]
    return {'hard_errors':sorted(set(errors)),'soft_findings':sorted(set(soft)),'claims':report['claims'],'visible_words':len(text.split()),'visible_characters':len(text)}

def validate_provenance_bundle(row,request,teacher,critic_request,critic):
    """Bind saved messages to actual immutable generation/review requests.

    This verifies record integrity, not independently observed backend identity.
    No hidden oracle or historical target is supplied to either model request.
    """
    errors=[]
    try:
        m=row['metadata'];s=row['scenario'];eid=m['example_id']
        target=strict_json(row['messages'][2]['content'])
        for name,value in [('request',request),('teacher',teacher),('critic_request',critic_request),('critic',critic)]:
            if not isinstance(value,dict):return ['PROVENANCE_NOT_OBJECT:'+name]
        request_hash=c.canonical_hash(request);critic_request_hash=c.canonical_hash(critic_request)
        if request_hash!=m['request_sha256']:errors.append('PROVENANCE_REQUEST_HASH')
        if request.get('example_id')!=eid or teacher.get('example_id')!=eid or critic_request.get('example_id')!=eid or critic.get('example_id')!=eid:errors.append('PROVENANCE_EXAMPLE_BINDING')
        if request.get('visible_input')!=s['input']:errors.append('PROVENANCE_VISIBLE_INPUT')
        if teacher.get('request_sha256')!=request_hash:errors.append('PROVENANCE_TEACHER_REQUEST_BINDING')
        if teacher.get('output')!=target:errors.append('PROVENANCE_TEACHER_OUTPUT_BINDING')
        if critic.get('critic_request_sha256')!=critic_request_hash:errors.append('PROVENANCE_CRITIC_REQUEST_BINDING')
        if critic.get('review')!=row['critic']:errors.append('PROVENANCE_CRITIC_REVIEW_BINDING')
        if m.get('critic_request_sha256') is not None and m['critic_request_sha256']!=critic_request_hash:errors.append('PROVENANCE_CRITIC_METADATA_BINDING')
        revision=request.get('revision')
        if type(revision) is not int or not 0<=revision<=c.ACCEPTANCE_GATES['max_revisions'] or revision!=m['revision_count']:errors.append('PROVENANCE_REVISION_BOUND')
        prompt_version=request.get('teacher_prompt_version')
        try:
            expected_system=c.teacher_prompt_text(prompt_version,revision)
        except ValueError:
            expected_system=None
        if expected_system is None or m.get('teacher_prompt_version')!=prompt_version or request.get('system')!=expected_system:errors.append('PROVENANCE_TEACHER_PROMPT')
        allowed={'example_id','teacher_prompt_version','system','visible_input','output_schema','quality_rubric','research_principles','acceptance_gates','requested_teacher','revision'}
        if revision!=0:allowed|={'previous_output','public_revision_requests','deterministic_failure_categories'}
        if set(request)!=allowed:errors.append('PROVENANCE_TEACHER_REQUEST_FIELDS')
        task=s['input']['task']
        if request.get('output_schema')!=c.OUTPUT_SCHEMAS[task] or request.get('quality_rubric')!=c.RUBRIC or request.get('acceptance_gates')!=c.ACCEPTANCE_GATES['per_record']:errors.append('PROVENANCE_CONTRACT_CONTENT')
        if request.get('requested_teacher')!={'model':'gpt-6-astra','reasoning':'ultra'}:errors.append('PROVENANCE_REQUESTED_MODEL')
        principles={}
        for p in (Path(__file__).resolve().parents[1]/'research/stage4c0').glob('*_principles.json'):
            for principle in read_json(p)['principles']:principles[principle['principle_id']]=principle
        expected_principles=[principles[pid] for pid in c.TASK_PRINCIPLES[task]]
        if request.get('research_principles')!=expected_principles:errors.append('PROVENANCE_RESEARCH_CONTENT')
        if critic_request.get('system')!=c.CRITIC_SYSTEM or critic_request.get('critic_prompt_version')!='critic.v1':errors.append('PROVENANCE_CRITIC_PROMPT')
        if critic_request.get('visible_input')!=s['input'] or critic_request.get('proposed_output')!=target:errors.append('PROVENANCE_CRITIC_CONTEXT')
        if critic_request.get('output_sha256')!=c.canonical_hash(target) or critic_request.get('visible_input_sha256')!=c.canonical_hash(s['input']):errors.append('PROVENANCE_CRITIC_CONTEXT_HASH')
        for key in ('output_schema','quality_rubric','research_principles'):
            if critic_request.get(key)!=request.get(key):errors.append('PROVENANCE_CRITIC_CONTRACT:'+key)
        if critic_request.get('critic_schema')!=c.CRITIC_SCHEMA:errors.append('PROVENANCE_CRITIC_SCHEMA')
        expected_inventory={p:{'path':p,'text':t,'text_sha256':c.text_hash(t)} for p,t in c.iter_audit_leaves(target)} if isinstance(target,dict) else {}
        actual_inventory=critic_request.get('required_leaf_inventory')
        # Inventory order follows JSON object insertion order, which canonical
        # serialization may change. Compare unique exact path-bound entries;
        # array indices stay in the pointer and remain semantically ordered.
        inventory_valid=isinstance(actual_inventory,list)
        actual_by_path={}
        if inventory_valid:
            for entry in actual_inventory:
                if not isinstance(entry,dict) or set(entry)!={'path','text','text_sha256'} or not isinstance(entry.get('path'),str) or entry['path'] in actual_by_path:
                    inventory_valid=False;break
                actual_by_path[entry['path']]=entry
        if not inventory_valid or actual_by_path!=expected_inventory:errors.append('PROVENANCE_CRITIC_LEAF_INVENTORY')
        critic_keys={'example_id','critic_prompt_version','system','visible_input','proposed_output','output_sha256','visible_input_sha256','quality_rubric','research_principles','output_schema','critic_schema','required_leaf_inventory'}
        if set(critic_request)!=critic_keys:errors.append('PROVENANCE_CRITIC_REQUEST_FIELDS')
    except (KeyError,ValueError,TypeError,IndexError,OSError) as exc:
        errors.append('MALFORMED_PROVENANCE:'+type(exc).__name__+':'+str(exc))
    return sorted(set(errors))


def validate_provenance(row,provenance_root):
    eid=row.get('metadata',{}).get('example_id','')
    if not isinstance(eid,str) or re.fullmatch(r's4c0_[0-9a-f]{24}',eid) is None:
        return {'passed':False,'errors':['PROVENANCE_UNSAFE_EXAMPLE_ID'],'files':{}}
    directory=Path(provenance_root)/eid;bundle={};errors=[];hashes={}
    for name in ('request','teacher','critic_request','critic'):
        path=directory/(name+'.json')
        try:
            hashes[name]=sha_file(path);bundle[name]=read_json(path)
        except (OSError,ValueError,TypeError) as exc:
            errors.append('PROVENANCE_FILE_UNAVAILABLE_OR_MALFORMED:'+name+':'+type(exc).__name__)
    if not errors:errors=validate_provenance_bundle(row,**bundle)
    return {'passed':not errors,'errors':errors,'files':hashes}


def validate_records(rows,tokenizer=None,require_complete=True,historical_root=None,provenance_root=None):
    errors=[];ids=set();audits=[];provenance_audits=[]
    if not rows:errors.append('EMPTY_DATASET')
    for row in rows:
        try:
            from .pipeline import example_id,messages
            m=row['metadata'];s=row['scenario'];target=strict_json(row['messages'][2]['content'])
            eid=m['example_id']
            if eid in ids:errors.append('DUPLICATE_EXAMPLE_ID:'+eid)
            ids.add(eid)
            if eid!=example_id(s):errors.append('UNSTABLE_EXAMPLE_ID:'+eid)
            if m['task']!=s['input']['task'] or m['split']!=s['split']:errors.append('METADATA_MISMATCH:'+eid)
            if m['split'] not in ['train','validation','test','challenge','pilot']:errors.append('INVALID_SPLIT:'+eid)
            if row['oracle']!=s['oracle'] or m['ground_truth_sha256']!=c.canonical_hash(s['oracle']):errors.append('GROUND_TRUTH_HASH:'+eid)
            if m['input_sha256']!=c.canonical_hash(s['input']):errors.append('INPUT_HASH:'+eid)
            if m['artifact_hash']!=c.canonical_hash(target):errors.append('ARTIFACT_HASH:'+eid)
            if row['messages']!=messages(s,target):errors.append('CHAT_MESSAGE_PROJECTION:'+eid)
            if type(m['revision_count']) is not int or not 0<=m['revision_count']<=c.ACCEPTANCE_GATES['max_revisions']:errors.append('REVISION_BOUND:'+eid)
            if m.get('acceptance_status')!='ACCEPT':errors.append('ACCEPTANCE_STATUS:'+eid)
            if m.get('grounding_status')!='PASS':errors.append('GROUNDING_STATUS:'+eid)
            if m.get('validator_version')!=VERSION or m.get('quality_rubric_version')!=c.VERSION or m.get('teacher_prompt_version') not in c.TEACHER_PROMPT_VERSIONS or m.get('critic_prompt_version')!='critic.v1':errors.append('CONTRACT_VERSION:'+eid)
            report=validate_target(s,target,row['critic']);audits.append({'example_id':eid,**report})
            errors.extend(eid+':'+e for e in report['hard_errors'])
            if provenance_root is not None:
                provenance=validate_provenance(row,provenance_root);provenance_audits.append({'example_id':eid,**provenance})
                errors.extend(eid+':'+e for e in provenance['errors'])
        except (KeyError,ValueError,TypeError,IndexError) as e:errors.append('MALFORMED_RECORD:'+str(e))
    leak=grouped_leakage(rows) if not errors else {'passed':False,'reason':'record validation failed'}
    if not leak['passed']:errors.append('LEAKAGE_AUDIT_FAILED')
    tokens=token_report(rows,tokenizer) if tokenizer is not None and not errors else None
    if tokens:
        counts={x['example_id']:x for x in tokens['examples']}
        for row in rows:
            m=row['metadata']
            if 'qwen_token_counts' in m and m['qwen_token_counts']!={k:counts[m['example_id']][k] for k in ['input_tokens','target_tokens','total_tokens']}:
                errors.append('STORED_TOKEN_COUNTS_MISMATCH:'+m['example_id'])
    if tokens and any(x['total_tokens']>c.ACCEPTANCE_GATES['token_budget']['provisional_complete_conversation_ceiling'] for x in tokens['examples']):errors.append('COMPLETE_SEQUENCE_EXCEEDS_PREREGISTERED_ENVELOPE')
    exclusion=None
    if historical_root is not None and not errors:
        from .exclusion import historical_audit
        exclusion=historical_audit(rows,Path(historical_root))
        if not exclusion['passed']:errors.append('HISTORICAL_EXCLUSION_FAILED')
    if require_complete and tokenizer is None:errors.append('TOKEN_VALIDATION_REQUIRED')
    if require_complete and historical_root is None:errors.append('HISTORICAL_EXCLUSION_REQUIRED')
    if require_complete and provenance_root is None:errors.append('PROVENANCE_VALIDATION_REQUIRED')
    return {'version':VERSION,'passed':not errors,'validation_scope':'complete_saved_dataset_audit' if require_complete else 'explicit_structural_preflight_not_release','release_ready':False,'records':len(rows),'errors':errors,'audits':audits,'leakage':leak,'historical_exclusion':exclusion,'provenance':provenance_audits,'provenance_validation_executed':provenance_root is not None,'tokens':tokens,'token_validation_executed':tokenizer is not None,'release_note':'Release also requires coverage, pilot gate, independent quality audit, near-duplicate disposition, manifest checks and protected-history verification.'}

def main():
    p=argparse.ArgumentParser();p.add_argument('records',type=Path);p.add_argument('--tokenizer',type=Path);p.add_argument('--report',type=Path);p.add_argument('--provenance-root',type=Path);a=p.parse_args()
    tok=None
    if a.tokenizer:
        from transformers import AutoTokenizer
        tok=AutoTokenizer.from_pretrained(a.tokenizer,local_files_only=True)
    result=validate_records(read_jsonl(a.records),tok,historical_root=Path.cwd(),provenance_root=a.provenance_root or a.records.parent/'provenance')
    result['records_file_sha256']=sha_file(a.records)
    if tok is not None:
        result['tokenizer_fingerprint']={'class':type(tok).__name__,'chat_template_sha256':digest(tok.chat_template),'files':{p.name:sha_file(p) for p in a.tokenizer.iterdir() if p.is_file() and ('token' in p.name or p.name in ['vocab.json','merges.txt','chat_template.jinja'])},'model_weights_loaded':False}
    if a.report:
        from .io import write_json
        write_json(a.report,result)
    print(json.dumps({k:result[k] for k in ['passed','records','errors','token_validation_executed']},indent=2))
    if not result['passed']:raise SystemExit(1)
if __name__=='__main__':main()
