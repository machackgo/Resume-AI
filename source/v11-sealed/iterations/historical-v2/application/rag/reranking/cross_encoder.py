"""Pinned local sequence classifier. Never runs a generative agent or remote code."""
import time
from .models import RerankerConfig
from ..domain import canonical

class LocalCrossEncoder:
    def __init__(self, spec, cache_dir, threads=4, batch_size=16):
        import torch
        import transformers
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        start = time.perf_counter()
        torch.set_num_threads(threads)
        torch.manual_seed(0)
        torch.use_deterministic_algorithms(True)
        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(spec['model'], revision=spec['revision'],
            cache_dir=str(cache_dir), local_files_only=True, trust_remote_code=False)
        self.model = AutoModelForSequenceClassification.from_pretrained(spec['model'], revision=spec['revision'],
            cache_dir=str(cache_dir), local_files_only=True, trust_remote_code=False,
            use_safetensors=True, attn_implementation='eager').to(device='cpu', dtype=torch.float32).eval()
        if self.model.config.num_labels != 1:
            raise ValueError('expected single relevance logit')
        self.config = RerankerConfig('transformers-cross-encoder-v1', spec['model'], spec['revision'],
            spec['revision'], batch_size=batch_size, max_tokens=spec['max_tokens'],
            runtime=canonical({'torch': torch.__version__, 'transformers': transformers.__version__,
                'threads': threads, 'attention': 'eager', 'overflow': 'reject', 'activation': 'raw-logit',
                'deterministic_algorithms': True, 'seed': 0}))
        self.parameter_count = sum(x.numel() for x in self.model.parameters())
        self.load_seconds = time.perf_counter() - start
        self.max_observed_tokens = 0

    def score(self, pairs):
        output = []
        for offset in range(0, len(pairs), self.config.batch_size):
            batch = pairs[offset:offset + self.config.batch_size]
            tokens = self.tokenizer([x.query for x in batch], [x.evidence for x in batch],
                                    padding=True, truncation=False, return_tensors='pt')
            length = int(tokens['attention_mask'].sum(1).max())
            self.max_observed_tokens = max(self.max_observed_tokens, length)
            if length > self.config.max_tokens:
                raise ValueError('pair exceeds token budget; truncation is forbidden')
            with self.torch.inference_mode():
                logits = self.model(**tokens).logits
            if tuple(logits.shape) != (len(batch), 1):
                raise ValueError('invalid logit shape')
            output.extend(float(x) for x in logits[:, 0].tolist())
        return tuple(output)
