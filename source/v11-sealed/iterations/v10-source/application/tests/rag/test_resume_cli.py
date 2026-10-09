import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from resume_pipeline.__main__ import main

class ResumeCommandTests(unittest.TestCase):
    def invoke(self,root,profile,job='Python API experience.'):
        (root/'profile.json').write_text(json.dumps(profile));(root/'job.txt').write_text(job)
        return main(['--root',str(root),'--kb',str(root),'--profile-file',str(root/'profile.json'),'--job-file',str(root/'job.txt'),'--output',str(root/'result.json')])
    def test_invalid_profile_is_structured_before_loading_model(self):
        with tempfile.TemporaryDirectory() as d,patch('resume_pipeline.__main__.BaseQwen') as model:
            root=Path(d);self.assertEqual(self.invoke(root,{'candidate_id':'a'}),1)
            result=json.loads((root/'result.json').read_text());self.assertEqual(result['failure_stage'],'input');self.assertIsNone(result['resume']);model.assert_not_called()
    def test_database_initialization_failure_is_structured(self):
        with tempfile.TemporaryDirectory() as d,patch('resume_pipeline.__main__.load_kb',side_effect=ValueError('snapshot scope mismatch')),patch('resume_pipeline.__main__.BaseQwen') as model:
            root=Path(d);self.assertEqual(self.invoke(root,{'candidate_id':'a','name':'A'}),1)
            result=json.loads((root/'result.json').read_text());self.assertEqual(result['failure_stage'],'knowledge_base');self.assertFalse(result['model_called']);model.assert_not_called()
    def test_existing_result_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as d,patch('resume_pipeline.__main__.load_kb') as kb:
            root=Path(d);(root/'result.json').write_text('original')
            with self.assertRaises(SystemExit):self.invoke(root,{'candidate_id':'a','name':'A'})
            self.assertEqual((root/'result.json').read_text(),'original');kb.assert_not_called()
