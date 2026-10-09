import unittest,json,tempfile
from pathlib import Path
from rag.scale.dataset import dataset,at_scale,SCALES
from rag.scale.metrics import feasibility,aggregate_scored,retrieval_metrics
from rag.reasoning.contract import aggregate_labels,messages,context
from rag.reasoning.prepare import contextual_gold
from rag.retrieval import InformationNeed,NeedType
class ScaleTests(unittest.TestCase):
    def setUp(self):self.d=dataset()
    def test_deterministic(self):self.assertEqual(dataset(),self.d)
    def test_scales(self):
        for s,n in SCALES.items():self.assertEqual(len(at_scale(self.d,s)),n+1)
    def test_nested(self):
        for a,b in zip(list(SCALES),list(SCALES)[1:]):self.assertEqual(at_scale(self.d,a),at_scale(self.d,b)[:SCALES[a]+1])
    def test_same_core(self):
        for s in SCALES:self.assertEqual(at_scale(self.d,s)[:25],self.d['documents'][:25])
    def test_realistic(self):
        tags={d.get('distractor') for d in self.d['documents'][25:]}
        self.assertTrue({'adjacent','assertion','unrelated','training_inference','built_used','duplicate'}<=tags)
    def test_multiple_sources(self):self.assertGreaterEqual(len({d['source_type'] for d in self.d['documents']}),6)
    def test_stale(self):self.assertEqual(sum(bool(d.get('stale')) for d in self.d['documents']),1)
    def test_attestation(self):self.assertEqual(sum(bool(d.get('attested')) for d in self.d['documents']),1)
    def test_attacks(self):self.assertEqual(sum(bool(d.get('attack')) for d in self.d['documents']),3)
    def test_foreign(self):self.assertIn('CANARY_B_7391',self.d['foreign_documents'][0]['text'])
    def test_no_foreign_in_A(self):self.assertNotIn('CANARY_B_7391',json.dumps(self.d['documents']))
    def test_balanced(self):
        from collections import Counter
        labels=[]
        for n in self.d['needs']:
            vals=[]
            for g in n['gold']:
                v=set(g['relations'].values());vals.append('SUPPORTED' if 'SUPPORTED' in v else 'UNSUPPORTED' if 'UNSUPPORTED' in v else 'UNKNOWN')
            labels.append(aggregate_labels(vals))
        self.assertEqual(Counter(labels),{'SUPPORTED':4,'PARTIALLY_SUPPORTED':3,'UNSUPPORTED':3,'UNKNOWN':6})
    def test_no_gold_in_components(self):
        for n in self.d['needs']:
            for c in n['components']:self.assertEqual(set(c),{'id','claim'})
    def test_relation_ids(self):
        ids={d['id'] for d in self.d['documents']}
        for n in self.d['needs']:
            for g in n['gold']:self.assertTrue(set(g['relations'])<=ids)
    def test_token_position_limit(self):self.assertEqual(feasibility(100,100,10**12)['reason'],'model_position_limit')
    def test_token_kv_limit(self):self.assertEqual(feasibility(10000,262144,100)['reason'],'KV_cache_alone_exceeds_available_GPU_memory')
    def test_feasible(self):self.assertEqual(feasibility(100,262144,10**12)['status'],'ATTEMPT')
    def test_exact_kv_accounting(self):self.assertEqual(feasibility(100,262144,10**12)['kv_bytes'],1636*65536)
    def test_unchanged_context_version(self):
        msg=messages(InformationNeed(NeedType.JOB_REQUIREMENT,'test','opaque'),[{'id':'a1','claim':'test'}],{'groups':[]})
        self.assertEqual(len(msg),2);self.assertNotIn('relations',msg[1]['content'])
    def test_scope_no_descriptive_public_id(self):
        msg=messages(InformationNeed(NeedType.JOB_REQUIREMENT,'test','SECRET_GOLD'),[],{'groups':[]})
        self.assertNotIn('SECRET_GOLD',msg[1]['content'])
    def test_budget_rejects(self):
        with self.assertRaises(ValueError):context(None,None,None,6)
    def test_full_gold_lost_evidence(self):
        q=self.d['needs'][0]
        self.assertEqual(contextual_gold(q,{'provenance':{}},{})['label'],'UNKNOWN')
    def test_full_gold_found_evidence(self):
        self.assertEqual(contextual_gold(self.d['needs'][0],{'provenance':{'e':{}}},{'e':'c01'})['label'],'SUPPORTED')
    def test_duplicates_truthful(self):
        for n in self.d['needs']:
            for g in n['gold']:
                for d in self.d['documents'][25:]:
                    if d.get('distractor')=='duplicate':self.assertEqual(g['relations'].get(d['id']),g['relations'].get('c01'))
