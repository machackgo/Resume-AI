"""Bind measured Qwen counts to saved messages; no estimation or truncation."""
import argparse
from pathlib import Path
from .io import read_json,read_jsonl,write_jsonl,sha_file,digest

def annotate(records,report,out):
    rows=read_jsonl(records);r=read_json(report)
    if not r.get('passed') or r.get('records_file_sha256')!=sha_file(records):raise ValueError('token audit not bound to exact validated records')
    fingerprint=r.get('tokenizer_fingerprint')
    if not fingerprint or not fingerprint.get('files') or not fingerprint.get('chat_template_sha256'):raise ValueError('missing real tokenizer fingerprint')
    tokens={x['example_id']:x for x in r['tokens']['examples']}
    if len(tokens)!=len(rows):raise ValueError('incomplete token coverage')
    for row in rows:
        t=tokens[row['metadata']['example_id']]
        if t['messages_sha256']!=digest(row['messages']) or t['assistant_text_sha256']!=digest(row['messages'][-1]['content']):raise ValueError('stale token measurement')
        row['metadata']['qwen_token_counts']={k:t[k] for k in ['input_tokens','target_tokens','total_tokens']}
        row['metadata']['tokenizer_fingerprint_sha256']=digest(fingerprint)
        row['metadata']['token_measurement_report_sha256']=sha_file(report)
    write_jsonl(out,rows)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('records',type=Path);p.add_argument('report',type=Path);p.add_argument('out',type=Path);a=p.parse_args();annotate(a.records,a.report,a.out)
