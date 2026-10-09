"""Optional pinned Transformers adapter; no model library imports in core."""
import json
from pathlib import Path
from .models import EmbeddingConfig
from ..domain import canonical


class LocalTransformerProvider:
    def __init__(self, spec, cache_dir, threads=4):
        import torch
        import transformers
        from transformers import AutoModel, AutoTokenizer
        torch.set_num_threads(threads)
        torch.manual_seed(0)
        torch.use_deterministic_algorithms(True)
        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(spec['model'], revision=spec['revision'],
                            cache_dir=cache_dir, local_files_only=True, trust_remote_code=False)
        self.model = AutoModel.from_pretrained(spec['model'], revision=spec['revision'],
                            cache_dir=cache_dir, local_files_only=True, trust_remote_code=False,
                            attn_implementation='eager').to('cpu').eval()
        self.max_tokens = spec['max_tokens']
        self.batch_size = 16
        self.parameter_count = sum(p.numel() for p in self.model.parameters())
        self.config = EmbeddingConfig('transformers-mean-pooling-v1', spec['model'], spec['revision'],
            self.model.config.hidden_size, True, spec['document_prefix'], spec['query_prefix'],
            canonical({'pooling':'attention-mask-mean', 'max_tokens':self.max_tokens,
                       'overflow':'reject', 'dtype':'float32', 'device':'cpu', 'batch_size':self.batch_size,
                       'torch':torch.__version__, 'transformers':transformers.__version__,
                       'tokenizer_revision':spec['revision'], 'attention':'eager', 'threads':threads}))
        self.max_observed_tokens = 0

    def _embed(self, texts, prefix):
        torch = self.torch
        output = []
        for start in range(0, len(texts), self.batch_size):
            batch = texts[start:start+self.batch_size]
            if any(not isinstance(t,str) or not t.strip() for t in batch):
                raise ValueError('nonempty text required')
            tokens = self.tokenizer([prefix+t for t in batch], padding=True, truncation=False, return_tensors='pt')
            lengths = tokens['attention_mask'].sum(1)
            self.max_observed_tokens = max(self.max_observed_tokens, int(lengths.max()))
            if int(lengths.max()) > self.max_tokens:
                raise ValueError('embedding input exceeds pinned token budget; refusing truncation')
            with torch.inference_mode():
                hidden = self.model(**tokens).last_hidden_state
                mask = tokens['attention_mask'].unsqueeze(-1)
                pooled = (hidden * mask).sum(1) / mask.sum(1)
                vectors = torch.nn.functional.normalize(pooled, p=2, dim=1)
            output.extend(tuple(float(x) for x in row) for row in vectors.tolist())
        return tuple(output)

    def embed_documents(self, texts):
        return self._embed(texts, self.config.document_prefix)

    def embed_queries(self, texts):
        return self._embed(texts, self.config.query_prefix)
