"""Read-only earlier-stage replays with all reports redirected to Stage 3G."""
import json,subprocess,sys,re
from pathlib import Path
from .prepare import ROOT,OUT,dump
from ..reranking.prepare import sha

def main(folder,audit=False):
    checks={};counts={}
    for name,args in {'stage3_tests':['-m','unittest','discover','-s','tests/rag','-v'],
        'stage1_stage2_tests':['-m','unittest','discover','-s','eval/tests','-v'],
        'stage2_replay':['eval/runners/verify_stage2_run.py','results/prompt_engineered/grounded-v3-benchmark-2325384-1'],
        'stage3a_demo':['-m','rag.demo'],'stage3b_demo':['-m','rag.chunking.demo']}.items():
        p=subprocess.run([sys.executable,'-B',*args],cwd=ROOT,capture_output=True,text=True)
        (OUT/(name+'.log')).write_text(p.stdout+p.stderr);checks[name]=p.returncode==0
        if name.endswith('_tests'):
            m=re.search(r'Ran (\d+) tests?',p.stderr);counts[name]=int(m[1]) if m else 0
        if name.endswith('_demo') and p.returncode==0:
            checks[name]=json.loads(p.stdout)==json.loads((ROOT/('results/'+name.split('_')[0]+'/demo.json')).read_text())
    # Existing replay modules have historical output globals. Redirect only their writers.
    from ..reranking import evaluator,replay
    evaluator.OUT=OUT/'historical';evaluator.OUT.mkdir(exist_ok=True)
    loaded=evaluator.load_legacy(folder/'legacy');loaded[2].close();checks['stage3e_112']=True
    # Replay reads original Stage 3F assets; its final summary writer alone is redirected via proxy.
    original=replay.OUT
    class ReadOriginalWriteSummary:
        def __truediv__(self,name):return (OUT/'historical'/name) if name=='independent-replay.json' else original/name
    replay.OUT=ReadOriginalWriteSummary();replay.main(folder/'stage3f');checks['stage3f_297']=True
    if audit:
        manifest=json.loads((OUT/'preexisting_manifest.json').read_text())
        changed=[p for p,h in manifest.items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h]
        checks['preservation']=not changed
        dump(OUT/'preservation.json',{'protected_files':len(manifest),'changed':changed})
    report={'checks':checks,'tests':counts,'total_tests':sum(counts.values()),'passed':all(checks.values())}
    dump(OUT/'regression.json',report);print(json.dumps(report),flush=True)
    if not report['passed']:raise SystemExit(1)
if __name__=='__main__':main(Path(sys.argv[1]),'--audit' in sys.argv)
