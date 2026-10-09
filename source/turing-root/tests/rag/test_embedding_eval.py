import json
from pathlib import Path
import unittest
from rag.embeddings.evaluation import evaluate,metrics,rank

class EvaluationTests(unittest.TestCase):
    def test_ranking_tie_determinism(self):
        self.assertEqual(rank([1,0],[('b',[1,0]),('a',[1,0])]),[('a',1.),('b',1.)])
    def test_duplicate_id(self):
        with self.assertRaises(ValueError): rank([1],[('a',[1]),('a',[1])])
    def test_metrics_multiple_relevant(self):
        self.assertEqual(metrics([('a',1),('b',.5),('c',0)],['a','c']),
                         {'recall_at_1':.5,'recall_at_3':1.,'mrr':1.})
    def test_mrr(self):
        self.assertEqual(metrics([('a',1),('b',.5)],['b'])['mrr'],.5)
    def test_bad_judgments(self):
        for relevant in ([],['absent']):
            with self.assertRaises(ValueError): metrics([('a',1)],relevant)
    def test_hard_negative_win_and_loss(self):
        q={'id':'q','category':'test','query':'query','relevant':['p'],'hard_negatives':['n']}
        for vector,win in (([1,0],1.),([0,1],0.)):
            r=evaluate([q],[vector],[('p',[1,0]),('n',[0,1])])
            self.assertEqual(r['metrics']['hard_negative_win_rate'],win)
    def test_tie_not_win(self):
        q={'id':'q','category':'test','query':'query','relevant':['p'],'hard_negatives':['n']}
        r=evaluate([q],[[1]],[('p',[1]),('n',[1])])
        self.assertEqual(r['metrics']['hard_negative_win_rate'],0)
        self.assertTrue(r['queries'][0]['tie'])
        self.assertEqual(r['queries'][0]['dangerous_top3'],['n'])
    def test_invalid_query_count(self):
        with self.assertRaises(ValueError): evaluate([],[],[])
    def test_dataset_integrity(self):
        d=json.loads((Path(__file__).resolve().parents[2]/'fixtures/rag/embedding_eval/resume_semantics_v1.json').read_text())
        ids={x['id'] for x in d['documents']}
        self.assertEqual(len(ids),44); self.assertEqual(len(d['queries']),22)
        for q in d['queries']:
            self.assertTrue(set(q['relevant']+q['hard_negatives']).issubset(ids))
            self.assertFalse(set(q['relevant'])&set(q['hard_negatives']))
    def test_macro_average(self):
        q={'id':'q','category':'test','query':'query','relevant':['p'],'hard_negatives':['n']}
        r=evaluate([q,q],[[1,0],[0,1]],[('p',[1,0]),('n',[0,1])])
        self.assertEqual(r['metrics'],{'recall_at_1':.5,'recall_at_3':1.,'mrr':.75,'hard_negative_win_rate':.5})

if __name__=='__main__': unittest.main()
