import tempfile,unittest
from pathlib import Path
from .annotate_tokens import annotate
from .io import write_json,write_jsonl,read_jsonl,sha_file,digest

class TokenProvenanceTests(unittest.TestCase):
    def fixture(self,root,changed=False):
        messages=[{'role':'system','content':'Contract'},{'role':'user','content':'Evidence'},{'role':'assistant','content':'{"artifact":"truth"}'}]
        rows=[{'messages':messages,'metadata':{'example_id':'e1'}}]
        data=root/'records.jsonl';write_jsonl(data,rows)
        report={'passed':True,'records_file_sha256':sha_file(data),'tokenizer_fingerprint':{'files':{'tokenizer.json':'test-fingerprint'},'chat_template_sha256':'test-template'},'tokens':{'examples':[{'example_id':'e1','messages_sha256':digest(messages),'assistant_text_sha256':digest(messages[-1]['content']),'input_tokens':10,'target_tokens':5,'total_tokens':15}]}}
        return data,report
    def test_valid_bound_annotation_preserves_messages(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);data,r=self.fixture(root);report=root/'report.json';write_json(report,r);out=root/'annotated.jsonl';annotate(data,report,out)
            self.assertEqual(read_jsonl(out)[0]['messages'],read_jsonl(data)[0]['messages'])
            self.assertEqual(read_jsonl(out)[0]['metadata']['qwen_token_counts']['total_tokens'],15)
    def test_stale_assistant_measurement_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);data,r=self.fixture(root);r['tokens']['examples'][0]['assistant_text_sha256']=digest('invented changed artifact');report=root/'report.json';write_json(report,r)
            with self.assertRaises(ValueError):annotate(data,report,root/'out.jsonl')
    def test_wrong_record_set_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);data,r=self.fixture(root);r['records_file_sha256']='wrong';report=root/'report.json';write_json(report,r)
            with self.assertRaises(ValueError):annotate(data,report,root/'out.jsonl')
    def test_missing_real_tokenizer_fingerprint_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);data,r=self.fixture(root);r['tokenizer_fingerprint']['files']={};report=root/'report.json';write_json(report,r)
            with self.assertRaises(ValueError):annotate(data,report,root/'out.jsonl')
    def test_pipeline_rejects_overflow_despite_accepting_critic(self):
        from .test_pipeline_audit import provenance_fixture,write_mock_run
        from .pipeline import audit
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);row,bundle=provenance_fixture();run=root/'run';run.mkdir();write_mock_run(run,row,bundle)
            report=root/'tokens.json';write_json(report,{'examples':[{'example_id':row['metadata']['example_id'],'messages_sha256':digest(row['messages']),'assistant_text_sha256':digest(row['messages'][-1]['content']),'input_tokens':3000,'target_tokens':1261,'total_tokens':4261}]})
            result=audit(run,Path(__file__).parents[1],root/'audit',token_report_path=report)
            self.assertEqual(result['accepted'],0)
            self.assertIn('COMPLETE_SEQUENCE_EXCEEDS_PREREGISTERED_ENVELOPE',result['hard_failure_categories'])

if __name__=='__main__':unittest.main()
