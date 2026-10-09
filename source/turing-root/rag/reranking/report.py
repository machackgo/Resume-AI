"""Derive reviewable tables, failures and selection from recorded experiments."""
from pathlib import Path
import hashlib
import json
from .prepare import ROOT, OUT

LABELS=('identity','minilm','tinybert')

def read(name): return json.loads((OUT/name).read_text())
def fmt(value): return 'n/a' if value is None else f'{value:.4f}'
def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(str(x) for x in row)+' |' for row in rows])+'\n'

def main():
    reports={name:read(name+'.json') for name in LABELS}
    legacy={name:read('legacy-'+name+'.json') for name in LABELS}
    data=json.loads((ROOT/'fixtures/rag/reranking_eval/stage3f_v1.json').read_text())
    qmap={q['id']:q for q in data['queries']}; docs={d['id']:d for d in data['documents']}
    validation=read('validation.json'); replay=read('independent-replay.json'); frozen=read('stage3e_replay.json')
    assert validation['passed'] and replay['passed'] and frozen['comparisons']==112
    selection={'stage':'3F','selected_provider':'identity','learned_reranker_promoted':False,
        'retrieval':{'strategy':'semantic','internal_budget':20,'top_k':5,'exact_duplicate_grouping':True,'expansion':False,'source_caps':None},
        'rerank_candidate_budget':5,'downstream_evidence_budget':5,
        'alternative_budget_3':'Optional only with measured evidence-loss tolerance; retains one direct relevant group for 33/33 extended and a frozen judged reference for 27/28 legacy needs. Does not preserve all judged evidence.',
        'reason':'Both learned models regress on frozen Stage 3E judgments and reduce top-three direct-evidence survival. MiniLM top-five MRR gain is real but insufficient for default promotion.',
        'score_semantics':'uncalibrated relevance priority only; never support or verification',
        'stage3g_started':False}
    (OUT/'selected_config.json').write_text(json.dumps(selection,indent=2)+'\n')
    # Complete per-query review including undeclared grade-zero/non-direct top-1 failures.
    failures=[]; regression=[]
    for label in LABELS:
        for row in reports[label]['queries']:
            q=qmap[row['id']]; budget=row['requested_candidate_budget']
            baseline=next(x for x in reports['identity']['queries'] if x['id']==row['id'] and x['requested_candidate_budget']==budget)
            failures.append({'model':label,'candidate_budget':budget,'id':row['id'],'need':q['query'],
                'category':q['category'],'metrics':row['metrics'],'declared_pair_failures':row['dangerous_failures'],
                'top1_grade':q['grades'][row['ranking'][0]],
                'top5':[{'document_id':doc,'text':docs[doc]['text'],'grade':q['grades'][doc],
                         'original_rank':x['original']['rank'],'rerank_rank':x['rerank_rank'],
                         'rerank_score':x['rerank_score'],'original_semantic_score':x['original']['semantic_score'],
                         'reference':x['original']['reference'],'corroborating_references':x['original']['corroborating_references']}
                        for doc,x in zip(row['ranking'][:5],row['results'][:5])]})
            if label!='identity':
                deltas={k:row['metrics'][k]-baseline['metrics'][k] for k in ('mrr','ndcg_at_3','ndcg_at_5','recall_at_1','recall_at_3','hit_at_3')}
                if any(v<0 for v in deltas.values()): regression.append({'model':label,'budget':budget,'query':row['id'],'deltas':deltas})
    (OUT/'failure_analysis.json').write_text(json.dumps(failures,indent=2)+'\n')
    (OUT/'regressions.json').write_text(json.dumps(regression,indent=2)+'\n')
    appendix=['# Stage 3F — dangerous neighbors and per-query review','',
        'All figures below are evaluation relevance, never support. Declared-pair inversion rates alone do not capture every error. These tables also show the actual top-one grade for every query and all direct-evidence survival failures. Full texts, scores, original ranks and provenance are in `results/stage3f/failure_analysis.json`; all metric regressions are in `regressions.json`.','']
    for label in LABELS:
        for budget in (5,10,20):
            rows=[x for x in failures if x['model']==label and x['candidate_budget']==budget]
            appendix+=['## '+label+' — candidate budget '+str(budget),'',table(['Need','Top 1 (grade)','Top 3 IDs','Direct evidence in top 3','Declared pair inversions'],[
                [x['id'],x['top5'][0]['document_id']+' ('+str(x['top1_grade'])+')',', '.join(y['document_id'] for y in x['top5'][:3]),int(x['metrics']['hit_at_3']),x['metrics']['danger_pairs_failed']] for x in rows]),'']
            for x in rows:
                if x['declared_pair_failures']:
                    appendix+=['### '+x['id'],'',table(['Stronger evidence','Rank','Weaker evidence ranked above it','Rank'],[
                        [', '.join(f['stronger_docs']),f['stronger_rank'],', '.join(f['weaker_docs']),f['weaker_rank']] for f in x['declared_pair_failures']]),'']
    (ROOT/'docs/stage3f_dangerous_neighbors.md').write_text('\n'.join(appendix)+'\n')
    text=['# Stage 3F completion report — evidence reranking','',
      '**Stage 3F complete. Retain semantic ordering through the identity reranker as the default. Neither learned model is promoted. Stage 3G and all later stages remain unstarted.**','',
      'Project: `~/scratch/resume-ai` on WPI Turing. All additions are isolated to Stage 3F paths. The implementation is provider-independent, uses actual candidate-scoped Stage 3E results, preserves their full provenance, and never converts scores into support/entailment labels.','',
      '## 1. Architecture and abstraction','',
      '`ScopedReranker` implements `Reranker.rerank(information_need, retrieval_results, top_n)` and returns frozen `RerankedEvidence` objects. A separate `ScoreProvider` receives only paired query/evidence text and returns finite positional scores. It cannot return new evidence. Each wrapper is bound to an authenticated scope and one Stage 3E response. Providers can be replaced without changing retrieval. See [architecture](stage3f_architecture.md).','',
      '`RerankedEvidence.original` retains the entire unchanged retrieval result, including original semantic score/rank, tenant/candidate, query, embedding/chunk/evidence/source/version, claim links, trust, semantic space, native locator and all corroborating references. New fields record need ID, rerank rank/score, provider configuration, actual candidate count, output budget and input hash.','',
      '## 2. Input construction and score meaning','',
      '`need-evidence-v1` pairs the exact information-need text with the raw resolved evidence chunk. It excludes identity, tenant, titles, trust flags, labels and retrieval scores. Exact numbers, names, versions, negations and prompt-like text are preserved. Combined inputs over 512 tokens are rejected rather than truncated. The largest measured evaluation pair was 78 tokens. Both real models passed an overlength rejection check.','',
      'Scores are raw relevance logits, not probabilities or verification. Identity scores encode original order only. Equal learned scores retain original retrieval order. Identical evidence text receives equal relevance scores regardless of source-origin metadata. Explicit verification language can influence text relevance, but even issuer-confirmation wording in this synthetic corpus remains untrusted evidence, not actual verified credentials.','',
      '## 3. Models and selection rationale','',
      'Two small English query–passage cross-encoders were selected to compare a moderate-capacity model against a low-latency model without downloading a large reranker. They jointly inspect each query/document pair, and their published task is passage ranking. Both model cards declare Apache-2.0; neither requires paid inference or a noncommercial-only model gate. This establishes a plausible product-evaluation option, not completed licensing/product diligence. Primary model cards: [MiniLM-L6](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2), [TinyBERT-L2](https://huggingface.co/cross-encoder/ms-marco-TinyBERT-L2-v2).','']
    specs=read('models.lock.json')
    text+=[table(['Model','Pinned revision','Parameters','Downloaded bytes','Pair limit / batch'],[
        [s['model'],s['revision'],reports[label]['resource']['parameters'],s['download_bytes'],'512 / 16'] for s,label in zip(specs,('minilm','tinybert'))]),'',
      'Both use local safetensors, no remote code, CPU float32, four threads, eager attention, eval/inference mode and deterministic algorithms. The separate cache is `models/stage3f/`. No Qwen or embedding asset was downloaded again or modified, and no environment dependency was changed. Larger BGE/instruction rerankers were not downloaded: this stage already establishes two real learned baselines and demonstrates material domain regressions; additional models would require a separately justified experiment.','',
      '## 4. Dataset, relevance labels and baseline integrity','',
      'The frozen track reconstructs the existing Stage 3E synthetic corpus from its saved vectors and reproduces all 112 semantic/lexical/hybrid/grouped responses exactly. Learned comparisons use the same 28 grouped semantic candidate sets; frozen binary/singleton labels are unchanged. The separate Stage 3C-compatible 22-query historical semantic results remain Recall@1 68.18%, Recall@3 90.91%, Recall@5 100%, MRR 0.8030; they are not relabeled or confused with the two tables below.','',
      'The extended track has 85 source records, 96 chunks/embedding records and 33 needs, reusing all Stage 3E documents. One stale source version is excluded from normal retrieval. New cases include REST construction/consumption/documentation, design/implementation, integration/development, production/local use, training/inference, adjacent frameworks/clouds, QLoRA/LoRA/4-bit inference/RAG, 40%/30%/4%/increased latency/unrelated accuracy, issuer-specific credential wording, Qwen/Llama/model versions, PostgreSQL versions, duplicates and malicious text. Candidate sets come from the unchanged Stage 3E API against the whole corpus.','',
      'Grades were authored before learned scoring: 3 directly addresses the need; 2 strongly related but incomplete; 1 adjacent/contextually useful; 0 irrelevant or misleading. Every active document has an explicit grade for every need. This is a single-author synthetic benchmark, not independently adjudicated production validation. Identical metadata-only texts have equal semantic relevance; no fabricated trust distinction is smuggled into model inputs. No labels, expected answers or hand-tuned boosts enter scoring.','',
      'Identity outputs exactly reproduce the input ranking and full original objects. For the extended track, exact text groups count once and retain all source references. Recall, MRR, MAP and survival use grade 3. nDCG uses gains 2^grade−1 and the full active-corpus ideal; candidate-conditional nDCG is separately recorded. Multiple relevant groups make Recall@1 lower than the fraction of successful queries.','',
      '## 5. Controlled ranking comparison — extended 33 needs, rerank 5','']
    keys=['mrr','ndcg_at_3','ndcg_at_5','recall_at_1','recall_at_3','top1_hard_negative_error','dangerous_neighbor_rate']
    text += [table(['Method','MRR','nDCG@3','nDCG@5','Recall@1','Recall@3','Declared hard-negative top-1','Danger pair rate'],[
        [label]+[fmt(reports[label]['summary'][0]['metrics'][k]) for k in keys] for label in LABELS]),'',
      '**Selected Stage 3F configuration equals the identity row.** MiniLM improves extended MRR and reduces declared neighbor inversions, but loses relevant evidence from top three and harms frozen-set ranking. TinyBERT also has harmful regressions. Aggregate MRR alone does not justify promotion.','',
      '## 6. Frozen Stage 3E comparison — 28 needs, same grouped candidates, rerank 5','',
      table(['Method','MRR','Representative R@1','Representative R@3','Grouped R@3','Grouped R@5'],[
       [label]+[fmt(legacy[label]['summary'][0]['metrics'][k]) for k in ('mrr','recall_at_1','recall_at_3','grouped_recall_at_3','grouped_recall_at_5')] for label in LABELS]),'',
      'Representative-only frozen labels can penalize an equivalent sibling; grouped recall is therefore shown explicitly. Nevertheless, both learned models also regress on grouped top-three recall. Returning all five preserves the same retrieved evidence regardless of ordering.','',
      '## 7. Hard negatives and dangerous neighbors','',
      'Dangerous-neighbor rate is the fraction of explicitly graded stronger/weaker pairs that are inverted, among pairs with both members actually retrieved. At budget five, the identical candidate pools expose 58 of 233 declared pairs: identity inverts 18, MiniLM 7, TinyBERT 8. Absent stronger evidence is tracked separately, not counted as a win. At budget twenty, 126 pairs are evaluable; changes in denominator mean cross-budget rates are not pure model improvements. Exact duplicates and repeated crowded-source chunks can correlate pair outcomes.','',
      'The declared hard-negative list is deliberately distinguishable from all ranking errors. For example, MiniLM elevates generic AWS credential wording above AWS deployment evidence, and TinyBERT ranks the malicious AWS-certification instruction first for AWS deployment. Those grade-zero errors are not in that query’s narrow cloud-neighbor list. They remain exposed in the following table and full per-query diagnostics.','']
    severe=[]
    for label in LABELS:
        part=[x for x in failures if x['model']==label and x['candidate_budget']==5]
        severe.append([label,sum(x['top1_grade']==0 for x in part),sum(x['top1_grade']<3 for x in part),sum(not x['metrics']['hit_at_3'] for x in part)])
    text += [table(['Method','Grade-zero top-1 /33','Non-direct top-1 /33','No direct evidence in top 3 /33'],severe),'',
      'Important regressions: MiniLM still puts consumed API evidence above built Python APIs; ranks hosted-service use above production deployment; places the deployed-inference direct match fifth; and puts credential text and prompt-like AWS claims above an AWS deployment match. TinyBERT promotes using a retrieval library above building one, implementation above a design request, generic performance above deployed inference, and pushes direct RAG evidence to fifth. These are relevance errors, never support decisions.','',
      'Every pair inversion at all three candidate budgets, every query’s top-three order, grade-zero errors and direct-evidence losses are enumerated in [dangerous-neighbor review](stage3f_dangerous_neighbors.md). Machine-readable complete scores/text/provenance: `results/stage3f/failure_analysis.json`; every per-query negative metric delta: `regressions.json`.','',
      '## 8. Numeric, entity, credential and action sensitivity','']
    sensitivity=[]
    for qid in ('api_production','qlora','inference_latency','latency','model_name','postgres_version','aws_verified','aws_relevant'):
        ranks=[]
        for label in LABELS:
            r=next(x for x in reports[label]['queries'] if x['id']==qid and x['requested_candidate_budget']==5)
            ranks.append(', '.join(r['ranking'][:3]))
        sensitivity.append([qid]+ranks)
    text += [table(['Need','Identity top 3','MiniLM top 3','TinyBERT top 3'],sensitivity),'',
      'Both learned models correct the 30%-above-40% inference-latency top-one error in this fixture. TinyBERT still puts the 30% result above one exact 40% result for the broader latency query. The exact Qwen model/version and PostgreSQL upgrade target remain first for all methods. The explicitly issuer-verified AWS credential stays first, while assertion and interest statements remain separately visible. These small checks are evidence of measured sensitivity, not guarantees for other percentages, models, versions or credentials.','',
      '## 9. Candidate-budget and latency experiment','']
    text += [table(['Method','Candidate cap','MRR','nDCG@3','R@3','Hit@2','Hit@3','Median ms','p95 ms','Docs/sec'],[
        [label,s['candidate_budget']]+[fmt(s['metrics'][k]) for k in ('mrr','ndcg_at_3','recall_at_3','hit_at_2','hit_at_3')]+[f"{s['latency_median_ms']:.2f}",f"{s['latency_p95_ms']:.2f}",f"{s['documents_per_second']:.1f}"]
        for label in LABELS for s in reports[label]['summary']]),'',
      'The Stage 3E internal semantic budget stays 20 in every experiment. Candidate caps are prefixes of its grouped response; some “20” runs have only 14–19 unique groups. All methods see exactly the same candidates at each cap. Increasing to 10 or 20 substantially worsens learned ranking and costs more CPU time; no increase is recommended. Median/p95 cover three warmed end-to-end rerank calls per need, including provenance resolution, tokenization and scoring, excluding initial model load and Stage 3E retrieval. Docs/sec counts actual documents, not requested caps.','',
      '## 10. Downstream evidence budget recommendation','',
      '**Recommend five evidence groups as the future downstream default, using identity ordering.** This preserves all frozen judged references in the retrieved five and avoids silently dropping relevant material. Three is a measured optional economy setting, not a guarantee: it covers at least one direct group for 33/33 extended needs but only 27/28 frozen needs, and frozen grouped evidence recall is 93.37%. Two is materially worse. No Qwen call was made.','']
    budgetrows=[]
    for label in LABELS:
        ext=reports[label]['summary'][0]['metrics']; old=legacy[label]['summary'][0]['metrics']
        lr=[x for x in legacy[label]['queries'] if x['candidate_budget']==5]
        for k in (2,3,5):
            budgetrows.append([label,k,fmt(ext['hit_at_'+str(k)]),fmt(ext['recall_at_'+str(k)]),
                               str(sum(x['metrics']['grouped_recall_at_'+str(k)]>0 for x in lr))+'/28',fmt(old['grouped_recall_at_'+str(k)])])
    text += [table(['Method (rerank 5)','Output groups','Extended hit rate','Extended direct recall','Frozen needs with a judged ref','Frozen grouped recall'],budgetrows),'',
      'The extended corpus contains multiple direct records/chunks for some needs, so even five-group recall is below 100%; survival of one direct item is not completeness. Independent replay explicitly tests that top-two/top-three API results match full-ranking prefixes and preserve scores.','',
      '## 11. Diversity and corroboration','',
      'Exact source grouping survives unchanged. All independently sourced references are retained inside each selected group, with their own trust and provenance. A tie-only source-diversity diagnostic changed no rankings for any method/budget on this dataset; it supplies no evidence for adding a diversity boost. Retain pure relevance and no source cap. This does not establish that diversity can never help; score-margin/source-cap policies remain unselected.','',
      '## 12. Resources and model-load cost','']
    resources=[read('resources-'+str(i)+'.json') for i in (0,1)]
    text += [table(['Model','Fresh-process constructor including imports (s)','Weight/tokenizer initialization (s)','Peak process RSS after 20 pairs (MiB)'],[
        [x['model'],f"{x['constructor_seconds_including_framework_imports']:.3f}",f"{x['weight_tokenizer_load_seconds']:.3f}",f"{x['peak_rss_kib_after_20_pairs']/1024:.1f}"] for x in resources]),'',
      'These independent resource probes load no embedding/Qwen model. Shared filesystem caches may be warm. Main evaluator process memory also includes its Stage 3E corpus, SQLite and prior embedding work; its cumulative peaks are retained rather than attributed solely to rerankers. Scheduler job-level accounting includes preparation, regression and file auditing; it is not interchangeable with isolated model RSS. CPU latency was sufficient, so no GPU comparison or GPU allocation was justified. All remote model/test computation used Slurm, account cs541, partition academic. GPU-capable node names do not mean a GPU was requested. See `slurm_accounting.txt`.','',
      '## 13. Security, lifecycle, provenance and trust verification','',
      'Tests reject foreign tenant/candidate references, forged query identities, altered retrieval results, unseen same-candidate evidence, foreign corroborating siblings, malformed score vectors, nonfinite scores, configuration drift and mixed semantic spaces. A provider returning evidence objects is rejected. A test replaces vector search with an exception and still successfully reranks, demonstrating no search call. Stale/deleted/purged evidence after retrieval fails closed.','',
      'Every extended record completes stored-vector → embedding-record → chunk/revision → canonical evidence → source/version → native locator resolution. Each scored representative and grouped sibling has all metadata revalidated against that chain. Immutable originals and deterministic full-result replay ensure trust, claim relationships, provenance events, semantic-space metadata and original scores are retained. All synthetic records remain untrusted data. Prompt-like content is passed as classifier data only; it can receive a bad score but cannot execute instructions or invoke tools. The trusted caller/OS boundary and serialized mutation requirement remain unchanged.','',
      '## 14. Determinism and reproducibility','',
      f"Within-run repeated calls reproduced {sum(d['exact_replays'] for d in reports.values())} full rankings exactly. A separate Slurm process reproduced {sum(x['full_result_replays'] for x in replay['checks'])} full result sets, including bitwise-equal learned float scores, and checked {sum(x['top2_top3_prefix_checks'] for x in replay['checks'])} output-budget prefixes. All 33 saved-vector candidate sets and all 112 historical Stage 3E responses matched exactly.",'',
      'Recorded identity includes model revision, tokenizer revision, input strategy, device, dtype, batch size, token limit, runtime library versions, deterministic settings, candidate/output budgets and input hashes. Artifact/model SHA-256 manifests and environment freeze are saved. These checks establish exact replay on the recorded CPU/software configuration, not universal bitwise equality across hardware, library upgrades, batching changes or nondeterministic devices.','',
      '## 15. Tests and preservation','',
      f"**{validation['total_tests']}/{validation['total_tests']} tests pass: all 205 prior tests unchanged plus 68 new Stage 3F tests.** Frozen Stage 2 replay and Stage 3A/3B demos also pass. All {validation['protected_files']} protected preexisting file paths are byte-identical, including {validation['protected_model_paths']} existing model/cache file paths (symlink-addressable assets may be counted at multiple paths). This larger manifest covers prior Stage 3E outputs as well as the previously protected earlier stages. The 14 newly pinned reranker snapshot assets also pass hash verification. No historical result file was overwritten.",'',
      'New unit coverage includes identity/provider abstraction, deterministic ties, score/cardinality validation, empty/zero/fewer-than-N cases, top-N/subsets, full provenance round trip, trust/claims/space preservation, three-source exact grouping, foreign/unseen evidence, post-retrieval lifecycle changes, malicious text, exact numbers/entities/actions, config drift, grade validation, nDCG/MRR/MAP/Recall, hard-negative coverage and dangerous-pair metrics. The learned behaviors are measured by the actual benchmark and independent replay, not mocked as guaranteed model successes.','',
      '## 16. Files created and modified','',
      '**No preexisting project file was modified.** Added source files in `rag/reranking/`: `__init__.py`, `models.py`, `base.py`, `input_builder.py`, `cross_encoder.py`, `metrics.py`, `evaluator.py`, `prepare.py`, `validate.py`, `replay.py`, `resources.py`, `report.py`, plus `prepare.slurm`, `evaluate.slurm`, `final_check.slurm`, `resources.slurm`.','',
      'Added tests: `tests/rag/test_reranking.py`, `test_reranking_security.py`, `test_reranking_metrics.py`. Added fixture: `fixtures/rag/reranking_eval/stage3f_v1.json`. Added documentation: this report, `stage3f_architecture.md`, `stage3f_dangerous_neighbors.md`. Added model cache: `models/stage3f/` only.','',
      'Added results under `results/stage3f/`: `preexisting_manifest.json`, `models.lock.json`, `environment.txt`, saved embeddings/query vectors/candidate sets, identity/MiniLM/TinyBERT full outputs and frozen-track comparisons, historical replay, independent replay, regression/test/demo logs, `validation.json`, resource probes, scheduler logs/accounting, closed-database archive, `failure_analysis.json`, `regressions.json`, `selected_config.json`, and file inventory/hash manifest. Per-query outputs include all traceability and scoring configuration.','',
      '## 17. Reproduction and limitations','',
      'Use the existing project `.venv` and Slurm scripts documented in [architecture](stage3f_architecture.md). One-time model preparation refuses to repin an existing lock. Evaluation and final-check scripts never write earlier-stage results. Archive current Stage 3F outputs before an intentional new run; do not replace the model lock or old-stage artifacts. `python -B -m rag.reranking.report` regenerates analysis from saved results without model inference.','',
      'Limitations: 33 authored synthetic needs, no independent annotator or held-out production sample; partial retrieval coverage of declared dangerous pairs; correlated duplicate/crowded-source evidence; short inputs only despite overflow checks; English MS MARCO-trained models with domain/action failures; no GPU comparison, long-document aggregation or serving concurrency benchmark. Trust cannot be inferred from identical text. No rule was fitted to individual expected answers, no model was trained, and no support threshold was introduced.','',
      '## 18. Stop condition','',
      '**Stage 3F is complete. Stop here.** Recommended default remains semantic retrieval (internal 20, output 5, exact grouping on, no expansion/caps), followed by identity reranking and five preserved evidence groups. Learned adapters remain available for explicit experimentation. No Stage 3G Qwen evidence judgment, support classification, RAG generation, QLoRA, fine-tuning, browser automation, applications, recruiter search or outreach was started.','']
    (ROOT/'docs/stage3f_report.md').write_text('\n'.join(text)+'\n')
    # Final additions inventory excludes the asset cache's duplicate blob/snapshot paths.
    files=[]
    for folder in (ROOT/'rag/reranking',ROOT/'fixtures/rag/reranking_eval',OUT):
        files.extend(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in ('artifact_manifest.json','files_created.json'))
    files.extend((ROOT/'tests/rag').glob('test_reranking*.py'))
    files.extend((ROOT/'docs').glob('stage3f*.md'))
    from .prepare import sha
    manifest={str(p.relative_to(ROOT)):sha(p) for p in sorted(set(files))}
    (OUT/'artifact_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (OUT/'files_created.json').write_text(json.dumps(sorted(manifest),indent=2)+'\n')
    print('Report generated; selected identity, candidate/output budgets 5/5.')

if __name__=='__main__': main()
