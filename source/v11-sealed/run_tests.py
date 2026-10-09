import os,sys,unittest,json,time
from pathlib import Path
D=Path(__file__).resolve().parent;R=D/'application';sys.path.insert(0,str(R));sys.path.insert(0,str(R/'tests/rag'));sys.dont_write_bytecode=True
blocked=[]
def guard(event,args):
 if event=='open' and isinstance(args[0],(str,bytes)):
  p=Path(os.fsdecode(args[0])).resolve()
  if any(x in {'fixtures','datasets','eval','scenarios','research','eval_snapshot'} or 'holdout' in x.lower() or 'heldout' in x.lower() for x in p.parts):
   blocked.append(str(p));raise PermissionError('Protected evaluation content prohibited')
sys.addaudithook(guard)
os.chdir(R)
os.environ['PYTHONPATH']=str(R)
start=time.monotonic();suite=unittest.defaultTestLoader.discover(str(R/'tests/rag'))
with (D/'test-results.log').open('w') as stream:result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
summary=dict(tests_run=result.testsRun,failures=[{'test':str(t),'error':e} for t,e in result.failures],errors=[{'test':str(t),'error':e} for t,e in result.errors],skipped=[{'test':str(t),'reason':r} for t,r in result.skipped],protected_reads_denied=blocked,seconds=time.monotonic()-start)
summary['passed']=result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped)
(D/'test-results.json').write_text(json.dumps(summary,indent=2));print({k:v if not isinstance(v,list) else len(v) for k,v in summary.items()})
