"""Additive task-coverage holdouts authored before final teacher targets.
No training, model calls, target access or modification of previous catalogs.
"""
import json, hashlib
from pathlib import Path
from .scenarios import action, family, req, build_record, digest, SEED
VERSION='stage4c0-heldout-coverage-v1'
RATIONALE='Preregistered input-coverage audit: validation lacked job analysis, semantic/personal application answers, missing-information and outreach; test lacked selection, cover letters and outreach. This expansion addresses task coverage, not observed model performance.'


def catalog():
 return [
 family('h_geospatial_service','Backend / ML Platform Engineer','mid_level','mixed','coastal mapping','tile inference queue',[
 action('Built a Python queue worker that ran shoreline-segmentation inference on submitted map tiles.','built',['Python','inference']),
 action('Implemented PostgreSQL records that linked each tile to its model version and processing status.','implemented',['PostgreSQL']),
 action('Deployed the worker with Docker on Azure.','deployed',['Docker','Azure']),
 action('Evaluated failed tile jobs with coastal analysts and documented invalid coordinate inputs.','evaluated',['evaluation'])],
 [req('Required: build asynchronous inference workflows.',0),req('Required: operate these workflows on AWS.'),req('Preferred: model-version traceability.',1,'preferred')],split='validation',style='heldout_geospatial_service_request',question='Describe a model-serving workflow you built and how you handled failed requests.'),
 family('h_embedded_project','Machine Learning Engineer','student_new_graduate','moderate','embedded acoustics','acoustic event prototype',[
 action('Trained a TensorFlow acoustic-event classifier in a graduate embedded-systems project.','trained',['TensorFlow'],event='project'),
 action('Evaluated false alarms on recordings collected in rooms excluded from training.','evaluated',['evaluation'],event='project'),
 action('Used Python to prepare the audio features; the model was not deployed to embedded hardware.','used',['Python'],event='project')],
 [req('Required: evaluate acoustic classifiers.',1),req('Preferred: deployment to embedded devices.',None,'preferred')],split='validation',style='heldout_embedded_recruitment_card',question='Are you authorized to work in the advertised country without employer sponsorship?',notes=['eligibility_absent','preference_absent']),
 family('h_validation_lab','Research Engineer','senior','strong','scientific instrumentation','instrument validation',[
 action('Designed a Python validation harness for instrument-derived regression models.','designed',['Python','evaluation']),
 action('Operated scheduled validation runs that compared model outputs with instrument calibration records.','operated',['evaluation']),
 action('Collaborated with instrument scientists to classify discrepancies before releasing evaluation reports.','collaborated',[]),
 action('Built SQL reconciliation checks in a prior laboratory software role.','built',['SQL'],event='prior'),
 action('Used Flask for an unrelated personal reading-list project.','used',['Flask'],event='project')],
 [req('Required: design reproducible scientific validation tools.',0),req('Required: collaborate on instrument-calibration review.',2),req('Preferred: historical data reconciliation.',3,'preferred')],split='validation',style='heldout_instrument_team_brief'),
 family('h_trial_analytics','Data Scientist','early_career','moderate','transport operations','schedule trial analysis',[
 action('Designed a Python analysis of a bus-schedule trial with separate weekday and weekend comparisons.','designed',['Python','evaluation']),
 action('Used SQL to align vehicle-arrival records with the correct trial schedule.','used',['SQL']),
 action('Collaborated with transit planners to explain why holiday observations were excluded from the comparison.','collaborated',[]),
 action('Built a TensorFlow image classifier in an unrelated personal project.','built',['TensorFlow'],event='project')],
 [req('Required: analyze operational trials using Python and SQL.',[0,1]),req('Preferred: causal identification expertise.',None,'preferred')],split='test',style='heldout_transport_problem_memo'),
 family('h_accessible_forms','NLP Engineer','entry_level','mixed','accessible public services','form-language assistant',[
 action('Implemented a Python tool that flagged complex phrases in public-service forms for editor review.','implemented',['Python']),
 action('Evaluated false-positive phrase flags with accessibility editors.','evaluated',['evaluation']),
 action('Used a transformer model to propose alternate phrases without automatically publishing them.','used',[]),
 action('Built a SQL record of accepted and rejected editorial suggestions.','built',['SQL'])],
 [req('Required: build human-reviewed language tools.',0),req('Required: fine-tune multilingual QLoRA adapters.'),req('Preferred: accessibility evaluation.',1,'preferred')],split='test',style='heldout_accessibility_screening_letter')]


