import unittest
from dataclasses import asdict
from test_reranking import Harness
from rag.reasoning.contract import context
from resume_pipeline.context_units import prepare_units

class ContextUnitTests(Harness,unittest.TestCase):
    def test_mid_sentence_expands_to_original_whole_line(self):
        sentence='Contributed to a team building a Python service with '+('documented tests and evaluations '*22)+'for controlled deployment.'
        self.add('source',sentence)
        ctx,_=context(self.scope,self.response(),self.resolver)
        prepared=prepare_units(ctx['provenance'],self.ledger)
        self.assertTrue(prepared)
        for p in prepared.values():
            self.assertEqual(p['content'],sentence)
            self.assertEqual([u['text'] for u in p['allowed_quotes']],[sentence])
            self.assertEqual(p['context_span'],[0,len(sentence)])
        self.assertEqual(len(prepared),1)
        self.assertGreater(len(next(iter(prepared.values()))['parent_chunk_ids']),1)
    def test_metadata_heading_has_exact_span(self):
        text='Project Vega | 2025 | Python\nImplemented Python APIs with strict validation.'
        self.add('source',text);ctx,_=context(self.scope,self.response(),self.resolver)
        prepared=prepare_units(ctx['provenance'],self.ledger)
        unit=next(iter(prepared.values()))['allowed_quotes'][0];h=unit['source_context']
        self.assertEqual(text[h['start']:h['end']],h['text'])
        self.assertEqual(text[unit['start']:unit['end']],unit['text'])
    def test_code_cannot_be_selected_as_resume_prose(self):
        self.add('source','import torch\ndef evaluate(model):\n    return model.forward()')
        ctx,_=context(self.scope,self.response(),self.resolver)
        self.assertFalse(any(p['allowed_quotes'] for p in prepare_units(ctx['provenance'],self.ledger).values()))
    def test_cross_source_duplicates_keep_distinct_unit_ids(self):
        self.add('one','Implemented Python APIs with strict validation.')
        self.add('two','Implemented Python APIs with strict validation.')
        ctx,_=context(self.scope,self.response(),self.resolver)
        self.assertEqual(len(prepare_units(ctx['provenance'],self.ledger)),2)
