"""Code-audit fixtures only: no teacher outputs or historical answers are read.

These tests exercise deterministic rejection boundaries. Mock critic reports are
unit-test scaffolding, never curriculum acceptance or semantic review evidence.
"""
import copy
import inspect
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch
from . import contracts as c
from . import analysis, exclusion, pipeline
from .validate import validate_records, validate_target, VERSION as VALIDATOR_VERSION


def scenario(task='IDENTIFY_MISSING_INFORMATION'):
    content='Built FastAPI inference endpoints and reduced median latency by 31%.'
    public={'schema_version':c.VERSION,'task':task,
        'job':{'job_id':'J1','text':'Required: build FastAPI inference endpoints.','requirements':[{'requirement_id':'R1','text':'Build FastAPI inference endpoints.','kind':'REQUIRED_QUALIFICATION','source_quote':'Required: build FastAPI inference endpoints.'}]},
        'profile':{'candidate_id':'C1','facts':[{'fact_id':'F1','event_id':'P1','field':'claim','value':content,'provenance':'EXTERNAL_OBSERVED'}]},
        'rag':[{'evidence_id':'E1','event_id':'P1','content':content,'source_id':'S1','source_type':'external_observation','origin':'unit_test_fixture','trust':'untrusted_data','verification':{'reference_policy':'resolve_supports','meaning':'Exact scoped support.'},'authenticated_attestations':[],'citation_handle':{'source_version':1,'span':[0,len(content)]}}],
        'request':{'instruction':'Identify material missing information.','section':None,'question':None,'question_type':None,'max_words':None,'max_characters':None,'channel':None,'purpose':None,'source_bullet':None},
        'constraints':{'locale':'en-US','as_of_date':'2026-09-29','excluded_fact_ids':[],'required_sections':[]}}
    fact={'fact_id':'F1','event_id':'P1','owner':'C1','kind':'claim','evidence_ids':['E1'],'action':'built','technologies':['FastAPI'],'numbers':['31%'],'entities':[],'polarity':'positive','provenance':'EXTERNAL_OBSERVED'}
    return {'scenario_id':'UNIT-S1','split':'train','input':public,'oracle':{'candidate_id':'C1','facts':[fact],'requirements':[{'requirement_id':'R1','label':'SUPPORTED','evidence_ids':['E1'],'fact_ids':['F1']}]},'metadata':{'scenario_family':'G1','template_family':'T1','candidate_archetype':'C1','job_archetype':'J1','counterfactual_group':None,'split_group':'G1'}}


def target(s,artifact=None):
    return {'schema_version':c.VERSION,'task':s['input']['task'],'status':'COMPLETE','artifact':artifact if artifact is not None else {'missing_information':[]},'trace':{'selected_requirement_ids':[],'selected_evidence_ids':[],'excluded_evidence_ids':[],'principle_ids':[c.TASK_PRINCIPLES[s['input']['task']][0]],'decisions':[]}}


def mock_critic(s,t):
    # Intended only for outputs with no prose leaves in isolated plumbing tests.
    return {'schema_version':c.VERSION,'output_sha256':c.canonical_hash(t),'visible_input_sha256':c.canonical_hash(s['input']),'leaf_reviews':[],
        'rubric_scores':{k:4 for k in c.RUBRIC['dimensions']},'rubric_assessments':{k:'Unit-test mock; no semantic certification.' for k in c.RUBRIC['dimensions']},
        'decision':'ACCEPT','revision_requests':[],'independence':'fresh_context_no_teacher_rationale_no_hidden_oracle'}


def record():
    s=scenario();t=target(s)
    m=dict(s['metadata'],example_id=pipeline.example_id(s),scenario_id=s['scenario_id'],task=s['input']['task'],split=s['split'],
        revision_count=0,acceptance_status='ACCEPT',grounding_status='PASS',validator_version=VALIDATOR_VERSION,quality_rubric_version=c.VERSION,
        teacher_prompt_version='teacher.v1',critic_prompt_version='critic.v1',ground_truth_sha256=c.canonical_hash(s['oracle']),input_sha256=c.canonical_hash(s['input']),artifact_hash=c.canonical_hash(t),request_sha256='0'*64)
    return {'messages':pipeline.messages(s,t),'metadata':m,'scenario':s,'oracle':copy.deepcopy(s['oracle']),'critic':mock_critic(s,t)}


