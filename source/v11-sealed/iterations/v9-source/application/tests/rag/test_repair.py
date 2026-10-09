"""Repair regressions use new synthetic controls, never protected fixtures."""
import json,unittest
from dataclasses import replace
from test_reranking import Harness
from rag.reasoning.contract import context,citation_id
from rag.component.retrieve import fair_merge
from rag.adapters import PlainTextAdapter
from rag.chunking.policy import POLICY_B
from rag.deep.raw import focused_spans
from resume_pipeline.pipeline import ResumePipeline,requirements
from rag.embeddings.models import EmbeddingConfig
from rag.domain import Scope

class Tokenizer:
    def __call__(self,text,**kw):return {'input_ids':list(range(len(text.encode())+2))}
class Provider:
    config=EmbeddingConfig('test','token-budget','v1',2,True)
    tokenizer=Tokenizer();max_tokens=180

class RepairTests(Harness,unittest.TestCase):
    def test_historical_multiple_chunks_one_document(self):
        self.add('document','Built Python APIs. '*45+'Deployed a SQL service. '*45)
        ctx,_=context(self.scope,self.response(),self.resolver)
        refs=list(ctx['provenance'].values())
        self.assertGreater(len(refs),1)
        self.assertEqual(len({r['reference']['evidence_id'] for r in refs}),1)
        self.assertEqual(len({r['reference']['chunk_id'] for r in refs}),len(refs))
        self.assertTrue(all(r['content'] for r in refs))
    def test_citation_stable_under_order_and_embedding_change(self):
        response=self.two();ref=response.results[0].reference
        self.assertEqual(citation_id(ref),citation_id(replace(ref,embedding_id='new_vector_space')))
        a,_=context(self.scope,response,self.resolver)
        self.assertEqual(set(a['provenance']),{citation_id(r.reference) for r in response.results})
    def test_candidate_source_chunk_aware_identity(self):
        ref=self.two().results[0].reference
        variants=[replace(ref,scope=Scope('tenant','B')),replace(ref,source_id='different'),replace(ref,chunk_id='different'),replace(ref,source_version=2)]
        self.assertEqual(len({citation_id(ref),*(citation_id(x) for x in variants)}),5)
    def test_duplicate_sources_keep_both_provenances(self):
        self.add('a','Implemented FastAPI.');self.add('b','Implemented FastAPI.')
        ctx,_=context(self.scope,self.response(),self.resolver)
        self.assertEqual(len(ctx['groups']),1);self.assertEqual(len(ctx['provenance']),2)
        self.assertEqual(len({r['reference']['source_id'] for r in ctx['provenance'].values()}),2)
    def test_component_mapping_uses_public_citations(self):
        response=self.two();rows,mapping,_=fair_merge({'c1':response.results,'c2':response.results},5,self.resolver)
        ctx,_=context(self.scope,response,self.resolver)
        self.assertEqual({e for m in mapping for e in m['evidence_ids']},{r.reference.evidence_id for r in response.results})
        self.assertEqual(set(ctx['provenance']),{citation_id(r.reference) for r in rows})
    def test_fit_preserves_exact_source_coverage(self):
        text='Implemented naïve Python APIs and tests. '*30
        e=self.ledger.ingest(PlainTextAdapter('overflow',text)).evidence
        original=self.service.generate(e.evidence_id,POLICY_B)
        fitted=self.service.fit_for_embedding(original,Provider())
        self.assertGreater(len(fitted),len(original));covered=set()
        for c in fitted:
            self.assertEqual(text[c.start:c.end],c.text);self.assertEqual(self.service.cite(c.chunk_id).chunk,c)
            covered.update(range(c.start,c.end))
        self.assertEqual(covered,set(range(len(text))))
        self.assertEqual(fitted,self.service.fit_for_embedding(original,Provider()))
    def test_fit_keeps_already_valid_identity(self):
        e=self.ledger.ingest(PlainTextAdapter('short','Built API.')).evidence
        original=self.service.generate(e.evidence_id)
        self.assertEqual(self.service.fit_for_embedding(original,Provider()),original)
    def test_fit_rejects_foreign_scope(self):
        e=self.ledger.ingest(PlainTextAdapter('short','Built API.')).evidence
        c=self.service.generate(e.evidence_id)[0]
        with self.assertRaises(ValueError):self.service.fit_for_embedding([replace(c,evidence=replace(e,scope=Scope('tenant','B')))],Provider())
    def test_raw_long_query_lossless(self):
        text='Required Python and PostgreSQL; not Redis. '*100
        spans=list(focused_spans(text,Provider()))
        self.assertEqual(''.join(text[a:b] for a,b in spans),text)
        self.assertTrue(all(b-a<180 for a,b in spans))
    def test_raw_job_preserves_duplicate_occurrences(self):
        raw='Requirements:\nImplemented Python APIs.\nImplemented Python APIs.'
        job,rs,_=requirements(raw,Provider())
        self.assertEqual(len(rs),2);self.assertNotEqual(rs[0]['requirement_id'],rs[1]['requirement_id'])
        self.assertTrue(all(job[r['start']:r['end']]==r['source_quote'] for r in rs))
    def test_raw_job_negation_and_multicomponent_retained(self):
        _,rs,_=requirements('Required Python and SQL, not Redis.',Provider())
        self.assertEqual(rs[0]['text'],'Required Python and SQL, not Redis.')
    def test_empty_job_structured_failure(self):
        class Engine:pass
        engine=Engine();engine.retriever=Engine();engine.retriever.store=self.store;engine.retriever.provider=Provider()
        result=ResumePipeline(engine,self.ledger,None,{'candidate_id':'A'}).run('','A')
        self.assertEqual(result['failure_stage'],'requirement_decomposition');self.assertFalse(result['model_called'])
    def test_pipeline_candidate_isolation_before_model(self):
        class Engine:pass
        engine=Engine();engine.retriever=Engine();engine.retriever.store=self.store
        result=ResumePipeline(engine,self.ledger,None,{'candidate_id':'A'}).run('Required Python.','B')
        self.assertEqual(result['failure_stage'],'candidate_scope')