def job_text(f):
 # These are independently authored, substantive styles—not family IDs appended to a shared template name.
 r=[x['text'] for x in f['reqs']]
 if f['key']=='h_geospatial_service':
  return ('Platform engineering request\nA coastal mapping unit needs a Backend / ML Platform Engineer for a tile-processing service. '
   'Responsibility: keep asynchronous inference jobs traceable when map inputs fail.\nSelection conditions:\n'
   + '\n'.join(r)+'\nLocation: hybrid in the supplied US office. A cloud provider is specified only where named in a condition.')
 if f['key']=='h_embedded_project':
  return ('Graduate recruitment card: Machine Learning Engineer\nProduct area: acoustic event prototypes. '
   'Responsibility: evaluate classifier behavior before hardware deployment.\n'
   +r[0]+'\n'+r[1]+'\nLocation: United States; office attendance and sponsorship policy are not specified. '
   'The application separately asks about authorization and relocation; the posting does not establish an applicant’s answers.')
 if f['key']=='h_validation_lab':
  return ('Instrument team briefing\nResearch Engineer — Synthetic Instrument Validation Lab\n'
   'The team reviews differences between model predictions and calibration records. Its next engineer will maintain reproducible evidence for those reviews.\n'
   +'\n'.join(r)+'\nWorking arrangement: on-site at the supplied laboratory. '
   'No claim about who makes hiring decisions is included in this briefing.')
 if f['key']=='h_trial_analytics':
  return ('Operational question: did a schedule trial change service reliability?\n'
   'Position: Data Scientist, Synthetic Schedule Analysis Lab. Responsibility: explain a trial comparison clearly enough for transit planners to review.\n'
   +r[0]+'\n'+r[1]+'\nRemote work is available within the United States. The post gives no minimum number of years and no degree requirement.')
 return ('Screening letter for an NLP Engineer opening\nSynthetic Accessible Forms Lab works on editor-reviewed form language. '
  'Responsibility: support reviewers without treating model suggestions as publication approval.\n'
  +'\n'.join(r)+'\nWork arrangement: hybrid; the exact office schedule remains unspecified. '
  'The phrase “cloud familiarity” appears in background context only and is not marked as a qualification.')


def generate_heldout(seed=SEED):
 schedules=[['ANALYZE_JOB','ANSWER_APPLICATION_QUESTION'],['ANSWER_APPLICATION_QUESTION','IDENTIFY_MISSING_INFORMATION'],['DRAFT_OUTREACH','SELECT_RESUME_CONTENT'],['SELECT_RESUME_CONTENT','GENERATE_COVER_LETTER'],['DRAFT_OUTREACH','ANALYZE_JOB']]
 out=[]
 for f,tasks in zip(catalog(),schedules):
  for task in tasks:
   record=build_record(f,task,400+len(out),seed)
   inp=record['input'];oracle=record['oracle'];request=inp['request']
   inp['job']['text']=job_text(f)
   if f['key']=='h_geospatial_service' and task=='ANSWER_APPLICATION_QUESTION':
    request.update(question=f['question'],question_type='BEHAVIORAL',max_words=100,max_characters=750)
    oracle.update(expected_status='COMPLETE',desired_field=None)
   if f['key']=='h_embedded_project':
    if task=='ANSWER_APPLICATION_QUESTION':
     request.update(question=f['question'],question_type='ELIGIBILITY',max_words=50,max_characters=400)
     oracle.update(expected_status='USER_INPUT_REQUIRED',desired_field='work_authorization_and_sponsorship')
    else:
     request.update(question='Would you relocate for this role, and what is your earliest start date?',question_type='PREFERENCE')
     oracle.update(expected_status='USER_INPUT_REQUIRED',desired_field='relocation_preference_and_availability')
   if task=='SELECT_RESUME_CONTENT':
    request['instruction']+=' Prioritize no more than two substantive experience or project events; preserve education if useful. Omit the unrelated personal project unless it fills a stated requirement.'
   if task=='DRAFT_OUTREACH':
    request.update(max_words=90,max_characters=750)
   record['metadata'].update(generator_version=VERSION,coverage_expansion_reason=RATIONALE,style_template=f['style'],ground_truth_sha256=digest({'profile':inp['profile'],'rag':inp['rag'],'oracle':oracle}))
   out.append(record)
 return out


def write_heldout(root):
 from .contracts import validate_input
 from .grounding import validate_scenario
 root=Path(root);root.mkdir(parents=True,exist_ok=True);rows=generate_heldout()
 for r in rows:
  errors=validate_input(r['input'])+validate_scenario(r)
  for requirement in r['oracle']['expected_job_requirements']:
   if requirement['source_quote'] not in r['input']['job']['text']:errors.append('SOURCE_QUOTE_NOT_PRESENT')
  if errors:raise ValueError((r['scenario_id'],errors))
 payloads={'heldout-coverage-v1.jsonl':rows,'heldout-coverage-v1-inputs.jsonl':[{'scenario_id':r['scenario_id'],'input':r['input']} for r in rows]}
 for name,payload in payloads.items():
  path=root/name;text=''.join(json.dumps(r,sort_keys=True,ensure_ascii=False,separators=(',',':'))+'\n' for r in payload)
  if path.exists() and path.read_text()!=text:raise ValueError('refusing to overwrite frozen '+name)
  if not path.exists():path.write_text(text)
 manifest={'version':VERSION,'authored_on':'2026-09-29','status':'frozen_inputs_before_final_target_generation','rationale':RATIONALE,'records':len(rows),'validation':6,'test':4,'new_families':5,'teacher_outputs_accessed':False,'pilot_outputs_accessed':False,'challenge_targets_accessed':False,'original_catalogs_modified':False,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'factory_dependency_sha256':hashlib.sha256(Path(__file__).with_name('scenarios.py').read_bytes()).hexdigest(),'sha256':{name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in payloads},'evaluation_limitation':'Task coverage is established, not statistically precise per-task performance. One or a few examples per held-out function give wide uncertainty; report failures individually and do not infer reliable population accuracy.'}
 text=json.dumps(manifest,indent=2)+'\n';path=root/'heldout-manifest.v1.json'
 if path.exists() and path.read_text()!=text:raise ValueError('refusing to mutate heldout manifest')
 if not path.exists():path.write_text(text)
 return manifest

if __name__=='__main__':
 import sys
 print(json.dumps(write_heldout(sys.argv[1] if len(sys.argv)>1 else 'scenarios'),indent=2))
