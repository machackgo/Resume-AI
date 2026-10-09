"""Read-only verification of the preserved interruption checkpoint and archive."""
import datetime
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
before = json.loads((D / 'checkpoint-preservation-before.json').read_text())
source = Path(before['source'])
archive = Path(before['archive'])
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
manifest = json.loads((source / 'SHA256SUMS.json').read_text())['files']
bad = [name for name, meta in manifest.items()
       if not (source/name).is_file() or sha(source/name) != meta['sha256']]
metadata = json.loads(archive.with_name(archive.stem+'-archive-metadata.json').read_text())
result = dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              files_checked=len(manifest), mismatches=bad,
              archive_sha256=sha(archive),
              archive_matches=sha(archive)==before['archive_sha256']==metadata['sha256'],
              manifest_matches=sha(source/'SHA256SUMS.json')==metadata['manifest_sha256'])
print(json.dumps(result, indent=2))
assert not bad and result['archive_matches'] and result['manifest_matches']