def preflight(rows):
    # During the audit the owning agent adds explicit non-release preflight mode.
    kwargs={'require_complete':False} if 'require_complete' in inspect.signature(validate_records).parameters else {}
    return validate_records(rows,**kwargs)


def append_unrelated(s,negative=False):
    text='No SQL implementation experience.' if negative else 'Used SQL to inspect archive records.'
    f={'fact_id':'F2','event_id':'P2','field':'claim','value':text,'provenance':'EXTERNAL_OBSERVED'}
    s['input']['profile']['facts'].append(f)
    e=copy.deepcopy(s['input']['rag'][0]);e.update(evidence_id='E2',event_id='P2',source_id='S2',content=text);e['citation_handle']['span']=[0,len(text)];s['input']['rag'].append(e)
    s['oracle']['facts'].append({'fact_id':'F2','event_id':'P2','owner':'C1','kind':'claim','evidence_ids':['E2'],'action':'used','technologies':['SQL'],'numbers':[],'entities':[],'polarity':'negative' if negative else 'positive','provenance':'EXTERNAL_OBSERVED'})


class StandaloneAuditTests(unittest.TestCase):
    def test_empty_dataset_cannot_pass_release(self):
        result=validate_records([])
        self.assertFalse(result['passed'])
        self.assertTrue(any('EMPTY' in x for x in result['errors']))

    def test_release_requires_real_token_validation(self):
        result=validate_records([record()])
        self.assertFalse(result['passed'])
        self.assertTrue(any('TOKEN' in x for x in result['errors']))

    def test_revision_scalar_is_bounded_nonboolean_integer(self):
        for value in [-1,True,0.5,'0',3]:
            with self.subTest(value=value):
                r=record();r['metadata']['revision_count']=value
                result=preflight([r])
                self.assertTrue(any('REVISION' in x or 'MALFORMED_RECORD' in x for x in result['errors']))

    def test_rejected_metadata_cannot_enter_accepted_records(self):
        r=record();r['metadata']['acceptance_status']='REJECT'
        self.assertTrue(any('ACCEPTANCE_STATUS' in x for x in preflight([r])['errors']))

    def test_failed_grounding_metadata_cannot_enter_release(self):
        r=record();r['metadata']['grounding_status']='NOT_ACCEPTED'
        self.assertTrue(any('GROUNDING_STATUS' in x for x in preflight([r])['errors']))

    def test_unknown_contract_version_rejected(self):
        r=record();r['metadata']['quality_rubric_version']='unregistered-override'
        self.assertTrue(any('CONTRACT_VERSION' in x or 'VERSION_MISMATCH' in x for x in preflight([r])['errors']))

    def test_exact_input_hash_bound(self):
        r=record();r['metadata']['input_sha256']='1'*64
        self.assertTrue(any('INPUT_HASH' in x for x in preflight([r])['errors']))

    def test_oracle_hash_bound(self):
        r=record();r['oracle']['facts'][0]['numbers']=['99%']
        self.assertTrue(any('GROUND_TRUTH_HASH' in x for x in preflight([r])['errors']))

    def test_critic_hash_bound(self):
        r=record();r['critic']['output_sha256']='2'*64
        self.assertTrue(any('wrong artifact hash' in x for x in preflight([r])['errors']))

    def test_strict_task_envelope(self):
        s=scenario();t=target(s);t['task']='ANALYZE_JOB'
        self.assertTrue(any('SCHEMA' in x for x in validate_target(s,t)['hard_errors']))

    def test_unknown_scalar_trace_reference_rejected(self):
        s=scenario();t=target(s);t['trace']['decisions']=[{'code':'REQUEST_FACT','reference_ids':['UNKNOWN']}]
        self.assertTrue(any('UNKNOWN_TRACE_REFERENCE' in x for x in validate_target(s,t)['hard_errors']))

    def test_private_marker_rejected_outside_claim_wrapper(self):
        s=scenario();t=target(s,{'missing_information':[{'field':'work_authorization','reason':'ABSENT','question':'Provide EV-SECRET details.','requirement_ids':[]}]})
        self.assertTrue(any('PRIVATE_OR_CONTROL_MARKER' in x for x in validate_target(s,t)['hard_errors']))

    def test_mapping_fact_reference_must_support_requirement(self):
        s=scenario('MAP_JOB_TO_CANDIDATE');append_unrelated(s)
        t=target(s,{'mappings':[{'requirement_id':'R1','label':'SUPPORTED','supported_claims':[],'evidence_ids':[],'fact_ids':['F2'],'gaps':[]}]})
        self.assertTrue(any('NONENTAILING_MAPPING_FACT' in x for x in validate_target(s,t)['hard_errors']))

    def test_supported_mapping_cannot_have_no_support(self):
        s=scenario('MAP_JOB_TO_CANDIDATE')
        t=target(s,{'mappings':[{'requirement_id':'R1','label':'SUPPORTED','supported_claims':[],'evidence_ids':[],'fact_ids':[],'gaps':[]}]})
        self.assertTrue(any('MAPPING_WITHOUT_SUPPORT' in x or 'MISSING_MAPPING_SUPPORT' in x for x in validate_target(s,t)['hard_errors']))

    def test_selection_evidence_alone_cannot_bypass_event_or_polarity(self):
        s=scenario('SELECT_RESUME_CONTENT');append_unrelated(s,negative=True)
        t=target(s,{'selections':[{'event_id':'P1','section':'EXPERIENCE','fact_ids':[],'evidence_ids':['E2'],'requirement_ids':['R1'],'priority':1}],'omissions':[],'section_order':['EXPERIENCE']})
        self.assertTrue(any('SELECTION_EVENT_MISMATCH' in x or 'SELECTION_UNSUPPORTED_EVIDENCE' in x for x in validate_target(s,t)['hard_errors']))


