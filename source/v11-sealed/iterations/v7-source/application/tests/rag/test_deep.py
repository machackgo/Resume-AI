"""Stage 3J unit and artifact contract checks; no model or network calls."""
import unittest,json,re,hashlib
from pathlib import Path
from dataclasses import replace
from rag.deep.retrieve import DeepConfig,normalize_query,QUERY_VERSION,key
from rag.component.decompose import RequirementDecomposer
from rag.retrieval import InformationNeed,NeedType
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/stage3j'
def read(name):return json.loads((OUT/name).read_text())
class DeepUnitTests(unittest.TestCase):
    def test_action_alias(self):
        for verb in ('Implemented','Built','Developed','Studied','Evaluated'):
            self.assertEqual(normalize_query(verb+' RAG for Cedar.'),verb+' retrieval augmented generation for Cedar.')
    def test_negation_preserved(self):self.assertEqual(normalize_query('Did not implement RAG.'),'Did not implement retrieval augmented generation.')
    def test_relations_preserved(self):self.assertEqual(normalize_query('Used AWS for deployment.'),'Used AWS for deployment.')
    def test_adjacent_unchanged(self):
        for s in ('Trained QLoRA.','Used LoRA.','Loaded a 4-bit model.','Used Azure.','Built an API.','Consumed an API.','Reduced latency by 40%.'):
            self.assertEqual(normalize_query(s),s)
    def test_boundaries(self):self.assertEqual(normalize_query('FRAGMENT ragged RAG'),'FRAGMENT ragged retrieval augmented generation')
    def test_query_version(self):self.assertEqual(QUERY_VERSION,'focused-exact-acronym-v2')
    def test_decomposition_version(self):
        d=RequirementDecomposer().decompose(InformationNeed(NeedType.JOB_REQUIREMENT,'Built and evaluated an API.','x'));self.assertEqual(d.strategy_version,'structural-relationship-v2');self.assertEqual(len(d.components),2)
    def test_internal_context_independence(self):
        for k in (3,5,10,20,40):self.assertEqual(DeepConfig(internal_k=k).global_budget,5)
    def test_invalid_depth(self):
        for k in (0,80,100,True):
            with self.assertRaises(ValueError):DeepConfig(internal_k=k)
    def test_invalid_context(self):
        with self.assertRaises(ValueError):DeepConfig(global_budget=40)

