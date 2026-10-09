"""Assemble audited saved outputs with exact provenance; never certify a release."""
import argparse,collections,json
from pathlib import Path
from .io import read_jsonl,read_json,write_json,write_jsonl,immutable_write,sha_file

def assemble(audits,out):
    selected={};attempts=[]
    for directory in map(Path,audits):
        attempts+=read_jsonl(directory/'attempts.jsonl')
        for row in read_jsonl(directory/'accepted.jsonl'):
            key=row['metadata']['example_id'];previous=selected.get(key)
            if previous and previous!=row:raise ValueError('multiple accepted versions require explicit disposition: '+key)
            selected[key]=row
    rows=sorted(selected.values(),key=lambda r:(r['metadata']['split'],r['metadata']['example_id']))
    for row in rows:
        m=row['metadata'];eid=m['example_id'];run=Path(m['generation_run'])
        sources={'request':run/'requests'/(eid+'.json'),'teacher':run/'teacher'/(eid+'.json'),'critic_request':Path(m['critic_request_directory'])/(eid+'.json'),'critic':run/'critic'/(eid+'.json')}
        for name,source in sources.items():
            if sha_file(source)!=m['raw_response_sha256'][name]:raise ValueError('raw provenance changed '+str(source))
            immutable_write(out/'provenance'/eid/(name+'.json'),source.read_text())
    write_jsonl(out/'records.jsonl',rows)
    for split in sorted({r['metadata']['split'] for r in rows}):write_jsonl(out/(split+'.jsonl'),[r for r in rows if r['metadata']['split']==split])
    write_jsonl(out/'attempts.jsonl',attempts)
    metrics={'assembled_not_frozen':True,'generation_attempts':len(attempts),'unique_scenarios_attempted':len({a['example_id'] for a in attempts}),'accepted_unique':len(rows),'rejected_attempts':sum(a['acceptance_status']!='ACCEPT' for a in attempts),'revision_attempts':sum(a['revision_count']>0 for a in attempts),'by_task':{},'splits':dict(collections.Counter(r['metadata']['split'] for r in rows)),'hard_failure_categories':dict(collections.Counter(e.split(':')[0] for a in attempts for e in a['hard_errors']))}
    for task in sorted({a['task'] for a in attempts}):
        aa=[a for a in attempts if a['task']==task];rr=[r for r in rows if r['metadata']['task']==task]
        metrics['by_task'][task]={'attempts':len(aa),'unique_scenarios_attempted':len({a['example_id'] for a in aa}),'accepted_unique':len(rr),'rejected_attempts':sum(a['acceptance_status']!='ACCEPT' for a in aa),'revision_attempts':sum(a['revision_count']>0 for a in aa),'attempt_acceptance_rate':sum(a['acceptance_status']=='ACCEPT' for a in aa)/len(aa)}
    write_json(out/'generation_statistics.json',metrics)
    return metrics

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True,type=Path);p.add_argument('audits',nargs='+');a=p.parse_args()
    print(json.dumps(assemble(a.audits,a.out),indent=2))
