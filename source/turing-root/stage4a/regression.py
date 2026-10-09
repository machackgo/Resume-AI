"""Run every prior test and saved-vector replay with new output destinations."""
import tempfile,json
from pathlib import Path
from rag.reasoning import regression
from .inspect import ROOT,OUT,sha,dump

def main():
 regression.OUT=OUT
 with tempfile.TemporaryDirectory(prefix='stage4a-regression-') as work:regression.main(Path(work))
 protected=json.loads((OUT/'protected-manifest.json').read_text())
 bad=[p for p,h in protected.items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h]
 dump(OUT/'preservation.json',dict(passed=not bad,files=len(protected),changed_or_missing=bad,includes_model_weights=True,includes_embedding_assets=True,includes_historical_caches=True))
 assert not bad,bad
 print('Historical protection verified',len(protected),flush=True)
if __name__=='__main__':main()