class RequestAndLeakageAuditTests(unittest.TestCase):
    def test_changed_request_cannot_be_sent_to_critic(self):
        s=scenario();t=target(s)
        req={'visible_input':s['input'],'quality_rubric':c.RUBRIC,'research_principles':[],'output_schema':c.OUTPUT_SCHEMAS[s['input']['task']]}
        eid=pipeline.example_id(s);old_hash=c.canonical_hash(req)
        with tempfile.TemporaryDirectory() as d:
            run=Path(d)
            (run/'requests').mkdir();(run/'teacher').mkdir()
            (run/'registry.jsonl').write_text(json.dumps({'example_id':eid,'request_sha256':old_hash})+'\n')
            (run/'teacher'/f'{eid}.json').write_text(json.dumps({'example_id':eid,'request_sha256':old_hash,'output':t}))
            req['visible_input']['request']['instruction']='Tampered after teacher execution.'
            (run/'requests'/f'{eid}.json').write_text(json.dumps(req))
            with self.assertRaises((ValueError,KeyError)):
                pipeline.critic_requests(run,Path(d))

    def test_split_group_is_an_explicit_leakage_edge(self):
        a=record();b=copy.deepcopy(a)
        b['metadata'].update(split='challenge',scenario_family='other',template_family='other',candidate_archetype='other',job_archetype='other')
        b['messages'][1]['content']+=' different'
        b['messages'][2]['content']+=' different'
        b['scenario']['input']['profile']['candidate_id']='C2';b['scenario']['input']['job']['job_id']='J2'
        result=analysis.grouped_leakage([a,b])
        self.assertFalse(result['passed'])

    def test_actual_candidate_identity_cannot_hide_behind_metadata_alias(self):
        a=record();b=copy.deepcopy(a)
        b['metadata'].update(split='test',scenario_family='other',template_family='other',candidate_archetype='other',job_archetype='other',split_group='other')
        b['messages'][1]['content']+=' different'
        b['messages'][2]['content']+=' different'
        b['scenario']['input']['job']['job_id']='J2'
        self.assertFalse(analysis.grouped_leakage([a,b])['passed'])

    def test_missing_group_metadata_fails_closed(self):
        r=record()
        for key in ['scenario_family','template_family','candidate_archetype','job_archetype','split_group']:
            r['metadata'].pop(key)
        self.assertFalse(analysis.grouped_leakage([r])['passed'])

    def test_historical_empty_fingerprint_inventory_is_not_clean(self):
        parent=types.ModuleType('stage4a');parent.__path__=[]
        module=types.ModuleType('stage4a.validate');module.historical_index=lambda:{'normalized_texts':[],'files':{}}
        with tempfile.TemporaryDirectory() as d,patch.dict(sys.modules,{'stage4a':parent,'stage4a.validate':module}):
            p=Path(d)/'datasets/stage4a/v1/test.jsonl';p.parent.mkdir(parents=True);p.write_text('')
            try:
                result=exclusion.historical_audit([record()],Path(d))
            except (ValueError,RuntimeError):
                return
            self.assertFalse(result['passed'])


