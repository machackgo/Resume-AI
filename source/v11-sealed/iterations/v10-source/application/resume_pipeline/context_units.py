"""Canonical whole-line quotation units with explicit chunk-to-span lineage.

Retrieved chunks can begin mid-sentence. Expand only their boundary lines, with
an explicit size cap, then expose whole source-authored prose units. No new
candidate fact is inferred. Units from different sources never share identity.
"""
import hashlib,json,re

def source_heading(source,offset):
    heading=None
    for h in re.finditer(r'[^\n]+',source[:offset]):
        value=h.group().strip()
        if (' | ' in value and not value.endswith('.')) or re.match(r'^#{1,6}\s+',value) or re.match(r'^\d+(?:\.[A-Z]|\.)?\s+(?:Section\s+)?[A-Z]',value):
            ha=h.start()+len(h.group())-len(h.group().lstrip())
            heading=dict(text=value,start=ha,end=ha+len(value))
    if heading:
        scopes=[]
        for sm in re.finditer(r'[^\n]+',source[:min(offset,400)]):
            if re.search(r'\b(?:assignment|coursework|university|classroom|academic|course)\b',sm.group(),re.I):
                st=sm.group().strip();sa=sm.start()+len(sm.group())-len(sm.group().lstrip())
                scopes.append(dict(text=st,start=sa,end=sa+len(st)))
        if scopes:heading={**heading,'document_scope':scopes}
    return heading

def prepare_units(provenance,ledger,max_characters=1800):
    output={}
    for parent_id,p in provenance.items():
        ref=p['reference'];e=ledger.evidence(ref['evidence_id']);source=ledger.content(e.normalized_ref).decode()
        a=source.rfind('\n',0,ref['start'])+1
        found=source.find('\n',ref['end']);b=found if found>=0 else len(source)
        if b-a>max_characters:a,b=ref['start'],ref['end']
        identity=(ref['scope'],ref['source_id'],ref['evidence_id'],ref['source_version'],a,b)
        eid='cite_'+hashlib.sha256(json.dumps(identity,sort_keys=True,separators=(',',':')).encode()).hexdigest()[:24]
        units=[]
        for match in re.finditer(r'[^\n]+',source[a:b]):
            text=match.group();offset=a+match.start()
            prefix=re.match(r'\s*(?:[-*•]\s+)?',text).end();text=text[prefix:].rstrip();offset+=prefix
            # The canonical line, not just the delivered prefix/suffix, must fit.
            if offset and source[offset-1] not in '\n \t*•-':continue
            if offset+len(text)<len(source) and source[offset+len(text)] not in '\n\r \t':continue
            if not text or not text[0].isupper() or not text.endswith(('.', '!', '?')) or len(text.split())<3:continue
            if any(t in text for t in ('def ','import ','return ','</','=>','```')):continue
            if not (offset<ref['end'] and offset+len(text)>ref['start']):continue
            # Confirm that a mid-line chunk has not masqueraded as a whole line.
            line_start=source.rfind('\n',0,offset)+1
            if source[line_start:offset].strip(' \t-*•'):continue
            endline=source.find('\n',offset);endline=len(source) if endline<0 else endline
            if source[offset+len(text):endline].strip():continue
            heading=source_heading(source,offset)
            unit=dict(text=text,start=offset,end=offset+len(text),source_context=heading)
            from .semantic_contracts import identity
            unit['semantic_identity']=identity(ref,unit,e)
            units.append(unit)
        if eid not in output:
            output[eid]=dict(reference=ref,content=source[a:b],context_span=[a,b],allowed_quotes=units,parent_citation_ids=[parent_id],parent_chunk_ids=[ref['chunk_id']],attestations=p.get('attestations',[]))
        else:
            old=output[eid]
            if old['content']!=source[a:b]:raise ValueError('canonical context identity conflict')
            old['parent_citation_ids'].append(parent_id);old['parent_chunk_ids'].append(ref['chunk_id'])
            for unit in units:
                if unit not in old['allowed_quotes']:old['allowed_quotes'].append(unit)
    return output
