"""Novel general contract tests; no protected evaluation data or model claims."""
import copy
import unittest
from resume_pipeline.semantic_contracts import *
from rag.component.decompose import RequirementDecomposer
from rag.retrieval import InformationNeed,NeedType
from test_reranking import Harness
import test_repair
import json

class Contracts(unittest.TestCase):
    def test_shared_technology_does_not_transfer_identity(self):
        for technology in ['Python','RAG','Qwen','LLMs']:
            with self.subTest(technology=technology):
                i=dict(project_label='Boreal',entity_id='b')
                self.assertFalse(identity_compatible('Atlas used '+technology,i,['Atlas','Boreal'])['compatible'])
                self.assertTrue(identity_compatible('Boreal used '+technology,i,['Atlas','Boreal'])['compatible'])
    def test_named_product_identity(self):
        self.assertFalse(identity_compatible('Resume AI evidence ingestion',dict(project_label='VeriBridge AI',entity_id='b'),['Resume-AI','VeriBridge AI'])['compatible'])
    def test_metric_cannot_move(self):
        self.assertFalse(identity_compatible('Reduced Project A latency by 20%',dict(project_label='Project B',entity_id='b'),['Project A','Project B'])['compatible'])
    def test_same_technology_different_achievement(self):
        self.assertFalse(identity_compatible('Python image retrieval in Atlas',dict(project_label='Boreal',entity_id='b'),['Atlas','Boreal'])['compatible'])
    def test_academic_startup_identity(self):
        self.assertFalse(identity_compatible('Atlas Startup API',dict(project_label='Atlas Coursework',entity_id='b'),['Atlas Startup','Atlas Coursework'])['compatible'])
    def test_context_entities_stay_separate(self):
        names=['Atlas','Boreal','Cedar']
        for a in names:
            for b in names:self.assertEqual(identity_compatible(a+' RAG',dict(project_label=b,entity_id=b),names)['compatible'],a==b)
    def test_setup_is_not_achievement(self):
        for text in ['Installed a Python package.','Initialized a database.','Loaded a model.','Created a generic button.','The frontend lives in apps/site and uses React.','FastAPI backend for a student MVP.']:
            self.assertFalse(achievement(text)['standalone'],text)
    def test_substantial_implementation_can_advance_to_audit(self):
        for text in ['Implemented image segmentation with OpenCV for live camera feeds.','Built a retrieval pipeline using PostgreSQL and vector indexing.','On the cloud, sensor data is served from PostgreSQL via an authenticated connector.','Two-branch CNN over short sequences of state/features and button history.']:
            self.assertIsNone(achievement(text)['standalone'],text)
    def test_numeric_processing_not_images(self):
        self.assertFalse(compatible(capability_types('image processing'),capability_types('CNN processing numeric game state and button history')))
    def test_images_are_images(self):
        self.assertTrue(compatible(capability_types('image processing'),capability_types('Processed camera images using OpenCV')))
    def test_hierarchical_vision(self):
        self.assertTrue(compatible(capability_types('image processing'),capability_types('Implemented computer vision object detection')))
    def test_generic_processing_not_images(self):
        self.assertFalse(compatible(capability_types('image processing'),capability_types('generic processing')))
    def test_postgres_not_automatically_pgvector(self):
        self.assertFalse(compatible(capability_types('pgvector vector retrieval'),capability_types('PostgreSQL connectivity')))
        self.assertTrue(compatible(capability_types('PostgreSQL database'),capability_types('PostgreSQL data connector')))
    def test_action_technology_relationship(self):
        r=relationship('Build retrieval services using PostgreSQL','r')
        self.assertEqual(r['action'],['Build']);self.assertEqual(r['object'],'retrieval services');self.assertEqual(r['technology'],['PostgreSQL'])
    def test_action_object_relationship(self):
        r=relationship('Process images using OpenCV','r')
        self.assertEqual(r['object'],'images');self.assertEqual(r['technology'],['OpenCV'])
    def test_purpose_constraint_qualifier(self):
        r=relationship('Use PostgreSQL for retrieval without Redis; preferred','r')
        self.assertTrue(r['purpose']);self.assertTrue(r['constraint']);self.assertIn('preferred',r['qualifier'])
    def test_multiple_technologies(self):
        r=relationship('Build APIs using Python and PostgreSQL','r')
        self.assertEqual(r['technology'],['Python','PostgreSQL']);self.assertEqual(r['object'],'APIs')
    def test_shared_action_binds_next_object_not_last(self):
        d=RequirementDecomposer().decompose(InformationNeed(NeedType.JOB_REQUIREMENT,'Built and deployed containerized services on GCP and implemented SQLite backups.','r'))
        self.assertTrue(any(c.text=='Built services.' for c in d.components))
        self.assertFalse(any('GCP' in c.text and 'SQLite' in c.text for c in d.components))
        self.assertFalse(any(c.text.startswith('Built SQLite') for c in d.components))
        self.assertTrue(all(c.semantic_relationship['parent_requirement_id']=='r' for c in d.components))
    def test_negation_preserved(self):
        text='Build APIs without Flask and do not deploy on AWS.'
        d=RequirementDecomposer().decompose(InformationNeed(NeedType.JOB_REQUIREMENT,text,'r'))
        self.assertEqual([c.text for c in d.components],[text])
    def test_relationship_identity_is_not_keyword_bag(self):
        a=relationship('Build images using Python','r');b=relationship('Build Python using images','r')
        self.assertNotEqual(a['relationship_id'],b['relationship_id']);self.assertNotEqual(a['object'],b['object'])
    def test_every_combined_license_dimension_is_required(self):
        base=dict(candidate_match=True,provenance_valid=True,factual_support=True,project_identity_compatible=True,requirement_semantics_compatible=True,capability_compatible=True,claim_strength_supported=True,contradicted=False,ambiguous=False,resume_worthy=True)
        self.assertTrue(license_contract(**base)['resume_promotion'])
        for key in base:
            x=dict(base);x[key]=not x[key];self.assertFalse(license_contract(**x)['resume_promotion'],key)
    def test_contradiction_quote_does_not_override_negative(self):
        source=dict(evidence_id='s',project_label='Atlas',content='Authentication and database features have not been implemented yet.')
        i=dict(project_label='Atlas');self.assertTrue(unresolved_negative('Built authentication and database features.',i,[source],['Atlas']))
    def test_other_project_negative_is_not_transferred(self):
        source=dict(evidence_id='s',project_label='Boreal',content='Authentication has not been implemented.')
        self.assertFalse(unresolved_negative('Built authentication.',dict(project_label='Atlas'),[source],['Atlas','Boreal']))
    def test_architecture_is_not_completed_implementation(self):
        source=dict(evidence_id='s',project_label='Atlas',content='Authentication has not been implemented.')
        self.assertFalse(unresolved_negative('Architected authentication flows.',dict(project_label='Atlas'),[source],['Atlas']))
    def test_identity_retains_exact_candidate_and_span(self):
        ref=dict(scope={'candidate_id':'a'},source_id='s',source_version=1,evidence_id='e')
        unit=dict(text='Built an API.',start=20,end=33,source_context={'text':'Atlas | Academic project','start':0})
        i=identity(ref,unit);self.assertEqual(i['candidate_id'],'a');self.assertEqual(i['canonical_evidence_id'],'e');self.assertEqual(i['provenance'],dict(source_version=1,start=20,end=33))
        other=copy.deepcopy(ref);other['scope']['candidate_id']='b';self.assertNotEqual(i['entity_id'],identity(other,unit)['entity_id'])