class TokenBoundaryAuditTests(unittest.TestCase):
    def run_encoded(self,encoded):
        parent=types.ModuleType('stage4a');parent.__path__=[]
        module=types.ModuleType('stage4a.data');module.tokenized=lambda row,tok:encoded
        with patch.dict(sys.modules,{'stage4a':parent,'stage4a.data':module}):
            return analysis.token_report([record()],object())

    def test_declared_counts_must_equal_actual_token_sequence(self):
        encoded={'input_tokens':2,'target_tokens':2,'total_tokens':4,'input_ids':[1,2,3],'labels':[-100,-100,3]}
        with self.assertRaises(ValueError):self.run_encoded(encoded)

    def test_zero_assistant_target_is_rejected(self):
        encoded={'input_tokens':2,'target_tokens':0,'total_tokens':2,'input_ids':[1,2],'labels':[-100,-100]}
        with self.assertRaises(ValueError):self.run_encoded(encoded)

    def test_prompt_loss_unmasked_rejected(self):
        encoded={'input_tokens':2,'target_tokens':1,'total_tokens':3,'input_ids':[1,2,3],'labels':[1,-100,3]}
        with self.assertRaises(ValueError):self.run_encoded(encoded)

# Kept below the earlier classes so each fixture can be used independently.
def provenance_fixture():
    r=record();s=r['scenario'];t=json.loads(r['messages'][2]['content']);eid=r['metadata']['example_id']
    research=pipeline.research(Path(__file__).resolve().parents[1])
    request={'example_id':eid,'teacher_prompt_version':'teacher.v1','system':c.TEACHER_SYSTEM,'visible_input':s['input'],'output_schema':c.OUTPUT_SCHEMAS[s['input']['task']],
        'quality_rubric':c.RUBRIC,'research_principles':[research[p] for p in c.TASK_PRINCIPLES[s['input']['task']]],'acceptance_gates':c.ACCEPTANCE_GATES['per_record'],'requested_teacher':{'model':'gpt-6-astra','reasoning':'ultra'},'revision':0}
    teacher={'example_id':eid,'request_sha256':c.canonical_hash(request),'output':t}
    critic_request={'example_id':eid,'critic_prompt_version':'critic.v1','system':c.CRITIC_SYSTEM,'visible_input':s['input'],'proposed_output':t,'output_sha256':c.canonical_hash(t),'visible_input_sha256':c.canonical_hash(s['input']),
        'quality_rubric':request['quality_rubric'],'research_principles':request['research_principles'],'output_schema':request['output_schema'],'critic_schema':c.CRITIC_SCHEMA,
        'required_leaf_inventory':[{'path':p,'text':v,'text_sha256':c.text_hash(v)} for p,v in c.iter_audit_leaves(t)]}
    critic={'example_id':eid,'critic_request_sha256':c.canonical_hash(critic_request),'review':r['critic']}
    r['metadata'].update(request_sha256=c.canonical_hash(request),critic_request_sha256=c.canonical_hash(critic_request))
    return r,{'request':request,'teacher':teacher,'critic_request':critic_request,'critic':critic}