@unittest.skipUnless((OUT/'top-k-summary.json').exists(),'retrieval artifacts required')
class DeepArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.trace=read('h06-forensic-traces.json');cls.summary=read('top-k-summary.json');cls.hard=read('targeted-results.json');cls.supp=read('supplement-results.json');cls.cfg=DeepConfig(**read('config.json')['selected']);cls.selected=key(cls.cfg)
    def test_trace_scales(self):self.assertEqual([t['scale'] for t in self.trace],['SMALL','MEDIUM','LARGE','XL'])
    def test_exact_ranks(self):self.assertEqual([t['components'][0]['gold_rank'] for t in self.trace],[2,9,42,125])
    def test_loss_location(self):self.assertEqual([t['components'][0]['cutoff_location'] for t in self.trace],[None,'per_component_top2_after_grouping','initial_semantic_top20','initial_semantic_top20'])
    def test_gold_identity(self):
        for t in self.trace:
            for g in t['gold_chains']:self.assertEqual(g['document_id'],'c04');self.assertEqual(g['embedding']['evidence_id'],g['canonical_evidence']['evidence_id'])
    def test_chunk_action_offsets(self):
        for t in self.trace:
            for g in t['gold_chains']:
                c=g['citation']['chunk'];self.assertIn('built retrieval augmented generation',c['text']);self.assertEqual(c['text'],g['original_fixture']['text'][c['start']:c['end']]);self.assertTrue(c['claim_links'])
    def test_embedding_and_space(self):
        for t in self.trace:
            for g in t['gold_chains']:self.assertEqual(len(g['embedding']['vector']),384);self.assertEqual(g['space_id'],g['retrieval_reference']['semantic_space_id']);self.assertEqual(g['stored_vector']['state'],'active')
    def test_original_query_action(self):
        for t in self.trace:self.assertEqual(t['components'][0]['query_plan']['text'],'Implemented RAG for the Juniper assistant.')
    def test_historical_context_replay(self):self.assertTrue(all(t['frozen_stage3i_replay_exact'] for t in self.trace))
    def test_ablation_depths(self):
        for s,v in self.summary.items():
            for k in (3,5,10,20,40):self.assertIn('alias-k%d-b5'%k,v);self.assertIn('original-k%d-b5'%k,v)
    def test_h06_survival(self):
        for scale in ('SMALL','MEDIUM','LARGE','XL'):
            r=next(r for r in read(scale+'-ablation.json') if r['case']['id']=='h06');self.assertTrue(r['measurements'][self.selected]['h06_gold_survived']);self.assertEqual(r['measurements'][self.selected]['h06_gold_rank'],1)
    def test_component_survival(self):
        for scale in ('LARGE','XL'):self.assertEqual(self.summary[scale][self.selected]['required_component_survival'],1)
    def test_all_covered(self):
        for scale in ('LARGE','XL'):self.assertEqual(self.summary[scale][self.selected]['all_required_components_covered'],1)
    def test_hard_cases_present(self):self.assertTrue({'rag','api','kubernetes','qlora_lora','qlora_inference','aws','pytorch','numeric','serving','credential'}<={r['case']['id'] for r in self.hard})
    def test_hard_no_coverage_regression(self):
        for r in self.hard:self.assertGreaterEqual(r['measurements'][self.selected]['survived_components'],r['measurements']['stage3i']['survived_components'])
    def test_bounded_selection(self):
        for r in self.hard+self.supp:
            for out in r['variants'].values():self.assertLessEqual(len(out['context']['groups']),5)
    def test_fair_coverage(self):
        r=next(r for r in self.supp if r['case']['id']=='fair_four');self.assertEqual(r['measurements'][self.selected]['survived_components'],4)
    def test_duplicate_provenance(self):
        r=next(r for r in self.supp if r['case']['id']=='duplicates');out=r['variants']['alias-k40-b5'];groups=out['context']['groups'];copies=[g for g in groups if 'Implemented' in g['evidence'][0]['content']];self.assertEqual(len(copies),1);self.assertEqual(len(copies[0]['evidence']),4)
    def test_missing_component(self):
        r=next(r for r in self.supp if r['case']['id']=='heldout_several_missing');self.assertTrue(all(c['status']=='no_plausible_candidate_retrieved' and not c['evidence_ids'] for c in r['variants'][self.selected]['context']['component_retrieval']))
    def test_decomposition_followup(self):
        for ident in ('under_d31','under_d32','under_d33'):
            r=next(r for r in self.supp if r['case']['id']==ident);self.assertEqual(r['measurements'][self.selected]['survived_components'],2)
    def test_isolation_at_every_depth(self):
        for r in read('security-results.json'):self.assertEqual(r['tested_k'],[3,5,10,20,40]);self.assertEqual(r['cross_candidate_leakage'],0);self.assertEqual(r['cross_tenant_leakage'],0);self.assertTrue(r['foreign_perfect_evidence'])
    def test_stale_filtering(self):
        for r in self.supp+self.hard:
            for out in r['variants'].values():self.assertFalse(set(r['security']['stale_ids'])&set(out['context']['provenance']))
    def test_trust_preservation(self):
        for r in self.supp+self.hard:
            for v in r['variants'][self.selected]['context']['provenance'].values():self.assertEqual(v['reference']['trust'],'untrusted_data');self.assertEqual(v['reference']['scope'],r['scope']);self.assertEqual(v['reference']['lifecycle'],'active')
    def test_injection_not_selector_command(self):
        r=next(r for r in self.supp if r['case']['id']=='injection_absent');out=r['variants'][self.selected]
        for x in out['selector_trace']:self.assertNotIn('SUPPORTED',x['reason']);self.assertEqual(x['trust_category'],'untrusted_data')
        self.assertNotIn('EV-SECRET',out['context']['provenance'])
    def test_credential_trust(self):
        r=next(r for r in self.hard if r['case']['id']=='credential');ctx=r['variants'][self.selected]['context']
        for e,p in ctx['provenance'].items():self.assertEqual(bool(p['attestations']),r['id_to_doc'][e]=='direct')
    def test_selector_explainability(self):
        for r in self.hard+self.supp:
            for x in r['variants'][self.selected]['selector_trace']:
                self.assertTrue(x['component_ids']);self.assertGreater(x['semantic_rank'],0);self.assertTrue(x['reason']);self.assertIn('source_version',x['provenance_handle'])
    def test_token_accounting(self):
        for r in self.hard:self.assertGreater(r['measurements'][self.selected]['prompt_tokens'],r['measurements'][self.selected]['evidence_tokens'])
    def test_deterministic_replay(self):self.assertTrue(all(r['deterministic'] for r in read('security-results.json')))
    def test_metric_ranges(self):
        for s,configs in self.summary.items():
            for m in configs.values():
                for k in ('recall_at_1','recall_at_3','recall_at_5','recall_at_10','mrr','required_component_survival','dangerous_neighbor_rate','duplicate_result_rate'):self.assertTrue(0<=m[k]<=1,(s,k,m[k]))
    def test_no_historical_source_edit(self):
        protected=read('protected-manifest.json')
        for name,h in protected.items():
            if name.startswith(('rag/','docs/','tests/','eval/prompts/')):self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),h,name)

def case_check(ident):
    def test(self):
        r=next(r for r in self.hard if r['case']['id']==ident)
        self.assertEqual(r['measurements'][self.selected]['survived_components'],1)
        self.assertTrue(r['measurements'][self.selected]['gold_ranks'])
    return test
for ident in ('rag','api','kubernetes','qlora_lora','qlora_inference','aws','pytorch','numeric','serving','credential'):
    setattr(DeepArtifactTests,'test_hard_'+ident,case_check(ident))
def depth_check(k):
    def test(self):
        for row in self.hard+self.supp:
            for prefix in ('alias','original'):
                out=row['variants'][prefix+'-k'+str(k)+'-b5']
                self.assertLessEqual(out['raw_pool_size'],k*len(out['decomposition']['components']))
                self.assertLessEqual(len(out['context']['groups']),5)
    return test
for k in (3,5,10,20,40):setattr(DeepArtifactTests,'test_depth_'+str(k),depth_check(k))
class AttributionTests(unittest.TestCase):
    def test_reasoning_after_delivery(self):
        from rag.deep.score import classify
        self.assertEqual(classify({},dict(failures=['QWEN REASONING'],retrieval_loss=False))[0]['layer'],'QWEN_REASONING')
    def test_citation_separate(self):
        from rag.deep.score import classify
        self.assertEqual(classify({},dict(failures=['CITATION'],retrieval_loss=False))[0]['layer'],'CITATION')
    def test_structured_output(self):
        from rag.deep.score import classify
        self.assertEqual(classify({},dict(failures=[],retrieval_loss=False,json_valid=False))[0]['layer'],'STRUCTURED_OUTPUT')
if __name__=='__main__':unittest.main()
