"""Reproducible approved BASE runtime and canonical capture rehydration."""
import json,hashlib,time,sqlite3,tempfile,os
from pathlib import Path
from rag.adapters import CanonicalDocument,normalize
from rag.domain import Scope,Origin,Locator,canonical
from rag.ingestion import MemoryLedger
from rag.chunking.chunker import CandidateChunks
from rag.chunking.policy import POLICY_B
from rag.embeddings.local import LocalTransformerProvider
from rag.vectorstore.models import EmbeddingSpace
from rag.vectorstore.config import StoreConfig
from rag.vectorstore.sqlite_reference import SQLiteVectorStore
from rag.retrieval import RetrievalConfig
from rag.reranking.base import CitationTextResolver
from rag.deep.retrieve import DeepRetriever,DeepConfig,QueryRetriever

class CaptureAdapter:
    def __init__(self,source):self.source=source
    def read(self):
        s=self.source;text=s['text'];raw=text.encode()
        if hashlib.sha256(raw).hexdigest()!=s['capture_sha256']:raise ValueError('capture integrity failure')
        attrs={'document_id':s['id'],'section':'whole document','original_location':s['native_file']};kind='document.v1'
        if s['source_type']=='github':
            kind='github.v1';attrs={'repository':'machackgo/'+s['project'],'commit':s['commit'],'file':s['native_file'],'line_start':1,'line_end':len(text.splitlines())}
        return CanonicalDocument(s['source_type'],s['source_key'],s['source_uri'],s['title'],raw,normalize(raw),Origin(s['origin']),'acceptance-capture','acceptance-capture-v1',Locator(kind,canonical(attrs)),metadata_json=canonical({k:v for k,v in s.items() if k!='text'}))

def load_kb(root,kb):
    records=json.loads((kb/'embedding-records.json').read_text());scopes={tuple(r['scope'][k] for k in ('tenant_id','candidate_id')) for r in records}
    if len(scopes)!=1:raise ValueError('KB must bind one authenticated scope')
    scope=Scope(*next(iter(scopes)));ledger=MemoryLedger(clock=lambda:'2026-10-07T12:00:00+00:00').for_candidate(scope)
    service=CandidateChunks(ledger)
    provider=LocalTransformerProvider(json.loads((root/'results/stage3c/models.lock.json').read_text())[0],str(root/'models/stage3c'))
    ledger.review_evidence=[]
    for s in json.loads((kb/'candidate_sources.json').read_text()):
        e=ledger.ingest(CaptureAdapter(s)).evidence
        service.fit_for_embedding(service.generate(e.evidence_id,POLICY_B),provider)
        ledger.review_evidence.append(e)
    store=open_local_snapshot(kb,scope)
    resolver=CitationTextResolver(store,service)
    retriever=QueryRetriever(store,provider,EmbeddingSpace(provider.config,'title-section-v1'),service,[r['record_id'] for r in records],RetrievalConfig(),normalize=True)
    return DeepRetriever(retriever,resolver,DeepConfig()),ledger,store

def open_local_snapshot(kb,scope):
    # SQLite's live connection must be on a local filesystem. The KB directory
    # is an immutable export/snapshot and may be on shared storage.
    temp=tempfile.TemporaryDirectory(prefix='resume-ai-sqlite-')
    original=list((kb/'candidate-vector-store').glob('*.sqlite3'))
    if len(original)!=1:temp.cleanup();raise ValueError('exactly one scoped SQLite snapshot required')
    target=Path(temp.name)/original[0].name
    with sqlite3.connect('file:'+str(original[0])+'?mode=ro',uri=True) as src, sqlite3.connect(target) as dest:
        if tuple(src.execute('SELECT tenant_id,candidate_id FROM scope_binding').fetchone())!=scope.key:
            temp.cleanup();raise ValueError('snapshot scope mismatch')
        src.backup(dest)
    target.chmod(0o600)
    class LocalSnapshotStore(SQLiteVectorStore):
        def export_snapshot(self,directory):
            directory=Path(directory);directory.mkdir(parents=True,exist_ok=True,mode=0o700)
            fd,name=tempfile.mkstemp(prefix='.snapshot-',dir=directory);os.close(fd)
            try:
                with sqlite3.connect(name) as destination:self._db.backup(destination)
                os.chmod(name,0o600)
                os.replace(name,directory/self.path.name)
            finally:
                if os.path.exists(name):os.unlink(name)
        def close(self):
            try:super().close()
            finally:temp.cleanup()
    return LocalSnapshotStore(StoreConfig(Path(temp.name)),scope)

class BaseQwen:
    def __init__(self,root):
        import torch
        from transformers import AutoTokenizer,AutoModelForCausalLM,BitsAndBytesConfig
        self.torch=torch;torch.manual_seed(410042);torch.cuda.manual_seed_all(410042)
        self.tokenizer=AutoTokenizer.from_pretrained(root/'models/Qwen3.8-27B',local_files_only=True)
        quant=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',bnb_4bit_use_double_quant=True,bnb_4bit_compute_dtype=torch.bfloat16)
        self.model=AutoModelForCausalLM.from_pretrained(root/'models/Qwen3.8-27B',local_files_only=True,quantization_config=quant,device_map={'':0},dtype=torch.bfloat16,attn_implementation='sdpa').eval()
        for p in self.model.parameters():p.requires_grad_(False)
        self.decode=dict(do_sample=False,max_new_tokens=1536,use_cache=True,pad_token_id=self.tokenizer.pad_token_id,eos_token_id=list(set([self.tokenizer.eos_token_id,self.tokenizer.convert_tokens_to_ids('<|im_end|>')])))
        self.configuration=dict(arm='BASE',adapter_loaded=False,quantization=quant.to_dict(),decode=self.decode,chat_template_sha256=hashlib.sha256(self.tokenizer.chat_template.encode()).hexdigest(),tokenizer_class=type(self.tokenizer).__name__,model_class=type(self.model).__name__,declared_context_limit=self.model.config.max_position_embeddings,operational_input_limit=8192,thinking=False)
    def prompt(self,messages):return self.tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=False)
    def token_count(self,messages):return len(self.tokenizer(self.prompt(messages),add_special_tokens=False)['input_ids'])
    def generate(self,messages):
        prompt=self.prompt(messages);x=self.tokenizer(prompt,add_special_tokens=False,return_tensors='pt').to('cuda');start=time.monotonic()
        if x['input_ids'].shape[1]>8192:raise ValueError('model input budget exceeded')
        with self.torch.inference_mode():y=self.model.generate(**x,**self.decode)
        ids=y[0,x['input_ids'].shape[1]:].tolist()
        return dict(text=self.tokenizer.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False),input_tokens=x['input_ids'].shape[1],generated_tokens=len(ids),termination='eos' if ids and ids[-1] in self.decode['eos_token_id'] else 'length',prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),seconds=time.monotonic()-start,arm='BASE',trainable_parameters=sum(p.numel() for p in self.model.parameters() if p.requires_grad),gradients_present=any(p.grad is not None for p in self.model.parameters()))
