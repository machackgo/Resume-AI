"""Versioned prompt assembly and unchanged strict parsing, no model dependencies."""
import json
from pathlib import Path

def build_messages(case, schema, vocabulary, prompt_dir):
    prompt_dir=Path(prompt_dir)
    payload={
        'task_instruction':(prompt_dir/'task.txt').read_text(),
        'candidate_evidence':case['evidence'],
        'job_description':case['job'],
        'candidate_request':case['request'],
        'proposed_claims':[{'id':c['id'],'text':c['text']} for c in case['gold']['claims']],
        'vocabulary':vocabulary,
        'output_schema':schema,
    }
    return [{'role':'system','content':(prompt_dir/'system.txt').read_text()},
            {'role':'user','content':json.dumps(payload,ensure_ascii=False)}]

def strict_parse(text):
    try:return json.loads(text),None
    except json.JSONDecodeError as error:return None,str(error)

def create_run_dir(root,run_id):
    if not run_id or Path(run_id).name!=run_id or run_id in {'.','..'}:
        raise ValueError('run-id must be a single directory name')
    path=Path(root)/'results/prompt_engineered'/run_id
    path.mkdir(parents=True,exist_ok=False)
    return path
