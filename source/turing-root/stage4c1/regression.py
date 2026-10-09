"""Historical CPU tests/replays with new report destinations; no model training."""
import json,subprocess,sys,tempfile
from pathlib import Path
from rag.reasoning import regression

def main():
    out=Path.cwd()/'results/stage4c1/historical';out.mkdir(parents=True,exist_ok=True)
    checks={}
    for name,args in [('stage4c1-tests',['-m','stage4c1.test_evaluate']),('stage4c0-tests',['-m','unittest','discover','-s','stage4c0','-t','.', '-v']),('stage4b-tests',['-m','stage4b.test_cpu']),('stage4a-tests',['-m','unittest','discover','-s','tests/stage4a','-v'])]:
        p=subprocess.run([sys.executable,'-B',*args],capture_output=True,text=True)
        (out/(name+'.log')).write_text(p.stdout+p.stderr)
        checks[name]=p.returncode
    regression.OUT=out
    with tempfile.TemporaryDirectory(prefix='stage4c1-regression-') as work:
        regression.main(Path(work))
    (out/'additional-checks.json').write_text(json.dumps(checks,indent=2)+'\n')
    if any(checks.values()):raise SystemExit('historical regression failure')

if __name__=='__main__':main()
