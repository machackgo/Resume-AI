import json,tempfile,subprocess,sys
from pathlib import Path
from rag.reasoning import regression
O=Path.cwd()/'results/stage4b/smoke'
for name,args in [('stage4b-tests',['-m','stage4b.test_cpu']),('stage4a-tests',['-m','unittest','discover','-s','tests/stage4a','-v'])]:
 p=subprocess.run([sys.executable,'-B',*args],capture_output=True,text=True);(O/(name+'.log')).write_text(p.stdout+p.stderr);print(name,p.returncode,flush=True);assert p.returncode==0,p.stderr
regression.OUT=O
with tempfile.TemporaryDirectory(prefix='stage4b-regression-') as work:regression.main(Path(work))