def write_mock_run(root,r,bundle,malformed=None):
    eid=r['metadata']['example_id'];s=r['scenario']
    for name,directory in [('request','requests'),('teacher','teacher'),('critic_request','critic_requests'),('critic','critic')]:
        path=root/directory/(eid+'.json');path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text('{malformed' if name==malformed else json.dumps(bundle[name]))
    registry={'example_id':eid,'scenario':s,'request_sha256':r['metadata']['request_sha256'],'input_sha256':c.canonical_hash(s['input']),'ground_truth_sha256':c.canonical_hash(s['oracle'])}
    (root/'registry.jsonl').write_text(json.dumps(registry)+'\n')


class ProvenanceAuditTests(unittest.TestCase):
    def check(self,r,bundle):
        from .validate import validate_provenance_bundle
        return validate_provenance_bundle(r,**bundle)

    def test_intact_mock_provenance_passes_integrity_only(self):
        r,b=provenance_fixture()
        self.assertEqual(self.check(r,b),[])

    def inventory_fixture(self):
        r,b=provenance_fixture()
        t=b['teacher']['output']
        t['artifact']={'missing_information':[{'field':'availability','reason':'ABSENT','question':'When can you start?','requirement_ids':[]}]}
        r['messages']=pipeline.messages(r['scenario'],t)
        r['metadata']['artifact_hash']=c.canonical_hash(t)
        b['critic_request']['output_sha256']=c.canonical_hash(t)
        b['critic_request']['required_leaf_inventory']=[{'path':p,'text':v,'text_sha256':c.text_hash(v)} for p,v in c.iter_audit_leaves(t)]
        b['critic']['review']['output_sha256']=c.canonical_hash(t)
        self.rebind_critic_request(r,b)
        return r,b

    def rebind_critic_request(self,r,b):
        h=c.canonical_hash(b['critic_request'])
        b['critic']['critic_request_sha256']=h;r['metadata']['critic_request_sha256']=h

    def test_inventory_object_key_order_is_nonsemantic(self):
        r,b=self.inventory_fixture()
        b['critic_request']['required_leaf_inventory'].reverse()
        self.rebind_critic_request(r,b)
        self.assertEqual(self.check(r,b),[])

    def test_inventory_duplicate_path_cannot_be_hidden_by_mapping(self):
        r,b=self.inventory_fixture()
        b['critic_request']['required_leaf_inventory'].append(copy.deepcopy(b['critic_request']['required_leaf_inventory'][0]))
        self.rebind_critic_request(r,b)
        self.assertIn('PROVENANCE_CRITIC_LEAF_INVENTORY',self.check(r,b))

    def test_inventory_missing_leaf_rejected(self):
        r,b=self.inventory_fixture();b['critic_request']['required_leaf_inventory'].pop()
        self.rebind_critic_request(r,b)
        self.assertIn('PROVENANCE_CRITIC_LEAF_INVENTORY',self.check(r,b))

    def test_inventory_wrong_text_or_array_position_rejected(self):
        for field,value in [('text','Changed text'),('text_sha256','f'*64),('path','/artifact/missing_information/1/field')]:
            with self.subTest(field=field):
                r,b=self.inventory_fixture();b['critic_request']['required_leaf_inventory'][0][field]=value
                self.rebind_critic_request(r,b)
                self.assertIn('PROVENANCE_CRITIC_LEAF_INVENTORY',self.check(r,b))

    def test_complete_validation_requires_provenance(self):
        result=validate_records([record()])
        self.assertIn('PROVENANCE_VALIDATION_REQUIRED',result['errors'])

    def test_teacher_wrapper_must_bind_exact_request(self):
        r,b=provenance_fixture();b['teacher']['request_sha256']='f'*64
        self.assertIn('PROVENANCE_TEACHER_REQUEST_BINDING',self.check(r,b))

    def test_critic_wrapper_must_bind_exact_request(self):
        r,b=provenance_fixture();b['critic'].pop('critic_request_sha256')
        self.assertIn('PROVENANCE_CRITIC_REQUEST_BINDING',self.check(r,b))

    def test_request_cannot_contain_hidden_oracle_even_when_rehashed(self):
        r,b=provenance_fixture();b['request']['oracle']={'expected':'secret'}
        h=c.canonical_hash(b['request']);r['metadata']['request_sha256']=h;b['teacher']['request_sha256']=h
        self.assertIn('PROVENANCE_TEACHER_REQUEST_FIELDS',self.check(r,b))

    def test_rehashed_schema_override_still_rejected(self):
        r,b=provenance_fixture();b['request']=copy.deepcopy(b['request'])
        b['request']['output_schema']={'type':'object'}
        h=c.canonical_hash(b['request']);r['metadata']['request_sha256']=h;b['teacher']['request_sha256']=h
        self.assertIn('PROVENANCE_CONTRACT_CONTENT',self.check(r,b))

    def test_critic_inventory_must_match_current_whole_artifact_traversal(self):
        r,b=provenance_fixture();b['critic_request']['required_leaf_inventory']=[{'path':'/artifact/imaginary','text':'invented','text_sha256':c.text_hash('invented')}]
        b['critic']['critic_request_sha256']=c.canonical_hash(b['critic_request'])
        r['metadata']['critic_request_sha256']=c.canonical_hash(b['critic_request'])
        self.assertIn('PROVENANCE_CRITIC_LEAF_INVENTORY',self.check(r,b))

    def test_provenance_files_fail_when_a_required_sidecar_is_missing(self):
        from .validate import validate_provenance
        r,b=provenance_fixture()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);folder=root/r['metadata']['example_id'];folder.mkdir()
            for name,value in b.items():
                if name!='critic_request':(folder/(name+'.json')).write_text(json.dumps(value))
            result=validate_provenance(r,root)
            self.assertFalse(result['passed'])
            self.assertTrue(any('critic_request' in x for x in result['errors']))

    def test_provenance_safe_id_rejects_path_traversal(self):
        from .validate import validate_provenance
        r,_=provenance_fixture();r['metadata']['example_id']='../../outside'
        self.assertEqual(validate_provenance(r,'.')['errors'],['PROVENANCE_UNSAFE_EXAMPLE_ID'])

    def test_malformed_teacher_is_preserved_and_counted_rejected(self):
        r,b=provenance_fixture()
        with tempfile.TemporaryDirectory() as d:
            run=Path(d)/'run';run.mkdir();write_mock_run(run,r,b,malformed='teacher')
            summary=pipeline.audit(run,Path(__file__).resolve().parents[1],Path(d)/'audit')
            self.assertEqual((summary['attempted'],summary['accepted'],summary['rejected']),(1,0,1))
            attempts=[json.loads(x) for x in (Path(d)/'audit/attempts.jsonl').read_text().splitlines()]
            self.assertTrue(any('MALFORMED_TEACHER_RESPONSE' in x for x in attempts[0]['hard_errors']))
            self.assertEqual((run/'teacher'/(r['metadata']['example_id']+'.json')).read_text(),'{malformed')
            self.assertIn('teacher',attempts[0]['raw_response_sha256'])

    def test_malformed_critic_is_preserved_and_counted_rejected(self):
        r,b=provenance_fixture()
        with tempfile.TemporaryDirectory() as d:
            run=Path(d)/'run';run.mkdir();write_mock_run(run,r,b,malformed='critic')
            summary=pipeline.audit(run,Path(__file__).resolve().parents[1],Path(d)/'audit')
            self.assertEqual((summary['attempted'],summary['accepted'],summary['rejected']),(1,0,1))
            attempts=[json.loads(x) for x in (Path(d)/'audit/attempts.jsonl').read_text().splitlines()]
            self.assertTrue(any('MALFORMED_CRITIC_RESPONSE' in x for x in attempts[0]['hard_errors']))
            self.assertIn('critic',attempts[0]['raw_response_sha256'])

    def test_revision_refuses_wrong_prior_critic_binding(self):
        r,b=provenance_fixture();b['critic']['critic_request_sha256']='f'*64
        with tempfile.TemporaryDirectory() as d:
            run=Path(d)/'run';run.mkdir();write_mock_run(run,r,b)
            audit=Path(d)/'audit';audit.mkdir()
            (audit/'attempts.jsonl').write_text(json.dumps({'example_id':r['metadata']['example_id'],'acceptance_status':'REJECT','hard_errors':['TEST_ONLY']})+'\n')
            with self.assertRaisesRegex(ValueError,'REVISION_PROVENANCE_BINDING'):
                pipeline.prepare_revision(run,Path(d)/'revision',audit)