class IntegrationTests(Harness,unittest.TestCase):
    def pipeline(self,mode='valid'):
        from rag.deep.retrieve import DeepRetriever,QueryRetriever,DeepConfig
        from rag.vectorstore.models import EmbeddingSpace
        from rag.retrieval import RetrievalConfig
        self.add('project','Deployment must finish before evaluation begins.' if mode=='policy' else 'Implemented Python APIs with FastAPI.')
        if mode=='partial_conflict':self.add('correction','The earlier Python API claim was incorrect; only a spreadsheet was produced.')
        self.embeddings.tokenizer=Tokenizer();self.embeddings.max_tokens=180
        retriever=QueryRetriever(self.store,self.embeddings,EmbeddingSpace(self.embeddings.config,'title-section-v1'),self.service,[r.record_id for r in self.records],RetrievalConfig(),normalize=True)
        engine=DeepRetriever(retriever,self.resolver,DeepConfig())
        class Model:
            def token_count(self,msgs):return len(str(msgs))//4
            def generate(self,msgs):
                task=json.loads(msgs[-1]['content'])
                if 'claim' in task:
                    conflict=mode=='partial_conflict'
                    if mode=='unsupported':
                        return {'text':json.dumps(dict(support='UNSUPPORTED',event_id=task['event_id'],evidence_ids=[],counterevidence_ids=[],reason='No Erlang support in Python-only evidence'))}
                    return {'text':json.dumps(dict(support='CONTRADICTED' if conflict else 'SUPPORTED',eligibility='E' if conflict else 'A',event_id=task['event_id'],links=[dict(requirement_id=r['requirement_id'],supported=not conflict,component=r['text'],reason='synthetic source relation') for r in task['requirements']],evidence_ids=[task['sources'][0]['evidence_id']],counterevidence_ids=[task['sources'][-1]['evidence_id']] if conflict else [],reason='Explicit correction contradicts the original activity' if conflict else 'Exact synthetic achieved activity'))}
                eid=next(e['evidence_id'] for e in task['evidence'] if ('Deployment must finish' if mode=='policy' else 'Implemented Python APIs') in e['content']);reqs=task['requirements']
                label='UNKNOWN' if mode=='unsupported' else 'PARTIALLY_SUPPORTED' if mode=='partial_conflict' else 'SUPPORTED'
                out=dict(requirements=[dict(requirement_id=r['requirement_id'],label=label,evidence_ids=[] if label=='UNKNOWN' else [eid],reason='The requested activity has conflicting evidence: the correction says only a spreadsheet was produced.' if mode=='partial_conflict' else 'synthetic test') for r in reqs],selected_quotes=[] if mode=='unsupported' else [dict(evidence_id='foreign' if mode=='foreign' else eid,quote='Invented 50% revenue increase.' if mode=='fabrication' else 'Deployment must finish before evaluation begins.' if mode=='policy' else 'Implemented Python APIs with FastAPI.',requirement_ids=[r['requirement_id'] for r in reqs])])
                return {'text':json.dumps(out)}
        return ResumePipeline(engine,self.ledger,Model(),{'candidate_id':'A','name':'Synthetic Candidate'})
    def test_raw_job_through_retrieval_model_compiler(self):
        r=self.pipeline().run('Requirements:\nImplemented Python APIs.','A')
        self.assertEqual(r['status'],'COMPLETE',r.get('error'));self.assertTrue(r['model_called']);self.assertTrue(r['compiler_valid'])
        claim=r['resume']['sections'][0]['claims'][0]
        self.assertEqual(claim['text'],'Implemented Python APIs with FastAPI.')
        self.assertTrue(r['compiler_bindings']['bindings']);self.assertEqual(len(claim['requirement_ids']),1)
    def test_unsupported_does_not_count_as_completion(self):
        r=self.pipeline('unsupported').run('Required Erlang.','A')
        self.assertEqual(r['status'],'FAILED');self.assertIsNone(r['resume']);self.assertEqual(r['failure_stage'],'grounding')
    def test_fabricated_claim_is_rejected(self):
        r=self.pipeline('fabrication').run('Required Python.','A')
        self.assertEqual(r['status'],'COMPLETE');self.assertTrue(any('non-exact' in x.get('reason','') for x in r['claim_reviews']));self.assertEqual([c['text'] for c in r['resume']['sections'][0]['claims']],['Implemented Python APIs with FastAPI.'])
    def test_foreign_model_reference_is_rejected(self):
        r=self.pipeline('foreign').run('Required Python.','A')
        self.assertEqual(r['status'],'COMPLETE');self.assertTrue(any('foreign' in x.get('reason','') and not x['accepted'] for x in r['claim_reviews']));self.assertNotIn('foreign',r['resume']['provenance']);self.assertEqual([c['text'] for c in r['resume']['sections'][0]['claims']],['Implemented Python APIs with FastAPI.'])
    def test_bounded_context_exhaustion_is_explicit(self):
        p=self.pipeline();p.max_context_tokens=10
        r=p.run('Required Python.','A')
        self.assertEqual(r['failure_stage'],'context_assembly');self.assertFalse(r['model_called'])

    def test_partial_requirement_cannot_license_contradicted_claim(self):
        r=self.pipeline('partial_conflict').run('Required Python API implementation.','A')
        self.assertEqual(r['status'],'FAILED','Known blocker: exact quotation plus PARTIALLY_SUPPORTED requirement is not claim-level entailment or contradiction resolution')
    def test_procedural_policy_is_not_candidate_experience(self):
        r=self.pipeline('policy').run('Required deployment experience.','A')
        self.assertEqual(r['status'],'FAILED','Known blocker: procedural instructions are not achieved candidate experience')
