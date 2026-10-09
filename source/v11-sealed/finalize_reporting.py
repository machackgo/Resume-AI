import json,hashlib,datetime,collections
from pathlib import Path
D=Path(__file__).resolve().parent
load=lambda n:json.loads((D/n).read_text())
def save(n,v):(D/n).write_text(json.dumps(v,indent=2)+'\n')
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
log=(D/'test-results.log').read_text().splitlines()
assert sum(x.endswith(' ... ok') for x in log)==532
assert sum(' ... skipped ' in x for x in log)==46
assert sum(x.startswith('setUpClass ') and ' ... skipped ' in x for x in log)==2
reg=load('final-regression-accounting.json');reg.update(passed=534,tests_accounted=584,test_executions=582,skip_events=46,individual_test_skips=44,class_setup_skips=2)
reg['base_suite']['passed']=532
reg['accounting_correction']='Verbose log contains 532 successful tests. unittest testsRun excludes two class setup skip events; subtracting all 46 skips from testsRun undercounted passes by two. Raw results and original CPU gate preserved.'
save('final-regression-accounting.json',reg)
save('regression-accounting-correction.json',dict(time_utc=now,raw_results_preserved=True,source='test-results.log',base_passed=532,additional_passed=2,failed=1,protected_blocked=3,individual_skips=44,class_setup_skip_events=2,test_executions=582,outcome_entries=584,explanation=reg['accounting_correction']))
r=D/'REPRODUCE.txt';r.write_text(r.read_text().replace('532 PASSED, 1 FAILED','534 PASSED, 1 FAILED')+'\nFinal accounting: 534 PASSED, 1 FAILED, 46 SKIPPED events (44 tests + 2 class setup), 3 PROTECTED-BLOCKED. 582 test executions; 584 outcome entries. See regression-accounting-correction.json.\nReporting only: python3 finalize_reporting.py\nSeal once after review: python3 seal_package.py\nNo new inference is authorized by the failed final regression gate.\n')
m=load('full-v1-acceptance-metrics.json');dec=load('full-v1-independent-decisions.json');profiles=load('independent-eligibility-profiles.json')['unique_claim_profiles']
assert len(dec)==30 and len(profiles)==10
rows=[]
for case,d in sorted(dec.items()):
 assert d['raw_sha256']==next(x['raw_sha256'] for x in m['cases'] if x['case']==case)
 for c in d['claims']:
  p=profiles[c['claim_id']];assert len(p['dimensions'])==8 and p['source_id']==c['source_id'] and p['span']==c['span']
  rows.append(dict(case=case,raw_sha256=d['raw_sha256'],**c,text=p['text'],eligibility_dimensions=p['dimensions'],content_eligible=c['content_class'] in ['STRONG ACHIEVEMENT','VALID NARROW BULLET'],combined_license_acceptable=c['factual_class']=='SUPPORTED' and c['relationship_class']!='OVERSTATED_SPECIFIC_REQUIREMENT'))