class FallbackContracts(Harness,unittest.TestCase):
    pipeline=test_repair.IntegrationTests.pipeline
    def test_postgresql_gets_license_despite_empty_selector(self):
        text='Sensor data is served from PostgreSQL via an authenticated Python connector.'
        self.add('postgres-project',text)
        p=self.pipeline();calls=[]
        class Model:
            def token_count(self,m):return len(str(m))//4
            def generate(self,m):
                task=json.loads(m[-1]['content']);calls.append(task)
                if 'claim' not in task:
                    return {'text':json.dumps(dict(requirements=[dict(requirement_id=r['requirement_id'],label='UNSUPPORTED',evidence_ids=[],reason='Selector declined') for r in task['requirements']],selected_quotes=[]))}
                okay=task['claim']==text
                obj=dict(support='SUPPORTED' if okay else 'UNSUPPORTED',event_id=task['event_id'],evidence_ids=[task['sources'][0]['evidence_id']] if okay else [],counterevidence_ids=[],reason='Independent synthetic connector support')
                if task['requirements']:obj.update(eligibility='A',links=[dict(requirement_id=r['requirement_id'],supported=okay,reason='Database connectivity only; no production-scale claim') for r in task['requirements']])
                return {'text':json.dumps(obj)}
        p.model=Model();result=p.run('Implemented PostgreSQL connectivity.','A')
        self.assertEqual(result['status'],'COMPLETE',result.get('error'))
        self.assertEqual([c['text'] for c in result['resume']['sections'][0]['claims']],[text])
        self.assertTrue(any(t.get('claim')==text for t in calls))
        self.assertFalse(any(t.get('selection_mode')=='fallback' for t in calls))
    def test_rejection_in_one_entity_does_not_suppress_another(self):
        from resume_pipeline.semantic_policy import ranked_candidates
        from resume_pipeline.licensing import event_identity
        text='Built a Python retrieval pipeline.'
        ref=dict(scope={'candidate_id':'A'},source_id='s',source_version=1,evidence_id='e',origin='candidate_supplied')
        a=dict(text=text,start=20,end=53,source_context={'text':'Atlas | project','start':0})
        b=dict(text=text,start=120,end=153,source_context={'text':'Boreal | project','start':100})
        units={'a':dict(reference=ref,allowed_quotes=[a]),'b':dict(reference=ref,allowed_quotes=[b])}
        review=dict(accepted=False,support='CONTRADICTED',eligibility='F',event_id=event_identity(ref,a),quote=dict(evidence_id='a',quote=text,requirement_ids=['r']))
        rows=ranked_candidates(units,{'r':{'a','b'}},['a','b'],[dict(requirement_id='r',text='Built Python retrieval.')],[review],[],set())
        self.assertEqual([r['evidence_id'] for r in rows],['b'])
