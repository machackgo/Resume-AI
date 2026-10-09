import unittest,json,hashlib
from pathlib import Path
import torch
from transformers import AutoTokenizer
from stage4a.data import tokenized,pad_batch
from stage4b.prepare import select,sha
R=Path.cwd();O=R/'results/stage4b/smoke';D=R/'datasets/stage4a/v1'
class Contracts(unittest.TestCase):
 @classmethod
 def setUpClass(c):
  c.tok=AutoTokenizer.from_pretrained(R/'models/Qwen3.8-27B',local_files_only=True);c.rows=[json.loads(l) for l in (D/'train.jsonl').read_text().splitlines()];c.man=json.loads((O/'subset_manifest.json').read_text());c.selected=[r for r in c.rows if r['metadata']['example_id'] in c.man['ids']];c.enc=[tokenized(r,c.tok) for r in c.selected]
 def test_release_checksums(self):
  for l in (D/'checksums.sha256').read_text().splitlines():
   h,p=l.split('  ',1);self.assertEqual(sha(D/p),h)
 def test_manifest_train_hash(self):self.assertEqual(sha(D/'train.jsonl'),self.man['train_sha256'])
 def test_deterministic_selection(self):self.assertEqual(select(self.rows),select(list(reversed(self.rows))))
 def test_train_only(self):self.assertTrue(all(r['metadata']['split']=='train' for r in self.selected))
 def test_validation_excluded(self):self.assertFalse(set(self.man['ids'])&{json.loads(l)['metadata']['example_id'] for l in (D/'validation.jsonl').read_text().splitlines()})
 def test_test_excluded(self):self.assertFalse(set(self.man['ids'])&{json.loads(l)['metadata']['example_id'] for l in (D/'test.jsonl').read_text().splitlines()})
 def test_tiny_subset(self):self.assertLessEqual(len(self.selected),64);self.assertGreaterEqual(len(self.selected),16)
 def test_labels(self):self.assertEqual({r['metadata']['expected_label'] for r in self.selected},{'SUPPORTED','PARTIALLY_SUPPORTED','UNKNOWN','UNSUPPORTED'})
 def test_atomic(self):self.assertTrue(any(not r['metadata']['compound'] for r in self.selected))
 def test_compound(self):self.assertTrue(any(r['metadata']['compound'] for r in self.selected))
 def test_hard_negative(self):self.assertTrue(any(r['metadata']['hard_negative'] for r in self.selected))
 def test_numeric(self):self.assertTrue(any(r['metadata']['numeric'] for r in self.selected))
 def test_trust(self):self.assertTrue(any('verified' in r['metadata']['trust_tags'] for r in self.selected))
 def test_action(self):self.assertTrue(any(r['metadata']['template_family']=='api' for r in self.selected))
 def test_adjacent(self):self.assertTrue(any(r['metadata']['template_family']=='adaptation' and r['metadata']['hard_negative'] for r in self.selected))
 def test_citations(self):self.assertTrue(any(json.loads(r['messages'][-1]['content'])['evidence_ids'] for r in self.selected))
 def test_template(self):
  for r in self.selected:self.assertTrue(self.tok.apply_chat_template(r['messages'],tokenize=False,enable_thinking=False).startswith(self.tok.apply_chat_template(r['messages'][:2],tokenize=False,add_generation_prompt=True,enable_thinking=False)))
 def test_prompt_mask(self):
  for e in self.enc:self.assertEqual(e['labels'][:e['input_tokens']],[-100]*e['input_tokens'])
 def test_target_exact(self):
  for r,e in zip(self.selected,self.enc):self.assertEqual(self.tok.decode(e['input_ids'][e['input_tokens']:-1]),r['messages'][-1]['content'])
 def test_eos(self):
  for e in self.enc:self.assertEqual(e['labels'][-1],self.tok.convert_tokens_to_ids('<|im_end|>'))
 def test_supervision_nonempty(self):
  for e in self.enc:self.assertGreater(e['target_tokens'],1)
 def test_no_control_tokens_in_json(self):
  for e in self.enc:self.assertFalse(set(e['input_ids'][e['input_tokens']:-1])&set(self.tok.all_special_ids))
 def test_lengths(self):
  for e in self.enc:self.assertLessEqual(len(e['input_ids']),4608)
 def test_padding(self):
  for b in pad_batch(self.enc,self.tok):
   for i,a in enumerate(b['attention_mask']):
    if not a:self.assertEqual(b['labels'][i],-100);self.assertEqual(b['input_ids'][i],self.tok.pad_token_id)
 def test_shift_and_selected_logits_equivalence(self):
  torch.manual_seed(1);x=torch.randn(1,13,31,requires_grad=True);labels=torch.tensor([[-100]*7+[1,2,3,4,5,6]])
  full=torch.nn.functional.cross_entropy(x[:,:-1].reshape(-1,31),labels[:,1:].reshape(-1));g1=torch.autograd.grad(full,x,retain_graph=True)[0]
  pos=torch.nonzero(labels[0,1:]!=-100).flatten();part=torch.nn.functional.cross_entropy(x[0,pos],labels[0,pos+1]);g2=torch.autograd.grad(part,x)[0]
  torch.testing.assert_close(full,part);torch.testing.assert_close(g1,g2)
 def test_architecture(self):
  a=json.loads((O/'architecture.json').read_text());self.assertEqual(a['class_name'],'Qwen3_5ForCausalLM');self.assertEqual(a['parameters'],26895998464)
 def test_target_existence_and_count(self):
  a=json.loads((O/'architecture.json').read_text());ms={n:m for n,m in a['modules'].items() if n.split('.')[-1] in ['q_proj','k_proj','v_proj','o_proj']};self.assertEqual(len(ms),64);self.assertEqual(sum(8*sum(m['shape']) for m in ms.values()),5242880)
 def test_config_serialization(self):
  a=json.loads((O/'subset_manifest.json').read_text());self.assertEqual(json.dumps(a,sort_keys=True),json.dumps(json.loads(json.dumps(a)),sort_keys=True))
 def test_quantization(self):
  from transformers import BitsAndBytesConfig
  q=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',bnb_4bit_use_double_quant=True,bnb_4bit_compute_dtype=torch.bfloat16)
  self.assertTrue(q.load_in_4bit);self.assertEqual(q.bnb_4bit_quant_type,'nf4');self.assertTrue(q.bnb_4bit_use_double_quant);self.assertEqual(q.bnb_4bit_compute_dtype,torch.bfloat16)
 def test_invalid_length_rejected(self):
  from stage4b.engine import validate_encoded
  with self.assertRaises(AssertionError):validate_encoded(dict(input_ids=[1]*4609,labels=[1]*4609,attention_mask=[1]*4609))
 def test_empty_supervision_rejected(self):
  from stage4b.engine import validate_encoded
  with self.assertRaises(AssertionError):validate_encoded(dict(input_ids=[1]*3,labels=[-100]*3,attention_mask=[1]*3))
 def test_invalid_label_rejected(self):
  from stage4b.engine import validate_encoded
  with self.assertRaises(AssertionError):validate_encoded(dict(input_ids=[1]*3,labels=[-100,2,1],attention_mask=[1]*3))
 def test_padding_supervision_rejected(self):
  from stage4b.engine import validate_encoded
  with self.assertRaises(AssertionError):validate_encoded(dict(input_ids=[1]*3,labels=[-100,1,1],attention_mask=[1,1,0]))
 def test_valid_encoded(self):
  from stage4b.engine import validate_encoded
  for e in self.enc:validate_encoded(e)
 def test_chunked_loss_and_gradient_equivalence(self):
  from stage4b.engine import chunked_cross_entropy
  torch.manual_seed(4);head=torch.nn.Linear(19,101,bias=False);head.requires_grad_(False);h=torch.randn(173,19,requires_grad=True);t=torch.randint(0,101,(173,))
  ref=torch.nn.functional.cross_entropy(head(h).float(),t);g=torch.autograd.grad(ref,h)[0]
  actual=chunked_cross_entropy(h,head,t,64);ga=torch.autograd.grad(actual,h)[0]
  torch.testing.assert_close(ref,actual);torch.testing.assert_close(g,ga)
if __name__=='__main__':unittest.main()
