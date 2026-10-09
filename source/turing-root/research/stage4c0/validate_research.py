"""Validate the existing normalized research snapshot without fetching or regenerating it."""
import json, hashlib, re
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def validate(root=ROOT):
    sources=[json.loads(l) for l in (root/'sources.jsonl').read_text().splitlines()]
    ids=[s['source_id'] for s in sources]
    assert len(ids)==len(set(ids)), 'duplicate source IDs'
    assert len({s['url'] for s in sources})==len(sources), 'duplicate URLs'
    for s in sources:
        assert s['url'].startswith('https://')
        assert s['verified_on']=='2026-09-29'
        assert s['evidence_summary'] and s['scope'] and s['limitations']
        assert s['access_method'] in {'web_search_page_text','web_open_page_text'}
        assert s['full_source_text_stored'] is False
        assert s['license']['restriction']
        v=dict(s); stored=v.pop('snapshot_note_sha256')
        assert hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False).encode()).hexdigest()==stored
    principles=[]
    for f in sorted(root.glob('*_principles.json')):
        data=json.loads(f.read_text())
        assert data['knowledge_base_version']=='stage4c0-research-v1'
        principles+=data['principles']
    assert len({p['principle_id'] for p in principles})==len(principles)
    byid={s['source_id']:s for s in sources}
    for p in principles:
        assert p['version']=='1.0.0' and p['principle'] and p['provenance']
        assert p['scope'] in {'context_dependent','universal_product_rule'}
        assert p['evidence_kind'] in {'source_supported','conservative_inference','research_informed_product_rule','user_requirement_research_context'}
        for ref in p['provenance']:
            assert byid[ref['source_id']]['url']==ref['source_url']
            assert p['principle_id'] in byid[ref['source_id']]['principle_ids']
    m=json.loads((root/'research_manifest.json').read_text())
    assert m['source_count']==len(sources) and m['principle_count']==len(principles)
    assert set(m['coverage'])==set('ABCDEFGHIJ')
    assert all(m['coverage'].values())
    assert m['private_candidate_records_used']==m['public_job_postings_copied']==m['external_training_corpora_included']==0
    return dict(status='PASS',sources=len(sources),principles=len(principles),categories_covered=list('ABCDEFGHIJ'),checks=['unique IDs','provenance references','source note hashes','source licensing disposition','A-J coverage','version metadata','zero source-body/private-record ingestion'])

if __name__=='__main__':
    print(json.dumps(validate(),indent=2))
