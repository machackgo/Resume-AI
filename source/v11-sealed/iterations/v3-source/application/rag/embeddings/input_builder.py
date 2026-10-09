"""Only existing source title and locator section may supplement chunk text."""
import json
from ..domain import digest
from .models import EmbeddingInput

STRATEGIES = ('raw-v1', 'title-section-v1')


def build_input(chunk, strategy='raw-v1'):
    if strategy not in STRATEGIES:
        raise ValueError('unknown input strategy')
    text = chunk.text
    if strategy == 'title-section-v1':
        section = json.loads(chunk.evidence.locator.attributes_json).get('section')
        text = 'Title: ' + chunk.evidence.source_title + '\n'
        if isinstance(section, str) and section.strip():
            text += 'Section: ' + section + '\n'
        text += 'Text: ' + chunk.text
    return EmbeddingInput(strategy, text, digest(text.encode('utf-8')))