assert len(rows)==23
save('independent-resume-worthiness-audit.json',dict(review='Independent source-based profiles joined to independently audited claim occurrences; no model eligibility labels used as authority.',claims=rows,content_counts=m['dimensions']['content_class'],note='Content worthiness alone does not authorize promotion. Four factual-scope failures and one specific relationship failure remain.'))
save('independent-multidimensional-audit-final.json',dict(cases=30,claims=23,unique_claim_ids=10,dimensions=m['dimensions'],occurrences=rows,case_decisions='full-v1-independent-decisions.json',complete=True,passed=False))
roots=load('full-v1-new-root-cause-matrix.json');roots['status']='FINAL_VALIDATION_FAILED';save('full-v1-new-root-cause-matrix.json',roots);save('remaining-root-cause-blockers.json',roots)
save('before-after-metrics.json',dict(baseline=dict(package='resume-ai-final-remediation-20261007',supported=20,partially_supported=0,unsupported=0,contradicted=1,verdict='C'),current=dict(supported=19,partially_supported=4,unsupported=0,contradicted=0,cross_project_contamination=0,generic_setup_promoted=0,broad_capability_incompatible=0,specific_requirement_overlicensed=1,cases_passed=23,cases_failed=7,verdict='C'),note='Claim occurrence denominators differ: baseline 21, current 23. Zero contradictions is insufficient for readiness.'))
save('model-decision.json',dict(verdict='C — NOT READY',model_reasoning_bottleneck_demonstrated=False,qlora_retraining_justified=False,adapter_promotion_authorized=False,agent_development_authorized=False,remaining_failure_classes=['FALLBACK','LICENSING','IDENTITY','CONTENT ELIGIBILITY','RETRIEVAL'],basis='Deterministic discovery veto and incomplete semantic/scope contracts remain. Correct independently reviewed context has not isolated a model reasoning bottleneck.'))
save('no-regression-verification.json',dict(regression=reg,mechanical_failures=0,controls_passed=40,controls_failed=0,canonical_context_span_checks=2684,maximum_input_tokens=8191,input_limit=8192,embedding_failures=0,evidence_id_collision_failures=0,candidate_isolation_failures=0,contradiction_blocking_failures=0,protected_runtime_open_successes=0,protected_cpu_checks_denied=3,protected_metadata_files_unchanged=894,frozen_artifacts_unchanged=True,benchmark_inputs_unchanged=True,application_changes_after_reconciliation=0,evidence=['full-v1-acceptance-metrics.json','integrity-local-final.json','integrity-remote-final.json','checkpoint-integrity-final.json','integrity-remote-history-final.json','protected-metadata-final.json','application-continuation-integrity.json','input-integrity.json'],semantic_gate_passed=False,note='Mechanical integrity is healthy. Semantic no-regression is not globally passed: see remaining-root-cause-blockers.json. Legacy skipped checks were not counted as passed.'))
state=load('WORK_STATE.json');state.update(state='VALIDATION_COMPLETE_NOT_READY',verdict='C — NOT READY / NO-GO FOR AGENT DEVELOPMENT',remaining=[],remaining_cases=[],active_jobs=[],active_runs=[],completed_jobs=[2351800,2351801,2351871,2351872,2351873],independent_full_passes=[k for k,v in dec.items() if v['case_passed']],independent_full_failures=[k for k,v in dec.items() if not v['case_passed']],final_regression='534 PASSED, 1 FAILED, 46 SKIPPED events, 3 PROTECTED-BLOCKED',cpu_gate='Original passing pre-inference gate preserved; corrected base accounting 532 passed, 0 failed, 46 skip events, 3 protected-blocked.',checkpoint_time_utc=now,remote_final_package_verified='See external post-seal receipt specified in archive-destination.json',completed_full_remainder_cases=[x['case'] for x in m['cases'] if x['case'] not in state['independent_historical_passes']])
state['completed']+=['all 30 unchanged acceptance/stress outputs reconciled and independently audited','all five Slurm jobs completed 0:0','final integrity verification passed','final regression exposed one deterministic licensing failure; no further GPU request']
save('WORK_STATE.json',state);save('full-audit-progress.json',dict(complete=True,remaining=[],cases=30,passed=23,failed=7,final_audit='independent-multidimensional-audit-final.json'))
save('final-verification.json',dict(time_utc=now,verdict='C — NOT READY',agent_gate='NO-GO FOR AGENT DEVELOPMENT',integrity_passed=True,independent_audit_complete=True,acceptance_passed=False,regression_passed=False,cases=30,claims=23,remaining_validation_steps=[],remaining_root_cause_blockers=4,archive_verification='Post-seal external receipt: '+load('archive-destination.json')['remote_receipt_local']))
report='''C — NOT READY
NO-GO FOR AGENT DEVELOPMENT

The unchanged full-v7 acceptance suite is complete: 20 original and 10 stress cases.
Eight valid fresh historical outputs were reused; only 22 unfinished cases required
new approved BASE-Qwen inference. Job 2351801 and S07 were reconciled after the
network outage without restarting completed work. All five Slurm jobs completed
0:0. Application source, approved BASE configuration and benchmark inputs remained
identical across this cohort. No adapter was loaded, trained or promoted.

INDEPENDENT FINAL RESULTS
23 cases passed; 7 failed: J02, J04, J07, J11, J13, J19, S04.
23 substantive claim occurrences, 10 unique claim IDs:
SUPPORTED 19; PARTIALLY SUPPORTED 4; UNSUPPORTED 0; CONTRADICTED 0.
STRONG ACHIEVEMENT 7; VALID NARROW BULLET 16; generic setup promoted 0.
CORRECT PROJECT/EVENT 23; CROSS-PROJECT CONTAMINATION 0.
Broad capability COMPATIBLE 23; INCOMPATIBLE 0.
One detailed requirement license is invalid despite broad capability compatibility.
Four factual bundles remain only partially supported. Content worthiness alone
cannot authorize those claims. The strict semantic acceptance gate has not passed.

REMAINING ROOT-CAUSE BLOCKERS
1. FALLBACK / LICENSING: retrieval-discovery membership vetoes an otherwise valid
   evidence/requirement pair before independent licensing; fallback inherits the
   bookkeeping rejection. J11 emits no resume despite valid architecture evidence.
   Evidence: new-fallback-forensic-J11.json and the failed general regression in
   discovery-license-regression-results.json. Fix the lifecycle distinction between
   discovery metadata and independent semantic rejection, preserving all safety gates.
2. LICENSING: generic monitoring evidence licenses specific request counters and
   latency predicates in J02 without exact packed supporting anchors. Broad
   OBSERVABILITY typing does not establish detailed entailment. The final quote is
   supported but the claimed requirement coverage is not. Evidence:
   new-specificity-forensic-J02.json and specificity-contract-diagnostics.json.
3. IDENTITY / LICENSING: explicit project aliases and service/version evidence are
   not reconciled in bounded review context. Four final occurrences in J07, J13,
   J19 and S04 retain unresolved dashboard/model/deployment scope. Related future-
   work and model-identity evidence requires narrowing or omission. These are
   PARTIALLY SUPPORTED, not presumed contradictions across unknown versions.
   Evidence: qa-source-scope-review.json and the per-case independent audits.
4. CONTENT ELIGIBILITY / RETRIEVAL: J04 recovers no usable standalone achievement
   from relevant implementation artifacts. Withholding generic setup and unsupported
   pgvector claims is correct, but an entirely empty resume is not successful
   positive-evidence recovery. Evidence: independent-full-v1-J04-audit.json.

SAFE OMISSION AND HISTORICAL GATE
All eight historical cases passed independently; the general classes above still
reproduce elsewhere. Runtime COMPLETE 22 / FAILED 8 includes six appropriate
unsupported-input refusals and two unusable positive-evidence resumes (J04/J11).
Pipeline coverage: 170 omitted/unsupported requirement occurrences, 28 partially
supported and 0 fully supported; occurrence counts include repeated background
requirements and are not an assertion that all omitted capabilities lack corpus
support. J14 duplicate supported wording is a minor presentation issue only.

REGRESSION AND INTEGRITY
PASSED 534; FAILED 1; SKIPPED 46 events; PROTECTED-BLOCKED 3.
There were 582 test executions. Skips comprise 44 tests and two class-setup events;
584 outcome entries therefore must not be mistaken for 584 test executions.
The inherited summary subtracted the class skips twice, undercounting passes by two.
Raw logs and the original pre-inference CPU gate remain preserved; see
regression-accounting-correction.json. The new failed regression is a real blocker.
All 40 runtime controls passed. Mechanical failures 0; canonical context/source-span
checks 2684. Maximum input 8191/8192 tokens; no length termination. Embedding,
evidence-ID integrity, provenance, candidate isolation and contradiction controls
remained healthy. This does not erase the semantic licensing/scope failures above.
Frozen local 338 and remote 749 entries unchanged. Prior evidence packages and both
sealed archives unchanged; 36 prior remote full-v7 outputs unchanged. Protected
metadata 894 files unchanged; metadata was inspected without reading protected
content, and runtime guards separately enforced the boundary. Benchmark inputs
unchanged. No application modifications followed outage reconciliation.

MODEL DECISION
QLoRA retraining is not justified. No model reasoning bottleneck has been isolated
under fully correct semantic inputs/context. Adapter promotion and agent development
are not authorized. No agent was built.

ARTIFACTS AND REPRODUCTION
Original forensic chains and failure_root_cause_matrix.json, application.patch,
changed-file-manifest.json, semantic-capability-taxonomy.json, five shards of raw
outputs/model traces, extracted licensing/fallback/decomposition traces, full-v1
cohort manifest, independent multidimensional and eight-dimension eligibility audits,
regression results, before/after metrics and integrity receipts are retained here.
REPRODUCE.txt records commands. SHA256SUMS.json covers the final package files.
The new final ZIP and SHA-256 metadata are retained beside this directory and copied
to the exclusive Turing destination recorded in archive-destination.json. Because an
archive cannot contain its own final transfer receipt without changing its hash,
post-seal remote verification is recorded in the external receipt named there.
'''
(D/'FINAL_REPORT.txt').write_text(report)
old=D.parent/'resume-ai-semantic-contracts-20261008';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
changes=[]
for p in sorted(D.iterdir()):
 if p.is_file() and (p.suffix in ['.py','.sbatch'] or p.name in ['REPRODUCE.txt','ssh-transport.json']):
  before=sha(old/p.name) if (old/p.name).is_file() else None
  if before!=sha(p):changes.append(dict(path=p.name,before_sha256=before,after_sha256=sha(p)))
save('continuation-harness-changes.json',dict(application_changed=False,changes=changes,scope='Transport, reconciliation, independent audit, general regression and final packaging helpers only; application v11 unchanged.'))
print(json.dumps(dict(cases=len(dec),claims=len(rows),regression=reg,verdict='C'),indent=2))