class TeacherV2RoutingTests(unittest.TestCase):
    def test_original_v1_prompt_bytes_unchanged(self):
        root=Path(__file__).resolve().parents[1]
        self.assertEqual((root/'contracts/prompts/teacher.v1.txt').read_text(),c.TEACHER_SYSTEM)
        manifest=json.loads((root/'contracts/manifest.v1.json').read_text())
        from .io import sha_file
        self.assertEqual(sha_file(root/'contracts/prompts/teacher.v1.txt'),manifest['files']['contracts/prompts/teacher.v1.txt'])

    def test_prepare_defaults_v2_and_explicit_v1_remains_available(self):
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as d:
            scenarios=Path(d)/'scenarios.jsonl';scenarios.write_text(json.dumps(scenario())+'\n')
            for version in ('teacher.v2','teacher.v1'):
                run=Path(d)/version
                rows=pipeline.prepare(scenarios,run,root) if version=='teacher.v2' else pipeline.prepare(scenarios,run,root,version)
                req=json.loads((run/'requests'/(rows[0]['example_id']+'.json')).read_text())
                self.assertEqual(req['teacher_prompt_version'],version)
                self.assertEqual(req['system'],c.teacher_prompt_text(version))
                self.assertEqual(req['visible_input'],scenario()['input'])

    def test_v2_exact_provenance_template_accepted_and_unregistered_edit_rejected(self):
        from .validate import validate_provenance_bundle
        r,b=provenance_fixture()
        b['request']['teacher_prompt_version']='teacher.v2';b['request']['system']=c.TEACHER_SYSTEM_V2
        r['metadata']['teacher_prompt_version']='teacher.v2'
        h=c.canonical_hash(b['request']);r['metadata']['request_sha256']=h;b['teacher']['request_sha256']=h
        self.assertEqual(validate_provenance_bundle(r,**b),[])
        b['request']['system']+=' Unregistered override.'
        h=c.canonical_hash(b['request']);r['metadata']['request_sha256']=h;b['teacher']['request_sha256']=h
        self.assertIn('PROVENANCE_TEACHER_PROMPT',validate_provenance_bundle(r,**b))

    def test_revision_preserves_each_base_prompt_lineage(self):
        for version in ('teacher.v1','teacher.v2'):
            with self.subTest(version=version),tempfile.TemporaryDirectory() as d:
                r,b=provenance_fixture()
                b['request']['teacher_prompt_version']=version;b['request']['system']=c.teacher_prompt_text(version)
                r['metadata']['teacher_prompt_version']=version
                h=c.canonical_hash(b['request']);r['metadata']['request_sha256']=h;b['teacher']['request_sha256']=h
                run=Path(d)/'run';run.mkdir();write_mock_run(run,r,b)
                audit=Path(d)/'audit';audit.mkdir()
                attempt={'example_id':r['metadata']['example_id'],'acceptance_status':'REJECT','hard_errors':['UNIT_TEST_ONLY'],
                    'request_sha256':h,'artifact_hash':c.canonical_hash(b['teacher']['output']),'critic_request_sha256':c.canonical_hash(b['critic_request'])}
                (audit/'attempts.jsonl').write_text(json.dumps(attempt)+'\n')
                out=Path(d)/'revision';rows=pipeline.prepare_revision(run,out,audit)
                req=json.loads((out/'requests'/(rows[0]['example_id']+'.json')).read_text())
                expected_version=version.replace('teacher.','revision.')
                self.assertEqual(req['teacher_prompt_version'],expected_version)
                self.assertEqual(req['system'],c.teacher_prompt_text(expected_version,1))
                self.assertEqual(req['visible_input'],r['scenario']['input'])

    def test_prompt_revision_index_is_type_and_version_checked(self):
        for version,index in [('teacher.v2',1),('revision.v1',0),('revision.v2',True),('revision.v2',3),('teacher.v9',0)]:
            with self.subTest(version=version,index=index),self.assertRaises(ValueError):
                c.teacher_prompt_text(version,index)


if __name__=='__main__':unittest.main()