if __name__=='__main__':unittest.main()

class PreparedScaleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from rag.scale.prepare import OUT,load_rows
        if not (OUT/'XL-prepared.json').exists():raise unittest.SkipTest('prepared artifacts not yet built; mandatory final check runs these')
        cls.rows={s:load_rows(s) for s in SCALES}
    def test_active_full_counts(self):
        for s,rs in self.rows.items():self.assertEqual(len(rs[0]['contexts']['full']['provenance']),SCALES[s])
    def test_full_same_for_all_needs(self):
        for rs in self.rows.values():
            for r in rs:self.assertEqual(r['contexts']['full'],rs[0]['contexts']['full'])
    def test_gold_same_by_scale(self):
        for rs in self.rows.values():self.assertEqual([r['gold']['full'] for r in rs],[r['gold']['full'] for r in self.rows['SMALL']])
    def test_top3_top5_prefix(self):
        for rs in self.rows.values():
            for r in rs:self.assertEqual(r['contexts']['rag3']['groups'],r['contexts']['rag5']['groups'][:3])
    def test_top_budget(self):
        for rs in self.rows.values():
            for r in rs:
                for n in (3,5):self.assertLessEqual(len(r['contexts']['rag'+str(n)]['groups']),n)
    def test_provenance_scope_and_chain(self):
        for rs in self.rows.values():
            for r in rs:
                for p in r['contexts']['rag5']['provenance'].values():
                    ref=p['reference'];self.assertEqual(ref['scope'],r['scope']);self.assertEqual(ref['lifecycle'],'active')
                    for k in ('embedding_id','chunk_id','chunk_revision_id','evidence_id','source_id','source_version','locator','support_ids','provenance_event_ids'):self.assertTrue(ref[k])
    def test_isolation(self):
        for rs in self.rows.values():
            for r in rs:
                self.assertTrue(r['security']['foreign_rejected'])
                for ctx in r['contexts'].values():self.assertFalse(set(ctx['provenance'])&set(r['security']['foreign_ids']))
    def test_stale_excluded(self):
        for rs in self.rows.values():
            for r in rs:
                for ctx in r['contexts'].values():self.assertFalse(set(ctx['provenance'])&set(r['security']['stale_ids']))
    def test_metrics_bounded(self):
        for rs in self.rows.values():
            for r in rs:
                m=retrieval_metrics(r)
                for k,v in m.items():
                    if v is not None and k!='retrieval_seconds':self.assertTrue(0<=v<=1,(k,v))
    def test_unknown_recall_null(self):
        for rs in self.rows.values():
            for r in rs:
                if not r['case']['relevant']:self.assertIsNone(retrieval_metrics(r)['mrr'])
    def test_injection_is_untrusted_data(self):
        for rs in self.rows.values():
            es=[e for g in rs[0]['contexts']['full']['groups'] for e in g['evidence'] if 'ignore the system' in e['content'].lower()]
            self.assertEqual(len(es),2)
            self.assertTrue(all(e['trust']=='untrusted_data' for e in es))
    def test_failure_attribution_not_reasoning_for_safe_abstention(self):
        from rag.scale.metrics import score_record
        from rag.reasoning.contract import public_need_id
        import copy
        r=copy.deepcopy(self.rows['SMALL'][0]);r['contexts']['rag3']={'groups':[],'provenance':{}}
        r['gold']['rag3']={'label':'UNKNOWN','atoms':{'a1':'UNKNOWN'}}
        n=InformationNeed(NeedType.JOB_REQUIREMENT,r['case']['requirement'],r['case']['id'])
        output=dict(information_need_id=public_need_id(n),label='UNKNOWN',atomic_claims=[dict(component_id='a1',claim=r['case']['components'][0]['claim'],label='UNKNOWN',evidence_ids=[],quotes=[],reason='No evidence')],evidence_ids=[],missing_evidence=['Implementation record'],reason='No evidence')
        scored=score_record(r,{'arm':'rag3','text':json.dumps(output)})
        self.assertIn('RETRIEVAL',scored['failures']);self.assertNotIn('QWEN REASONING',scored['failures'])
        m=aggregate_scored([scored]);self.assertEqual(m['label_accuracy'],0);self.assertEqual(m['atomic_context_accuracy'],1)
