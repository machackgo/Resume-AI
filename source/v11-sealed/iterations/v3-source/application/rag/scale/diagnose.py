"""Read-only retrieval diagnostics; never feed alternative rankings to Qwen."""
import json
from .prepare import OUT,dump,load_rows
from .dataset import SCALES
from ..embeddings.similarity import cosine

def main():
    data=json.loads((OUT/'dataset.json').read_text());docs={d['id']:d for d in data['documents']}
    queryvec=json.loads((OUT/'query-vectors.json').read_text());output=[]
    hard_core={'h01':['c06','c18'],'h02':['c13','c16','c17'],'h03':['c11'],'h04':['c23'],
               'h05':['c13','c16'],'h06':['c05','c22'],'h07':['c14'],'h08':['c02'],
               'h09':['c23'],'h10':[],'h11':['c02','c13','c16'],'h12':['c04','c05','c22'],
               'h13':['c06'],'h14':['c11'],'h15':['c23'],'h16':['c02','c17']}
    for scale in SCALES:
        meta=json.loads((OUT/(scale+'-corpus.json')).read_text());rows=load_rows(scale)
        active=set(rows[0]['contexts']['full']['provenance']);owners=meta['owners']
        records=[r for r in meta['records'] if r['evidence_id'] in active]
        for row in rows:
            q=row['case'];ranking=sorted([(cosine(queryvec[row['response']['query']['text']],r['vector']),r['record_id'],owners[r['chunk_id']]) for r in records],key=lambda x:(-x[0],x[1]))
            unique=[];seen=set()
            for score,rid,did in ranking:
                text=' '.join(docs[did]['text'].split())
                if text not in seen:unique.append((score,rid,did));seen.add(text)
            relevant=q['relevant'];details=[]
            for did in relevant:
                fullrank=next(i for i,x in enumerate(ranking,1) if x[2]==did)
                # Equivalent duplicate content counts as same group rank.
                text=' '.join(docs[did]['text'].split())
                urank=next(i for i,x in enumerate(unique,1) if ' '.join(docs[x[2]]['text'].split())==text)
                details.append(dict(document=did,raw_vector_rank=fullrank,distinct_text_rank=urank))
            entry=dict(scale=scale,id=q['id'],relevant_ranks=details,distinct_groups_in_top20=len(row['response']['results']),duplicate_suppressed=row['response']['duplicate_suppressed'])
            relational={d for g in q['gold'] for d in g['relations']}
            for n in (3,5):
                got=[row['id_to_doc'][e['evidence_id']] for g in row['contexts']['rag'+str(n)]['groups'] for e in g['evidence']]
                dangerous=[d for d in got if d not in relational and (d in hard_core[q['id']] or docs[d].get('distractor') in ('adjacent','assertion','training_inference','built_used'))]
                entry['dangerous_neighbor_rate_at_'+str(n)]=len(dangerous)/len(got) if got else 0
                entry['dangerous_docs_at_'+str(n)]=dangerous
            output.append(entry)
    dump(OUT/'retrieval-diagnostics.json',{'definition':'Authored adjacent core documents or distractor categories adjacent/assertion/training_inference/built_used, excluding records with an authored relation. Relatedness depends on retrieval; all-other-neighbor upper bound is separately reported. Diagnostic distinct-text ranks are not an evaluated alternate retrieval arm.','rows':output})
if __name__=='__main__':main()
