import math
import unittest
from rag.reranking.metrics import dcg,evaluate,aggregate

class MetricTests(unittest.TestCase):
    def test_graded_ndcg(self):
        m=evaluate(['b','a','c'],{'a':3,'b':2,'c':0})
        self.assertAlmostEqual(m['ndcg_at_3'],(3+7/math.log2(3))/(7+3/math.log2(3)))
    def test_ndcg_perfect(self):
        self.assertEqual(evaluate(['a','b'],{'a':3,'b':1})['ndcg_at_5'],1)
    def test_ndcg_full_corpus_denominator(self):
        m=evaluate(['b'],{'a':3,'b':2})
        self.assertLess(m['ndcg_at_3'],1); self.assertEqual(m['conditional_ndcg_at_3'],1)
    def test_mrr(self): self.assertEqual(evaluate(['c','b','a'],{'a':3,'b':2,'c':1})['mrr'],1/3)
    def test_recall_multiple(self):
        m=evaluate(['a','c','b'],{'a':3,'b':3,'c':1})
        self.assertEqual(m['recall_at_1'],.5); self.assertEqual(m['recall_at_3'],1)
    def test_hit_distinct_from_recall(self):
        m=evaluate(['a'],{'a':3,'b':3}); self.assertEqual(m['hit_at_1'],1); self.assertEqual(m['recall_at_1'],.5)
    def test_danger_pair(self):
        m=evaluate(['b','a'],{'a':3,'b':1},['b'],[('a','b')])
        self.assertEqual(m['dangerous_neighbor_rate'],1); self.assertEqual(m['top1_hard_negative_error'],1)
    def test_hard_negative_win(self):
        m=evaluate(['a','b'],{'a':3,'b':1},['b'],[('a','b')]); self.assertEqual(m['positive_over_hard_negative_win_rate'],1)
    def test_missing_stronger_not_win(self):
        m=evaluate(['b'],{'a':3,'b':1},['b'],[('a','b')])
        self.assertIsNone(m['dangerous_neighbor_rate']); self.assertEqual(m['dangerous_pairs_missing_stronger'],1)
        self.assertEqual(m['mrr'],0)
    def test_empty(self):
        m=evaluate([],{'a':3}); self.assertEqual(m['ndcg_at_3'],0); self.assertEqual(m['mrr'],0)
    def test_unjudged(self):
        with self.assertRaises(ValueError): evaluate(['x'],{'a':3})
    def test_invalid_grade(self):
        for grade in (-1,4,True,1.5):
            with self.assertRaises(ValueError): evaluate(['a'],{'a':grade})
    def test_duplicate_group(self):
        with self.assertRaises(ValueError): evaluate(['a','a'],{'a':3})
    def test_no_relevant(self):
        with self.assertRaises(ValueError): evaluate(['a'],{'a':2})
    def test_bad_pair(self):
        with self.assertRaises(ValueError): evaluate(['a','b'],{'a':3,'b':3},[],[('a','b')])
    def test_pairwise_accuracy(self):
        self.assertEqual(evaluate(['c','b','a'],{'a':3,'b':2,'c':1})['pairwise_accuracy'],0)
    def test_map(self): self.assertAlmostEqual(evaluate(['a','c','b'],{'a':3,'b':3,'c':0})['map'],(1+2/3)/2)
    def test_aggregate_micro_danger(self):
        a=evaluate(['b','a'],{'a':3,'b':1},['b'],[('a','b')])
        b=evaluate(['a','b','c'],{'a':3,'b':1,'c':1},['b','c'],[('a','b'),('a','c')])
        self.assertAlmostEqual(aggregate([a,b])['dangerous_neighbor_rate'],1/3)
    def test_budget_survival(self):
        self.assertEqual(evaluate(['b','c','a'],{'a':3,'b':2,'c':1})['hit_at_2'],0)
        self.assertEqual(evaluate(['b','c','a'],{'a':3,'b':2,'c':1})['hit_at_3'],1)
