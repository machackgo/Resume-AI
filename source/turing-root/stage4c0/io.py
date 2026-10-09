"""Canonical, replayable file-backed data-factory I/O. No model or network calls."""
import hashlib,json,os,re,tempfile
from pathlib import Path

VERSION='stage4c0-factory-v1'
def canonical(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False)
def digest(x):return hashlib.sha256((x if isinstance(x,str) else canonical(x)).encode()).hexdigest()
def strict_json(text):
    def pairs(xs):
        d={}
        for k,v in xs:
            if k in d:raise ValueError('duplicate JSON key '+k)
            d[k]=v
        return d
    def bad(x):raise ValueError('nonfinite JSON '+x)
    return json.loads(text,object_pairs_hook=pairs,parse_constant=bad)
def read_json(path):return strict_json(Path(path).read_text())
def read_jsonl(path):
    rows=[]
    for n,line in enumerate(Path(path).read_text().splitlines(),1):
        if not line.strip():raise ValueError(f'{path}:{n}: blank JSONL record')
        try:rows.append(strict_json(line))
        except (ValueError,TypeError) as e:raise ValueError(f'{path}:{n}: {e}') from e
    return rows
def immutable_write(path,text):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():
        if p.read_text()!=text:raise ValueError('refusing to overwrite immutable artifact '+str(p))
        return
    with p.open('x') as f:f.write(text)
def write_json(path,value):immutable_write(path,json.dumps(value,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def write_jsonl(path,rows):immutable_write(path,''.join(canonical(x)+'\n' for x in rows))
def sha_file(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
def norm(text):return ' '.join(re.findall(r'\w+|%|\$',text.casefold()))
def leaves(value,pointer=''):
    if isinstance(value,dict):
        for k,v in value.items():yield from leaves(v,pointer+'/'+str(k).replace('~','~0').replace('/','~1'))
    elif isinstance(value,list):
        for k,v in enumerate(value):yield from leaves(v,pointer+'/'+str(k))
    else:yield pointer,value
def pointer_get(value,pointer):
    for part in pointer.split('/')[1:]:
        key=part.replace('~1','/').replace('~0','~')
        value=value[int(key)] if isinstance(value,list) else value[key]
    return value
