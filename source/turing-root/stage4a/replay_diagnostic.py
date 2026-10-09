"""Diagnostic copy of historical replay; records first mismatch, never changes it."""
import json,tempfile,os,platform
from pathlib import Path
from .inspect import ROOT,OUT,dump

def compare(actual,expected,label,case,budget):
 if actual==expected:return
 changes=[]
 def walk(a,b,p=''):
  if type(a)!=type(b):changes.append([p,a,b])
  elif isinstance(a,dict):
   for k in set(a)|set(b):walk(a.get(k),b.get(k),p+'/'+k)
  elif isinstance(a,list):
   if len(a)!=len(b):changes.append([p+'/length',len(a),len(b)])
   for i,(x,y) in enumerate(zip(a,b)):walk(x,y,p+'/'+str(i))
  elif a!=b:changes.append([p,a,b])
 walk(actual,expected)
 dump(OUT/'historical-replay-first-mismatch.json',dict(host=platform.node(),slurm_job=os.environ.get('SLURM_JOB_ID'),label=label,case=case,budget=budget,differences=changes))
 raise ValueError('historical bitwise replay mismatch saved')
def main():
 source=(ROOT/'rag/reranking/replay.py').read_text()
 old="assert json.loads(json.dumps([asdict(x) for x in result]))==row['results'], (label,row['id'],budget)"
 assert old in source
 source=source.replace(old,"compare(json.loads(json.dumps([asdict(x) for x in result])),row['results'],label,row['id'],budget)")
 scope=dict(__name__='stage4a_historical_diagnostic',__package__='rag.reranking',compare=compare)
 exec(compile(source,'stage4a-diagnostic-copy-of-replay','exec'),scope)
 # On success, redirect only historical writer; reads stay frozen.
 original=scope['OUT']
 class Proxy:
  def __truediv__(self,n):return OUT/'diagnostic-replay-success.json' if n=='independent-replay.json' else original/n
 scope['OUT']=Proxy()
 with tempfile.TemporaryDirectory(prefix='stage4a-replay-diagnostic-') as work:scope['main'](Path(work))
if __name__=='__main__':main()
